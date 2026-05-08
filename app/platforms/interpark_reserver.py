import asyncio
import time
from playwright.async_api import async_playwright
from core.ua_generator import UAGenerator
import httpx
import xml.etree.ElementTree as ET
from core.config_loader import CONFIG

class InterparkReserver:
    def __init__(self, auth_path="interpark_auth.json"):
        self.auth_path = auth_path
        self.stealth_scripts = """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['ko-KR', 'ko', 'en-US', 'en'] });
        """
    # 실제 지점 클릭을 위한 빈영역 클릭 함수    
    async def check_xml_availability(self, api_url:str, site_info:dict):
        # 1. 설정값 준비
        site_group_arr = site_info.get("site_group_arr", []) # ['RGN001', 'RGN005']
        
        available_blocks = []

        async with httpx.AsyncClient() as client:
            try:
                # 2. GET 요청
                response = await client.get(api_url)
                response.raise_for_status()

                # 3. XML 파싱 (자바의 DocumentBuilder와 유사)
                root = ET.fromstring(response.text)

                # 4. <Table> 태그 순회
                for table in root.findall('Table'):
                    self_define_block = table.find('SelfDefineBlock').text
                    remain_cnt_text = table.find('RemainCnt').text
                    
                    # RemainCnt가 없는 경우를 대비한 방어 코드
                    remain_cnt = int(remain_cnt_text) if remain_cnt_text else 0

                    # 5. 조건 필터링
                    # - SelfDefineBlock이 감시 대상(site_group_arr)에 포함되는가?
                    # - RemainCnt가 0보다 큰가?
                    if self_define_block in site_group_arr and remain_cnt > 0:
                        available_blocks.append({
                            "block": self_define_block,
                            "remain": remain_cnt
                        })
                        print(f"[*] 빈구역 발견: {self_define_block} (잔여: {remain_cnt})")

            except Exception as e:
                print(f"[!] XML 파싱 중 오류 발생: {e}")

        return available_blocks

    async def reserve(self, params: dict, site_info: dict):
        """
        params: 감시 요청 파라미터 (date, stay_day 등)
        site_info: 발견된 사이트 정보 (site_code, site_name 등)
        """
        async with async_playwright() as p:
            # 1. 브라우저 설정
            browser = await p.chromium.launch(
                headless=False, # 자동 예약 시에는 과정을 보는 것이 좋음
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            # 2. 컨텍스트 생성 (저장된 세션 로드)
            context = await browser.new_context(storage_state=self.auth_path)
            page = await context.new_page()
            await page.add_init_script(self.stealth_scripts)

            try:
                # 3. 웨이팅 URL 접속 (Token 획득 로직)
                play_date = params['date'].replace("-", "")
                stay_day = params['stay_day'] # 인터파크는 시퀀스 코드가 필요함
                goods_code = params['camp_id'] 
                play_seq = len(stay_day.split(',')) if stay_day else 1
                
                wait_url = f"https://api-ticketfront.interpark.com/v1/goods/{goods_code}/waiting?channelCode=cp&preSales=N&playDate={play_date}&playSeq={stay_day}"
                print(f"자동 예약 진입 url : {wait_url}")
                print(site_info['site_code'])

                site_group_arr = site_info.get("site_group_arr", [])

                async with page.expect_response("**/v1/goods/*/waiting**") as response_info:
                    await page.goto(wait_url)
                
                resp = await response_info.value
                if resp.status == 200:
                    data = await resp.json()
                    target_url = data.get("data")
                    if not target_url: return False
                    
                    # 4. 실제 예약 페이지 진입
                    await page.goto(target_url)
                    await page.wait_for_url("**/CampingBook/BookMain.asp", timeout=5000)

                    # 5. 팝업 닫기 및 프레임 진입
                    try:
                        btn_close = await page.wait_for_selector("div.layerWrap span a", timeout=2000)
                        await btn_close.click()
                    except: pass

                    await page.wait_for_timeout(2100)

                    tmgs_or_not = await page.locator("#TmgsOrNot").get_attribute("value")
                    place_code = await page.locator("#PlaceCode").get_attribute("value")

                    print(f"추출된 TmgsOrNot: {tmgs_or_not}")
                    print(f"추출된 PlaceCode: {place_code}")

                    api_url = f"https://poticket.interpark.com/CampingBook/Lib/BookInfoXml.asp?Flag=AllBlock&GoodsCode={goods_code}&PlaceCode={place_code}&PlaySeqList={stay_day}&TmgsOrNot={tmgs_or_not}"
                    available_blocks = await self.check_xml_availability(api_url, site_info)

                    if not available_blocks:
                        print("[!] 예약 가능한 구역(Block)이 XML 데이터에 존재하지 않습니다.")
                        return False
                    
                    # 첫 번째 예약 가능 구역 추출 (자바의 list.get(0)과 동일)
                    target_block_code = available_blocks[0]['block']
                    print(f"[*] 최종 예약 시도 구역: {target_block_code}")

                    # 6. 구역 선택 및 좌석(사이트) 선택
                    # site_info['site_code']는 UI에서 선택한 구역 코드 (RGN001 등)
                    iframe = page.frame_locator("#ifrmSeat")
                    await iframe.locator("map#Map area").first.wait_for(state="attached", timeout=5000)
                    
                    print(f"[*] 1 Step 예약 구역 화면 표출")

                    # JS 함수 직접 실행으로 구역 이동
                    iframe_handle = await page.query_selector("#ifrmSeat")
                    frame = await iframe_handle.content_frame()
                    await frame.evaluate(f"GetBlockSeatList('', '', '{target_block_code}')")
                    print(f"[*] 2 Step영역 클릭 : {target_block_code}")
                    
                    await page.wait_for_timeout(1500)
                    print(f"[*] 3 Step 사이트 선택 화면 표출")
                    # 7. 좌석 선택 (이미 발견된 좌석이 있으므로 첫 번째 사용 가능한 좌석 클릭)
                    seats = await iframe.locator("div#map img.stySeat").all()
                    if seats:
                        await seats[0].click()
                        
                        # 다음 단계 버튼
                        next_step = iframe.locator("a.btn_next_step")
                        await next_step.click(force=True)
                    else:
                        return False

                    # 8. 권종/할인 선택 (무통장 입금 단계까지)
                    await page.wait_for_timeout(2500)
                    book_step = page.frame_locator("#ifrmBookStep")
                    
                    # 가격 선택 (일반가 11 등)
                    prices = await book_step.locator('input[name="PriceType"]').all()
                    if prices:
                        found_price_target = False
                        target_text = "관광주민"
                        for p_type in prices:
                            grade_name = await p_type.get_attribute("pricegradename")
                            #if await p_type.get_attribute("value") == "11":
                            if grade_name and target_text in grade_name:
                                found_price_target = True
                                await p_type.click()
                                break
                    
                        if not found_price_target:
                            await prices[-1].click()
                            print(f"[*] '관광주민' 옵션이 없어 마지막 옵션({await prices[-1].get_attribute('value')})을 선택했습니다.")


                    await page.wait_for_timeout(2500)
                    # 다음 버튼
                    btns = await book_step.locator("div[id='btn_Default'] a").all()
                    await btns[1].click() # 다음단계


                    await page.wait_for_timeout(1000)
                    # 딕셔너리에서 안전하게 값을 가져오기 위해 .get()을 사용합니다.                
                    self.birth_date = CONFIG['info']['birth_date']
                    self.car_number = CONFIG['info']['car_number']
                    self.email = CONFIG['info']['email']

                    print(f"자동 예약에 필요한 정보 - 생년월일: {self.birth_date}, 차량번호: {self.car_number}, 이메일: {self.email}")

                    # 9. 예약자 정보 입력 및 결제 수단(무통장)
                    
                    # 개인 정보 (생년월일, 차량번호 등) - 환경설정 데이터 연동 권장
                    book_step = page.frame_locator("#ifrmBookStep")
                    birth_input = book_step.locator('input[name="YYMMDD"]')
                    custom_etc = book_step.locator('input[name="CustomEtc"]')
                    await birth_input.wait_for(state="attached", timeout=5000) #나타날때까지 대기
                    
                    payments = await book_step.locator('input[name="Payment"]').all()
                    for pay in payments:
                        if await pay.get_attribute("value") == "22004": # 무통장
                            await pay.click()
                            break
                    
                    # 은행 선택 (국민은행 등)
                    await book_step.locator('select[id="BankCode"]').select_option("38051")
                    
                    await page.wait_for_timeout(1000)
                    # 입력 필드 채우기
                    await birth_input.click()
                    await page.wait_for_timeout(200)
                    await birth_input.fill(str(self.birth_date)) 
                    
                    await custom_etc.click()
                    await page.wait_for_timeout(200)
                    await custom_etc.fill(str(self.car_number)) 

                    await page.wait_for_timeout(1500)
                    
                    # 다음 버튼 이동
                    await btns[1].click()
                    await page.wait_for_timeout(1000)

                    # 10. 최종 동의 및 예약 완료
                    book_step = page.frame_locator("#ifrmBookStep")                    
                    cancel_agree_btn = book_step.locator('input[id="CancelAgree"]')
                    await cancel_agree_btn.wait_for(state="attached", timeout=5000) #나타날때까지 대기
                    await cancel_agree_btn.click()
                    
                    # 예약 확인
                    final_btns = await book_step.locator("div[id='btn_Default'] a").all()
                    await final_btns[0].click() # 예약하기

                    await page.wait_for_timeout(2000)
                    return True

            except Exception as e:
                print(f"자동 예약 중 오류: {e}")
                return False
            finally:
                await browser.close()