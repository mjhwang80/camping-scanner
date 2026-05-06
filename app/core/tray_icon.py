import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import webbrowser
import platform
import subprocess

class TrayIcon:
    def __init__(self, host, port, stop_callback):
        self.url = f"http://{host}:{port}"
        self.stop_callback = stop_callback
        self.icon = None
        self.allow_notification = True

    def create_camping_icon(self):
        width, height = 64, 64
        # Mac의 다크 모드/라이트 모드를 고려하여 투명 배경 권장
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        dc.polygon([(32, 10), (10, 54), (54, 54)], fill=(234, 179, 8)) 
        dc.rectangle([25, 40, 39, 54], fill=(120, 53, 15)) 
        return image

    def notify(self, title, message):
        """OS별 알림 처리"""
        if not self.allow_notification:
            return

        if platform.system() == "Darwin": # Mac 환경
            # AppleScript를 사용하여 시스템 알림 발송
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script])
        else: # Windows 등 기타
            if self.icon:
                self.icon.notify(message, title)

    def run(self):
        """
        [중요] Mac에서는 이 함수가 반드시 Main Thread에서 호출되어야 합니다.
        """
        menu = (
            item('브라우저 열기', lambda: webbrowser.open(self.url)),
            item('알람 설정', self.toggle_notification, checked=lambda item: self.allow_notification),
            item('프로그램 종료', self.on_quit),
        )
        self.icon = pystray.Icon("CampingScanner", self.create_camping_icon(), "Camping Scanner", menu)
        # icon.run()은 블로킹 함수입니다.
        self.icon.run()

    def toggle_notification(self, icon, item):
        self.allow_notification = not self.allow_notification

    def on_quit(self, icon):
        icon.stop()
        self.stop_callback()