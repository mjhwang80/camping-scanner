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
- /camping-scanner/app/platforms/mirihae.py # 미래해 크롤링 로직
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
