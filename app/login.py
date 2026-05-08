from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
    context = browser.new_context()
    page = context.new_page()

    # 인터파크 로그인 페이지로 이동
    page.goto("https://tickets.interpark.com/goods/21005592")

    print("=========================================")
    print("브라우저 창에서 직접 아이디/비번을 치고 로그인하세요!")
    print("클라우드플레어 인증도 직접 통과해 주세요.")
    print("로그인이 완전히 끝나고 메인 화면이 나오면 아래에서 엔터를 치세요.")
    print("=========================================")

    page.wait_for_timeout(5000)
    
    # 사용자가 직접 로그인할 때까지 파이썬 코드를 잠시 멈춤
    input("로그인 완료 후 엔터를 눌러주세요: ")

    #page.pause()

    #page.wait_for_timeout(50000)

    # ⭐️ 핵심: 현재 완벽하게 로그인된 상태(쿠키)를 auth.json 파일로 영구 저장!
    context.storage_state(path="auth.json")
    
    print("✅ 로그인 상태가 'auth.json' 파일로 안전하게 저장되었습니다!")

    browser.close()