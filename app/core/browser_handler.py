# /app/core/browser_handler.py
from playwright.async_api import async_playwright
import logging
import asyncio

logger = logging.getLogger("camping.browser")

class BrowserHandler:
    @staticmethod
    async def get_final_content(url):
        async with async_playwright() as p:
            # 1. 실제 브라우저처럼 보이게 인자 추가 (stealth 관련 설정)
            browser = await p.chromium.launch(headless=True)
            # 실제 사용자의 환경과 유사하게 컨텍스트 생성
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                logger.info(f"[*] 보안 페이지 통과 시도: {url}")
                
                # 2. 페이지 이동 (timeout을 늘리고 네트워크가 안정될 때까지 대기)
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # 3. '웹 대기' 페이지가 완전히 사라지고 #tocken이 나타날 때까지 명시적 대기
                # 타임아웃 오류 방지를 위해 대기 시간을 20초로 상향
                await page.wait_for_selector("#tocken", state="attached", timeout=20000)
                
                # 4. JavaScript 실행 완료를 위해 아주 짧은 시간 추가 대기
                await asyncio.sleep(1)
                
                content = await page.content()
                return content
                
            except Exception as e:
                logger.error(f"[!] 브라우저 자동화 중 오류 (타임아웃 등): {e}")
                # 오류 발생 시점의 스크린샷을 찍어두면 디버깅에 큰 도움이 됩니다.
                # await page.screenshot(path="debug_error.png")
                return None
            finally:
                await browser.close()