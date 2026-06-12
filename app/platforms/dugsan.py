#/app/platforms/dugsan.py
import site

from fastapi import params
import httpx
import asyncio
from bs4 import BeautifulSoup
import pprint  # Java의 Pretty Printer (Jackson 등) 역할
import re
from datetime import datetime, timedelta



from .base import CampingMonitor
from core.notifier import notifier

from core.websocket_manager import ws_manager
from core.termination_handler import handle_monitoring_stop
from core.ua_generator import UAGenerator
from core.browser_handler import BrowserHandler
import time
from core.config_loader import CONFIG

from core.logger import logger as central_logger
import logging

# 로거 가져오기
logger = logging.getLogger("camping.dugsan")


class DugsanMonitor(CampingMonitor): 

    def __init__(self):
        self.execution_count = 0  # 실행 횟수를 저장할 변수
        self.client = httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False)


    async def check_availability(self, params: dict):

        self.execution_count += 1  # 호출될 때마다 1 증가
        print(f"[*] {params['camp_id']} 덕산캠핑장 조회 중...") 
           
        #기본 값
        camp_id = params.get("camp_id") 
        group_code = params.get("groupCode") #idKey
        uuid = params.get("watchUuid")
        campsite_name = params.get("campsiteName")
        auto_reserve = params.get("autoReserve", "N") #자동 예약

        #감시 사이트 대상
        target_site_codes = params.get("site_codes", [])
        target_site_codes = [str(code) for code in target_site_codes] 

        hasCategory = params.get("hasCategory") #그룹으로 찾을지 사이트로 찾을지

        #예약 정보
        req_date = params.get("date") # 예: "2026-05-14"
        stay_days = int(params.get("stay_day", "1"))
           

        start_datetime = datetime.strptime(req_date, "%Y-%m-%d") 
        end_dt = start_datetime + timedelta(days=stay_days)   
       

         #감시 정보 전달
        await ws_manager.broadcast({"messageType" : "monitor", "data" : {"uuid" : uuid, "count" : self.execution_count}}) 
                
        logger.info(f"[*] Dugsan 감시 시작 - 덕산 캠핑장 : {campsite_name} 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박일수: {stay_days}")

        current_headers = UAGenerator.get_headers({
            "Accept": "*/*",
            "Host": "www.ghss.or.kr",
            "Origin": "https://www.ghss.or.kr",
            "Referer": f"https://www.ghss.or.kr/ttreserve/reserve/dscamp.do",     
            "X-Requested-With": "XMLHttpRequest",       
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",  
        })


        url = "https://www.ghss.or.kr/ttreserve/reserve/room_list.ajax"
        data = {
            "facl_id" : camp_id,
            "bgng_ymd" : req_date,
            "end_ymd" : end_dt.strftime("%Y-%m-%d"),
            "stay_cnt" : stay_days,
            "week" : self.get_week_day(params.get("date")),
            "fcgp_id" : ""
        }

        find_items = []
        page_num = 1  # 페이지 번호

        while True:
            data["pageNo"] = page_num
            response = await self.client.post(url, data=data, headers=current_headers, timeout=10.0)
            if response.status_code != 200:
                logger.error(f"[!] HTTP {response.status_code} 오류 발생 - 페이지 {page_num}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select("div.item ul")
            find_site_count = len(items)
            if find_site_count > 0:
                for item in items:
                    a_tag = item.find("a", onclick=True)
                    if not a_tag:
                        continue
                    ## f_RoomChoice('dscamp','INSAM','00001') -> ['dscamp', 'INSAM', '00001']
                    onclick_val = a_tag["onclick"]
                    function_args = re.findall(r"'(.*?)'", onclick_val)
                    if len(function_args) >= 3:
                        room_group = function_args[1]  # 'INSAM'
                        room_code = function_args[2]   # '00001'

                        dt_tag = item.find("dt")
                        site_name = dt_tag.get_text(strip=True) if dt_tag else "명칭 없음"

                        find_items.append({
                            "site_name": site_name,
                            "room_group": room_group,
                            "room_code": room_code                               
                        })

                if find_site_count == 10: # 개수가 10개라면 다음 데이터가 더 있을 것으로 판단하고 반복
                    page_num += 1 # 페이지 번호 증가가 필요할 경우
                    continue
                else:
                    # 10개 미만이면 마지막 데이터이므로 루프 종료
                    break
            else:
                # 사이트가 더 이상 없으면 루프 종료
                break        
        
        found_sites = []
        for find_item in find_items:
            room_group = find_item.get("room_group")
            room_code = find_item.get("room_code")

            # 사이트 코드로 체크
            if room_code in target_site_codes:
                logger.info(f"[{campsite_name}] {find_item['site_name']} 사이트 예약 가능! (그룹: {room_group}, 코드: {room_code})")
                found_sites.append({
                    "group_code": room_group,
                    "site_code": room_code,
                    "site_name": find_item['site_name']
                    }) 

        sites_string = ""
        if found_sites:
            site_names = [s['site_name'] for s in found_sites]
            sites_string = ", ".join(site_names)          

            link = f"https://www.ghss.or.kr/ttreserve/reserve/dscamp.do"
            
            msg = (
                        f"<b>빈자리 발견!</b>\n"
                        f"캠핑장: {campsite_name}\n"
                        f"날짜: {req_date} ({stay_days}박)\n"
                        f"구역: {sites_string}\n"
                        f"<a href='{link}'>예약하러 가기</a>"
                    )
            # 알림 전송                
            await notifier.send_message(msg) 

            alert_msg = {
                "messageType" : "alert" 
                ,"data" : {
                    "campseq": camp_id,
                    "res_dt": req_date,                           
                    "res_days": stay_days,
                    "link" : link,
                    "list" : found_sites
                    }
            }

            # 실시간 웹소켓 알림 전송
            await ws_manager.broadcast(alert_msg)     
            
            logger.info(f"[감시 성공] 예약 가능 사이트 발견 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박일수: {stay_days} 사이트 : 사이트 발견: {sites_string}")
            print(f"[감시 성공] 예약 가능 사이트 발견: {sites_string}") 

            # 모니터링 종료 체크
            from main import scheduler
            await handle_monitoring_stop(scheduler, ws_manager, params, found_sites)

            # 시스템 트레이 알림 호출
            try:
                from main import tray_manager # 순환 참조 방지
                if tray_manager:
                    tray_manager.notify(
                        "빈자리 알림", 
                        f"[{params['campsiteName']}] 구역에 자리가 났습니다."
                    )
            except Exception as e:
                logger.error(f"트레이 알림 호출 실패: {e}")


            return True                 

        return False
    
    def get_week_day(self, day_str: str) -> int:
        # 1. 문자열을 datetime 객체로 파싱 (Java의 LocalDate.parse와 동일)
        # 날짜 형식이 "20260515" 라면 "%Y%m%d", "2026-05-15" 라면 "%Y-%m-%d"
        dt = datetime.strptime(day_str, "%Y-%m-%d")
        
        # 2. ISO 요일 가져오기 (월:1, 화:2, ..., 일:7)
        v = dt.isoweekday() + 1
        
        # 3. 범위를 1~7로 조정 (일요일 처리)
        if v >= 8:
            v = 1
            
        return v

    async def close_client(self):
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            logger.info("[*] [덕산캠핑장] httpx AsyncClient 커넥션 풀을 안전하게 닫았습니다.")            
           