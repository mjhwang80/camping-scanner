import os
import shutil
import nest_asyncio
from playwright.sync_api import sync_playwright

nest_asyncio.apply()

def create_auth_with_copy():
    # 1. 원본 크롬 프로필 경로 설정
    # (일반적으로 Default 폴더가 포함된 User Data 경로)
    original_user_data = os.path.join(os.environ['LOCALAPPDATA'], "Google/Chrome/User Data")
    
    # 2. 임시 복사본 경로 설정 (현재 스크립트 폴더 내 temp_profile)
    temp_profile_path = os.path.abspath("./temp_profile")

    # 기존에 복사본이 있다면 삭제하고 새로 복사 (세션 최신화)
    if os.path.exists(temp_profile_path):
        print("기존 임시 프로필 삭제 중...")
        shutil.rmtree(temp_profile_path, ignore_errors=True)

    print("🚀 크롬 프로필 복사 중... (잠시만 기다려주세요)")
    try:
        # User Data 전체를 복사하면 너무 크므로, 필요한 프로필 폴더만 필터링하거나 전체 복사
        # 여기서는 안정성을 위해 폴더 구조를 복사합니다.
        shutil.copytree(original_user_data, temp_profile_path, 
                        ignore=shutil.ignore_patterns('Default/Cache*', 'Default/Code Cache*', 'Default/GPUCache*'))
        print("✅ 복사 완료.")
    except Exception as e:
        print(f"❌ 복사 실패: {e}")
        print("크롬이 켜져 있다면 종료하고 다시 시도하세요.")
        return

    with sync_playwright() as p:
        print("🌐 브라우저 실행 중...")
        # 3. 복사된 임시 경로로 브라우저 실행
        context = p.chromium.launch_persistent_context(
            user_data_dir=temp_profile_path,            
            channel="chrome",
            headless=False, # 눈으로 확인하기 위해 False 권장
            args=[
                "--disable-blink-features=AutomationControlled",
                "--profile-directory=Default" # 본인의 실제 프로필 폴더명으로 수정 가능
            ]
        )

        page = context.pages[0] if context.pages else context.new_page()

        try:
            print("🔗 인터파크 접속 중...")
            page.goto("https://tickets.interpark.com", wait_until="networkidle")
            
            # 실제 로그인이 유지되어 있는지 확인하기 위해 5초 대기
            print("👀 로그인 상태를 확인하세요. (자동으로 auth.json을 생성합니다)")
            page.wait_for_timeout(5000)

            # 4. 상태 저장
            context.storage_state(path="auth.json")
            print("✨ 'auth.json' 생성 완료!")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        finally:
            context.close()
            # 5. 작업 종료 후 임시 폴더 삭제 (용량 확보)
            # shutil.rmtree(temp_profile_path, ignore_errors=True)

if __name__ == "__main__":
    create_auth_with_copy()