from unittest import result
from urllib import response

import httpx
import asyncio
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime, timedelta
import pprint 
from .base import CampingMonitor
from core.notifier import notifier
from core.websocket_manager import ws_manager
from core.termination_handler import handle_monitoring_stop
from core.ua_generator import UAGenerator

# 로거 설정
logger = logging.getLogger("camping.foresttrip")

class ForesttripMonitor(CampingMonitor): 

    def __init__(self):
        super().__init__()
        self.execution_count = 0  # 실행 횟수 카운터
        self.campsite_name = ""
        self._csrf = ""
        self.saltVals = ""
        self.client = httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False)
        self.cookies_initialized = False
        self.csrf_initialized = False
        self.login_initialized = False

    async def _check_single_group(self, client, camp_id, target_group, start_date, end_date, stay_days, headers):
        """
        [내부 함수] 단일 구역(Group)의 예약 가능 여부를 체크합니다.
        """
        logger.info(f"[*] [foresttrip] 구역 감시 시작 ID: {target_group} 요청일: ({start_date}, {stay_days}박)")

        nf_key = await self.get_netfunnel_key(service_id="service_1", action_id="action2")
        if nf_key == "WAIT" or nf_key == "":
            logger.info(f"[*] [foresttrip] 구역 감시 시작 실패: 대기열에 걸렸음.")
            return None # 대기열이 걸렸거나 실패 시 이번 조회를 우회/스킵 처리

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

        #pprint.pprint(data)

        try:
            # 타임아웃 발생 시 무한 대기를 방지하기 위해 명시적으로 지정
            response = await client.get(url, params=data, headers=headers, timeout=10.0)

            if response.status_code != 200:
                logger.error(f"[!] 구역 {target_group} 서버 응답 실패: 상태 코드 {response.status_code}")
                return None
            
            # 응답 데이터가 정상적으로 수신되는지 터미널 확인용

            print(response.text)
            soup = BeautifulSoup(response.text, "html.parser")
            site_list = soup.select("div.list_box")
            found_sites = []
            
            for site in site_list:
                try:
                    # ① 실제 예약 버튼 엘리먼트 추출
                    # <span class="txtRsrvt">예약하기</span>가 들어있는 태그를 찾습니다.
                    btn_rsrvt = site.select_one(".btn_group a.board .txtRsrvt")
                    btn_wtng = site.select_one(".btn_group a.board .txtWtng")
                    
                    # 💡 중요 방어 로직: '대기신청' 버튼이 켜져있거나 '예약하기' 문구가 없으면 매진이므로 패스합니다.
                    if not btn_rsrvt or (btn_wtng and btn_wtng.get("style") != "display:none;"):
                        # '대기신청' 상태이거나 예약하기가 없으면 다음 사이트로 넘어감
                        continue

                    # ② 고유 상품 코드(goodsId / item_no) 추출 
                    # <a class="item" data-value="G0111..."> 태그에서 가져옵니다.
                    item_link = site.select_one("a.item")
                    if not item_link:
                        continue
                    
                    goods_id = item_link.get("data-value", "").strip()

                    # ③ 사이트명(방 이름) 추출 및 정제
                    # 자식 노드들의 텍스트가 섞여서 나올 수 있으므로, 내부의 아이콘 텍스트를 지우고 
                    # 순수 텍스트(예: "[야영데크]야영데크(106)")만 분리해 냅니다.
                    opt1_tag = site.select_one(".opt1")
                    if not opt1_tag:
                        continue
                        
                    # clone 개념으로 텍스트 정제 (icon_group 안의 문자를 지우고 남은 text만 가져옴)
                    # 만약 icon_group이 있다면 그 안의 글자를 날려버립니다.
                    if opt1_tag.select_one(".icon_group"):
                        # 추출용 임시 텍스트 연산 (전체 텍스트에서 아이콘용 숨김 텍스트 제거)
                        pure_text = opt1_tag.text.replace("사용가능 시설", "").strip()
                    else:
                        pure_text = opt1_tag.text.strip()
                    
                    # 불필요한 엔터값이나 연속된 공백 제거
                    site_name = " ".join(pure_text.split())

                    # ④ 디버깅 터미널 출력
                    #print(f"🌲 [빈자리 검출] {site_name} (코드: {goods_id}) - 즉시 예약 가능!")

                    # ⑤ 전체 알람 시스템과 연동할 데이터 맵 누적
                    found_sites.append({
                        "site_name": site_name,         # 예: [야영데크]야영데크(106)
                        "room_name": site_name,
                        "item_no": goods_id,            # 예: G01110200200300144
                        "room_no": goods_id,
                        "room_area_no": target_group,   # 상위에서 주입받은 구역코드
                    })

                except Exception as parse_err:
                    # 특정 한 자리를 파싱하다가 에러가 나도 전체 스케줄러가 죽지 않도록 방어
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

        # 수정 포인트 3: 쿠키 및 로그인 파라미터 보완
        if not self.cookies_initialized:
            await self.get_browser_cookies(camp_id)

        if not self.csrf_initialized:
            if not await self.create_csrf(camp_id):
                logger.error("[!] CSRF 발급 실패로 이번 턴의 조회를 스킵합니다.")
                return False

        if not self.login_initialized:
            if not await self.login(params):
                logger.error("[!] 국립휴양림 로그인 실패로 이번 턴의 감시를 진행할 수 없습니다. 계정 정보를 확인하세요.")
                return False


        # 랜덤 헤더 생성
        current_headers = UAGenerator.get_headers({
            "host": "www.foresttrip.go.kr",
            "origin": "https://www.foresttrip.go.kr",            
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "content-type": "application/x-www-form-urlencoded",
            "Referer": f"https://www.foresttrip.go.kr/com/login.do?hmpgId={camp_id}"
        })


        found_sites = []

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
                site_name = site.get("site_name")

                link = f"https://www.foresttrip.go.kr/indvz/main.do?hmpgId={camp_id}"
                #link = f"https://www.foresttrip.go.kr/rep/or/sssn/fcfsRsrvtPssblGoodsDetls.do?hmpgId={camp_id}&menuId=001001"

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

        # 수정 포인트 5: Host를 주소 도메인과 완벽하게 일치시킴
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
        pprint.pprint(data)  # 로그인 데이터 디버깅용 출력

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
        
        # 1. 넷퍼넬 규격 URL 조립 (opcode 5101 = getTidChkEnter)
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
            # 2. 대기열 서버에 통과 요청 선언
            response = await self.client.get(nf_url, params=params, headers=headers, timeout=10.0)
            res_text = response.text

            # 3. 정규식을 통해 응답 데이터 추출 (result='...' 내부 문자열 파싱)
            # 예: 5101:200:key=토큰값&ip=...
            match = re.search(r"result='(.*?)'", res_text)
            if not match:
                logger.error("[!] 넷퍼넬 응답 포맷 파싱 실패")
                return ""

            result_content = match.group(1)
            result_parts = result_content.split(":")
            
            if len(result_parts) < 3:
                return ""

            status_code = result_parts[1] # '200' 또는 '201'
            payload_str = result_parts[2] # 'key=토큰값&ip=...'

            # 쿼리스트링 파서처럼 key= 값 파싱
            kv_pairs = dict(item.split("=") for item in payload_str.split("&") if "=" in item)
            netfunnel_key = kv_pairs.get("key", "")

            if status_code == "200":
                logger.info(f"[*] 넷퍼넬 대기열 즉시 통과 완료. Key 획득 성공")
                return netfunnel_key
            
            elif status_code == "201":
                # 만약 사람이 몰려 대기 상태(201)라면 nwait(대기수)가 반환됩니다.
                # 크롤러 특성상 대기 팝업을 띄울 수 없으므로 잠시 후 재시도 하거나 건너뛰어야 합니다.
                nwait = kv_pairs.get("nwait", "다수")
                logger.warning(f"[!] 넷퍼넬 대기열 정체 발생 (앞에 {nwait}명 대기 중). 3초 후 재시도 필요.")
                return "WAIT"

        except Exception as e:
            logger.error(f"[!] 넷퍼넬 통신 중 예외 에러: {str(e)}")
        
        return ""    