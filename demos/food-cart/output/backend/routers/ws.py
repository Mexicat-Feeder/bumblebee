from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from realtime import manager

router = APIRouter(prefix='/api/ws', tags=['websocket'])

@router.websocket('/orders')
async def admin_orders_socket(websocket: WebSocket):
    await manager.connect_admin(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_admin(websocket)

@router.websocket('/orders/{order_id}')
async def order_status_socket(order_id: int, websocket: WebSocket):
    await manager.connect_order(order_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_order(order_id, websocket)
