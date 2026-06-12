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
from core.config_loader import CONFIG

# 로거 가져오기
from core.logger import logger as central_logger
import logging
logger = logging.getLogger("camping.campingtalk")


class CampingtalkQMonitor(CampingMonitor):  
     
    def __init__(self):
        self.execution_count = 0  # 실행 횟수를 저장할 변수 

    async def check_availability(self, params: dict):
        
        self.execution_count += 1  # 호출될 때마다 1 증가

        print(f"[*] {params['camp_id']} Campingtalk 조회 중...")       
        
        campsite_name = params.get("campsiteName", "이름 없음")
        camp_id = params.get("camp_id")
        uuid = params.get("watchUuid")
        req_date = params.get("date")
        stay_days = int(params.get("stay_day", "1"))
        has_category = params.get("hasCategory") #그룹으로 찾을지 사이트로 찾을지

        auto_reserve = params.get("autoReserve", "N") #자동 예약

        # 1. 문자열을 datetime 객체로 변환
        start_dt = datetime.strptime(req_date, "%Y-%m-%d")
        # 2. 종료일 계산: (숙박일수 - 1)을 더함
        # 1박(stay_days=1) -> +0일 -> 2026-05-12
        # 2박(stay_days=2) -> +1일 -> 2026-05-13
        end_dt = start_dt + timedelta(days=stay_days)  
        
        #일반적인 박수 계산
        normal_end_dt = start_dt + timedelta(days=stay_days) 

         #감시 정보 전달
        await ws_manager.broadcast({"messageType" : "monitor", "data" : {"uuid" : uuid, "count" : self.execution_count}}) 
                
        logger.info(f"[*] Campingtalk 감시 시작 - 캠핑장 : {campsite_name} 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박정보: {stay_days}")

        #감시 사이트 대상
        target_site_codes = params.get("site_codes", [])
        target_site_codes = [str(code) for code in target_site_codes]

        res_dt = req_date.replace("-", "")
        res_edt = end_dt.strftime("%Y%m%d")
        res_days = stay_days

        info_config = CONFIG.get("info", {})
        member_adult = int(info_config.get("member_adult") or 0)
        member_teen = int(info_config.get("member_teen") or 0)
        member_child = int(info_config.get("member_child") or 0)
        
        total_people = member_adult + member_teen + member_child

        data = {
            "bookingStartDate": params.get("camp_id"),
            "bookingStartDate": res_dt,
            "bookingEndDate": res_edt,
            "peopleNumber": total_people,
            "sortIndex": "sortOrder"           
        }            

        pprint.pprint(f"요청 파라미터 : {data}")

        # 호출 시마다 새로운 랜덤 헤더 생성
        current_headers = UAGenerator.get_headers({
            "Referer": f"https://www.campingtalk.me/",
            "Accept": "application/json"
        })

        #https://info.campingtalk.me/product/v3/site-group/pubsec/camp/3797/salelist?bookingStartDate=20260521&bookingEndDate=20260522&peopleNumber=2&sortIndex=sortOrder
        #https://info.campingtalk.me/product/v3/site-group/pubsec/camp/3797/salelist?bookingStartDate=20260521&bookingEndDate=20260522&peopleNumber=3&sortIndex=sortOrder
        url = f"https://info.campingtalk.me/product/v3/site-group/pubsec/camp/{camp_id}/salelist?bookingStartDate={res_dt}&bookingEndDate={res_edt}&peopleNumber={total_people}&sortIndex=sortOrder"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=current_headers,  cookies={"auth": "token"}, timeout=10.0)
                response.raise_for_status() # 200 OK가 아니면 예외 발생
                result = response.json()

                data_content = result.get("data", {})
                sale_content = data_content.get("sale", {})
                schedule_results = sale_content.get("scheduleSummaryResults", [])

                print(f"[*] 총 {len(schedule_results)}개의 사이트 정보를 가져왔습니다.")

                found_sites = []
                for site in schedule_results:
                    site_name = site.get("siteGroupName")
                    zone_name = site.get("zoneName")
                    zone_id = site.get("zoneId")
                    status = site.get("reservationStatus") # "예약가능" 등
                    is_possible = site.get("isBookingPossible") # True/False
                    site_group_id = str(site.get("siteGroupId", "")) # True/False

                    #print(f"<site group='{zone_id}' code='{site_group_id}'><![CDATA[[{site_name}]]></site>")
                    #print(f"사이트명: {site_name}, 구역명: {zone_name}, 예약상태: {status}, 예약가능 여부: {is_possible}, 사이트 그룹 ID: {site_group_id}")

                    if is_possible:
                        #pprint.pprint(f"예약 가능 사이트 발견: {site_name} (코드: {site_group_id}) - 상태: {is_possible}")
                        if site_group_id in target_site_codes:
                                found_sites.append({
                                    "site_name": site_name,
                                    "site_code": site_group_id,
                                    "status": status,
                                    "zone_name": zone_name
                                })

                sites_string = ""
                if found_sites:
                    
                    site_names = [s['site_name'] for s in found_sites]
                    sites_string = ", ".join(site_names)
                    
                    for site in found_sites:   
                        pprint.pprint(site)     

                        link = f"https://www.campingtalk.me/pubsec/camp/{camp_id}/siteGroupList?campId={camp_id}&bookingStartDate={res_dt}&bookingEndDate={res_edt}"
                        logger.error(f"{campsite_name} 예약 URL: {link}")

                        msg = (
                            f"<b>빈자리 발견!</b>\n"
                            f"캠핑장: {campsite_name}\n"
                            f"날짜: {params['date']} ({stay_days}박)\n"
                            f"구역: {site['zone_name']}({site['site_name']})\n"
                            f"<a href='{link}'>예약하러 가기</a>"
                        )
                        # 알림 전송                
                        await notifier.send_message(msg)

                       
                        alert_msg = {
                            "messageType" : "alert" 
                            ,"data" : {
                                "campseq": camp_id,                               
                                "res_dt": start_dt,                           
                                "res_days": stay_days,
                                "link" : link,
                                "list" : found_sites                                
                                }
                        }
                        # 실시간 웹소켓 알림 전송
                        await ws_manager.broadcast(alert_msg)

                        #한바퀴만 돌고 멈춤
                        break

                    logger.info(f"[감시 성공] 예약 가능 사이트 발견 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박일수: {stay_days} 사이트 : 사이트 발견: {sites_string}")
                    print(f"[감시 성공] 예약 가능 사이트 발견: {sites_string}")

                    # 시스템 트레이 알림 호출
                    try:
                        from main import tray_manager # 순환 참조 방지
                        if tray_manager:
                            tray_manager.notify(
                                "빈자리 알림", 
                                f"[{params['campsite_name']}] 구역에 자리가 났습니다."
                            )
                    except Exception as e:
                        logger.error(f"트레이 알림 호출 실패: {e}")
                    
                    # 모니터링 종료 체크
                    from main import scheduler
                    await handle_monitoring_stop(scheduler, ws_manager, params, found_sites)
                    
                    return True   
                else:
                    return False    
            except Exception as e:
                logger.error(f"[!] 캠핑톡 데이터 요청 중 오류 발생: {e}")

            return False

    async def _stop_and_remove_ui(self, params):
        job_id = params.get("watchUuid")
        try:
            from app.main import scheduler 
            
            # 스케줄러에서 작업 제거
            scheduler.remove_job(job_id)
            logger.info(f"감시 성공 종료: {job_id}")

            # 웹 화면에 삭제 명령 전송
            await ws_manager.broadcast({
                "messageType": "remove_monitor",
                "data": { "uuid": job_id }
            })
        except Exception as e:
            logger.error(f"종료 처리 중 오류: {e}")