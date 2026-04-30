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
logger = logging.getLogger("camping.thankq")


class ThankQMonitor: 
     
    def __init__(self):
        self.execution_count = 0  # 실행 횟수를 저장할 변수 

    async def check_availability(self, params: dict):
        # Java의 Map<String, String> data 구성과 동일
        
        self.execution_count += 1  # 호출될 때마다 1 증가

        print(f"[*] {params['camp_id']} 땡큐캠핑 조회 중...")       

        camp_id = params.get("camp_id")
        uuid = params.get("watchUuid")
        req_date = params.get("date")
        stay_days = int(params.get("stay_day", "1"))

        # 1. 문자열을 datetime 객체로 변환
        start_dt = datetime.strptime(req_date, "%Y-%m-%d")
        # 2. 종료일 계산: (숙박일수 - 1)을 더함
        # 1박(stay_days=1) -> +0일 -> 2026-05-12
        # 2박(stay_days=2) -> +1일 -> 2026-05-13
        end_dt = start_dt + timedelta(days=stay_days - 1)  
        
        #일반적인 박수 계산
        normal_end_dt = start_dt + timedelta(days=stay_days) 

         #감시 정보 전달
        await ws_manager.broadcast({"messageType" : "monitor", "data" : {"uuid" : uuid, "count" : self.execution_count}}) 
                
        logger.info(f"[*] 땡큐캠핑 감시 시작 - 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박일수: {stay_days}")

        #감시 사이트 대상
        target_site_codes = params.get("site_codes", [])
        target_site_codes = [str(code) for code in target_site_codes]

        res_dt = req_date.replace("-", "")
        res_edt = end_dt.strftime("%Y%m%d")
        res_days = stay_days

        

        data = {
            "campseq": params.get("camp_id"),
            "res_dt": res_dt,
            "res_edt": res_edt,
            "res_days": res_days,
            "site_tp": "",
            "only_able_yn": ""
        }            

        pprint.pprint(f"요청 파라미트 : {data}")

        # 호출 시마다 새로운 랜덤 헤더 생성
        current_headers = UAGenerator.get_headers({
            "Referer": f"https://tickets.interpark.com/goods/{params.get('camp_id')}"
        })

        url = "https://m.thankqcamping.com/resv/axResCampSite.hbb"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=current_headers, timeout=10.0)
            soup = BeautifulSoup(response.text, "lxml")

            # 2. 모든 사이트 리스트(li) 순회
            # 제공해주신 구조상 li 하위에 site_div가 있는 항목들 추출
            site_list = soup.select("li div.site_div")
            
            found_sites = []

            for site in site_list:
                # A. 예약 가능 여부 체크 (q_tip 클래스에 'og'가 포함되어 있는지)
                q_tip = site.select_one(".q_tip")
                if not q_tip or "og" not in q_tip.get("class", []):
                    continue # 예약 불가능하면 패스

                # B. 사이트 고유 ID 추출 (onClick="goNoMemResAlert('116308', '')" 에서 숫자만 추출)
                onclick_text = site.get("onclick", "")
                # 정규표현식으로 첫 번째 인자인 숫자 ID 추출 (Java의 Pattern/Matcher 역할)
                match = re.search(r"goNoMemResAlert\('(\d+)'", onclick_text)
                
                if match:
                    current_site_code = match.group(1)
                    
                    # C. 사용자가 요청한 감시 대상 리스트에 포함되어 있는지 확인
                    if current_site_code in target_site_codes:
                        site_name = site.select_one(".na").text if site.select_one(".na") else "알 수 없음"                        
                        found_sites.append({"site_name":site_name, "site_code" : current_site_code})

            sites_string = ""
            if found_sites:

                link = f"https://m.thankqcamping.com/resv/view.hbb?disc_per=&cseq={camp_id}&res_dt={res_dt}&res_edt={ normal_end_dt.strftime("%Y%m%d") }&res_days={stay_days}"
                
                print(link)

                site_names = [s['site_name'] for s in found_sites]
                sites_string = ", ".join(site_names)
                
                msg = (
                    f"<b>빈자리 발견!</b>\n"
                    f"캠핑장: {params['campsiteName']}\n"
                    f"날짜: {params['date']} ({res_days}박)\n"
                    f"구역: {sites_string}\n"
                    f"<a href='{link}'>예약하러 가기</a>"
                )

                alert_msg = {
                    "messageType" : "alert" 
                    ,"data" : {
                         "campseq": camp_id,
                         "res_dt": res_dt,
                         "res_edt": res_edt,
                         "res_days": res_days,
                         "campsiteseq" : "",
                         "res_path" : "HM",
                         "enter_path" : "",
                         "temporary_yn" : "",
                         "wg_pass" : "",
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

# --- Java의 main 메서드와 같은 역할 ---
if __name__ == "__main__":
    # 테스트용 파라미터 (Map 구조)
    test_params = {
        "camp_id": "16706",       # 가평 용소캠핑장 예시
        "date": "2026-05-14",   # 예약 희망일
        "stay_day": 1,
        "site_codes": [116159, 116160]
    }

    # 비동기 함수를 실행하기 위한 엔트리 포인트
    try:
        print("=== 땡큐캠핑 독립 실행 테스트 시작 ===")
        asyncio.run(ThankQMonitor().check_availability(test_params))
    except KeyboardInterrupt:
        print("\n중단되었습니다.")