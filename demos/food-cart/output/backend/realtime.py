from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.admin_connections: List[WebSocket] = []
        self.order_connections: Dict[int, List[WebSocket]] = {}

    async def connect_admin(self, websocket: WebSocket):
        await websocket.accept()
        self.admin_connections.append(websocket)

    def disconnect_admin(self, websocket: WebSocket):
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)

    async def connect_order(self, order_id: int, websocket: WebSocket):
        await websocket.accept()
        self.order_connections.setdefault(order_id, []).append(websocket)

    def disconnect_order(self, order_id: int, websocket: WebSocket):
        sockets = self.order_connections.get(order_id, [])
        if websocket in sockets:
            sockets.remove(websocket)

    async def broadcast_admin(self, message: dict):
        for websocket in list(self.admin_connections):
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect_admin(websocket)

    async def broadcast_order(self, order_id: int, message: dict):
        for websocket in list(self.order_connections.get(order_id, [])):
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect_order(order_id, websocket)

manager = ConnectionManager()
