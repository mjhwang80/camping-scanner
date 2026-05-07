import nest_asyncio
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
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(storage_state="auth.json")
    page = context.new_page()

    page.add_init_script(stealth_scripts)
     
    page.goto("about:blank")
    url = "https://api-ticketfront.interpark.com/v1/goods/21005592/waiting?channelCode=cp&preSales=N&playDate=20260519&playSeq=G64,G65"   
    
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


            iframe_handle = page.query_selector("#ifrmSeat")
            if iframe_handle:
                frame = iframe_handle.content_frame()
                frame.evaluate("GetBlockSeatList('', '', 'RGN006')")

            page.wait_for_timeout(2000) 

            seats = iframe.locator("div#map img.stySeat").all()    
            print(f"발견된 좌석 개수: {len(seats)}")
            for seat in seats:                  
                seat_name = seat.get_attribute("alt")
                print(f"좌석명: {seat_name}")
                


        page.wait_for_timeout(10000) 
    
    browser.close()