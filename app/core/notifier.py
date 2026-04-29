import httpx
import logging
from .config_loader import CONFIG

logger = logging.getLogger("camping.notifier")

class TelegramNotifier:
    def __init__(self):
        # YAML 설정 로드 (KeyError 방지를 위해 get 사용 권장)
        tel_config = CONFIG.get('telegram', {})
        self.token = tel_config.get('token')
        self.chat_ids = tel_config.get('chat_ids', [])
        self.use_yn = tel_config.get('use_yn', 'N')
        
        # self.chat_id -> self.chat_ids로 수정
        if self.use_yn == 'Y' and self.token and self.chat_ids:
            self.is_active = True
            self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            logger.info("텔레그램 알림 기능이 활성화되었습니다.")
        else:
            self.is_active = False
            self.api_url = None
            logger.warning("텔레그램 설정이 미비하여 비활성화되었습니다.")

    async def send_message(self, message):
        if not self.is_active:
            return

        async with httpx.AsyncClient() as client:
            # 루프를 AsyncClient 내부로 이동
            for chat_id in self.chat_ids:
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                try:
                    response = await client.post(self.api_url, json=payload)
                    if response.status_code == 200:
                        logger.info(f"알림 발송 성공 (ID: {chat_id})")
                    else:
                        logger.error(f"발송 실패 ({chat_id}): {response.text}")
                except Exception as e:
                    logger.error(f"통신 오류 ({chat_id}): {e}")

# 공통 인스턴스 생성
notifier = TelegramNotifier()