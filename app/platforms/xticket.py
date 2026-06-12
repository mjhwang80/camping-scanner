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
from core.logger import logger as central_logger
import logging

# 로거 가져오기
logger = logging.getLogger("camping.xticket")


class XticketMonitor(CampingMonitor): 

    def __init__(self):
        self.execution_count = 0  # 실행 횟수를 저장할 변수     
        self.client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
        self.cookies_initialized = False

    async def check_availability(self, params: dict):

        self.execution_count += 1  # 호출될 때마다 1 증가
        print(f"[*] {params['camp_id']} xticket 조회 중...") 
           
        #기본 값
        camp_id = params.get("camp_id") 
        groupCode = params.get("groupCode") #idKey
        uuid = params.get("watchUuid")
        campsiteName = params.get("campsiteName")

        auto_reserve = params.get("autoReserve", "N") #자동 예약

        #예약 정보
        req_date = params.get("date") # 예: "2026-05-14"
        stay_days = int(params.get("stay_day", "1"))
           

        start_datetime = datetime.strptime(req_date, "%Y-%m-%d") 
        end_dt = start_datetime + timedelta(days=stay_days - 1)   

        start_dt = req_date = req_date.replace("-", "")     


        #감시 사이트 대상
        target_site_codes = params.get("site_codes", [])
        target_site_codes = [str(code) for code in target_site_codes] 

        hasCategory = params.get("hasCategory") #그룹으로 찾을지 사이트로 찾을지

         #감시 정보 전달
        await ws_manager.broadcast({"messageType" : "monitor", "data" : {"uuid" : uuid, "count" : self.execution_count}}) 
                
        logger.info(f"[*] xticket 감시 시작 - 캠핑장 : {params['campsiteName']} 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박일수: {stay_days}")

        if not self.cookies_initialized:
            await self.get_browser_cookies(camp_id)



        

   
        current_headers = UAGenerator.get_headers({
            "Accept": "*/*",
            "Host": "camp.xticket.kr",
            "Origin": "https://camp.xticket.kr",
            "Referer": f"https://camp.xticket.kr/web/main?shopEncode={camp_id}",     
            "X-Requested-With": "XMLHttpRequest",       
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",  
        })


        url = "https://camp.xticket.kr/Web/Book/GetBookProduct010001.json"
        data = {
            "start_date" : start_dt,
            "end_date" : end_dt.strftime("%Y%m%d"),
            "book_days" : stay_days,
            "two_stay_days" : "0",           
            "shopCode" : groupCode,           
            "time" : int(time.time() * 1000),           
        }

        

        found_sites = []

        for area in target_site_codes:
            
            data["product_group_code"] = area

            pprint.pprint(data)
            
            try:
                response = await self.client.post(url, data=data, headers=current_headers)
                print(response.status_code)
                print(response.text)
                result = response.json()

                site_list = result.get("data", {}).get("bookProductList", [])

                for find_site in site_list:
                    select_yn = find_site.get("select_yn", "0")                        
                    if select_yn == "1":
                        
                        product_name = find_site.get("product_name")
                        product_code = find_site.get("product_code")
                        
                        if "Y" == hasCategory:
                            # 원하는 사이트 체크
                             if product_code in target_site_codes:                                
                                logger.info(f"[{campsiteName}] {product_name} 사이트 예약 가능! (ID: {product_code})")
                                found_sites.append({
                                    "shopCode": groupCode,
                                    "shopEncode": camp_id,
                                    "product_name": product_name,
                                    "site_name": product_name,
                                    "product_code": product_code,                             
                                    
                                })        
                        else:                          
                            logger.info(f"[{campsiteName}] {product_name} 사이트 예약 가능! (ID: {product_code})")
                            found_sites.append({
                                "shopCode": groupCode,
                                "shopEncode": camp_id,
                                "product_name": product_name,
                                "site_name": product_name,
                                "product_code": product_code,                             
                                
                            })                           

            except Exception as e:
                logger.error(f"[{params['camp_id']}] 잔여석 확인 중 에러: {e}")         

        sites_string = ""
        if found_sites:

            site_names = [s['site_name'] for s in found_sites]
            sites_string = ", ".join(site_names)
            
            for site in found_sites:
                #pprint.pprint(site)

                #자동 예약시 수행
                if auto_reserve == "Y":
                    print("자동 처리를 수행해야 할 구역입니다.")

                link = f"https://camp.xticket.kr/web/main?shopEncode={camp_id}"

                logger.info(f"예약 URL: {link}")

                msg = (
                    f"<b>빈자리 발견!</b>\n"
                    f"캠핑장: {campsiteName}\n"
                    f"날짜: {params['date']} ({stay_days}박)\n"
                    f"사이트명: {site["site_name"]}\n"
                    f"<a href='{link}'>예약하러 가기</a>"
                )
                # 알림 전송                
                await notifier.send_message(msg)
                
                alert_msg = {
                    "messageType" : "alert",
                    "data" : {
                        "campseq" : camp_id,
                        "groupCode" : groupCode,
                        "res_dt" : start_dt,                           
                        "res_days" : stay_days,
                        "link" : link,
                        "list" : found_sites,
                        "site_name" : site["site_name"],

                        "shopCode" : groupCode,
                        "shopEncode" : camp_id
                    }
                }
                pprint.pprint(alert_msg)
                # 실시간 웹소켓 알림 전송
                await ws_manager.broadcast(alert_msg)

                #한바퀴만 돌고 멈춤
                break

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
            
            # 모니터링 종료 체크           
            from main import scheduler
            await handle_monitoring_stop(scheduler, ws_manager, params, found_sites)
            
            logger.info(f"[감시 성공] 예약 가능 사이트 발견 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박일수: {stay_days} 사이트 : 사이트 발견: {sites_string}")
            print(f"[감시 성공] 예약 가능 사이트 발견: {sites_string}")

            return True
        
        return False
    
    async def get_browser_cookies(self, camp_id:str):

        url = f"https://camp.xticket.kr/web/main?shopEncode={camp_id}"

        logger.info(f"[*] {url}에서 쿠키를 새로 받습니다.")

        current_headers = UAGenerator.get_headers({
            "Host": "camp.xticket.kr" ,    
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"     
        })             
            
        response = await self.client.get(url, headers=current_headers)
        self.cookies_initialized = True
        # 2. 서버가 보낸 쿠키 확인
        print(f"[*] 획득한 쿠키: {self.client.cookies}")
            
    async def close_client(self):
        """외부에서 호출 가능한 클라이언트 정리 메서드"""
        if hasattr(self, 'client') and self.client:
            if not self.client.is_closed:
                await self.client.aclose()
                logger.info("[*] [xticket] 클라이언트가 정상적으로 정리되었습니다.")       