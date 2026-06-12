from unittest import result
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
logger = logging.getLogger("camping.foresttrip")

class ForesttripMonitor(CampingMonitor): 

    def __init__(self):
        super().__init__()
        self.execution_count = 0  # 실행 횟수 카운터
        self.campsite_name = ""
        self._csrf = ""
        self.saltVals = ""
        # verify=False로 지정하여 최신 파이썬 환경에서의 SSL 인증서 트래픽 튕김 현상을 사전 예방합니다.
        self.client = httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False)
        self.cookies_initialized = False
        self.csrf_initialized = False
        self.login_initialized = False

    async def _check_single_group(self, client, camp_id, target_group, start_date, end_date, stay_days, headers):
        """
        [내부 함수] 단일 구역(Group)의 예약 가능 여부를 체크합니다.
        """
        logger.info(f"[*] [foresttrip] 구역 감시 시작 ID: {target_group} 요청일: ({start_date}, {stay_days}박)")

        # 1. 조회를 시도하기 전 실시간 넷퍼넬 대기열을 우회 및 통과 키 발급
        nf_key = await self.get_netfunnel_key(service_id="service_1", action_id="action2")
        if nf_key == "WAIT" or nf_key == "":
            logger.info(f"[*] [foresttrip] 구역 {target_group} 감시 스킵: 대기열이 밀려있거나 실패함.")
            return None 

        url = f"https://www.foresttrip.go.kr/rep/or/sssn/fcfsRsrvtPssblGoodsDetls.do"
        
        # 기본 Payload 조립
        data = {
            "_csrf": self._csrf,
            "srchInsttId": camp_id,
            "hmpgId": camp_id,
            "menuId": "001001",
            "srchRsrvtBgDt": start_date,
            "srchRsrvtEdDt": end_date,
            "goodsClsscHouseCdArr": target_group,  
            "srchSthngCnt": str(stay_days),
            "netfunnel_key": nf_key,

            "srchInsttArcd": "",
            "srchWord": "",
            "houseCampSctin": "",
            "rsrvtPssblYn": "",
            "rsrvtWtngSctin": "01",       
            "srchHouseCharg": "",
            "srchCampCharg": "",
            "goodsClsscCampCdArr": "",
            "srchInsttTpcd": "",
            "srchStngNofpr": "2",      
            "cmdogYn": "N",
            "bbqYn": "N",
            "dsprsYn": "N",
            "otsdWeterYn": "N",
            "wifiYn": "N",
            "snowPlaceYn": "N",
            "srchMyLtd": "",
            "srchMyLng": "",
            "srchDstnc": "",
            "gNowPage": "1",
            "srchGoodsId": ""
        }

        # 🛠️ 안전망: 멀티 비동기 환경에서 특정 구역의 Referer 조작 시 헤더 동시 오염 방지를 위한 카피 스코프 선언
        req_headers = headers.copy()
        req_headers["Referer"] = f"https://www.foresttrip.go.kr/com/login.do?hmpgId={camp_id}"

        try:
            # 🛠️ GET 전용 params 매핑 처리 완수
            response = await client.get(url, params=data, headers=req_headers, timeout=10.0)

            if response.status_code != 200:
                logger.error(f"[!] 구역 {target_group} 서버 응답 실패: 상태 코드 {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, "html.parser")
            site_list = soup.select("div.list_box")
            found_sites = []
            
            for site in site_list:
                try:
                    # ① 실제 예약 버튼 엘리먼트 추출
                    btn_rsrvt = site.select_one(".btn_group a.board .txtRsrvt")
                    btn_wtng = site.select_one(".btn_group a.board .txtWtng")
                    
                    # '대기신청' 버튼이 켜져있거나 '예약하기' 문구가 없으면 매진이므로 패스합니다.
                    if not btn_rsrvt or (btn_wtng and btn_wtng.get("style") != "display:none;"):
                        continue

                    # ② 고유 상품 코드(goodsId) 추출 
                    item_link = site.select_one("a.item")
                    if not item_link:
                        continue
                    
                    goods_id = item_link.get("data-value", "").strip()

                    # ③ 사이트명(방 이름) 추출 및 정제
                    opt1_tag = site.select_one(".opt1")
                    if not opt1_tag:
                        continue
                        
                    if opt1_tag.select_one(".icon_group"):
                        pure_text = opt1_tag.text.replace("사용가능 시설", "").strip()
                    else:
                        pure_text = opt1_tag.text.strip()
                    
                    # 불필요한 엔터값이나 연속된 공백 제거
                    site_name = " ".join(pure_text.split())

                    # ④ 전체 알람 시스템과 연동할 데이터 맵 누적
                    found_sites.append({
                        "site_name": site_name,         
                        "room_name": site_name,
                        "item_no": goods_id,            
                        "room_no": goods_id,
                        "room_area_no": target_group,   
                    })

                except Exception as parse_err:
                    logger.error(f"[!] list_box 요소 파싱 중 개별 스킵: {str(parse_err)}")
                    continue

            return found_sites
        except Exception as e:
            logger.error(f"[!] 구역 {target_group} 통신/파싱 중 예외 에러: {str(e)}")
        
        return None

    async def check_availability(self, params: dict):
        """
        [메인 로직] 모든 대상 구역을 병렬로 감시합니다.
        """
        self.execution_count += 1
        
        camp_id = params.get("camp_id")
        self.campsite_name = params.get("campsiteName", "이름 없음")
        req_date = params.get("date")
        stay_days = int(params.get("stay_day", "1"))
        uuid = params.get("watchUuid")
        target_site_groups = [str(code) for code in params.get("site_group_codes", [])]
        target_site_codes = [str(code) for code in params.get("site_codes", [])]

        next_date = datetime.strptime(req_date, "%Y-%m-%d") + timedelta(days=stay_days) 
        start_dt = req_date.replace("-", "")
        end_dt = next_date.strftime("%Y%m%d")

        # UI 업데이트 (실행 횟수 전송)
        await ws_manager.broadcast({
            "messageType": "monitor", 
            "data": {"uuid": uuid, "count": self.execution_count}
        })

        logger.info(f"[*] [Foresttrip] 감시 시작: {self.campsite_name} ({req_date}, {stay_days}박)")

        # 세션 초기화 방어 밸리데이션 영역
        if not self.cookies_initialized:
            await self.get_browser_cookies(camp_id)

        if not self.csrf_initialized:
            if not await self.create_csrf(camp_id):
                logger.error("[!] CSRF 발급 실패로 이번 턴의 조회를 스킵합니다.")
                return False

        if not self.login_initialized:
            if not await self.login(params):
                logger.error("[!] 국립휴양림 로그인 실패로 이번 턴의 감시를 진행할 수 없습니다.")
                return False

        # 공통 기저 헤더 바인딩 생성
        current_headers = UAGenerator.get_headers({
            "host": "www.foresttrip.go.kr",
            "origin": "https://www.foresttrip.go.kr",            
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })

        found_sites = []

        # 🛠️ 오타 수정 가이드: target_site_codes가 아니라 상위 구역인 target_site_groups 단락으로 루프 재설정 완료
        tasks = [
            self._check_single_group(self.client, camp_id, group, start_dt, end_dt, stay_days, current_headers)
            for group in target_site_codes
        ]

        # 모든 요청을 동시에 실행 및 결과 수집 (Parallel Execution)
        results = await asyncio.gather(*tasks)

        # 결과 중 None 제외하고 유효한 데이터만 추출
        raw_results = [r for r in results if r is not None]
        
        # 2차원 리스트 평탄화
        for site_list in raw_results:
            found_sites.extend(site_list)

        logger.info(f"{self.campsite_name} 캠핑장 빈자리 {len(found_sites)}개 발견")

        # 4. 빈자리 발견 시 처리
        if found_sites:
            sites_string = ", ".join([s['site_name'] for s in found_sites])
            
            for site in found_sites:
                link = f"https://www.foresttrip.go.kr/indvz/main.do?hmpgId={camp_id}"

                # 텔레그램 메시지 구성
                msg = (
                    f"<b>[국립자연휴양림] 빈자리 발견!</b>\n"
                    f"캠핑장: {self.campsite_name}\n"
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
                            f"[{self.campsite_name}] {sites_string} 자리가 났습니다."
                        )
                except: pass

                # 스케줄러가 종료될 때 client 안전 폐기
                await self.close_client()

                from main import scheduler
                await handle_monitoring_stop(scheduler, ws_manager, params, found_sites)
                logger.info(f"[SUCCESS] {self.campsite_name} 빈자리 발견: {sites_string}")
                break
            
            return True

        return False

    async def close_client(self):
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            logger.info("[*] [foresttrip] httpx AsyncClient 커넥션 풀을 안전하게 닫았습니다.")

    async def get_browser_cookies(self, camp_id: str):
        url = f"https://www.foresttrip.go.kr/indvz/main.do?hmpgId={camp_id}"
        logger.info(f"[*] {url}에서 쿠키를 새로 받습니다.")

        current_headers = UAGenerator.get_headers({
            "Host": "www.foresttrip.go.kr",    
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"     
        })             
            
        response = await self.client.get(url, headers=current_headers)
        self.cookies_initialized = True
        print(f"[*] 획득한 쿠키: {self.client.cookies}")    

    async def create_csrf(self, hmpg_id: str):
        """
        [내부 함수] 로그인/메인 페이지에 접속하여 CSRF 및 saltVals 파싱
        """
        login_page_url = f"https://www.foresttrip.go.kr/com/login.do?hmpgId={hmpg_id}"
        logger.info(f"[*] {login_page_url}에서 csrf를 새로 받습니다.")

        current_headers = UAGenerator.get_headers({
            "Host": "www.foresttrip.go.kr",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })

        try:
            response = await self.client.get(login_page_url, headers=current_headers, timeout=15.0)
            soup = BeautifulSoup(response.text, "html.parser")

            csrf_element = soup.select_one("#fripPotForm input[name=_csrf]")
            salt_element = soup.select_one("#fripPotForm input[name=saltVals]")

            self._csrf = csrf_element.get("value", "") if csrf_element else ""
            self.saltVals = salt_element.get("value", "") if salt_element else ""
            
            logger.info(f"csrf : {self._csrf}, saltVals: {self.saltVals}")
            print(f"[*] [{self.campsite_name}] csrf 생성 완료: {self._csrf}")

            self.csrf_initialized = True
            return True

        except Exception as e:
            logger.error(f"[!] csrf 생성 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return False        

    async def login(self, params_config: dict):
        """
        [내부 함수] 수집된 CSRF 토큰과 유저 정보를 바탕으로 서버에 로그인 POST 요청을 보냅니다.
        """
        hmpg_id = params_config.get("hmpgId", "")
        login_url = f"https://www.foresttrip.go.kr/com/login"

        logger.info(f"[*] {login_url}에서 로그인을 처리합니다.")

        data = {
            "_csrf": self._csrf,
            "loginId": params_config.get("userId", ""),
            "loginPwd": params_config.get("userPw", ""),
            "socialToken": "",
            "passCI": "",
            "simpleCI": "",
            "targetUrl": "",
            "saveId": "",
            "mmberNm": "",
            "mmberBrthd": "",
            "signedVals": "",
            "saltVals": self.saltVals
        }
        print(f"[*] 쿠키: {self.client.cookies}")  
        # pprint.pprint(data)

        current_headers = UAGenerator.get_headers({
            "Host": "www.foresttrip.go.kr",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.foresttrip.go.kr",
            "Referer": f"https://www.foresttrip.go.kr/com/login.do?hmpgId={hmpg_id}"
        })

        try:
            response = await self.client.post(login_url, data=data, headers=current_headers, timeout=15.0)
            logger.info(f"[{self.campsite_name}] 로그인 응답 상태 코드: {response.status_code}")
            print(f"[*] [{self.campsite_name}] 로그인 시도 상태: {response.status_code}")

            if response.status_code in [200, 302]:
                self.login_initialized = True
                return True
            return False

        except Exception as e:
            logger.error(f"[!] 로그인 요청 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
    async def get_netfunnel_key(self, service_id="service_1", action_id="action2"):
        """
        [넷퍼넬 우회] 대기열 서버에 직접 찔러서 즉시 통과 키(Key)를 받아옵니다.
        """
        import time
        timestamp = int(time.time() * 1000)
        
        nf_url = "https://nf.foresttrip.go.kr/ts.wseq"
        params = {
            "opcode": "5101",
            "nfid": "0",
            "prefix": "NetFunnel.gRtype=5101;",
            "sid": service_id,
            "aid": action_id,
            "js": "yes",
            str(timestamp): ""
        }
        
        headers = {
            "Host": "nf.foresttrip.go.kr",
            "User-Agent": self.client.headers.get("User-Agent", "Mozilla/5.0"),
            "Referer": "https://www.foresttrip.go.kr/"
        }

        try:
            response = await self.client.get(nf_url, params=params, headers=headers, timeout=10.0)
            res_text = response.text

            match = re.search(r"result='(.*?)'", res_text)
            if not match:
                logger.error("[!] 넷퍼넬 응답 포맷 파싱 실패")
                return ""

            result_content = match.group(1)
            result_parts = result_content.split(":")
            
            if len(result_parts) < 3:
                return ""

            status_code = result_parts[1] 
            payload_str = result_parts[2] 

            kv_pairs = dict(item.split("=") for item in payload_str.split("&") if "=" in item)
            netfunnel_key = kv_pairs.get("key", "")

            if status_code == "200":
                logger.info(f"[*] 넷퍼넬 대기열 즉시 통과 완료. Key 획득 성공")
                return netfunnel_key
            
            elif status_code == "201":
                nwait = kv_pairs.get("nwait", "다수")
                logger.warning(f"[!] 넷퍼넬 대기열 정체 발생 (앞에 {nwait}명 대기 중). 3초 후 재시도 필요.")
                return "WAIT"

        except Exception as e:
            logger.error(f"[!] 넷퍼넬 통신 중 예외 에러: {str(e)}")
        
        return ""    
    
    async def get_info(self, hmpg_id: str, campsite_name: str = None):
        """
        [유틸리티 기능] 국립자연휴양림 메인 페이지에서 구역 목록 선택상자를 긁어와 XML 텍스트를 출력합니다.
        """
        url = f"https://www.foresttrip.go.kr/indvz/main.do?hmpgId={hmpg_id}"
        display_name = campsite_name if campsite_name else getattr(self, "campsite_name", "이름 없음")

        current_headers = UAGenerator.get_headers({
            "Host": "www.foresttrip.go.kr",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })

        try:
            response = await self.client.get(url, headers=current_headers, timeout=20.0)
            
            if response.status_code != 200:
                logger.error(f"[!] 정보 조회 실패: 상태 코드 {response.status_code}")
                return False

            soup = BeautifulSoup(response.text, "html.parser")
            site_options = soup.select("select#goodsClssCd > option")

            print("\n" + "="*50)
            print("🚀 [XML 데이터 생성 완료] 복사하여 XML 파일에 붙여넣으세요.")
            print("="*50)
            print("<campsite>")
            print(f"\t<name>{display_name}</name>")
            print(f"\t<hmpgId>{hmpg_id}</hmpgId>")
            print("\t<maxStayDay>2</maxStayDay>")
            print("\t<sites>")

            for option in site_options:
                site_name = option.text.strip()
                site_code = option.get("value", "").strip()

                if site_code:
                    print(f'\t\t<site code="{site_code}"><![CDATA[{site_name}]]></site>')

            print("\t</sites>")
            print("</campsite>")
            print("="*50 + "\n")

            return True

        except Exception as e:
            logger.error(f"[!] 휴양림 정보(XML용) 파싱 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

# 🛠️ 수정 포인트 1: 단독 테스트 전용 비동기 런 함수와 메인 진입점을 클래스 외부로 완전히 격리시켰습니다.
async def test_run():
    # 1. 국립자연휴양림 모니터 객체 생성
    monitor = ForesttripMonitor()
    
    # 2. 테스트할 국립자연휴양림 기관 정보 설정
    test_hmpg_id = "0111" 
    test_campsite_name = "유명산자연휴양림"
    
    print("\n==================================================")
    print(f"📡 [{test_campsite_name}] get_info 단독 테스트를 시작합니다...")
    print("==================================================\n")
    
    # 3. get_info 메서드만 딱 1회 강제 호출
    success = await monitor.get_info(hmpg_id=test_hmpg_id, campsite_name=test_campsite_name)
    
    print("\n--------------------------------------------------")
    print(f"🎯 테스트 완료 여부: {'성공(SUCCESS)' if success else '실패(FAILED)'}")
    print("--------------------------------------------------\n")
    
    # 4. 테스트 종료 후 커넥션 풀 자원 안전하게 닫기
    await monitor.close_client()

if __name__ == "__main__":
    # 비동기 루프 점화
    asyncio.run(test_run())