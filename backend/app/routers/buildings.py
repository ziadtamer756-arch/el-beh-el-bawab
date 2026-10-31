from fastapi import APIRouter, HTTPException, status
from app.core.database import get_db
from app.schemas.models import BuildingCreate

router = APIRouter(prefix="/api/buildings", tags=["02. Buildings API (إدارة العمارات واتحاد الملاك)"])


@router.get("")
def list_buildings():
    """[API #2] عرض كل العمارات المسجلة وحالة المرافق (الأسانسير وموتور المياه)."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT b.*,
                   (SELECT COUNT(*) FROM users u WHERE u.building_id = b.id AND u.role = 'resident') AS residents_count,
                   (SELECT COUNT(*) FROM users u WHERE u.building_id = b.id AND u.role = 'bawab') AS bawabs_count,
                   (SELECT COUNT(*) FROM orders o WHERE o.building_id = b.id) AS total_orders
            FROM buildings b
            ORDER BY b.id DESC;
        """).fetchall()
        return [dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_building(payload: BuildingCreate):
    """إضافة عمارة جديدة بكود دعوة خاص للسكان."""
    with get_db() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO buildings (name, address, city, invite_code, floors_count, monthly_maintenance_fee)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (payload.name, payload.address, payload.city, payload.invite_code, payload.floors_count, payload.monthly_maintenance_fee),
            )
            row = conn.execute("SELECT * FROM buildings WHERE id = ?;", (cur.lastrowid,)).fetchone()
            return dict(row)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"تعذر إنشاء العمارة: {exc}")
