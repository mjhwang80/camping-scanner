import logging
import os
import asyncio
from logging.handlers import RotatingFileHandler

# 웹소켓 전송용 비동기 큐 (Java의 BlockingQueue와 유사)
log_queue = asyncio.Queue()

class WebSocketLogHandler(logging.Handler):
    """로그 발생 시 웹소켓 전송 큐에 삽입하는 커스텀 핸들러"""
    def emit(self, record):
        log_entry = self.format(record)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(log_queue.put(log_entry))
        except RuntimeError:
            pass # 이벤트 루프가 없는 경우(단독 실행 등) 무시

def setup_logging():
    # 'camping'이라는 이름의 루트 로거 생성
    logger = logging.getLogger("camping")
    logger.setLevel(logging.INFO)
    
    # logs 폴더가 없으면 생성
    log_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 로그 출력 포맷 설정
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    # --- 핸들러 설정 ---
    
    # 1. 콘솔 로그 (터미널 출력용)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. 파일 로그 (로그 파일 저장용 - 용량 제한 및 백업 설정)
    file_path = os.path.join(log_dir, "camping_monitor.log")
    file_handler = RotatingFileHandler(
        file_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 3. 웹소켓 로그 (실시간 웹 화면 표출용)
    ws_handler = WebSocketLogHandler()
    ws_handler.setFormatter(logging.Formatter('%(message)s')) # 소켓은 간결하게 전송
    logger.addHandler(ws_handler)

    return logger

# 앱 전체에서 사용할 로거 인스턴스
logger = setup_logging()