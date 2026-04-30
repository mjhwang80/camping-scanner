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

# 로거 가져오기
logger = logging.getLogger("camping.interpark")


class InterparkMonitor: 

    def __init__(self):        
        self.execution_count = 0  # 실행 횟수를 저장할 변수      
    

    async def check_availability(self, params: dict):
        """
        스케줄러가 호출할 때 params를 넘겨줍니다.
        params 예: {"camp_id": "22016459", "date": "2026-04-28", ...}
        """

        self.execution_count += 1  # 호출될 때마다 1 증가

        print(f"[*] {params['camp_id']} 인터파크 조회 중...")

        camp_id = params.get("camp_id")
        uuid = params.get("watchUuid")
        req_date = params.get("date")
        stay_days = params.get("stay_day", "")

        # 1. 문자열을 datetime 객체로 변환
        start_dt = datetime.strptime(req_date, "%Y-%m-%d")
        logger.info(f"[*] 인터파크 감시 시작 - 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박정보: {stay_days}")

        #감시 사이트 대상
        target_site_codes = params.get("site_codes", [])
        target_site_codes = [str(code) for code in target_site_codes]

        res_dt = req_date.replace("-", "")
        res_days = stay_days       

        # URL 구성 (playSeq 포함)
        url = f"https://api-ticketfront.interpark.com/v1/goods/{camp_id}/playSeq/PlaySeq/{stay_days}/REMAINSEAT"

        print(url)

        #감시 정보 전달
        await ws_manager.broadcast({"messageType" : "monitor", "data" : {"uuid" : uuid, "count" : self.execution_count}}) 

        # 호출 시마다 새로운 랜덤 헤더 생성
        current_headers = UAGenerator.get_headers({
            "Referer": f"https://tickets.interpark.com/goods/{params.get('camp_id')}"
        })

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=current_headers,  cookies={"auth": "token"}, timeout=10.0)

                #print(response.text)

                result = response.json()
                remain_seats = result.get("data", {}).get("remainSeat", []) # 인터파크 API 응답 키 확인 필요

                found_sites = []

                for site in remain_seats:

                    pprint.pprint(site)

                    remainCnt = int(site.get("remainCnt", 0)) #잔여석
                    seatGradeName = site.get("seatGradeName") #사이트명
                    seatGrade = site.get("seatGrade") #사이트 고유번호
                    
                    if remainCnt > 0: #잔여석이 있으면.
                        # 원하는 사이트 체크
                        if seatGrade in target_site_codes:
                            found_sites.append({
                                "site_name": seatGradeName,
                                "site_code": seatGrade
                            })

                sites_string = ""
                if found_sites:
                    link = f"https://tickets.interpark.com/goods/{camp_id}"

                    site_names = [s['site_name'] for s in found_sites]
                    sites_string = ", ".join(site_names)
                
                    msg = (
                        f"<b>빈자리 발견!</b>\n"
                        f"캠핑장: {params['campsiteName']}\n"
                        f"날짜: {params['date']} ({len(res_days.split(','))}박)\n"
                        f"구역: {sites_string}\n"
                        f"<a href='{link}'>예약하러 가기</a>"
                    )

                    alert_msg = {
                        "messageType" : "alert" 
                        ,"data" : {
                            "campseq": camp_id,
                            "res_dt": res_dt,                           
                            "res_days": len(res_days.split(',')),
                            "link" : link,
                            "list" : found_sites
                            }
                    }

                    # 실시간 웹소켓 알림 전송
                    await ws_manager.broadcast(alert_msg)     
                    
                    # 알림 전송                
                    await notifier.send_message(msg) 

                    
                    
                    logger.info(f"[감시 성공] 예약 가능 사이트 발견 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박일수: {stay_days} 사이트 : 사이트 발견: {sites_string}")
                    print(f"[감시 성공] 예약 가능 사이트 발견: {sites_string}")

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
                   
                
                    return True        

                return False
                
            except Exception as e:
                logger.error(f"[{params['camp_id']}] 잔여석 확인 중 에러: {e}")  
    
