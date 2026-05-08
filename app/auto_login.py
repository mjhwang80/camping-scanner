import nest_asyncio
import os
nest_asyncio.apply()  # 루프 충돌 방지 핵심 코드

from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import expect


# 1. 외부 다운로드 없이 핵심 스텔스 로직 직접 정의
stealth_scripts = """
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    window.chrome = { runtime: {} };
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['ko-KR', 'ko', 'en-US', 'en'] });
"""

with sync_playwright() as p:

    #파라미터 정보
    site_code = "RGN001"
    play_date = "20260519"
    play_seq = "G64,G65"
    goods_code = "21005592"   


    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(storage_state="interpark_auth.json")
    page = context.new_page()

    page.add_init_script(stealth_scripts)
     
    page.goto("about:blank")
    url = f"https://api-ticketfront.interpark.com/v1/goods/{goods_code}/waiting?channelCode=cp&preSales=N&playDate={play_date}&playSeq={play_seq}"   
    
    target_url = None
    with page.expect_response("**/v1/goods/*/waiting**") as response_info:
        page.goto(url)

    response = response_info.value
    if response and response.status == 200:
        result_json = response.json()
        if "data" in result_json and result_json["data"]:
            target_url = result_json["data"]
    
    if target_url:
        page.goto(target_url)
        page.wait_for_url("**/CampingBook/BookMain.asp")
        
        # 특정 파일 로드될 때까지 대기
        with page.expect_response("**/CampingBook/Lib/BookInfoXml.asp") as info:
            # 팝업 닫기
            try:
                close_button = page.wait_for_selector("div.layerWrap span a", timeout=2000)
                if close_button:
                    close_button.click()
            except:
                print("팝업이 없습니다.")

            iframe = page.frame_locator("#ifrmSeat")
            
            # iframe 로드 대기 (중요)
            iframe.locator("map#Map area").first.wait_for(state="attached")
            
            areas = iframe.locator("map#Map area").all()
            print(f"총 {len(areas)}개의 구역을 찾았습니다.")

            # 다음단계 버튼 클릭 (필요 시)
            try:
                next_button = iframe.locator("a.btn_next_step")
                if next_button.is_visible():
                    next_button.click(force=True)
            except:
                pass

            
            page.wait_for_timeout(1500) 

            iframe_handle = page.query_selector("#ifrmSeat")
            if iframe_handle:
                frame = iframe_handle.content_frame()
                frame.evaluate(f"GetBlockSeatList('', '', '{site_code}')")

            page.wait_for_timeout(1500) 

            seats = iframe.locator("div#map img.stySeat").all()    
            print(f"발견된 좌석 개수: {len(seats)}")
            for seat in seats:                  
                seat_name = seat.get_attribute("alt")
                print(f"좌석명: {seat_name}")
                seat.click()
                break;



            #next_button = page.query_selector("a.btn_next_step")
            page.wait_for_timeout(1000) 
            next_button = iframe.locator("a.btn_next_step")
            if next_button.is_visible():
                next_button.click(force=True)     
            
            
            page.wait_for_timeout(1500)     
            iframe = page.frame_locator("#ifrmBookStep")
            price_types = iframe.locator('input[name="PriceType"]').all()
            print(f"발견된 옵션 개수: {len(price_types)}")
            for price_type in price_types: 
                value = price_type.get_attribute("value")
                if value == "11":
                    price_type.click()
                    break

            button_groups = iframe.locator("div[id='btn_Default'] a").all()
            print(f"발견된 버튼 개수: {len(button_groups)}")
            button_groups[1].click()

            page.wait_for_timeout(1500) 
            iframe = page.frame_locator("#ifrmBookStep")
            iframe.locator('input[name="YYMMDD"]').fill("800622")
            iframe.locator('input[name="CustomEtc"]').fill("283구2941")
            payments = iframe.locator('input[name="Payment"]').all()
            print(f"발견된 결재수단 개수: {len(payments)}")
            for payment in payments: 
                value = payment.get_attribute("value")
                if value == "22004": #무통장
                    payment.click()
                    break
        
            page.wait_for_timeout(1000)
        
            bankCode = iframe.locator('select[id="BankCode"]').select_option("38051");
            page.wait_for_timeout(500)
            
            button_groups[1].click()

            page.wait_for_timeout(1000)
            iframe.locator('input[id="CancelAgree"]').click();
            page.wait_for_timeout(500)

            button_groups = iframe.locator("div[id='btn_Default'] a").all()
            button_groups[0].click()

        page.wait_for_timeout(10000) 
    
    browser.close()


