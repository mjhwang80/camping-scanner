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
logger = logging.getLogger("camping.mirihae")


class MirihaeMonitor: 

    def __init__(self):
        self.execution_count = 0  # 실행 횟수를 저장할 변수 
        self.token = None  # 토큰정보

        self.client = httpx.AsyncClient(
            follow_redirects=True, # HTTP 표준 리다이렉트 자동 추적
            timeout=20.0,
            headers=UAGenerator.get_headers({
                "Referer": "https://mirihae.com/",
                "Upgrade-Insecure-Requests": "1"
            })
        )

    async def check_availability(self, params: dict):

        self.execution_count += 1  # 호출될 때마다 1 증가
        print(f"[*] {params['camp_id']} 미리해 조회 중...") 
        
        if not self.token or not self.token.strip():
            logger.info("[*] 토큰이 없거나 만료되어 새로 요청합니다.")
            self.token = await self.get_token(params)

        if not self.token:
            logger.error("[!] 토큰 획득 실패로 감시를 중단합니다.")
            return False

        logger.info(f"수집한 토큰정보 : {self.token}")

        camp_id = params.get("camp_id")
        groupCode = params.get("groupCode")
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
                
        logger.info(f"[*] 미리해 감시 시작 - 캠핑장 : {params['campsiteName']} 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박일수: {stay_days}")

        url = "https://mirihae.com/campsite/selectAjaxDatePinInfo.do"
        data = {
            "pageId" : camp_id,
            "tocken" : self.token,
            "groupCode" : groupCode,
            "selectStartDate" : start_dt,
            "selectEndDate" : end_dt,
            "selectMonth" : select_month,
            
            "device" : "pc",
            "selectCategoryId" : "",
            "selectItemId" : "",
            "selectPageItemType" : "",
            "selectBusSeatId" : "",
            "cnt" : "",
            "infoType" : "",
            "token" : "",
        }

        #pprint.pprint(data)

        current_headers = UAGenerator.get_headers({
            "host": "mirihae.com",
            "origin": "https://mirihae.com",
            "Referer": f"https://mirihae.com/${groupCode}/campsite/{camp_id}",
            "x-requested-with": "XMLHttpRequest"
        })

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=data, headers=current_headers,  cookies={"auth": "token"}, timeout=10.0)

                result = response.json()

                print(result)

                pin_list = result.get("pinCategoryList", [{}])[0].get("pinList", [])
                
                found_sites = []
                for pin in pin_list:
                    #print(pin)

                    item_id = pin.get("itemId")
                    item_nm = pin.get("itemNm")
                    item_no = pin.get("itemNo")
                    category_nm = pin.get("categoryNm")
                    use_at = pin.get("useAt", "N") # Y: 사용가능, N: 불가능
                    color = pin.get("color") # 사이트 구역

                    # 예약 가능한 상태인지 체크 (예: 예약수가 0이고 사용가능 여부가 Y인 경우)
                    if use_at == "Y":
                        logger.info(f"[{category_nm}] {item_nm} 사이트 예약 가능! (ID: {item_id})")
                        # 원하는 사이트 체크
                        if color in target_site_codes:
                            found_sites.append({
                                "site_name": item_nm,
                                "item_no": item_no,
                                "site_code": item_id,
                                "category_nm": category_nm,
                                "site_color": color
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

                        await self.call_api("자리 체크","https://mirihae.com/campsite/selectReservationCheck.do", params, check_data) # 자리 체크
                        await self.call_api("티켓 정보 체크","https://mirihae.com/campsite/selectTicketInfo.do", params, check_data) # 티켓 정보
                        await self.call_api("전체 가격 체크","https://mirihae.com/campsite/totalTicketPrice.do", params, check_data) # 전체 가격

                        parameter = f"gubun=gugu&tocken={self.token}&selectMonth={select_month}&selectStartDate={start_dt}&selectEndDate={end_dt}&selectItemId={site.get("site_code")}"
                        link = f"https://oduck-kwon.github.io/camp/gateway.htm?{parameter}"

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
    

    async def call_api(self, txt:str, url:str, params: dict, req_data: dict):
        #url = "https://mirihae.com/campsite/selectReservationCheck.do"
        
        current_headers = UAGenerator.get_headers({
            "host": "mirihae.com",
            "origin": "https://mirihae.com",
            "Referer": f"https://mirihae.com/{params.get('groupCode')}/campsite/{params.get('camp_id')}",
            "x-requested-with": "XMLHttpRequest"
        })

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=req_data, headers=current_headers,  cookies={"auth": "token"}, timeout=10.0)
                status_code = response.status_code
                is_success = response.is_success

                if is_success:
                    logger.info(f"{txt} 성공 : {status_code}")
                    return True
                else:
                    logger.error(f"{txt} 실패 : {status_code}, 사유: {response.text}")
                    return False

            except Exception as e:
                logger.error(f"[{params['camp_id']}] 자리 선점중 에러: {e}")   

        return False

        

    async def get_token(self, params: dict):
        camp_id = params.get("camp_id")
        url = f"https://mirihae.com/pccamp/campsite/{camp_id}"

        try:
            # Playwright 핸들러를 통해 보안 단계를 통과한 최종 HTML 획득
            final_html = await BrowserHandler.get_final_content(url)
            
            if final_html:
                soup = BeautifulSoup(final_html, "html.parser")
                token_element = soup.find(id="tocken")
                
                if token_element:
                    self.token = token_element.get("value")
                    logger.info(f"[*] 보안 단계 통과 및 토큰 획득 성공: {self.token}")
                else:
                    logger.warning("[!] 토큰 엘리먼트를 찾지 못했습니다. 선택자 확인 필요.")
            else:
                logger.error("[!] 브라우저로부터 소스를 가져오지 못했습니다.")
                
        except Exception as e:
            logger.error(f"[!] 토큰 추출 중 예외 발생: {e}")

        return self.token

    async def close(self):
        """세션 종료 (자바의 close와 유사)"""
        await self.client.aclose()


    @staticmethod
    async def get_final_content(url):
        async with async_playwright() as p:
            # 브라우저 실행 (headless=True로 하면 창이 뜨지 않음)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                logger.info(f"[*] 브라우저 접속 시도: {url}")
                # 네트워크가 조용해질 때까지 대기하여 entering.html 과정을 통과
                await page.goto(url, wait_until="networkidle") 
                
                # '웹 대기' 페이지가 지나가고 실제 'tocken' ID가 나타날 때까지 대기 (최대 10초)
                await page.wait_for_selector("#tocken", timeout=10000)
                
                content = await page.content()
                return content
            except Exception as e:
                logger.error(f"[!] 브라우저 자동화 중 오류: {e}")
                return None
            finally:
                await browser.close()


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