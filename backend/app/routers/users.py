from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.core.database import get_db
from app.schemas.models import UserCreate

router = APIRouter(prefix="/api/users", tags=["03. Users & Availability API (السكان والبوابين)"])


@router.get("")
def list_users(
    building_id: Optional[int] = Query(default=None),
    role: Optional[str] = Query(default=None),
):
    """[API #3] عرض قائمة السكان والبوابين في العمارة."""
    query = "SELECT * FROM users WHERE 1=1"
    params = []
    if building_id is not None:
        query += " AND building_id = ?"
        params.append(building_id)
    if role is not None:
        query += " AND role = ?"
        params.append(role)
    query += " ORDER BY id ASC;"
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate):
    """إضافة ساكن جديد أو بواب."""
    with get_db() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO users (full_name, phone, role, building_id, apartment_number, floor_number)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (payload.full_name, payload.phone, payload.role, payload.building_id, payload.apartment_number, payload.floor_number),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?;", (cur.lastrowid,)).fetchone()
            return dict(row)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"تعذر تسجيل المستخدم: {exc}")


@router.patch("/{user_id}/availability")
def toggle_bawab_availability(user_id: int, is_available: bool = Query(...)):
    """تحديث حالة تواجد البواب (متاح الآن بالعمارة / في مشوار خارجي)."""
    with get_db() as conn:
        conn.execute("UPDATE users SET is_available = ? WHERE id = ?;", (int(is_available), user_id))
        row = conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
        return dict(row)
