import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import webbrowser

class TrayIcon:
    def __init__(self, host, port, stop_callback):
        self.url = f"http://{host}:{port}"
        self.stop_callback = stop_callback
        self.icon = None
        self.allow_notification = True  # 알람 수신 여부 상태값

    def create_camping_icon(self):
        """캠핑 텐트 모양의 아이콘 이미지를 생성합니다."""
        width, height = 64, 64
        image = Image.new('RGB', (width, height), color=(30, 58, 138)) # 밤하늘 배경
        dc = ImageDraw.Draw(image)
        dc.polygon([(32, 10), (10, 54), (54, 54)], fill=(234, 179, 8)) # 노란 텐트
        dc.rectangle([25, 40, 39, 54], fill=(120, 53, 15)) # 입구
        return image

    def toggle_notification(self, icon, item):
        """알람 받기 상태를 반전시킵니다."""
        self.allow_notification = not self.allow_notification
        print(f"[*] 알람 수신 설정 변경: {self.allow_notification}")

    def notify(self, title, message):
        """'NoneType' 오류 방지: icon이 준비되었고 알람 설정이 켜져 있을 때만 노출"""
        if self.icon is not None and self.allow_notification:
            try:
                self.icon.notify(message, title) # 실제 윈도우 알림 호출
            except Exception as e:
                print(f"[!] 알림 발송 중 오류: {e}")
        elif self.icon is None:
            print(f"[!] 트레이 아이콘 초기화 대기 중... 알림 보류: {title}")

    def run(self):
        # 메뉴 구성: 알람 받기 여부를 체크박스(Checked) 형태로 제공
        menu = (
            item('브라우저 열기', lambda: webbrowser.open(self.url)),
            item('알람 받기', self.toggle_notification, checked=lambda item: self.allow_notification),
            item('프로그램 종료', lambda icon: [icon.stop(), self.stop_callback()]),
        )
        self.icon = pystray.Icon("CampingScanner", self.create_camping_icon(), "Camping Scanner", menu)
        self.icon.run()