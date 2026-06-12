#app/platforms/interpark.py
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
from .interpark_reserver import InterparkReserver

# 로거 가져오기
from core.logger import logger as central_logger
import logging
logger = logging.getLogger("camping.interpark")
logger.propagate = True


class InterparkMonitor: 

    def __init__(self):        
        self.execution_count = 0  # 실행 횟수를 저장할 변수      
        self.reserver = InterparkReserver() # 예약 객체 생성    

    async def check_availability(self, params: dict):
        """
        스케줄러가 호출할 때 params를 넘겨줍니다.
        params 예: {"camp_id": "22016459", "date": "2026-04-28", ...}
        """

        self.execution_count += 1  # 호출될 때마다 1 증가

        print(f"[*] {params['camp_id']} 인터파크 조회 중...")

        campsiteName = params.get("campsiteName", "이름 없음")
        camp_id = params.get("camp_id")
        uuid = params.get("watchUuid")
        req_date = params.get("date")
        stay_days = params.get("stay_day", "")
        
        nights_count = len(stay_days.split(',')) if stay_days else 1
       
        auto_reserve = params.get("autoReserve", "N") #자동 예약

        # 1. 문자열을 datetime 객체로 변환
        start_dt = datetime.strptime(req_date, "%Y-%m-%d")
        logger.info(f"[*] 인터파크(NOL) 감시 시작 - 캠핑장 : {campsiteName} 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박정보: {nights_count}")

        raw_site_codes = params.get("site_codes", [])
        target_site_codes = [] # ['1', '2']
        target_site_group = [] # ['RGN001', 'RGN002']
        target_site_map = {}  # { '1': ['RGN001'], '2': ['RGN002', 'RGN007'] }
        for raw in raw_site_codes:
            if ":" in raw:
                # 1. 분리 (자바의 split)
                key, value_str = raw.split(":", 1)
                key = key.strip()
                
                # 2. "|" 기준으로 쪼개서 리스트 생성
                values = value_str.split("|")
                
                # 3. 개별 리스트 업데이트 (감시용 통합 리스트)
                target_site_codes.append(key)
                target_site_group.extend(values) # flatten 처리
                
                # 4. Map(Dict) 구조 생성
                target_site_map[key] = values
            else:
                # ":"가 없는 예외 처리
                val = raw.strip()
                target_site_codes.append(val)
                target_site_group.append(val)
                target_site_map[val] = [val]


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

                print(response.text)

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
                                "site_code": seatGrade,
                                "site_group_arr": target_site_map.get(str(seatGrade), [])
                            })

                sites_string = ""
                if found_sites:

                    site_names = [s['site_name'] for s in found_sites]
                    sites_string = ", ".join(site_names)                   
                       

                    #알람 처리
                    link = f"https://tickets.interpark.com/goods/{camp_id}"
                
                    msg = (
                        f"<b>빈자리 발견!</b>\n"
                        f"캠핑장: {params['campsiteName']}\n"
                        f"날짜: {params['date']} ({nights_count}박)\n"
                        f"구역: {sites_string}\n"
                        f"<a href='{link}'>예약하러 가기</a>"
                    )
                    # 알림 전송                
                    await notifier.send_message(msg) 

                    alert_msg = {
                        "messageType" : "alert" 
                        ,"data" : {
                            "campseq": camp_id,
                            "res_dt": res_dt,                           
                            "res_days": nights_count,
                            "link" : link,
                            "list" : found_sites
                            }
                    }

                    # 실시간 웹소켓 알림 전송
                    await ws_manager.broadcast(alert_msg)     
                    
                    logger.info(f"[감시 성공] 예약 가능 사이트 발견 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박일수: {nights_count} 사이트 : 사이트 발견: {sites_string}")
                    print(f"[감시 성공] 예약 가능 사이트 발견: {sites_string}") 

                    # 모니터링 종료 체크
                    from main import scheduler # 순환 참조 방지를 위해 함수 내 임포트
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

                    #자동 예약시 수행
                    if auto_reserve == "Y":
                        logger.info(f"[자동 예약] 예약 진입: {found_sites[0]['site_name']}")
                        success = await self.reserver.reserve(params, found_sites[0])
                        if success:
                            logger.info("자동 예약 요청 성공 (무통장 입금 대기)")
                        else:
                            logger.error("자동 예약 실패 (세션 만료 또는 선점됨)")
                   
                
                    return True        

                return False
                
            except Exception as e:
                logger.error(f"[{params['camp_id']}] 잔여석 확인 중 에러: {e}")  
    
