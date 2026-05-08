## 프로젝트 구조

- /camping-scanner/.venv # 가상환경
- /camping-scanner/app # 소스 경로
- /camping-scanner/app/main.py # FastAPI 엔트리 포인트 (Server 기동)
- /camping-scanner/app/core/ # 핵심 공통 로직
- /camping-scanner/app/core/config_loader.py # YAML 설정 로드
- /camping-scanner/app/core/logger.py # 로그 핸들러
- /camping-scanner/app/core/notifier.py # 텔레그램 알림 발송
- /camping-scanner/app/core/scheduler.py # APScheduler 설정 및 시작
- /camping-scanner/app/core/termination_handler.py # 감시 종료 및 UI 제거 로직
- /camping-scanner/app/core/websocket_manager.py # 웹소켓 연결 관리
- /camping-scanner/app/core/ua_generator.py # User-Agent 정보를 관리하고 무작위로 반환해 줄 유틸리티
- /camping-scanner/app/core/tray_icon.py # 트래이 아이콘
- /camping-scanner/app/core/browser_handler.py # Playwright 기반 보안 통과
- /camping-scanner/app/platforms # 사이트별 크롤링 모듈 (전략 패턴)
- /camping-scanner/app/platforms/base.py # 추상 베이스 클래스
- /camping-scanner/app/platforms/interpark.py # 인터파크 크롤링 로직
- /camping-scanner/app/platforms/interpark_reserver.py # 자동예약처리 로직
- /camping-scanner/app/platforms/mirihae.py # 미래해 크롤링 로직
- /camping-scanner/app/platforms/thankq.py # 땡큐캠핑 크롤링 로직
- /camping-scanner/app/platforms/maketicket.py # 메이크티켓 크롤링 로직
- /camping-scanner/app/platforms/xticket.py # X티켓 크롤링 로직
- /camping-scanner/app/services # 비즈니스 로직 처리 (모니터링 서비스 등)
- /camping-scanner/app/services/monitor_service.py
- /camping-scanner/app/services/notification.py
- /camping-scanner/app/static # CSS, JS, Image 등 정적 파일
- /camping-scanner/app/static/css/style.css
- /camping-scanner/app/static/js/script.js # 프론트엔드 메인 로직
- /camping-scanner/app/templates # HTML 템플릿 (Jinja2)
- /camping-scanner/app/templates/index.html # 웹 초기 화면
- /camping-scanner/config # 배포시 외부에서 수정 가능한 설정 파일 경로
- /camping-scanner/config/config.yaml # 서버 포트, API 토큰 등 설정 (Git 제외 대상)
- /camping-scanner/data # 캠핑장 정보 XML 파일들
- /camping-scanner/data/thankqcamping-campsite.xml # 땡큐캠핑 목록 XML
- /camping-scanner/data/interpark-campsite.xml # 인터파크 목록 XML
- /camping-scanner/data/camfit-campsite.xml
- /camping-scanner/data/campingtalk-campsite.xml
- /camping-scanner/data/etc-campsite.xml
- /camping-scanner/data/forcamper-campsite.xml
- /camping-scanner/data/maketicket-campsite.xml
- /camping-scanner/data/mirihae-campsite.xml
- /camping-scanner/data/naver-campsite.xml
- /camping-scanner/data/xticket-campsite.xml
- /camping-scanner/logs # 로그 저장소
- /camping-scanner/.gitignore # Git 관리 예외 설정 파일
- /camping-scanner/.prettierignore
- /camping-scanner/.prettierrc
- /camping-scanner/build.py # 빌드 배포를 위한 파일
- /camping-scanner/README.md
- /camping-scanner/requirements.txt

## 1. 프로젝트 개요

- **언어 및 프레임워크:** python 3.14.0
- **목적:** 캠핑장 빈자리 알람 프로그램

## 2. 질문 사항

- [] ** 토큰 추출 :** 여러단계를 리다이렉트 하는거 같은데 끝가지 가도록 할 수 있어?.

## 3. 분석 대상 코드

### [/camping-scanner/app/platforms/mirihae.py]

```python
from fastapi import params
import httpx
import asyncio
from bs4 import BeautifulSoup
import pprint  # Java의 Pretty Printer (Jackson 등) 역할
import re
from datetime import datetime, timedelta

import logging

from base import CampingMonitor


# 로거 가져오기
logger = logging.getLogger("camping.mirihae")


class MirihaeMonitor:

    def __init__(self):
        self.execution_count = 0  # 실행 횟수를 저장할 변수
        self.token = None  # 토큰정보

    async def check_availability(self, params: dict):

        camp_id = params.get("camp_id")



        token = await self.get_token(params)

        print(token)

        return True


    async def get_token(self, params: dict):
        camp_id = params.get("camp_id")

        url = f"https://mirihae.com/pccamp/campsite/{camp_id}"

        headers = {
             "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            ,"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
            ,"Referer": "https://mirihae.com/"
            ,"Upgrade-Insecure-Requests": "1"
        }

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=headers, timeout=15.0)
                response.raise_for_status()

                # 최종 도달한 페이지에서 BeautifulSoup으로 토큰 추출
                soup = BeautifulSoup(response.text, "html.parser")
                token_element = soup.find(id="tocken")

                if token_element:
                    self.token = token_element.get("value")
                    logger.info(f"[*] 리다이렉트 완료 후 토큰 획득 성공: {self.token}")
                else:
                    logger.warning("[!] 토큰 엘리먼트를 찾을 수 없습니다. 보안 단계가 추가되었을 수 있습니다.")

            except Exception as e:
                logger.error(f"[!] 리다이렉트 추적 중 오류 발생: {e}")

        return self.token



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
```

## 1. 질문 사항

- [] ** 세센 유지 :** 요청시 세션을 유지할 수 있는 방법이 없을까?

## 2. 분석 대상 코드

### [/camping-scanner/app/platforms/xticket.py]

```python
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
import time
import logging

# 로거 가져오기
logger = logging.getLogger("camping.xticket")


class XticketMonitor:

    def __init__(self):
        self.execution_count = 0  # 실행 횟수를 저장할 변수
        self.client = httpx.AsyncClient(timeout=15.0, )
        self.cookies_initialized = False

    async def check_availability(self, params: dict):

        self.execution_count += 1  # 호출될 때마다 1 증가
        print(f"[*] {params['camp_id']} xticket 조회 중...")

        #기본 값
        camp_id = params.get("camp_id")
        groupCode = params.get("groupCode") #idKey
        uuid = params.get("watchUuid")
        campsiteName = params.get("campsiteName")

        #예약 정보
        req_date = params.get("date") # 예: "2026-05-14"
        stay_days = int(params.get("stay_day", "1"))


        start_datetime = datetime.strptime(req_date, "%Y-%m-%d")
        end_dt = start_datetime + timedelta(days=stay_days - 1)

        start_dt = req_date = req_date.replace("-", "")


        #감시 사이트 대상
        target_site_codes = params.get("site_codes", [])
        target_site_codes = [str(code) for code in target_site_codes]

         #감시 정보 전달
        await ws_manager.broadcast({"messageType" : "monitor", "data" : {"uuid" : uuid, "count" : self.execution_count}})

        logger.info(f"[*] xticket 감시 시작 - 캠핑장 : {params['campsiteName']} 캠핑장 ID: {camp_id} 예약일: {req_date} 숙박일수: {stay_days}")

        if not self.cookies_initialized:
            await self.get_browser_cookies(camp_id)






        current_headers = UAGenerator.get_headers({
            "Accept": "*/*",
            "Host": "camp.xticket.kr",
            "Origin": "https://forest.maketicket.co.kr",
            "Referer": f"https://camp.xticket.kr/web/main?shopEncode={camp_id}",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        })


        url = "https://camp.xticket.kr/Web/Book/GetBookProduct010001.json"
        data = {
            "start_date" : start_dt,
            "end_date" : end_dt.strftime("%Y%m%d"),
            "book_days" : stay_days,
            "two_stay_days" : "0",
            "shopCode" : groupCode,
            "time" : int(time.time() * 1000),
        }



        found_sites = []

        for area in target_site_codes:

            data["product_group_code"] = area

            pprint.pprint(data)

            try:
                response = await self.client.post(url, data=data, headers=current_headers)
                print(response.status_code)
                print(response.text)
                result = response.json()

                site_list = result.get("data", {}).get("bookProductList", [])

                for find_site in site_list:
                    select_yn = find_site.get("select_yn", "0")
                    if select_yn == "1":

                        product_name = find_site.get("product_name")
                        product_code = find_site.get("product_code")

                        logger.info(f"[{campsiteName}] {product_name} 사이트 예약 가능! (ID: {product_code})")
                        found_sites.append({
                            "shopCode": groupCode,
                            "shopEncode": camp_id,
                            "product_name": product_name,
                            "site_name": product_name,
                            "product_code": product_code,

                        })

            except Exception as e:
                logger.error(f"[{params['camp_id']}] 잔여석 확인 중 에러: {e}")

        sites_string = ""
        if found_sites:

            site_names = [s['site_name'] for s in found_sites]
            sites_string = ", ".join(site_names)

            for site in found_sites:
                #pprint.pprint(site)


                link = f"https://camp.xticket.kr/web/main?shopEncode={camp_id}"

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
                        "site_name" : site["ri_name"],

                        "shopCode" : groupCode,
                        "shopEncode" : camp_id
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

    async def get_browser_cookies(self, camp_id:str):

        url = f"https://camp.xticket.kr/web/main?shopEncode={camp_id}"

        logger.info(f"[*] {url}에서 쿠키를 새로 받습니다.")

        current_headers = UAGenerator.get_headers({
            "Host": "camp.xticket.kr" ,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        })

        response = await self.client.get(url, headers=current_headers)
        self.cookies_initialized = True
        # 2. 서버가 보낸 쿠키 확인
        print(f"[*] 획득한 쿠키: {self.client.cookies}")


```
