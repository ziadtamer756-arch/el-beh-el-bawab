from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.database import get_db

router = APIRouter(prefix="/api/notifications", tags=["Notifications & WebSockets (الإشعارات اللحظية)"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


@router.get("/{user_id}")
def get_user_notifications(user_id: int):
    """جلب قائمة الإشعارات الخاصة بالمستخدم (الساكن أو البواب)."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 30;",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.patch("/{notification_id}/read")
def mark_notification_read(notification_id: int):
    """تحديد الإشعار كمقروء."""
    with get_db() as conn:
        conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ?;", (notification_id,))
        return {"status": "ok", "id": notification_id}


@router.websocket("/ws/{building_id}")
async def building_websocket_endpoint(websocket: WebSocket, building_id: int):
    """قناة اتصال لحظي (WebSocket) لإرسال تنبيهات الطلبات الجديدة وتحديثاتها فوراً."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast({"building_id": building_id, "event": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
