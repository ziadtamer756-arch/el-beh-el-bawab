from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect
from app.core.database import get_db
from app.schemas.models import EmergencySOSCreate
from app.services.ai_agents_engine import run_ai_agent

router = APIRouter(prefix="/api/emergency", tags=["14. Emergency SOS & Realtime Alerts API (طوارئ العمارة والاستغاثة)"])


@router.get("/{building_id}")
def list_emergency_alerts(building_id: int = 1):
    """[API #14] عرض بلاغات الطوارئ والاستغاثة النشطة في العمارة."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT e.*, u.full_name AS reporter_name, u.apartment_number
            FROM emergency_alerts e
            JOIN users u ON u.id = e.reporter_id
            WHERE e.building_id = ?
            ORDER BY e.created_at DESC;
            """,
            (building_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/sos", status_code=status.HTTP_201_CREATED)
def trigger_emergency_sos(payload: EmergencySOSCreate):
    """إطلاق نداء استغاثة عاجل (احتجاز أسانسير / تسريب غاز / مياه) وتوليد خطة طوارئ فورية عبر AI Agent #14."""
    ai_plan = run_ai_agent("agent_14_emergency_sos", f"{payload.emergency_type} في {payload.apartment_or_location}", payload.building_id)
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO emergency_alerts (building_id, reporter_id, emergency_type, apartment_or_location, status, ai_action_plan)
            VALUES (?, ?, ?, ?, 'active', ?);
            """,
            (payload.building_id, payload.reporter_id, payload.emergency_type, payload.apartment_or_location, ai_plan["summary_ar"]),
        )
        row = conn.execute("SELECT * FROM emergency_alerts WHERE id = ?;", (cur.lastrowid,)).fetchone()
        return dict(row)


@router.websocket("/ws/{building_id}")
async def emergency_websocket(websocket: WebSocket, building_id: int):
    """قناة اتصال لحظي لبلاغات الطوارئ والإشعارات."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"building_id": building_id, "alert": data})
    except WebSocketDisconnect:
        pass
