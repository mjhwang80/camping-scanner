import asyncio
import httpx
import pprint
import logging

# 터미널 디버깅용 로그 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("camping.gtdc")

async def test_gtdc_api():
    # 1. 대상 API 주소 세팅
    url = "https://camping.gtdc.or.kr/dzSmart/plugins/Reserv/procedure/reserv-02-zone.json"
    
    # 2. 전송할 Form Data 세팅 (application/x-www-form-urlencoded 규격)
    # 파이썬 딕셔너리는 f-string 서식을 Key로 사용할 수 있어 동적 페이로드 조립에 유연합니다.
    data = {
        "actMode": "zone_state",
        "areadate": "2-26-06-30-1",
        "base": "",
        "isDates[20260630][type]": "Usual",
        "isDates[20260630][seas]": "normal",
        "isSets": "true",
        "isAges": "true",
        "isZones": "true",
        "isRooms": "true"
    }
    
    # 3. 브라우저인 척 요청을 통과시키기 위한 헤더 구성 (대소문자 오동작 방지를 위해 첫글자 대문자 고정)
    headers = {
        "Host": "camping.gtdc.or.kr",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Author": "20260608180138",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://camping.gtdc.or.kr",
        "Referer": "https://camping.gtdc.or.kr/pub/reserv.do?tmonth=202606&sp=z&tarea=2-26-06-30-1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    print("\n" + "="*60)
    print(f"📡 [고성군 관광지 예약 시스템] 구역 상태 API 호출을 시작합니다...")
    print("="*60)

    # 4. AsyncClient를 활용하여 안전하게 커넥션 풀을 관리하며 비동기 POST 요청 실행
    # 인증서 무오류(SSL) 우회를 위해 verify=False 옵션을 동봉합니다.
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, verify=False) as client:
        try:
            # 💡 핵심 가이드: 데이터 타입을 data=data로 넘겨야 Form 바디 포맷으로 인코딩되어 날아갑니다.
            response = await client.post(url, data=data, headers=headers)
            
            print(f"[*] HTTP 응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                print("\n[✔] RECEIVED DATA (서버 수신 결과):")
                
                # API 응답 규격이 JSON이라면 바로 파이썬 딕셔너리로 변환하여 출력합니다.
                try:
                    result_json = response.json()
                    pprint.pprint(result_json)
                except ValueError:
                    # 만약 서버가 JSON이 아닌 생짜 텍스트나 HTML을 반환할 경우의 예외 처리
                    print(response.text)
            else:
                print(f"[!] 서버 응답 에러 본문: {response.text}")
                
        except Exception as e:
            logger.error(f"[!] 통신 중 예외 오류 발생: {str(e)}")
            
    print("="*60 + "\n")

if __name__ == "__main__":
    # 비동기 이벤트 루프 기동
    asyncio.run(test_gtdc_api())