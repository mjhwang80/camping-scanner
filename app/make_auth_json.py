import nest_asyncio
import os
from playwright.sync_api import sync_playwright

nest_asyncio.apply()


# 1. 경로 설정 (현재 크롬의 프로필 경로)
# 주의: 크롬이 완전히 종료된 상태여야 에러가 안 납니다.
user_data_path = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data"

with sync_playwright() as p:
    # 2. 브라우저 실행
    context = p.chromium.launch_persistent_context(
        user_data_dir=user_data_path,
        channel="chrome",      # 실제 설치된 크롬 사용
        headless=False,        # 가급적 False로 해서 눈으로 확인하세요
        args=["--no-first-run"]
        #slow_mo=500
    )

    # launch_persistent_context는 페이지가 자동으로 하나 열릴 수 있습니다.
    page = context.pages[0]
    
    try:
        page.goto("https://tickets.interpark.com/goods/21005592",timeout=60000)
        
        # 3. 로그인 여부 확인을 위한 대기
        # 실제로 로그인이 되어 있는지 화면에서 확인하는 시간이 필요합니다.
        print("페이지 로딩 중... 로그인 상태를 확인합니다.")
        page.wait_for_timeout(5000) 

        # 4. 상태 저장
        context.storage_state(path="auth.json")
        print("✅ 로그인 상태가 'auth.json' 파일로 안전하게 저장되었습니다!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    finally:
        context.close()