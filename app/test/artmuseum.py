import httpx
import asyncio
import json

async def check_campsite_availability():
    url = "https://reserve.yjuc.or.kr/main/camping/camp_req_place_list.json"
    
    # 요청 데이터 설정
    data = {
        "cpgtIdx": 2,
        "stayDays": 1,
        "checkIn": "2026-06-18",
        "checkOut": "2026-06-19"
    }
    
    # 일반적인 웹 브라우저 헤더 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Host": "reserve.yjuc.or.kr",
        "Origin": "https://reserve.yjuc.or.kr",
        "Referer": "https://reserve.yjuc.or.kr/main/camping/camp_rent_req_list.do",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie" : "_ga=GA1.1.828568410.1777526298; _ga_9CHRHVVPTK=GS2.1.s1777526298$o1$g0$t1777526335$j23$l0$h0; allowToken=userAllowToken660.0.031983252551897046; mainPop_hidden=Y; YJUC_USER1_MYSQL_TOMCAT_JSESSIONID=6EDF8099B9EFF73928EBDB26F42EE9CF.user1; _ga_F79SLSKDD6=GS2.1.s1781227707$o2$g1$t1781229080$j60$l0$h0"
    }

    async with httpx.AsyncClient() as client:
        try:
            # POST 요청 전송
            response = await client.post(url, data=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("result") == "success":
                    print(f"--- 조회 성공: {data['checkIn']} ~ {data['checkOut']} ---")
                    campsite_list = result.get("list", [])
                    
                    for site in campsite_list:
                        status = site.get("cdsCdNm") # "예약가능" 또는 "예약불가"
                        name = site.get("cpgNm")
                        price = site.get("totalPay")
                        
                        print(f"[{status}] {name} | 가격: {price:,}원")
                else:
                    print("API 응답은 성공했으나 데이터 처리 중 문제가 발생했습니다.")
            else:
                print(f"요청 실패: 상태 코드 {response.status_code}")
                
        except Exception as e:
            print(f"오류 발생: {e}")

# 실행
if __name__ == "__main__":
    asyncio.run(check_campsite_availability())