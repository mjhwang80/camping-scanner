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
logger = logging.getLogger("camping.camplink")

class CamplinkMonitor(CampingMonitor): 
    def __init__(self):
        super().__init__()
        self.execution_count = 0  # 실행 횟수 카운터

    async def _check_single_group(self, client, camp_id, target_group, req_date, stay_days, headers):

        logger.info(f"[*] [Camplink] 구역 감시 시작 ID: {target_group} 요청일: ({req_date}, {stay_days}박)")

        """
        [내부 함수] 단일 구역(Group)의 예약 가능 여부를 체크합니다.
        자바의 CompletableFuture 내에서 실행되는 Task와 유사합니다.
        """
        url = f"https://camplink.co.kr:444/index/0booking/order.php?camplink={camp_id}&no={target_group}&select={req_date}"
        
        try:
            # 타임아웃을 넉넉히 주어 네트워크 지연에 대비
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # 1. 예약 정보를 담고 있는 특정 p.explain 섹션 찾기
            explain_p = soup.select_one('p.explain:has(select[name="select"])')
            if not explain_p:
                return None
            
            # 2. 내부 테이블 추출
            target_table = explain_p.find("table")
            if not target_table:
                return None
            
            # 3. 행(tr) 순회하며 숙박 옵션 체크
            tbody = target_table.find("tbody")
            rows = tbody.find_all("tr") if tbody else target_table.find_all("tr")

            for row in rows:
                cols = row.find_all("td")
                if not cols: continue

                # stay[인덱스] 형태의 select 박스 존재 여부 확인
                stay_select = row.select_one('select[name^="stay["]')
                if stay_select:
                    # 사용자가 원하는 숙박 일수(value)가 옵션에 존재하는지 체크
                    stay_option = stay_select.find("option", attrs={"value": str(stay_days)})
                    if stay_option:
                        site_name = cols[0].get_text(strip=True)
                        return {
                            "site_name": site_name, 
                            "stay_days": stay_days, 
                            "site_group": target_group,
                            "link": url
                        }
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
        target_site_codes = [str(code) for code in params.get("site_codes", [])]

        # UI 업데이트 (실행 횟수 전송)
        await ws_manager.broadcast({
            "messageType": "monitor", 
            "data": {"uuid": uuid, "count": self.execution_count}
        })

        logger.info(f"[*] [Camplink] 감시 시작: {campsite_name} ({req_date}, {stay_days}박)")

        # 랜덤 헤더 생성
        current_headers = UAGenerator.get_headers({
            "Referer": f"https://camplink.co.kr/?camp={camp_id}"
        })

        # 비동기 클라이언트 생성 (커넥션 풀 재사용)
        async with httpx.AsyncClient(verify=False) as client:
            # 1. 모든 구역에 대해 Task 생성 (Java의 Stream -> List<CompletableFuture>와 유사)
            tasks = [
                self._check_single_group(client, camp_id, group, req_date, stay_days, current_headers)
                for group in target_site_codes
            ]
            
            # 2. 모든 요청을 동시에 실행 및 결과 수집 (Parallel Execution)
            results = await asyncio.gather(*tasks)

            # 3. 결과 중 None(실패/빈자리 없음)을 제외하고 유효한 데이터만 추출
            found_sites = [r for r in results if r is not None]

        # 4. 빈자리 발견 시 처리
        if found_sites:
            # 첫 번째 발견된 장소를 대표 링크로 사용
            main_link = found_sites[0]["link"]
            sites_string = ", ".join([s['site_name'] for s in found_sites])

            # 텔레그램 메시지 구성
            msg = (
                f"<b>[캠프링크] 빈자리 발견!</b>\n"
                f"캠핑장: {campsite_name}\n"
                f"날짜: {req_date} ({stay_days}박)\n"
                f"구역: {sites_string}\n"
                f"<a href='{main_link}'>👉 예약 페이지 바로가기</a>"
            )
            await notifier.send_message(msg)

            # 웹소켓 알림 전송 (브라우저 팝업용)
            await ws_manager.broadcast({
                "messageType": "alert",
                "data": {
                    "campseq": camp_id,
                    "res_dt": req_date,
                    "res_days": stay_days,
                    "link": main_link,
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

            # 감시 자동 종료 처리
            from main import scheduler
            await handle_monitoring_stop(scheduler, ws_manager, params, found_sites)
            
            logger.info(f"[SUCCESS] {campsite_name} 빈자리 발견: {sites_string}")
            return True

        return False