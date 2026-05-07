from fastapi import params
import httpx
import asyncio
from bs4 import BeautifulSoup
import pprint  # Java의 Pretty Printer (Jackson 등) 역할
import re
from datetime import datetime, timedelta

import logging

from .base import CampingMonitor
from core.notifier import notifier

from core.websocket_manager import ws_manager
from core.termination_handler import handle_monitoring_stop
from core.ua_generator import UAGenerator
from core.browser_handler import BrowserHandler

import logging

# 로거 가져오기
logger = logging.getLogger("camping.maketicket")


class MaketicketMonitor: 

    def __init__(self):
        self.execution_count = 0  # 실행 횟수를 저장할 변수 

    async def check_availability(self, params: dict):

        self.execution_count += 1  # 호출될 때마다 1 증가
        print(f"[*] {params['camp_id']} Maketicket 조회 중...") 
           
        #기본 값
        camp_id = params.get("camp_id") 
        groupCode = params.get("groupCode") #idKey
        uuid = params.get("watchUuid")
        campsiteName = params.get("campsiteName")

        #예약 정보
        req_date = params.get("date") # 예: "2026-05-14"
        stay_days = int(params.get("stay_day", "1"))
        start_dt = req_date = req_date.replace("-", "")          


        #감시 사이트 대상
        target_site_codes = params.get("site_codes", [])
        target_site_codes = [str(code) for code in target_site_codes] 

         #감시 정보 전달
        await ws_manager.broadcast({"messageType" : "monitor", "data" : {"uuid" : uuid, "count" : self.execution_count}}) 
                
        logger.info(f"[*] Maketicket 감시 시작 - 캠핑장 : {params['campsiteName']} 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박일수: {stay_days}")

        url = "https://forest.maketicket.co.kr/event/event.do"
        data = {
            "command" : 'reserve_position_room_info_json',
            "idkey" : groupCode,
            "gd_seq" : camp_id,
            "sd_date" : start_dt,
            "lodge_day" : stay_days,           
            "dc_ri_seq" : '',           
        }

        current_headers = UAGenerator.get_headers({
            "host": "forest.maketicket.co.kr",
            "origin": "https://forest.maketicket.co.kr",
            "Referer": "https://forest.maketicket.co.kr/event/event.do",
            "x-requested-with": "XMLHttpRequest"
        })


        found_sites = []

        for area in target_site_codes:
            
            data["ri_area_code"] = area

            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(url, data=data, headers=current_headers,  cookies={"auth": "token"}, timeout=10.0)
                    result = response.json()
                    site_list = result.get("resultList", [{}])
                    for find_site in site_list:
                        use_yn = find_site.get("use_yn", "N")
                        reserve_ready_yn = find_site.get("reserve_ready_yn", "N")
                        if use_yn == "Y" and reserve_ready_yn == "Y":
                            
                            ri_name = find_site.get("ri_name")
                            ri_seq = find_site.get("ri_seq")

                            logger.info(f"[{campsiteName}] {ri_name} 사이트 예약 가능! (ID: {ri_seq})")
                            found_sites.append({
                                "idkey": groupCode,
                                "gd_seq": camp_id,
                                "ri_name": ri_name,
                                "site_name": ri_name,
                                "ri_seq": ri_seq,                              
                                "sd_date": start_dt,                              
                                "lodge_day": stay_days,                              
                                "ri_area_code": area
                            })                           

                except Exception as e:
                    logger.error(f"[{params['camp_id']}] 잔여석 확인 중 에러: {e}")         

        sites_string = ""
        if found_sites:

            site_names = [s['ri_name'] for s in found_sites]
            sites_string = ", ".join(site_names)
            
            for site in found_sites:
                #pprint.pprint(site)

                if camp_id == "GD123":
                    link = "https://ggtour.or.kr/camping/token/cookie/reservation.do"
                else:
                    link = f"https://forest.maketicket.co.kr/ticket/{camp_id}"

                logger.info(f"예약 URL: {link}")

                msg = (
                    f"<b>빈자리 발견!</b>\n"
                    f"캠핑장: {campsiteName}\n"
                    f"날짜: {params['date']} ({stay_days}박)\n"
                    f"사이트명: {site["ri_name"]}\n"
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

                        "idkey" : site["idkey"],
                        "gd_seq" : site["gd_seq"],
                        "ri_name" : site["ri_name"],
                        "site_name" : site["ri_name"],
                        "ri_seq" : site["ri_seq"],                              
                        "sd_date" : site["sd_date"],                              
                        "lodge_day" : site["lodge_day"],                              
                        "ri_area_code" : site["ri_area_code"]     
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
            from main import scheduler # 순환 참조 방지를 위해 함수 내 임포트
            await handle_monitoring_stop(scheduler, ws_manager, params, found_sites)

            logger.info(f"[감시 성공] 예약 가능 사이트 발견 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박일수: {stay_days} 사이트 : 사이트 발견: {sites_string}")
            print(f"[감시 성공] 예약 가능 사이트 발견: {sites_string}")

            return True
        
        return False