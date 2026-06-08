import asyncio
import httpx
import logging
from datetime import datetime, timedelta

# 터미널 디버깅용 로그 설정
logging.basicConfig(level=logging.ERROR, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("camping.xml_purifier")

# [비동기 함수 1] 2단계: 특정 단지 안의 구역 코드(ROOM_AREA_NO)를 넘겨받아 세부 자리(sites)들의 XML 리스트 반환
async def fetch_sites_xml_block(client, camp_id, area_no, base_headers):
    url = f"https://gwgs.pubcamping.kr/{camp_id}/productSelectJson.do"
    
    test_check_in = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")
    test_check_out = (datetime.now() + timedelta(days=2)).strftime("%Y%m%d")

    data = {
        "stay_cnt": "1",
        "check_in": test_check_in,
        "check_out": test_check_out,
        "room_area_no": str(area_no)
    }
    
    req_headers = base_headers.copy()
    req_headers["Referer"] = f"https://gwgs.pubcamping.kr/{camp_id}/html/reservation/online.html"
    
    xml_lines = []
    try:
        response = await client.post(url, data=data, headers=req_headers, timeout=10.0)
        if response.status_code == 200:
            result_json = response.json()
            if result_json.get("RESULT_CODE") == "SUCCESS":
                room_list = result_json.get("RESULT_DATA", [])
                for room in room_list:
                    room_no = room.get("ROOM_NO")
                    room_name = room.get("ROOM_NAME")
                    if room_no and room_name:
                        xml_lines.append(f"\t\t\t\t<site group='{area_no}' code='{room_no}'><![CDATA[{room_name}]]></site>")
    except Exception as e:
        logger.error(f"[!] camp_id: {camp_id} | 구역 {area_no} 상세 사이트 패치 중 예외 발생: {str(e)}")
        
    return xml_lines


# [마스터 함수] 단일 캠핑장 정보 내부에서 모든 camp_no 단지들을 수집한 뒤 단 하나의 <campsite> 구조만 독립 출력
async def generate_campsite_xml_by_id(campsite_info: dict):
    camp_id = campsite_info.get("camp_id")
    campsite_name = campsite_info.get("campsiteName")
    camp_no = campsite_info.get("camp_no")
    test_check_in = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")
    
    search_url = f"https://gwgs.pubcamping.kr/{camp_id}/productSearchJson.do"
    
    base_headers = {
        "Host": "gwgs.pubcamping.kr",
        "Origin": "https://gwgs.pubcamping.kr",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 🛠️ 수정 포인트 1: 캠핑장(camp_id)별로 단 하나의 통합 보관 공간을 선언합니다.
    local_groups = []
    local_sites = []

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False) as client:
        try:
            #print(f"\n📡 [스캔 시작] 단지 통합 추적 가동: {campsite_name} ({camp_id})")
            
            search_data = {
                "stay_cnt": "1",
                "check_in": test_check_in,
                "camp_no": str(camp_no)
            }
            
            response = await client.post(search_url, data=search_data, headers=base_headers)
            if response.status_code != 200:
                return False
            search_result = response.json()
            area_list = search_result.get("RESULT_DATA", [])
            
            # 더 이상 단지 정보가 리턴되지 않으면 내부 단지 탐색 완료 루프 탈출
            if not area_list:
                return False
            
            # 발견된 구역 정보를 공유 보관 통인 local_groups에 순차 누적
            current_area_nodes = []
            for area in area_list:
                area_no = area.get("ROOM_AREA_NO")
                area_name = area.get("ROOM_AREA_NAME")
                if area_no and area_name:
                    local_groups.append(f'\t\t<group code="{area_no}">{area_name}</group>')
                    current_area_nodes.append(area_no)
            
            # 현재 단지에서 긁어온 구역 코드를 바탕으로 자식 세부 사이트(ROOM) 패치 연동
            if current_area_nodes:
                sub_tasks = [
                    fetch_sites_xml_block(client, camp_id, area_no, base_headers)
                    for area_no in current_area_nodes
                ]
                all_sites_results = await asyncio.gather(*sub_tasks)
                
                # 공유 보관 통인 local_sites에 연속 병합 누적
                for site_lines in all_sites_results:
                    local_sites.extend(site_lines)
            
            
            # 🛠️ 수정 포인트 2: while True 단지 순회가 모두 끝난 후, 캠핑장(camp_id)당 '딱 한 번만' XML 구조를 빌드출력 합니다.
            if local_groups:
                #print("\n" + "═"*75)
                #print(f"🌲 [통합 XML 덤프] {campsite_name} ({camp_id}) 마스터 노드 완료")
                #print("═"*75)
                
                print("<campsite>")
                print(f"\t<name>{campsite_name}</name>")
                print(f"\t<code>{camp_id}</code>")
                print("\t<maxStayDay>3</maxStayDay>")
                print(f"\t<homepage><![CDATA[https://gwgs.pubcamping.kr/{camp_id}/index?]]></homepage>")
                
                # 모든 단지에서 긁어모은 대분류 그룹 일괄 덤프
                print("\t<groups>")
                for group_line in local_groups:
                    print(group_line)
                print("\t</groups>")
                
                # 모든 단지에서 긁어모은 세부 자식 사이트 일괄 덤프
                print("\t<sites>")
                for site_line in local_sites:
                    print(site_line)
                print("\t</sites>")
                
                print("</campsite>")
                #print("═"*75 + "\n")
            else:
                logger.warning(f"⚠️ [{campsite_name}] 활성화된 데이터가 없어 출력을 패스합니다.")

        except Exception as err:
            logger.error(f"[!] [{campsite_name}] 배치 조립 중 예외 에러: {str(err)}")


# [배치 코어 엔트리] 고성군 6대 공공캠핑장을 안전하게 순차 순회
async def main_batch_process():
    campsite_list = [
       # {"camp_id": "@myeongpa", "campsiteName": "명파오토캠핑장", "camp_no" : 3},
        {"camp_id": "@baekdo", "campsiteName": "백도오토캠핑장", "camp_no" : 2},
        {"camp_id": "@bongsucamp", "campsiteName": "봉수대오토캠핑장", "camp_no" : 5},
        {"camp_id": "@song", "campsiteName": "송지호 오토캠핑장", "camp_no" : 3},
        {"camp_id": "@oho", "campsiteName": "오호 캠핑장", "camp_no" : 1},
        {"camp_id": "@jajakdo", "campsiteName": "자작도 캠핑장", "camp_no" : 4}
    ]
    
    print("🎬 고성군 공공캠핑장 전체 6개소 개별 격리 XML 파일용 추출 스캐너 기동.")
    
    for campsite in campsite_list:
        await generate_campsite_xml_by_id(campsite)
        
    print("🏁 전체 캠핑장의 개별 격리 XML 구조화 생성이 모두 종료되었습니다.")


if __name__ == "__main__":
    # 비동기 엔진 점화
    asyncio.run(main_batch_process())