from fastapi import APIRouter, status
from app.core.database import get_db
from app.schemas.models import MaintenanceTicketCreate
from app.ai.ai_agents_engine import run_ai_agent

router = APIRouter(prefix="/api/maintenance", tags=["05. Home Maintenance API (الصيانة والأعطال المنزلية)"])


@router.get("")
def list_maintenance_tickets(building_id: int = 1):
    """[API #5] عرض بلاغات الصيانة المنزلية (سباكة، كهرباء، غاز، أسانسير) مع تشخيص الذكاء الاصطناعي."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT m.*, u.full_name AS resident_name, u.apartment_number
            FROM maintenance_tickets m
            JOIN users u ON u.id = m.resident_id
            WHERE m.building_id = ?
            ORDER BY m.created_at DESC;
            """,
            (building_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_maintenance_ticket(payload: MaintenanceTicketCreate):
    """فتح تذكرة صيانة جديدة مع تشغيل وكيل تشخيص الأعطال (AI Agent #4) تلقائياً."""
    ai_diag = run_ai_agent("agent_04_maintenance_diagnostician", f"{payload.issue_title} - {payload.description}", payload.building_id)
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO maintenance_tickets (
                building_id, resident_id, specialty, issue_title, description,
                urgency, assigned_technician, estimated_cost, ai_diagnosis
            ) VALUES (?, ?, ?, ?, ?, ?, 'بإشراف عم عبد السميع والفني المختص', ?, ?);
            """,
            (
                payload.building_id,
                payload.resident_id,
                payload.specialty,
                payload.issue_title,
                payload.description,
                payload.urgency,
                payload.estimated_cost,
                ai_diag["summary_ar"],
            ),
        )
        row = conn.execute("SELECT * FROM maintenance_tickets WHERE id = ?;", (cur.lastrowid,)).fetchone()
        return dict(row)
