#미술관옆 캠핑장
##/app/platforms/artmuseum.py
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
logger = logging.getLogger("camping.artmuseum")

class ArtmuseumCampingMonitor(CampingMonitor): 
    def __init__(self):
        super().__init__()
        self.execution_count = 0  # 실행 횟수 카운터
        self.client = httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False)
        self.cookies_initialized = False
        self.login_initialized = False
        self.access_token = ""

    async def _check_single_group(self, client, camp_id, target_group, start_date, end_date, stay_days, headers):

        logger.info(f"[*] [미술관옆캠핑장] 구역 감시 시작 ID: {target_group} 요청일: ({start_date}, {stay_days}박)")

        """
        [내부 함수] 단일 구역(Group)의 예약 가능 여부를 체크합니다.
        자바의 CompletableFuture 내에서 실행되는 Task와 유사합니다.
        """
        url = f"https://reserve.yjuc.or.kr/main/camping/camp_req_place_list.json"
        data = {
            "stayDays" : stay_days,
            "checkIn" : start_date,
            "checkOut" : end_date,
            "cpgtIdx" : target_group       
        }

        pprint.pprint(data)

        try:
            # 타임아웃을 넉넉히 주어 네트워크 지연에 대비
            response = await client.post(url, data=data, headers=headers, timeout=10.0)
            #print(response.text)
            if response.status_code != 200:
                return None

            result = response.json()
            pin_list = result.get("list", [])
            found_sites = []
            for pin in pin_list:
                cds_cd = pin.get("cdsCd")
                cds_cd_name = pin.get("cdsCdNm")
                cpg_nm = pin.get("cpgNm")
                cpgt_idx = pin.get("cpgtIdx")
                cpt_idx = pin.get("cptIdx")
                cpat_idx = pin.get("cpatIdx")

                # 예약 가능한 상태인지 체크 (예: CDS0100000 예약 가능, CDS0200000 예약 불가능)
                if cds_cd == 'CDS0100000':
                    print(pin)
                    found_sites.append({
                        "site_name": cpg_nm,
                        "room_name": cpg_nm,
                        "item_no": cpt_idx,
                        "room_area_no": cpgt_idx,
                    })      

            return found_sites
        except Exception as e:
            logger.error(f"[!] 구역 {target_group} 파싱 중 오류: {str(e)}")
        
        return None

    async def check_availability(self, params: dict):
        """
        [메인 로직] 모든 대상 구역을 병렬로 감시합니다.
        """
        self.execution_count += 1
        
        camp_id = params.get("camp_id")
        campsite_name = params.get("campsiteName", "이름 없음")
        req_date = params.get("date")
        stay_days = int(params.get("stay_day", "1"))
        uuid = params.get("watchUuid")
        target_site_codes = [str(code) for code in params.get("site_codes", [])] #사이트 코드
        target_site_groups = [str(code) for code in params.get("site_group_codes", [])] #사이트 그룹 코드

        next_date = datetime.strptime(req_date, "%Y-%m-%d") + timedelta(days=stay_days) 
        #start_dt = req_date.replace("-", ""); 
        start_dt = req_date; 
        end_dt = next_date.strftime("%Y-%m-%d")

        # UI 업데이트 (실행 횟수 전송)
        await ws_manager.broadcast({
            "messageType": "monitor", 
            "data": {"uuid": uuid, "count": self.execution_count}
        })

        logger.info(f"[*] [미술관옆캠핑장] 감시 시작: {campsite_name} ({req_date}, {stay_days}박)")

        # 세션 초기화 방어 밸리데이션 영역
        if not self.cookies_initialized:
            await self.get_browser_cookies(camp_id)

        if not self.login_initialized:
            if not await self.login(params):
                logger.error("[!] 미술관옆캠핑장 로그인 실패로 이번 턴의 감시를 진행할 수 없습니다.")
                return False
            
        # 랜덤 헤더 생성
        current_headers = UAGenerator.get_headers({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Host": "reserve.yjuc.or.kr",
            "Origin": "https://reserve.yjuc.or.kr",
            "Referer": "https://reserve.yjuc.or.kr/main/camping/camp_rent_req_list.do",
            "X-Requested-With": "XMLHttpRequest"
        })


        
        self.do_refresh_token(self.client, self.access_token)


        found_sites = []

        # 비동기 클라이언트 생성 (커넥션 풀 재사용)
        # 1. 모든 구역에 대해 Task 생성 (Java의 Stream -> List<CompletableFuture>와 유사)
        tasks = [
            self._check_single_group(self.client, camp_id, group, start_dt, end_dt, stay_days, current_headers)
            for group in target_site_groups
        ]

        # 2. 모든 요청을 동시에 실행 및 결과 수집 (Parallel Execution)
        results = await asyncio.gather(*tasks)

        # 2차원 리스트를 1차원으로 평탄화 (Flatten)
        found_list = []
        for r in results:
            if r is not None and isinstance(r, list):
                found_list.extend(r) # 리스트 안의 요소를 하나씩 추가
        
        #선택된 사이트만 목록에 넣기
        found_sites = [site for site in found_list if str(site["item_no"]) in target_site_codes]

        logger.info(f"{campsite_name} 캠핑장 빈자리 {len(found_sites)}개 발견")

        # 4. 빈자리 발견 시 처리
        if found_sites:
            # 첫 번째 발견된 장소를 대표 링크로 사용
            link = f"https://reserve.yjuc.or.kr/main/camping/camp_rent_req_list.do"
            sites_string = ", ".join([s['site_name'] for s in found_sites])

            # 텔레그램 메시지 구성
            msg = (
                f"<b>[미술관옆 캠핑장] 빈자리 발견!</b>\n"
                f"캠핑장: {campsite_name}\n"
                f"날짜: {req_date} ({stay_days}박)\n"
                f"구역: {sites_string}\n"
                f"<a href='{link}'>예약 페이지 바로가기</a>"
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
                        f"[{campsite_name}] {sites_string} 자리가 났습니다."
                    )
            except: pass

            # 감시 자동 종료 처리
            from main import scheduler
            await handle_monitoring_stop(scheduler, ws_manager, params, found_sites)
            
            logger.info(f"[SUCCESS] {campsite_name} 빈자리 발견: {sites_string}")
            return True

        return False

    async def close_client(self):
        """외부에서 호출 가능한 클라이언트 정리 메서드"""
        if hasattr(self, 'client') and self.client:
            if not self.client.is_closed:
                await self.client.aclose()
                logger.info("[*] [미술관옆캠핑장] 클라이언트가 정상적으로 정리되었습니다.")


    async def get_browser_cookies(self, camp_id: str):
        url = f"https://reserve.yjuc.or.kr/main/login/login.do"
        logger.info(f"[*] {url}에서 쿠키를 새로 받습니다.")

        current_headers = UAGenerator.get_headers({
            "Host": "reserve.yjuc.or.kr",    
            "Referer": "https://reserve.yjuc.or.kr/",    
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"     
        })             
            
        response = await self.client.get(url, headers=current_headers)
        self.cookies_initialized = True
        print(f"[*] 획득한 쿠키: {self.client.cookies}")        

    async def login(self, params_config: dict):
        """
        [내부 함수] 로그인 POST 요청을 보냅니다.
        """
        login_url = f"https://member.yjuc.or.kr/api/auth/login"

        logger.info(f"[*] {login_url}에서 로그인을 처리합니다.")

        data = {
            "site_idx": 2,
            "mem_id": params_config.get("userId", ""),
            "mem_pwd": params_config.get("userPw", ""),
        }
         
        # pprint.pprint(data)

        current_headers = UAGenerator.get_headers({
            "Host": "reserve.yjuc.or.kr",    
            "Referer": "https://reserve.yjuc.or.kr/",    
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"     
        })  

        try:
            response = await self.client.post(login_url, data=data, headers=current_headers, timeout=15.0)
            logger.info(f"[양주 미술관옆캠핑장] 로그인 응답 상태 코드: {response.status_code}")
            print(f"[*] [양주 미술관옆캠핑장] 로그인 시도 상태: {response.status_code}")
            
            if response.status_code in [200, 302]:
                self.login_initialized = True

                result = response.json()
                token = result.get("AUTH_TOKEN", {}).get("ACCESS_TOKEN")
                if token:
                    self.access_token = token
                    print(f"토큰 확인됨: {token}")
                    # 이후 헤더 설정 등에 사용
                    session_data = await self.do_create_session(self.client, token)
                else:
                    print("ACCESS_TOKEN이 존재하지 않습니다.")

                print(f"[*] 쿠키: {self.client.cookies}") 

                return True
            return False

        except Exception as e:
            logger.error(f"[!] 로그인 요청 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    async def do_create_session(self, client: httpx.AsyncClient, token: str):
        """
        인증 토큰을 사용하여 세션을 생성하는 비동기 함수
        
        :param client: 재사용 가능한 httpx.AsyncClient 인스턴스
        :param token: Bearer 인증에 사용할 액세스 토큰
        :return: 응답 데이터 (dict) 또는 None
        """
        url = "https://reserve.yjuc.or.kr/main/login/createSession.json"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            # POST 요청 수행
            response = await client.post(url, headers=headers)
            
            # 상태 코드 확인 (200 OK)
            response.raise_for_status()
            
            print(f"[*] 쿠키: {self.client.cookies}") 

            #logger.info(f"세션 생성 성공:{response.text}")
            return "data"
            
        except httpx.HTTPStatusError as e:
            logger.error(f"세션 생성 실패 (HTTP 상태 코드 오류): {e.response.status_code}")
        except Exception as e:
            logger.error(f"세션 생성 중 예외 발생: {e}")
            
        return None
    

    async def do_refresh_token(self, client: httpx.AsyncClient, current_token: str):
        """
        토큰 검증 및 갱신 프로세스를 수행합니다.
        
        :param client: 공용 httpx.AsyncClient 인스턴스
        :param mem_url: API 기본 URL
        :param current_token: 현재 로컬에 저장된 액세스 토큰
        :return: 갱신된 토큰 (str) 또는 None
        """
        try:
            # 1. 토큰 검증 API 호출
            verify_url = f"https://member.yjuc.or.kr/api/auth/verify"
            verify_headers = {"Authorization": f"Bearer {current_token}"}
            
            response = await client.post(verify_url, headers=verify_headers)
            response.raise_for_status()
            verify_data = response.json()
            
            # 결과 처리
            if verify_data.get("verify_result") == "TKN_OK":
                # 2. 토큰 갱신 API 호출
                refresh_url = f"https://member.yjuc.or.kr/api/auth/refresh"
                # Refresh 요청 시에는 Authorization 헤더를 비워두거나 필요에 따라 조정
                refresh_headers = {"Authorization": "Bearer "} 
                
                ref_response = await client.post(refresh_url, headers=refresh_headers)
                ref_data = ref_response.json()
                
                if ref_data.get("statusCode") == 500:
                    logger.error("토큰 갱신 서버 에러 발생")
                    return None
                
                # 3. 새로운 토큰 추출 및 세션 생성
                new_token = ref_data.get("AUTH_TOKEN", {}).get("ACCESS_TOKEN")
                if new_token:
                    logger.info("토큰 갱신 성공")
                    self.access_token = new_token
                    # 갱신 후 do_create_session을 호출하여 세션 동기화
                    await self.do_create_session(client, new_token)
                    return new_token
                    
            elif verify_data.get("verify_result") == "TKN_EXP":
                logger.warning("세션 만료: 로그아웃 처리 필요")
                # 로그아웃 처리가 필요한 경우의 로직을 여기에 구현하세요.
                
        except Exception as e:
            logger.error(f"토큰 갱신 프로세스 중 오류 발생: {e}")
            
        return None        