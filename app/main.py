#app/main.py
import os
import sys
import yaml
import signal
import webbrowser
import xml.etree.ElementTree as ET
from threading import Timer, Thread
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi import Request, HTTPException, FastAPI, WebSocket, WebSocketDisconnect, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import httpx
import asyncio
import logging

from core.config_loader import get_resource_path, get_external_path, CONFIG, load_full_config, save_config
#from core.logger import log_queue, logger
from core.logger import log_queue, logger, setup_logging
from core.scheduler import scheduler, start_scheduler
from core.websocket_manager import ws_manager
from core.browser_handler import get_browser_path
from core.tray_icon import TrayIcon

# 플랫폼 전략 패턴 클래스군 로드
from platforms.thankq import ThankQMonitor
from platforms.interpark import InterparkMonitor
from platforms.mirihae import MirihaeMonitor
from platforms.maketicket import MaketicketMonitor
from platforms.xticket import XticketMonitor
from platforms.campingtalk import CampingtalkQMonitor
from platforms.camplink import CamplinkMonitor
from platforms.dugsan import DugsanMonitor
from platforms.pubcamping import PubcampingMonitor
from platforms.gtdc import GtdcMonitor
from platforms.foresttrip import ForesttripMonitor
from platforms.artmuseum import ArtmuseumCampingMonitor

from utils.download import download_cdn_video, download_youtube
from fastapi import BackgroundTasks
from core.monitor_manager import MonitorManager
from concurrent.futures import ThreadPoolExecutor

try:
    path = get_browser_path()
    print(f"[*] 브라우저 경로 설정 완료: {path}")
except Exception as e:
    print(f"[!] 브라우저 경로 설정 실패: {e}")

app = FastAPI()
tray_manager = None

@app.on_event("startup")
async def startup_event():
    setup_logging()  # 여기서 한 번만 전체 로깅 환경을 초기화
    start_scheduler()
    async def simulate_logging():
        while True:
            logger.info("캠핑장 실시간 모니터링 엔진 정상 기동중...")
            await asyncio.sleep(60 * 3)
    asyncio.create_task(simulate_logging())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("[*] 애플리케이션 종료 프로세스 시작...")

    # 1. 스케줄러를 먼저 멈춰서 신규 작업 진입 차단
    if scheduler.running:
        scheduler.shutdown(wait=False) # wait=False로 설정하여 빠르게 종료
        logger.info("[*] 스케줄러 가동 중단 완료.")

    # 2. MonitorManager를 통해 모든 모니터 객체 가져오기
    all_monitors = MonitorManager.get_all()
    
    # 3. 모든 모니터를 순회하며 자원 해제
    for monitor_id, monitor in all_monitors.items():
        try:
            if hasattr(monitor, 'close_client'):
                await monitor.close_client()
                logger.info(f"[-] 모니터 {monitor_id} 자원 해제 완료.")
        except Exception as e:
            logger.error(f"[!] 모니터 {monitor_id} 종료 중 오류 발생: {e}")

    logger.info("[*] 모든 자원 정리가 완료되었습니다.")

def run_server():
    target_port = int(CONFIG['server']['port'])    
    target_host = str(CONFIG['server']['host'])
    uvicorn.run(app, host=target_host, port=target_port, log_config=None, workers=1)

def stop_server():
    os.kill(os.getpid(), signal.SIGTERM)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
log_queue = asyncio.Queue()
class WSLogHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(log_queue.put(msg))
        except RuntimeError:
            pass

logger = logging.getLogger("camping")
logger.setLevel(logging.INFO)
handler = WSLogHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(handler)
"""


def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_config():
    base_path = get_base_path()
    config_path = os.path.join(base_path, "config", "config.yaml")
    default_config = {"server": {"port": 8000, "host": "127.0.0.1"}}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                return content if content else default_config
        except Exception as e:
            print(f"[!] 설정 오버라이드 실패: {e}")
    return default_config

static_path = get_resource_path(os.path.join("app", "static"))
app.mount("/static", StaticFiles(directory=static_path), name="static")

template_path = get_resource_path(os.path.join("app", "templates"))
templates = Jinja2Templates(directory=template_path)

def open_browser(host, port):
    webbrowser.open(f"http://{host}:{port}")

def get_platform_info():
    base_path = get_base_path()
    data_dir = os.path.join(base_path, "data")
    platforms = []
    if not os.path.exists(data_dir):
        return platforms

    for filename in os.listdir(data_dir):
        if filename.endswith("-campsite.xml"):
            file_path = os.path.join(data_dir, filename)
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                type_name = root.findtext('typeName', '이름 없음').strip()
                type_order = int(root.findtext('typeOrder', '999').strip())
                platforms.append({
                    "filename": filename,
                    "typeName": type_name,
                    "typeOrder": type_order
                })
            except Exception as e:
                logger.error(f"[!] {filename} 파싱 에러: {e}")

    platforms.sort(key=lambda x: x['typeOrder'])
    return platforms

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    sorted_platforms = get_platform_info()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "platform_list": sorted_platforms, "port": CONFIG['server']['port']}
    )

@app.get("/api/campsites/{filename}", response_class=PlainTextResponse)
async def get_campsite_list(filename: str):
    file_path = get_external_path(os.path.join("data", filename))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"파일 분실: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitor/start")
async def start_monitor(params: dict = Body(...)):
    platform_type = params.get("type")
    interval = int(params.get("requestInterval", 60))
    job_id = params.get("watchUuid")
    exec_type = params.get("execType", "NOW")
    reserved_time_str = params.get("reservedTime")

    # 전략 패턴 모니터 인스턴스 할당
    if platform_type == "Thankqcamping": monitor = ThankQMonitor()
    elif platform_type == "Interpark": monitor = InterparkMonitor()
    elif platform_type == "Mirihae": monitor = MirihaeMonitor()
    elif platform_type == "Maketicket": monitor = MaketicketMonitor()
    elif platform_type == "Xticket": monitor = XticketMonitor()
    elif platform_type == "Campingtalk": monitor = CampingtalkQMonitor()
    elif platform_type == "Camplink": monitor = CamplinkMonitor()
    elif platform_type == "Dugsan": monitor = DugsanMonitor()
    elif platform_type == "Pubcamping": monitor = PubcampingMonitor()
    elif platform_type == "Gtdc": monitor = GtdcMonitor()
    elif platform_type == "Foresttrip": monitor = ForesttripMonitor()
    elif platform_type == "ArtMuseum": monitor = ArtmuseumCampingMonitor()

    else: return {"status": "error", "message": "미지원 크롤링 타깃"}

    existing_job = scheduler.get_job(job_id)
    if existing_job:
        return {"status": "success", "message": "동일 작업 실행중"}

    if exec_type == "RESERVED" and reserved_time_str:
        try:
            clean_time_str = reserved_time_str.replace("T", " ")
            start_time = datetime.strptime(clean_time_str, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"[!] 예약 포맷 파싱 오류: {e}")
            return {"status": "error", "message": "시간 파싱 에러"}
    else:
        start_time = datetime.now()

    dynamic_jitter = int(interval * 0.2)
    scheduler.add_job(
        monitor.check_availability,
        'interval',
        seconds=interval,
        jitter=dynamic_jitter,
        args=[params],
        id=job_id,
        next_run_time=start_time
    )
    monitor.params = params
    MonitorManager.add(job_id, monitor)

    # [다중기기 동기화 알림] 다른 기기 브라우저 화면에도 실시간으로 갱신되도록 웹소켓 브로드캐스팅 방출
    asyncio.create_task(ws_manager.broadcast({
        "messageType": "add_monitor",
        "data": params
    }))

    return {"status": "success", "message": "감시 작업 커맨드 접수"}

@app.post("/api/monitor/stop/{watch_uuid}")
async def stop_monitor(watch_uuid: str):

    logger.info(f"[*] 감시 종료 요청 접수: {watch_uuid}") # 진입 로그 추가
    try:
        # 1. MonitorManager를 통해 모니터 객체 확보
        monitor = MonitorManager.get(watch_uuid)
        
        # 2. 리소스 정리 (close_client)
        if monitor:
            if hasattr(monitor, 'close_client'):
                await monitor.close_client()
            # 관리자에서 제거
            MonitorManager.remove(watch_uuid)
        else:
            logger.warning(f"[!] 모니터 객체를 찾을 수 없음: {watch_uuid}")
        
        if scheduler.get_job(watch_uuid):
            scheduler.remove_job(watch_uuid)
            
        await ws_manager.broadcast({"messageType": "remove_monitor", "data": {"uuid": watch_uuid}})
        return {"status": "success", "message": "Job stopped"}
    except Exception as e:
        logger.error(f"[!] stop_monitor 오류: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/monitor/list")
async def get_monitor_list():
    running_jobs = []
    
    # 1. MonitorManager에서 모든 모니터 객체 가져오기
    all_monitors = MonitorManager.get_all()
    
    for job_id, monitor in all_monitors.items():
        # 2. 스케줄러에 해당 작업이 실제로 존재하는지 확인
        if scheduler.get_job(job_id):
            # 3. monitor 객체에서 params 속성을 가져와 리스트에 추가
            # 모니터 클래스 구현 시 self.params가 설정되어 있어야 합니다.
            if hasattr(monitor, 'params'):
                running_jobs.append(monitor.params)
            else:
                # 만약 params 속성이 없다면, 기본값 처리 혹은 로그 기록
                logger.warning(f"[!] 모니터 객체 {job_id}에 params 속성이 없습니다.")
                
    return running_jobs

@app.post("/api/shutdown")
async def shutdown():    
    logger.info("[*] 종료 시그널 접수.")
    
    logger.info("서버 종료 중... 모든 모니터링 클라이언트 정리")
    all_monitors = MonitorManager.get_all()
    for job_id, monitor in all_monitors.items():
        if hasattr(monitor, 'close_client'):
            await monitor.close_client()
    
    def kill_process():
        try: os.kill(os.getpid(), signal.SIGTERM)
        except: os._exit(0)
    Timer(1.0, kill_process).start()
    return {"status": "success"}

@app.websocket("/ws/logs")
async def websocket_endpoint_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 큐에서 데이터를 가져와 전송
            log_msg = await log_queue.get()
            await websocket.send_text(log_msg)
    except WebSocketDisconnect:
        logger.info("로그 웹소켓 연결이 해제되었습니다.")
    except Exception as e:
        logger.error(f"로그 웹소켓 오류: {e}")

@app.websocket("/ws/alerts")
async def websocket_endpoint_alerts(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

@app.get("/api/interpark/play-seq")
async def proxy_interpark_api(goodsCode: str, start_date: str, end_date: str):
    url = f"https://api-ticketfront.interpark.com/v1/goods/{goodsCode}/playSeq"
    params = {"goodsCode": goodsCode, "startDate": start_date, "endDate": end_date, "isBookableDate": "true", "page": 1, "pageSize": 1550}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": f"https://tickets.interpark.com/goods/{goodsCode}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        return response.json()

@app.get("/api/settings")
async def get_settings():
    return {"telegram": CONFIG.get("telegram", {"use_yn": "N", "token": "", "chat_ids": []}), "info": CONFIG.get("info", {})}

@app.post("/api/settings/telegram")
async def save_telegram(settings: dict = Body(...)):
    save_config({"telegram": settings})
    return {"status": "success"}

@app.post("/api/settings/info")
async def save_info(info: dict = Body(...)):
    save_config({"info": info})
    return {"status": "success"}

@app.post("/api/auth/interpark-session")
async def create_interpark_session():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context()
        page = await context.new_page()
        closed_event = asyncio.Event()

        async def on_close(p):
            await context.storage_state(path="interpark_auth.json")
            closed_event.set()

        page.on("close", on_close)
        await page.goto("https://nol.interpark.com/ticket")
        await closed_event.wait()
        await browser.close()
        return {"status": "success"}



# [추가] 미디어 다운로드 전용 고정 스레드 풀 정의 (자바의 Executors.newFixedThreadPool(2) 역할)
# 사양에 따라 동시 다운로드 개수를 조절하세요. FFmpeg 연산 부하 때문에 2~3개를 추천합니다.
DOWNLOAD_THREAD_POOL = ThreadPoolExecutor(max_workers=2)

@app.post("/api/tools/download")
async def api_download_media(
    background_tasks: BackgroundTasks, 
    payload: dict = Body(...)
):
    dl_type = payload.get("type")
    url = payload.get("url", "").strip()
    referer = payload.get("referer", "").strip() 

    if not url:
        return {"status": "error", "message": "URL을 입력해주세요."}

    actual_referer = referer if referer else None
    
    # [추가] 현재 이벤트 루프 가져오기
    loop = asyncio.get_running_loop()

    if dl_type == "cdn":
        # background_tasks 안에서 고정 스레드 풀을 통해 실행되도록 위임(Delegate)
        background_tasks.add_task(
            lambda: loop.run_in_executor(DOWNLOAD_THREAD_POOL, download_cdn_video, url, actual_referer)
        )
    elif dl_type in ["youtube_mp3", "youtube_video"]:
        # background_tasks 안에서 고정 스레드 풀을 통해 실행되도록 위임(Delegate)
        background_tasks.add_task(
            lambda: loop.run_in_executor(DOWNLOAD_THREAD_POOL, download_youtube, url, dl_type, actual_referer)
        )
    else:
        return {"status": "error", "message": "올바르지 않은 다운로드 타입입니다."}

    logger.info(f"[요청 수신] {dl_type} 다운로드 큐 등록 완료 (Referer 설정여부: {bool(actual_referer)})")
    return {"status": "success", "message": "다운로드 요청을 접수했습니다. 정해진 순서대로 진행되니 하단 로그 콘솔을 모니터링 하세요."}

def check_expiration():
    if datetime.now() > datetime(2026, 7, 30):
        print("[!] 프로그램 사용 기한이 만료되었습니다.")
        sys.exit()

if __name__ == "__main__":
    check_expiration()
    get_browser_path()
    target_port = int(CONFIG['server']['port'])
    
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()

    Timer(2.0, open_browser, args=["127.0.0.1", target_port]).start()
    tray_manager = TrayIcon("127.0.0.1", target_port, stop_server)
    tray_manager.run()