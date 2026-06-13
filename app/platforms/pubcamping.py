#/app/platforms/pubcamping.py
import httpx
import asyncio
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime, timedelta

from .base import CampingMonitor
from core.notifier import notifier
from core.websocket_manager import ws_manager
from core.termination_handler import handle_monitoring_stop
from core.ua_generator import UAGenerator

# 로거 설정
logger = logging.getLogger("camping.pubcamping")

class PubcampingMonitor(CampingMonitor): 
    def __init__(self):
        super().__init__()
        self.client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
        self.execution_count = 0  # 실행 횟수 카운터

    async def _check_single_group(self, client, camp_id, target_group, start_date, end_date, stay_days, headers):

        logger.info(f"[*] [pubcamping] 구역 감시 시작 ID: {target_group} 요청일: ({start_date}, {stay_days}박)")

        """
        [내부 함수] 단일 구역(Group)의 예약 가능 여부를 체크합니다.
        자바의 CompletableFuture 내에서 실행되는 Task와 유사합니다.
        """
        url = f"https://gwgs.pubcamping.kr/{camp_id}/productSelectJson.do"
        data = {
            "stay_cnt" : stay_days,
            "check_in" : start_date,
            "check_out" : end_date,
            "room_area_no" : target_group       
        }

        try:
            # 타임아웃을 넉넉히 주어 네트워크 지연에 대비
            response = await client.post(url, data=data, headers=headers, timeout=10.0)
            if response.status_code != 200:
                return None

            result = response.json()
            pin_list = result.get("RESULT_DATA", [])
            found_sites = []
            for pin in pin_list:
                room_area_no = pin.get("ROOM_AREA_NO")
                stay_cnt = pin.get("STAY_CNT")
                wait_state = pin.get("WAIT_STATE")
                room_no = pin.get("ROOM_NO")
                room_name = pin.get("ROOM_NAME")

                # 예약 가능한 상태인지 체크 (예: 예약수가 0이고 사용가능 여부가 Y인 경우)
                if stay_cnt == 1 and wait_state == 'Y':
                    found_sites.append({
                        "site_name": room_name,
                        "room_name": room_name,
                        "item_no": room_no,
                        "room_area_no": room_area_no,
                    })      

            return found_sites
        except Exception as e:
            logger.error(f"[!] 구역 {target_group} 파싱 중 오류: {str(e)}")
        
        return None

    async def check_availability(self, params: dict):
        """
        [메인 로직] 모든 대상 구역을 병렬로 감시합니다.
        """
        self.execution_count += 1
        
        camp_id = params.get("camp_id")
        campsite_name = params.get("campsiteName", "이름 없음")
        req_date = params.get("date")
        stay_days = int(params.get("stay_day", "1"))
        uuid = params.get("watchUuid")

        target_site_groups = [str(code) for code in params.get("site_group_codes", [])]
        target_site_codes = [str(code) for code in params.get("site_codes", [])]

        next_date = datetime.strptime(req_date, "%Y-%m-%d") + timedelta(days=stay_days) 
        start_dt = req_date.replace("-", ""); 
        end_dt = next_date.strftime("%Y%m%d")

        # UI 업데이트 (실행 횟수 전송)
        await ws_manager.broadcast({
            "messageType": "monitor", 
            "data": {"uuid": uuid, "count": self.execution_count}
        })

        logger.info(f"[*] [pubcamping] 감시 시작: {campsite_name} ({req_date}, {stay_days}박)")

        # 랜덤 헤더 생성
        current_headers = UAGenerator.get_headers({
            "host": "gwgs.pubcamping.kr",
            "origin": "https://gwgs.pubcamping.kr",
            "Referer": f"https://gwgs.pubcamping.kr/{camp_id}/index?",
            "x-requested-with": "XMLHttpRequest"
        })

        # 비동기 클라이언트 생성 (커넥션 풀 재사용)
        # 1. 모든 구역에 대해 Task 생성 (Java의 Stream -> List<CompletableFuture>와 유사)
        tasks = [
            self._check_single_group(self.client, camp_id, group, start_dt, end_dt, stay_days, current_headers)
            for group in target_site_groups
        ]
        
        # 2. 모든 요청을 동시에 실행 및 결과 수집 (Parallel Execution)
        results = await asyncio.gather(*tasks)
        # 3. 결과 중 None(실패/빈자리 없음)을 제외하고 유효한 데이터만 추출
        #found_sites = [r for r in results if r is not None]

        # 2차원 리스트를 1차원으로 평탄화 (Flatten)
        found_sites = []
        for r in results:
            if r is not None and isinstance(r, list):
                found_sites.extend(r) # 리스트 안의 요소를 하나씩 추가


        # 4. 빈자리 발견 시 처리
        if found_sites:
            
            sites_string = ", ".join([s['site_name'] for s in found_sites])

            for site in found_sites:

                # 첫 번째 발견된 장소를 대표 링크로 사용
                link = f"https://mjhwang80.github.io/public_page/pubcamping_gateway.html?camp_id={camp_id}&room_area_no={site['room_area_no']}&stay_cnt={stay_days}&check_in={start_dt}&check_out={end_dt}&roomNoArr={site['item_no']}"
                #link = f"https://gwgs.pubcamping.kr/{camp_id}/reservation"
            

                # 텔레그램 메시지 구성
                msg = (
                    f"<b>[고성군 공공캠핑장] 빈자리 발견!</b>\n"
                    f"캠핑장: {campsite_name}\n"
                    f"날짜: {req_date} ({stay_days}박)\n"
                    f"구역: {sites_string}\n"
                    f"<a href='{link}'>👉 예약 페이지 바로가기</a>"
                )
                await notifier.send_message(msg)

                # 웹소켓 알림 전송 (브라우저 팝업용)
                await ws_manager.broadcast({
                    "messageType": "alert",
                    "data": {
                        "campseq": camp_id,
                        "res_dt": req_date,
                        "res_days": stay_days,
                        "link": link,
                        "list": found_sites
                    }
                })

                # 시스템 트레이 알림 (Windows 알림)
                try:
                    from main import tray_manager
                    if tray_manager:
                        tray_manager.notify(
                            "빈자리 발견!", 
                            f"[{campsite_name}] {sites_string} 자리가 났습니다."
                        )
                except: pass

                # 모니터링 종료 체크           
                from main import scheduler
                await handle_monitoring_stop(scheduler, ws_manager, params, found_sites)
            
                logger.info(f"[SUCCESS] {campsite_name} 빈자리 발견: {sites_string}")

                break # 1건만 찾고 멈춤

            return True

        return False

    async def close_client(self):
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            logger.info("[*] [Pubcamping] httpx AsyncClient 커넥션 풀을 안전하게 닫았습니다.")          