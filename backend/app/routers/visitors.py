import random
from fastapi import APIRouter, status
from app.core.database import get_db
from app.schemas.models import VisitorPassCreate

router = APIRouter(prefix="/api/visitors", tags=["06. Visitors & Gate Security API (تصاريح الزوار والدليفري)"])


@router.get("")
def list_visitor_passes(building_id: int = 1):
    """[API #6] عرض قائمة الزوار ومندوبي الدليفري المتوقع وصولهم للبوابة."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT v.*, u.full_name AS resident_name, u.apartment_number
            FROM visitors_passes v
            JOIN users u ON u.id = v.resident_id
            WHERE v.building_id = ?
            ORDER BY v.created_at DESC;
            """,
            (building_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_visitor_pass(payload: VisitorPassCreate):
    """إصدار تصريح دخول مؤقت (QR / Pass Code) لزائر أو دليفري وإبلاغ البواب."""
    pass_code = f"PASS-{random.randint(100, 999)}"
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO visitors_passes (building_id, resident_id, visitor_name, visitor_type, pass_code, expected_time, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (payload.building_id, payload.resident_id, payload.visitor_name, payload.visitor_type, pass_code, payload.expected_time, payload.notes),
        )
        row = conn.execute("SELECT * FROM visitors_passes WHERE id = ?;", (cur.lastrowid,)).fetchone()
        return dict(row)
