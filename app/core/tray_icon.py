import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import webbrowser

class TrayIcon:
    def __init__(self, host, port, stop_callback):
        self.url = f"http://{host}:{port}"
        self.stop_callback = stop_callback
        self.icon = None
        self.allow_notification = True  # 알람 수신 여부

    def create_camping_icon(self):
        """캠핑 텐트 모양의 아이콘 이미지를 생성합니다."""
        width, height = 64, 64
        image = Image.new('RGB', (width, height), color=(30, 58, 138)) # 밤하늘
        dc = ImageDraw.Draw(image)
        # 노란색 텐트 삼각형
        dc.polygon([(32, 10), (10, 54), (54, 54)], fill=(234, 179, 8)) 
        dc.rectangle([25, 40, 39, 54], fill=(120, 53, 15)) # 입구
        return image

    def toggle_notification(self, icon, item):
        self.allow_notification = not self.allow_notification
        print(f"[*] 시스템 알림 설정 변경: {self.allow_notification}")

    def notify(self, title, message):
        """윈도우 알림 노출 (아이콘 객체 존재 여부 및 설정 체크)"""
        if self.icon is not None and self.allow_notification:
            # 윈도우 알림 센터에 'CampingScanner' 알림 권한이 있는지 확인 필요
            self.icon.notify(message, title)
        elif self.icon is None:
            print(f"[!] 트레이 아이콘이 아직 준비되지 않았습니다: {title}")

    def run(self):
        menu = (
            item('브라우저 열기', lambda: webbrowser.open(self.url)),
            item('알람 받기', self.toggle_notification, checked=lambda item: self.allow_notification),
            item('프로그램 종료', lambda icon: [icon.stop(), self.stop_callback()]),
        )
        self.icon = pystray.Icon("CampingScanner", self.create_camping_icon(), "Camping Scanner", menu)
        self.icon.run()