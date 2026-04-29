import os
import sys
import yaml
import webbrowser
import xml.etree.ElementTree as ET
from threading import Timer
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi import Request, HTTPException
from platforms.thankq import ThankQMonitor
from platforms.interpark import InterparkMonitor

from core.logger import log_queue, logger
from core.config_loader import CONFIG
import httpx
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from core.scheduler import scheduler, start_scheduler
from core.websocket_manager import ws_manager

import logging


app = FastAPI()

@app.on_event("startup")
async def startup_event():
    start_scheduler()

# 1. CORS 설정 (가장 유력한 에러 원인 해결)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 로그를 가로챌 큐와 핸들러 (Java의 Appender 역할)
log_queue = asyncio.Queue()

class WSLogHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        # 루프가 실행 중일 때만 큐에 넣음
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(log_queue.put(msg))
        except RuntimeError:
            pass

# 로거 세팅
logger = logging.getLogger("camping")
logger.setLevel(logging.INFO)
handler = WSLogHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(handler)

# [경로 설정]
def get_base_path():
    """
    프로젝트 루트 경로를 반환합니다.
    - 배포 시: .exe 파일이 있는 폴더
    - 개발 시: app/ 폴더의 부모 폴더 (camping-scanner/)
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.dirname(sys.executable)
    
    # 현재 파일(main.py)의 부모(app)의 부모(root) 경로를 계산
    current_file_path = os.path.abspath(__file__)
    parent_dir = os.path.dirname(current_file_path) # app/
    root_dir = os.path.dirname(parent_dir)         # camping-scanner/
    return root_dir

def get_resource_path(relative_path):
    """
    PyInstaller의 임시 작업 폴더(_MEIPASS)를 기준으로 절대 경로를 생성합니다.
    Java의 ClassLoader.getResource()와 유사한 역할을 합니다.
    """
    if hasattr(sys, '_MEIPASS'):
        # 빌드 후: 임시 폴더 내의 경로
        return os.path.join(sys._MEIPASS, relative_path)
    # 개발 환경: 프로젝트 루트 기준 (app/main.py 위치에서 상위로 이동)
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), relative_path)


def load_campsites():
    """
    프로젝트 루트의 data/ 폴더에서 XML 파일들을 읽어 
    { '플랫폼명': ['캠핑장1', '캠핑장2'] } 구조로 반환합니다.
    """
    # [참고] Java의 ResourceLoader처럼 물리적 경로 계산
    base_path = get_base_path()
    data_dir = os.path.join(base_path, "data")
    
    # 전달해주신 파일명 리스트 매핑
    campsite_files = {
        "인터파크": "interpark-campsite.xml",
        "메이킹티켓": "maketicket-campsite.xml",
        "X티켓": "xticket-campsite.xml",
        "캠프링크": "camplink-campsite.xml",
        "숲나들e": "foresttrip-campsite.xml",
        "땡큐캠핑": "thankqcamping-campsite.xml",
        "캠핑톡": "campingtalk-campsite.xml",
        "네이버": "naver-campsite.xml",
        "포캠퍼": "forcamper-campsite.xml",
        "캠핏": "camfit-campsite.xml",
        "미리해": "mirihae-campsite.xml",
        "기타": "etc-campsite.xml"
    }
    
    result = {}
    
    # 1. data 폴더 존재 유무 확인 (Java의 익셉션 핸들링 대신 가벼운 체크)
    if not os.path.exists(data_dir):
        print(f"[!] 데이터 폴더를 찾을 수 없습니다: {data_dir}")
        return result

    for platform, filename in campsite_files.items():
        file_path = os.path.join(data_dir, filename)
        result[platform] = []
        
        if os.path.exists(file_path):
            try:
                # XML 파싱 시작 (DOM 파서와 유사)
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                # <campsite> 태그 내부의 <name> 추출
                for site in root.findall('campsite'):
                    name_node = site.find('name')
                    if name_node is not None and name_node.text:
                        result[platform].append(name_node.text.strip())
            except Exception as e:
                print(f"[!] {filename} 파싱 에러: {e}")
        else:
            # 파일이 없으면 빈 리스트 유지
            print(f"[-] 파일을 찾을 수 없음 (무시됨): {filename}")
            
    return result

# [설정 로드] - 호출 시점에 읽도록 수정
def load_config():
    """외부 config/config.yaml 로드"""
    base_path = get_base_path()
    # base_path가 이미 프로젝트 루트이므로 바로 config 폴더 결합
    config_path = os.path.join(base_path, "config", "config.yaml")
    
    print(f"[*] 설정 파일을 찾는 중: {config_path}") # 경로 확인용 출력
    
    default_config = {"server": {"port": 8000, "host": "127.0.0.1"}}
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                return content if content else default_config
        except Exception as e:
            print(f"[!] 설정 로드 실패: {e}")
    else:
        print(f"[!] 설정 파일을 찾지 못했습니다: {config_path}")
        
    return default_config

def get_xml_content(filename: str):
    """data/ 폴더에서 XML 파일의 원문을 문자열로 읽어옵니다."""
    # os.path.join은 Java의 Paths.get()과 유사한 역할을 합니다.
    file_path = os.path.join("data", filename)
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# static 폴더 경로 설정 (빌드 대응)
static_path = get_resource_path(os.path.join("app", "static"))
app.mount("/static", StaticFiles(directory=static_path), name="static")

template_path = get_resource_path(os.path.join("app", "templates"))
templates = Jinja2Templates(directory=template_path)


#프로젝트 루트의 data 폴더 경로 계산
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# [브라우저 오픈] - 호출될 때 config를 다시 확인
def open_browser(host, port):
    webbrowser.open(f"http://{host}:{port}")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):

    platform_map = {
        "인터파크": "interpark-campsite.xml",
        "메이킹티켓": "maketicket-campsite.xml",
        "X티켓": "xticket-campsite.xml",
        "캠프링크": "camplink-campsite.xml",
        "숲나들e": "foresttrip-campsite.xml",
        "땡큐캠핑": "thankqcamping-campsite.xml",
        "캠핑톡": "campingtalk-campsite.xml",
        "네이버": "naver-campsite.xml",
        "포캠퍼": "forcamper-campsite.xml",
        "캠핏": "camfit-campsite.xml",
        "미리해": "mirihae-campsite.xml",
        "기타": "etc-campsite.xml"
    }

    campsite_list = load_campsites()

    # 이제 templates 폴더 내부의 'index.html'을 찾습니다.
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"request": request, "campsites": campsite_list, "platform_map": platform_map, "port": CONFIG['server']['port'] }
    )


# API: 플랫폼 변경 시 호출될 엔드포인트 (AJAX용)
@app.get("/api/campsites/{filename}", response_class=PlainTextResponse)
async def get_campsite_list(filename: str):
    """
    선택된 플랫폼의 XML 파일 원문을 읽어서 반환합니다.
    Java의 ResponseEntity<String>과 유사합니다.
    """
    file_path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitor/start")
async def start_monitor(params: dict = Body(...), background_tasks: BackgroundTasks = None):
        
    print(f"[*] 요청 수신: {params}")

    logger.info(f"Monitor started for: {params.get('camp_id')}")

    """
    request_data: JSON Body가 Python dict(Map)으로 자동 매핑됨
    예: {"type": "THANKQ", "camp_id": "3446", "date": "2026-04-28", "site_codes": ["14147"]}
    """
    platform_type = params.get("type")
    interval = int(params.get("requestInterval", 60))
    job_id = params.get("watchUuid")

    # 전략 패턴을 이용한 인스턴스 생성

    if platform_type == "Thankqcamping":
        monitor = ThankQMonitor()
    elif platform_type == "Interpark":
        monitor = InterparkMonitor()
    else:
        return {"status": "error", "message": "지원하지 않는 플랫폼입니다."}

    
    # 백그라운드에서 감시 시작 (Spring의 @Async와 유사)
    existing_job = scheduler.get_job(job_id)
    if existing_job:
        return {"status": "success", "message": f"이미 실행중인 작업입니다."}

    # 런타임에 스케줄링 작업 등록 (Spring의 dynamic scheduling과 유사)
    scheduler.add_job(
        monitor.check_availability,  # 실행할 함수
        'interval', 
        seconds=interval, 
        args=[params],               # 함수에 넘길 파라미터(Map/dict)
        id=job_id
    )
    
    return {"status": "success", "message": f"{platform_type} 감시 시작"}

@app.post("/api/monitor/stop/{watch_uuid}")
async def stop_monitor(watch_uuid: str):
    try:
        
        # 등록된 스케줄러 작업 삭제 (Java의 scheduler.cancel(jobId) 역할)
        scheduler.remove_job(watch_uuid)
        logger.info(f"Monitor stopped for: {watch_uuid}")

        return {"status": "success", "message": f"Job {watch_uuid} stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def monitor_loop(monitor, params):
    import asyncio
    while True:
        found = await monitor.check_availability(params)
        if found:
            # 알림 발송 로직 호출
            print("🔥 빈자리 발견!")
            break
        await asyncio.sleep(60) # 1분 대기

@app.post("/api/shutdown")
async def shutdown():
    print("[*] 애플리케이션 종료 요청을 받았습니다.")
    # 브라우저에 응답을 보낸 후 1초 뒤에 프로세스를 종료합니다.
    # 바로 종료하면 브라우저가 응답을 못 받을 수 있기 때문입니다.
    def kill_process():
        os.kill(os.getpid(), signal.SIGTERM)
        
    Timer(1.0, kill_process).start()
    return {"status": "success", "message": "프로그램을 종료합니다."}

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 큐에 로그가 들어올 때까지 대기 (Java의 queue.take())
            log_msg = await log_queue.get()
            await websocket.send_text(log_msg)
    except WebSocketDisconnect:
        print("로그 웹소켓 연결 종료")

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    
    try:
        # 2. 중요: 무한 루프를 통해 연결 상태를 유지합니다.
        # 이 루프가 있어야 함수가 종료되지 않고 '감시' 상태를 유지합니다.
        while True:
            # 클라이언트로부터 메시지를 기다림 (연결 유지를 위한 통신)
            # 수신할 데이터가 없더라도 이 대기 상태가 필요합니다.
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        # 3. 브라우저 창을 닫으면 리스트에서 제거
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"웹소켓 에러: {e}")
        ws_manager.disconnect(websocket)


@app.get("/api/interpark/play-seq")
async def proxy_interpark_api(goodsCode: str, start_date: str, end_date: str):
    url = f"https://api-ticketfront.interpark.com/v1/goods/{goodsCode}/playSeq"
    params = {
        "goodsCode": goodsCode,
        "startDate": start_date,
        "endDate": end_date,
        "isBookableDate": "true",
        "page": 1,
        "pageSize": 1550
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Referer": f"https://tickets.interpark.com/goods/{goodsCode}"
    }

    async with httpx.AsyncClient() as client:
        # 서버가 대신 인터파크에 물어봅니다.
        response = await client.get(url, params=params, headers=headers)
        return response.json()

# 테스트용 크롤링 시뮬레이션 태스크
@app.on_event("startup")
async def start_demo_logging():
    async def simulate_logging():
        while True:
            logger.info("서버가 정상 기동중...")
            await asyncio.sleep(10)
    asyncio.create_task(simulate_logging())

if __name__ == "__main__":
    # 1. 실행 직전에 설정을 읽습니다.
    current_config = load_config()
    target_port = int(current_config['server']['port'])
    target_host = current_config['server']['host']
    
    print(f"[*] Starting server on {target_host}:{target_port}")

    # 2. 타이머에 현재 읽은 포트 정보를 넘깁니다.
    Timer(1.5, open_browser, args=[target_host, target_port]).start()
    
    # 3. uvicorn에 현재 읽은 포트를 적용합니다.
    uvicorn.run(
        app, 
        host=target_host, 
        port=target_port, 
        log_config=None, 
        workers=1
    )