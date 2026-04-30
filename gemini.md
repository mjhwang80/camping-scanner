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

## 1. 질문 사항

- [] ** 목록 추출 :** json 결과 값에서 pinCategoryList 의 첫번재 pinList 배열 목록을 가져오고 싶어. result = response.json() 부터 자료 추출부터 for문 까지 예제를 보여줘.

## 2. 분석 대상 코드

### [json 파일 구조]

```json
{
    "preOpenCnt": 1,
    "pinCategoryList": [
        {
            "pinList": [
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000000998", "positionTop": "370", "positionLeft": "728", "color": "color1", "DATE_DIFF": 1, "categoryNm": "A사이트", "reserveCnt": 0, "itemNo": "1", "useAt": "Y", "itemNm": "A01", "categoryId": "CATEGORY_00000000113" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000000999", "positionTop": "397", "positionLeft": "740", "color": "color1", "DATE_DIFF": 1, "categoryNm": "A사이트", "reserveCnt": 1, "itemNo": "2", "useAt": "N", "itemNm": "A02", "categoryId": "CATEGORY_00000000113" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001000", "positionTop": "422", "positionLeft": "754", "color": "color1", "DATE_DIFF": 1, "categoryNm": "A사이트", "reserveCnt": 0, "itemNo": "3", "useAt": "Y", "itemNm": "A03", "categoryId": "CATEGORY_00000000113" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001001", "positionTop": "450", "positionLeft": "766", "color": "color1", "DATE_DIFF": 1, "categoryNm": "A사이트", "reserveCnt": 0, "itemNo": "4", "useAt": "Y", "itemNm": "A04", "categoryId": "CATEGORY_00000000113" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001002", "positionTop": "476", "positionLeft": "778", "color": "color1", "DATE_DIFF": 1, "categoryNm": "A사이트", "reserveCnt": 0, "itemNo": "5", "useAt": "Y", "itemNm": "A05", "categoryId": "CATEGORY_00000000113" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001003", "positionTop": "504", "positionLeft": "792", "color": "color1", "DATE_DIFF": 1, "categoryNm": "A사이트", "reserveCnt": 0, "itemNo": "6", "useAt": "Y", "itemNm": "A06", "categoryId": "CATEGORY_00000000113" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001008", "positionTop": "408", "positionLeft": "678", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "1", "useAt": "Y", "itemNm": "B01", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001009", "positionTop": "436", "positionLeft": "688", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 1, "itemNo": "2", "useAt": "N", "itemNm": "B02", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001010", "positionTop": "464", "positionLeft": "696", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "3", "useAt": "Y", "itemNm": "B03", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001011", "positionTop": "492", "positionLeft": "706", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "4", "useAt": "Y", "itemNm": "B04", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001012", "positionTop": "519", "positionLeft": "716", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "5", "useAt": "Y", "itemNm": "B05", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001013", "positionTop": "547", "positionLeft": "726", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "6", "useAt": "Y", "itemNm": "B06", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001014", "positionTop": "266", "positionLeft": "590", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "7", "useAt": "Y", "itemNm": "B07", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001015", "positionTop": "294", "positionLeft": "598", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "8", "useAt": "Y", "itemNm": "B08", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001016", "positionTop": "322", "positionLeft": "608", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "9", "useAt": "Y", "itemNm": "B09", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001017", "positionTop": "350", "positionLeft": "616", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "10", "useAt": "Y", "itemNm": "B10", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001018", "positionTop": "378", "positionLeft": "624", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "11", "useAt": "Y", "itemNm": "B11", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001019", "positionTop": "406", "positionLeft": "632", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "12", "useAt": "Y", "itemNm": "B12", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001020", "positionTop": "434", "positionLeft": "640", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "13", "useAt": "Y", "itemNm": "B13", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001021", "positionTop": "462", "positionLeft": "650", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "14", "useAt": "Y", "itemNm": "B14", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001022", "positionTop": "490", "positionLeft": "660", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "15", "useAt": "Y", "itemNm": "B15", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001023", "positionTop": "518", "positionLeft": "670", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "16", "useAt": "Y", "itemNm": "B16", "categoryId": "CATEGORY_00000000114" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001024", "positionTop": "135", "positionLeft": "42", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 1, "itemNo": "1", "useAt": "N", "itemNm": "C01", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001025", "positionTop": "162", "positionLeft": "47", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 1, "itemNo": "2", "useAt": "N", "itemNm": "C02", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001026", "positionTop": "188", "positionLeft": "52", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "3", "useAt": "Y", "itemNm": "C03", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001027", "positionTop": "214", "positionLeft": "58", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "4", "useAt": "Y", "itemNm": "C04", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001028", "positionTop": "240", "positionLeft": "64", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "5", "useAt": "Y", "itemNm": "C05", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001029", "positionTop": "285", "positionLeft": "78", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "6", "useAt": "Y", "itemNm": "C06", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001030", "positionTop": "308", "positionLeft": "92", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "7", "useAt": "Y", "itemNm": "C07", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001031", "positionTop": "332", "positionLeft": "108", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "8", "useAt": "Y", "itemNm": "C08", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001032", "positionTop": "354", "positionLeft": "126", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "9", "useAt": "Y", "itemNm": "C09", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001033", "positionTop": "378", "positionLeft": "144", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "10", "useAt": "Y", "itemNm": "C10", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001034", "positionTop": "400", "positionLeft": "161", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 1, "itemNo": "11", "useAt": "N", "itemNm": "C11", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001035", "positionTop": "422", "positionLeft": "180", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "12", "useAt": "Y", "itemNm": "C12", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001036", "positionTop": "444", "positionLeft": "198", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "13", "useAt": "Y", "itemNm": "C13", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001037", "positionTop": "468", "positionLeft": "216", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "14", "useAt": "Y", "itemNm": "C14", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001038", "positionTop": "500", "positionLeft": "245", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "15", "useAt": "Y", "itemNm": "C15", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001039", "positionTop": "520", "positionLeft": "268", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "16", "useAt": "Y", "itemNm": "C16", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001040", "positionTop": "536", "positionLeft": "294", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "17", "useAt": "Y", "itemNm": "C17", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001041", "positionTop": "552", "positionLeft": "322", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 1, "itemNo": "18", "useAt": "N", "itemNm": "C18", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001042", "positionTop": "556", "positionLeft": "354", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 0, "itemNo": "19", "useAt": "Y", "itemNm": "C19", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001043", "positionTop": "552", "positionLeft": "384", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 1, "itemNo": "20", "useAt": "N", "itemNm": "C20", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001044", "positionTop": "548", "positionLeft": "414", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 1, "itemNo": "21", "useAt": "N", "itemNm": "C21", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001045", "positionTop": "542", "positionLeft": "444", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 1, "itemNo": "22", "useAt": "N", "itemNm": "C22", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001046", "positionTop": "537", "positionLeft": "474", "color": "color3", "DATE_DIFF": 1, "categoryNm": "C사이트", "reserveCnt": 1, "itemNo": "23", "useAt": "N", "itemNm": "C23", "categoryId": "CATEGORY_00000000115" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001047", "positionTop": "223", "positionLeft": "132", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "1", "useAt": "N", "itemNm": "D01", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001048", "positionTop": "190", "positionLeft": "136", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "2", "useAt": "N", "itemNm": "D02", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001049", "positionTop": "158", "positionLeft": "147", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "3", "useAt": "N", "itemNm": "D03", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001050", "positionTop": "130", "positionLeft": "170", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "4", "useAt": "N", "itemNm": "D04", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001051", "positionTop": "112", "positionLeft": "198", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "5", "useAt": "N", "itemNm": "D05", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001052", "positionTop": "102", "positionLeft": "250", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "6", "useAt": "N", "itemNm": "D06", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001053", "positionTop": "106", "positionLeft": "286", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "7", "useAt": "N", "itemNm": "D07", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001054", "positionTop": "120", "positionLeft": "318", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "8", "useAt": "N", "itemNm": "D08", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001055", "positionTop": "142", "positionLeft": "342", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "9", "useAt": "N", "itemNm": "D09", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001056", "positionTop": "172", "positionLeft": "362", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "10", "useAt": "N", "itemNm": "D10", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001057", "positionTop": "238", "positionLeft": "372", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "11", "useAt": "N", "itemNm": "D11", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001058", "positionTop": "270", "positionLeft": "362", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "12", "useAt": "N", "itemNm": "D12", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001059", "positionTop": "300", "positionLeft": "342", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "13", "useAt": "N", "itemNm": "D13", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001060", "positionTop": "322", "positionLeft": "318", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "14", "useAt": "N", "itemNm": "D14", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001061", "positionTop": "378", "positionLeft": "222", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 0, "itemNo": "15", "useAt": "Y", "itemNm": "D15", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001062", "positionTop": "354", "positionLeft": "202", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 0, "itemNo": "16", "useAt": "Y", "itemNm": "D16", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001063", "positionTop": "330", "positionLeft": "182", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 0, "itemNo": "17", "useAt": "Y", "itemNm": "D17", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001064", "positionTop": "306", "positionLeft": "162", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 0, "itemNo": "18", "useAt": "Y", "itemNm": "D18", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001065", "positionTop": "282", "positionLeft": "144", "color": "color4", "DATE_DIFF": 1, "categoryNm": "D사이트", "reserveCnt": 1, "itemNo": "19", "useAt": "N", "itemNm": "D19", "categoryId": "CATEGORY_00000000116" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001066", "positionTop": "317", "positionLeft": "380", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "1", "useAt": "N", "itemNm": "E01", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001067", "positionTop": "310", "positionLeft": "410", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "2", "useAt": "N", "itemNm": "E02", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001068", "positionTop": "384", "positionLeft": "332", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "3", "useAt": "N", "itemNm": "E03", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001069", "positionTop": "374", "positionLeft": "366", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "4", "useAt": "N", "itemNm": "E04", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001070", "positionTop": "420", "positionLeft": "338", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "5", "useAt": "N", "itemNm": "E05", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001071", "positionTop": "410", "positionLeft": "374", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "6", "useAt": "N", "itemNm": "E06", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001072", "positionTop": "366", "positionLeft": "416", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "7", "useAt": "N", "itemNm": "E07", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001073", "positionTop": "358", "positionLeft": "450", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "8", "useAt": "N", "itemNm": "E08", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001074", "positionTop": "400", "positionLeft": "422", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "9", "useAt": "N", "itemNm": "E09", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001075", "positionTop": "392", "positionLeft": "457", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "10", "useAt": "N", "itemNm": "E10", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001076", "positionTop": "468", "positionLeft": "350", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "11", "useAt": "N", "itemNm": "E11", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001077", "positionTop": "460", "positionLeft": "386", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "12", "useAt": "N", "itemNm": "E12", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001078", "positionTop": "504", "positionLeft": "358", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "13", "useAt": "N", "itemNm": "E13", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001079", "positionTop": "494", "positionLeft": "394", "color": "color5", "DATE_DIFF": 1, "categoryNm": "E사이트", "reserveCnt": 1, "itemNo": "14", "useAt": "N", "itemNm": "E14", "categoryId": "CATEGORY_00000000117" },
                { "SCHEDULE_DATE_CNT": 1, "itemId": "ITEM_000000000001105", "positionTop": "546", "positionLeft": "678", "color": "color2", "DATE_DIFF": 1, "categoryNm": "B사이트", "reserveCnt": 0, "itemNo": "17", "useAt": "Y", "itemNm": "B17", "categoryId": "CATEGORY_00000000114" }
            ]
        }
    ],
    "categoryList": [
        { "group_id": "GROUP_00000000000012", "group_code": "pccamp", "page_id": "C27562955", "category_id": "CATEGORY_00000000113", "category_history_id": "CH_00000000000000307", "category_nm": "A사이트", "img_id": "", "max_cnt": 0, "pre_open_cnt": 2, "color": "color1", "info_text": "", "sort_ordr": "1", "category_type": "oneday", "item_type": "item", "usage_type": "camping", "member_type": "", "use_at": "Y", "reg_id": "MANAGER_000000000081", "reg_nm": "관리자", "reg_date": "20230811114030", "del_yn": "N", "car_cnt": 1, "upd_date": "20250531194647", "upd_id": "MANAGER_000000000081", "upd_nm": "유지보수" },
        { "group_id": "GROUP_00000000000012", "group_code": "pccamp", "page_id": "C27562955", "category_id": "CATEGORY_00000000114", "category_history_id": "CH_00000000000000308", "category_nm": "B사이트", "img_id": "", "max_cnt": 0, "pre_open_cnt": 5, "color": "color2", "info_text": "", "sort_ordr": "2", "category_type": "oneday", "item_type": "item", "usage_type": "camping", "member_type": "", "use_at": "Y", "reg_id": "MANAGER_000000000081", "reg_nm": "관리자", "reg_date": "20230811114055", "del_yn": "N", "upd_date": "20250531194924", "upd_id": "MANAGER_000000000081", "upd_nm": "유지보수", "car_cnt": 1 },
        { "group_id": "GROUP_00000000000012", "group_code": "pccamp", "page_id": "C27562955", "category_id": "CATEGORY_00000000115", "category_history_id": "CH_00000000000000309", "category_nm": "C사이트", "img_id": "", "max_cnt": 0, "pre_open_cnt": 7, "color": "color3", "info_text": "", "sort_ordr": "3", "category_type": "oneday", "item_type": "item", "usage_type": "camping", "member_type": "", "use_at": "Y", "reg_id": "MANAGER_000000000081", "reg_nm": "관리자", "reg_date": "20230811114127", "del_yn": "N", "car_cnt": 1, "info_desc": "차량번호를 입력해주세요", "upd_date": "20250531194934", "upd_id": "MANAGER_000000000081", "upd_nm": "유지보수" },
        { "group_id": "GROUP_00000000000012", "group_code": "pccamp", "page_id": "C27562955", "category_id": "CATEGORY_00000000116", "category_history_id": "CH_00000000000000310", "category_nm": "D사이트", "img_id": "", "max_cnt": 0, "pre_open_cnt": 6, "color": "color4", "info_text": "", "sort_ordr": "4", "category_type": "oneday", "item_type": "item", "usage_type": "camping", "member_type": "", "use_at": "Y", "reg_id": "MANAGER_000000000081", "reg_nm": "관리자", "reg_date": "20230811114153", "del_yn": "N", "car_cnt": 1, "info_desc": "차량번호를 입력해주세요", "upd_date": "20250531194944", "upd_id": "MANAGER_000000000081", "upd_nm": "유지보수" },
        { "group_id": "GROUP_00000000000012", "group_code": "pccamp", "page_id": "C27562955", "category_id": "CATEGORY_00000000117", "category_history_id": "CH_00000000000000311", "category_nm": "E사이트", "img_id": "", "max_cnt": 0, "pre_open_cnt": 4, "color": "color5", "info_text": "", "sort_ordr": "5", "category_type": "oneday", "item_type": "item", "usage_type": "camping", "member_type": "", "use_at": "Y", "reg_id": "MANAGER_000000000081", "reg_nm": "관리자", "reg_date": "20230811114210", "del_yn": "N", "car_cnt": 1, "info_desc": "차량번호를 입력해주세요", "upd_date": "20250531194953", "upd_id": "MANAGER_000000000081", "upd_nm": "유지보수" }
    ],
    "resultCode": "",
    "message": "",
    "selectDateCheck": true,
    "preOpenCheck": true
}
```
