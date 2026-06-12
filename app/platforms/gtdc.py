#연곡해변캠핑장
#app/platforms/gtdc.py

from urllib import response

import httpx
import asyncio
from bs4 import BeautifulSoup
import re

from datetime import datetime, timedelta
import pprint 
from .base import CampingMonitor
from core.notifier import notifier
from core.websocket_manager import ws_manager
from core.termination_handler import handle_monitoring_stop
from core.ua_generator import UAGenerator

# 로거 설정
from core.logger import logger as central_logger
import logging
logger = logging.getLogger("camping.gtdc")

class GtdcMonitor(CampingMonitor): 
    def __init__(self):
        super().__init__()
        self.execution_count = 0  # 실행 횟수 카운터

        self.client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
        self.cookies_initialized = False

    async def _check_single_group(self, client, camp_id, target_group, start_date, end_date, stay_days, headers):

        logger.info(f"[*] [연곡해변캠핑장] 구역 감시 시작 ID: {target_group} 요청일: ({start_date}, {stay_days}박)")

        parsed_start_date = datetime.strptime(start_date, "%Y%m%d") 
        formatted_yy_mm_dd = parsed_start_date.strftime("%y-%m-%d")
        formatted_yyyy_mm = parsed_start_date.strftime("%Y-%m")

        """
        [내부 함수] 단일 구역(Group)의 예약 가능 여부를 체크합니다.
        자바의 CompletableFuture 내에서 실행되는 Task와 유사합니다.
        """
        url = f"https://camping.gtdc.or.kr/dzSmart/plugins/Reserv/procedure/reserv-02-zone.json"
        data = {
            "actMode" : 'zone_state',
            "areadate" : f'{target_group}-{formatted_yy_mm_dd}-{stay_days}',
            "base" : '',
            "isSets" : 'true',       
            "isAges" : 'true',       
            "isZones" : 'true',       
            "isRooms" : '',       
        }

        # stay_days(박수)만큼 반복문 실행 (예: 2박이면 i는 0, 1)
        start_date_obj = datetime.strptime(start_date, "%Y%m%d")
        for i in range(stay_days):
            # i일만큼 증가시킨 날짜 계산
            current_date = start_date_obj + timedelta(days=i)
            # 날짜를 YYYYMMDD 형태로 포맷팅
            date_str = current_date.strftime("%Y%m%d")
            
            # 딕셔너리에 동적으로 Key/Value 쌍 추가
            #data[f"isDates[{date_str}][type]"] = 'Usual'
            #data[f"isDates[{date_str}][seas]"] = 'normal'


        tmonth=formatted_yyyy_mm
        tarea=f"{target_group}-{formatted_yy_mm_dd}-{stay_days}"
  

        now = datetime.now()
        formatted_time = now.strftime("%Y%m%d%H%M%S")
        req_headers = headers.copy()
        req_headers["Referer"] = f"https://camping.gtdc.or.kr/pub/reserv.do?tmonth={tmonth}&sp=z&tarea={tarea}"
        req_headers["Author"] = formatted_time

        #pprint.pprint(data)  # 디버깅용 데이터 출력

        try:
            # 타임아웃을 넉넉히 주어 네트워크 지연에 대비
            response = await client.post(url, data=data, headers=req_headers, timeout=10.0)           

            if response.status_code != 200:
                return None

            result = response.json()
            #print(result)  # 디버깅용 전체 응답 데이터 출력

            block_list = result.get("block", [])
            rooms_data = result.get("rooms") or {}

            # block_list를 순회하며 일치하는 rooms_data의 키를 삭제
            for b_no in block_list:
                str_key = str(b_no)  # 숫자형 76 -> 문자열 "76" 변환
                if str_key in rooms_data:
                    del rooms_data[str_key]  # 딕셔너리에서 해당 방 정보 완전 제거
                    #print(f"[삭제 완료] 블록 지정된 방 번호 '{str_key}' 가 rooms_data에서 제거되었습니다.")

            found_sites = []
            for room_no, room_info in rooms_data.items():
                #pprint.pprint(room_info)
                sort = room_info.get("sort")
                tit = room_info.get("tit")
                type = room_info.get("type")               

                # 예약 가능한 상태인지 체크 (예: 예약수가 0이고 사용가능 여부가 Y인 경우)
                found_sites.append({
                    "site_name": tit,
                    "room_name": tit,
                    "item_no": room_no,
                    "room_no": room_no,
                    "type": type,
                    "sort": sort,
                    "room_area_no": target_group,
                    "tmonth": tmonth,
                    "tarea": tarea,
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

        logger.info(f"[*] [연곡솔향기] 감시 시작: {campsite_name} ({req_date}, {stay_days}박)")

        if not self.cookies_initialized:
            await self.get_browser_cookies(camp_id)

        current_headers = UAGenerator.get_headers({
            "Host": "camping.gtdc.or.kr",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",            
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://camping.gtdc.or.kr",         
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        })

        found_sites = []

        tasks = [
            self._check_single_group(self.client, camp_id, group, start_dt, end_dt, stay_days, current_headers)
            for group in target_site_groups
        ]

        # 2. 모든 요청을 동시에 실행 및 결과 수집 (Parallel Execution)
        results = await asyncio.gather(*tasks)

        # 3. 결과 중 None(실패/빈자리 없음)을 제외하고 유효한 데이터만 추출
        raw_results = [r for r in results if r is not None]
        
        # 2차원 리스트를 1차원 리스트로 평탄화(Flattening)
        for site_list in raw_results:
            found_sites.extend(site_list)

        logger.info(f"{campsite_name} 캠핑장 빈자리 {len(found_sites)}개 발견")
        

        # 4. 빈자리 발견 시 처리
        if found_sites:

            sites_string = ", ".join([s['site_name'] for s in found_sites])
            
            for site in found_sites:
                item_no = site.get("item_no")
                room_area_no = site.get("room_area_no")
                tmonth = site.get("tmonth")
                tarea = site.get("tarea")
                
                if str(item_no) in target_site_codes:
                    
                    link = f"https://camping.gtdc.or.kr/pub/reserv.do?tmonth={tmonth}&sp=z&tarea={tarea}"

                    # 텔레그램 메시지 구성
                    msg = (
                        f"<b>[연곡해변캠핑장] 빈자리 발견!</b>\n"
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

                    # 감시 자동 종료 처리

                    from main import scheduler
                    await handle_monitoring_stop(scheduler, ws_manager, params, found_sites)
                    
                    logger.info(f"[SUCCESS] {campsite_name} 빈자리 발견: {sites_string}")

                    break
            
            return True

        return False  # 마지막 오타 부분 수정 완료

    async def close_client(self):
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            logger.info("[*] [연곡솔향기] httpx AsyncClient 커넥션 풀을 안전하게 닫았습니다.")

    async def get_browser_cookies(self, camp_id:str):

            url = f"https://camping.gtdc.or.kr/"

            logger.info(f"[*] {url}에서 쿠키를 새로 받습니다.")

            current_headers = UAGenerator.get_headers({
                "Host": "camping.gtdc.or.kr",    
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"     
            })             
                
            response = await self.client.get(url, headers=current_headers)

            data = {"type":"event", "payload": {
                "website" : "792c3c37-2f9f-4776-a2bb-f0516bed18c3",
                "screen" : '1707x1068',
                "language" : 'ko-KR',
                "title" : '',
                "url" : 'https://camping.gtdc.or.kr/pub/reserv.do',
                "referrer" : 'https://camping.gtdc.or.kr'}
            }
            #response = await self.client.post(url, data=data,headers=current_headers)

            self.cookies_initialized = True
            # 2. 서버가 보낸 쿠키 확인
            print(f"[*] 획득한 쿠키: {self.client.cookies}")    