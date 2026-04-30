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
- /camping-scanner/app/platforms # 사이트별 크롤링 모듈 (전략 패턴)
- /camping-scanner/app/platforms/base.py # 추상 베이스 클래스
- /camping-scanner/app/platforms/interpark.py # 인터파크 크롤링 로직
- /camping-scanner/app/platforms/thankq.py # 땡큐캠핑 크롤링 로직
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

- [] **User-Agent 추가 검토:** IP 차단 방지를 위한 'User-Agent' 관련 기능을 추가 하고 싶어.

## 3. 분석 대상 코드

### [/camping-scanner/app/platforms/interpark.py]

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

# 로거 가져오기
logger = logging.getLogger("camping.interpark")


class InterparkMonitor:

    def __init__(self):

        self.execution_count = 0  # 실행 횟수를 저장할 변수

        # 생성자에서는 파라미터를 받지 않고 공통 설정만 초기화합니다.
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }



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

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, cookies={"auth": "token"})

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
                            "res_days": res_days,
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

                    from main import scheduler # 순환 참조 방지를 위해 함수 내 임포트
                    await handle_monitoring_stop(scheduler, ws_manager, params, found_sites)

                    return True

                return False

            except Exception as e:
                logger.error(f"[{params['camp_id']}] 잔여석 확인 중 에러: {e}")


```
