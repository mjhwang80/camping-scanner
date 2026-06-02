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
logger = logging.getLogger("camping.pubcamping")


class PubcampingMonitor: 

    def __init__(self):
        self.execution_count = 0  # 실행 횟수를 저장할 변수 
        self.token = None  # 토큰정보

        self.client = httpx.AsyncClient(
            follow_redirects=True, # HTTP 표준 리다이렉트 자동 추적
            timeout=20.0,
            headers=UAGenerator.get_headers({
                "Referer": "https://gwgs.pubcamping.kr",
                "Upgrade-Insecure-Requests": "1"
            })
        )

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

        self.execution_count += 1  # 호출될 때마다 1 증가
        print(f"[*] {params['camp_id']} pubcamping 조회 중...")           

        campsiteName = params.get("campsiteName", "이름 없음")
        camp_id = params.get("camp_id")
        groupCode = params.get("groupCode")
        hasCategory = params.get("hasCategory") #그룹으로 찾을지 사이트로 찾을지

        auto_reserve = params.get("autoReserve", "N") #자동 예약
        
        uuid = params.get("watchUuid")
        req_date = params.get("date") # 예: "2026-05-14"
        stay_days = int(params.get("stay_day", "1"))

        start_dt = datetime.strptime(req_date, "%Y-%m-%d")
        select_month = start_dt.strftime("%Y-%m")
        next_date = start_dt + timedelta(days=stay_days) 
        end_dt = next_date.strftime("%Y-%m-%d")     

        start_dt = req_date   


        #감시 사이트 대상
        target_site_codes = params.get("site_codes", [])
        target_site_codes = [str(code) for code in target_site_codes] 

         #감시 정보 전달
        await ws_manager.broadcast({"messageType" : "monitor", "data" : {"uuid" : uuid, "count" : self.execution_count}}) 
                
        logger.info(f"[*] pubcamping 감시 시작 - 캠핑장 : {campsiteName} 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박정보: {stay_days}")

        url = f"https://gwgs.pubcamping.kr/{camp_id}/productSelectJson.do"
        data = {
            "stay_cnt" : 1,
            "check_in" : 20260619,
            "check_out" : 20260620,
            "room_area_no" : 5       
        }

        #pprint.pprint(data)

        current_headers = UAGenerator.get_headers({
            "host": "gwgs.pubcamping.kr",
            "origin": "https://gwgs.pubcamping.kr",
            "Referer": f"https://gwgs.pubcamping.kr/{camp_id}/index?",
            "x-requested-with": "XMLHttpRequest"
        })

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=data, headers=current_headers,   cookies={"auth": "token"}, timeout=10.0)

                result = response.json()

                print(result)

                pin_list = result.get("RESULT_DATA", [])
                
                found_sites = []
                for pin in pin_list:
                    #print(pin)

                    room_area_no = pin.get("ROOM_AREA_NO")
                    stay_cnt = pin.get("STAY_CNT")
                    wait_state = pin.get("WAIT_STATE")
                    room_no = pin.get("ROOM_NO")
                    room_name = pin.get("ROOM_NAME")


                    # 예약 가능한 상태인지 체크 (예: 예약수가 0이고 사용가능 여부가 Y인 경우)
                    if stay_cnt == 1 and wait_state == 'Y':
                        logger.info(f"[{room_area_no}] {room_name} 사이트 예약 가능! (ID: {room_no})")

                        # 원하는 사이트 체크
                        if room_no in target_site_codes:
                            found_sites.append({
                                "room_name": room_name,
                                "item_no": room_no,
                                "room_area_no": room_area_no,
                            })      

                sites_string = ""
                if found_sites:

                    for site in found_sites:
                        
                        pprint.pprint(site)

                        check_data = {
                            "tocken" : self.token
                            ,"approvalId" : ""
                            ,"checkType" : "selectPin"
                            ,"device" : "pc"
                            ,"pageId" : camp_id
                            ,"groupCode" : groupCode
                            ,"selectStartDate" : start_dt
                            ,"selectEndDate" : end_dt
                            ,"selectCategoryId" : "" 
                            ,"selectMonth" : select_month
                            ,"selectItemId" : site.get("site_code")
                            ,"selectPageItemType" : ""
                            ,"selectBusSeatId" : ""
                            ,"cnt" : ""
                            ,"infoType" : ""
                            ,"token" : ""
                        }


                        parameter = f"gubun=gugu&tocken={self.token}&selectMonth={select_month}&selectStartDate={start_dt}&selectEndDate={end_dt}&selectItemId={site.get("site_code")}"
                        link = f"https://mjhwang80.github.io/camping-scanner/app/templates/gugu_gateway.html?{parameter}"

                        logger.error(f"예약 URL: {link}")

                        site_names = [s['site_name'] for s in found_sites]
                        sites_string = ", ".join(site_names)
                
                        msg = (
                            f"<b>빈자리 발견!</b>\n"
                            f"캠핑장: {params['campsiteName']}\n"
                            f"날짜: {params['date']} ({stay_days}박)\n"
                            f"구역: {site["category_nm"]}({site["site_name"]})\n"
                            f"<a href='{link}'>예약하러 가기</a>"
                        )
                        # 알림 전송                
                        await notifier.send_message(msg)

                        localLink = f"/gateway/gugu?{parameter}"
                        alert_msg = {
                            "messageType" : "alert" 
                            ,"data" : {
                                "campseq": camp_id,
                                "groupCode": groupCode,
                                "res_dt": start_dt,                           
                                "res_days": stay_days,
                                "link" : localLink,
                                "list" : found_sites,
                                "tocken" : self.token
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

        return True    
    

    async def close(self):
        """세션 종료 (자바의 close와 유사)"""
        await self.client.aclose()

   

if __name__ == "__main__":
    # 테스트용 파라미터 (Map 구조)
    test_params = {
        "camp_id": "C27562955",       # 가평 용소캠핑장 예시
        "date": "2026-05-14",   # 예약 희망일
        "stay_day": 1,
        "site_codes": []
    }

    # 비동기 함수를 실행하기 위한 엔트리 포인트
    try:
        print("=== 미리해 독립 실행 테스트 시작 ===")
        asyncio.run(MirihaeMonitor().check_availability(test_params))
    except KeyboardInterrupt:
        print("\n중단되었습니다.")