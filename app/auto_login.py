from playwright.sync_api import sync_playwright

# 1. 외부 다운로드 없이 핵심 스텔스 로직을 직접 문자열로 정의합니다.
stealth_scripts = """
    // Webdriver 속성 숨기기 (가장 핵심)
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    
    // 일반 크롬 브라우저처럼 보이기 위한 가짜 Chrome 객체 생성
    window.chrome = { runtime: {} };
    
    // 봇이 아닌 것처럼 플러그인 배열 채우기
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    
    // 정상적인 한국어 사용자처럼 언어 설정
    Object.defineProperty(navigator, 'languages', { get: () => ['ko-KR', 'ko', 'en-US', 'en'] });
"""

with sync_playwright() as p:
    
    my_profile_path = "/Users/mjhwang/Library/Application Support/Google/Chrome"
    
    # 일반 launch가 아니라, 내 크롬 데이터를 덮어씌워 실행합니다.
    '''
    
    context = p.chromium.launch_persistent_context(
        user_data_dir=my_profile_path,
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
        ]
    )
    page = context.pages[0] 
    '''
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(storage_state="auth.json")
    # 새 탭을 열지 않고 첫 번째 열린 탭을 사용합니다.
    page = context.new_page()

    # 혹시 모를 탐지를 대비해 간단한 스텔스 스크립트만 추가
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

    # 4. 고장난 파이썬 패키지 대신, 스텔스 자바스크립트를 직접 주입!
    #page.add_init_script(stealth_scripts)

    page.goto("https://tickets.interpark.com/goods/21005592")
    page.wait_for_timeout(5000)
    print("✅ 로그인 페이지 로드 완료 (완전 독립형 스텔스 적용)")

    """
    # 1. 사람처럼 마우스를 화면 중간으로 스르륵 움직입니다.
    page.mouse.move(500, 500)
    page.wait_for_timeout(500)
    page.mouse.move(300, 400)
    page.wait_for_timeout(500)

    # 2. 클라우드플레어 체크박스 자동 클릭 시도
   
    try:
        print("체크박스 클릭 시도...")
        # 클라우드플레어 iframe을 찾습니다.
        cf_frame = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
        
        # iframe 내부의 체크박스(또는 메인 영역)를 찾아 클릭합니다.
        # 사람처럼 약간의 딜레이를 주고 클릭합니다.
        cf_frame.locator("body").click(delay=150) 
        
        print("✅ 체크박스 클릭 완료!")
        page.wait_for_timeout(3000) # 통과 후 로딩 대기
    except Exception as e:
        print("체크박스를 찾지 못했거나 이미 통과되었습니다.")

    # 4. 로그인 시도 (사람처럼 보이게 딜레이 추가)
    page.type("input[name='username']", "hmjkor", delay=100)
    page.type("input[name='password']", "xoddl1004@i", delay=100)
    page.click("button[type='submit']")
    """
    page.wait_for_timeout(30000)
   
