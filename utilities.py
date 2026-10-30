from fastapi import APIRouter, status
from app.core.database import get_db
from app.schemas.models import UtilityBillCreate

router = APIRouter(prefix="/api/utilities", tags=["09. Shared Utilities & Meters API (فواتير المرافق المشتركة)"])


@router.get("")
def list_utility_bills(building_id: int = 1):
    """[API #9] عرض فواتير المياه المشتركة، كهرباء الأسانسير، والنظافة ونصيب كل شقة."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM utility_bills WHERE building_id = ? ORDER BY created_at DESC;",
            (building_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_utility_bill(payload: UtilityBillCreate):
    """إضافة فاتورة مرافق مشتركة وتقسيمها آلياً على شقق العمارة."""
    share = round(payload.total_amount / max(payload.apartments_count, 1), 2)
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO utility_bills (building_id, utility_type, month_label, total_amount, per_apartment_share, paid_apartments_count)
            VALUES (?, ?, ?, ?, ?, 0);
            """,
            (payload.building_id, payload.utility_type, payload.month_label, payload.total_amount, share),
        )
        row = conn.execute("SELECT * FROM utility_bills WHERE id = ?;", (cur.lastrowid,)).fetchone()
        return dict(row)
