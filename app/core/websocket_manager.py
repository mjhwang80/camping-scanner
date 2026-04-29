from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # 연결된 모든 브라우저에게 JSON 메시지 전송
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # 연결이 끊긴 경우 리스트에서 제거 시도
                pass

# 싱글톤 인스턴스 생성
ws_manager = ConnectionManager()