import random
from fastapi import APIRouter, status
from app.core.database import get_db
from app.schemas.models import ParcelCreate

router = APIRouter(prefix="/api/parcels", tags=["07. Parcels & Safe-Keeping API (استلام الطرود وأمانات البوابة)"])


@router.get("")
def list_parcels(building_id: int = 1):
    """[API #7] عرض الطرود والشحنات المستلمة لدى البواب في غرفة الحارس."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT p.*, u.full_name AS resident_name, u.apartment_number
            FROM parcels p
            JOIN users u ON u.id = p.resident_id
            WHERE p.building_id = ?
            ORDER BY p.received_at DESC;
            """,
            (building_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def register_parcel(payload: ParcelCreate):
    """تسجيل استلام طرد جديد بواسطة البواب وإضافة مبلغ الدفع عند الاستلام (COD) للعهدة."""
    pickup_code = f"BOX-{random.randint(10, 99)}"
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO parcels (building_id, resident_id, bawab_id, courier_name, tracking_Or_desc, cod_amount, paid_by_bawab, pickup_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                payload.building_id,
                payload.resident_id,
                payload.bawab_id,
                payload.courier_name,
                payload.tracking_Or_desc,
                payload.cod_amount,
                int(payload.paid_by_bawab),
                pickup_code,
            ),
        )
        if payload.paid_by_bawab and payload.cod_amount > 0:
            conn.execute(
                """
                INSERT INTO wallet_transactions (building_id, user_id, tx_type, amount, payment_method, description)
                VALUES (?, ?, 'reimbursement', ?, 'cash', ?);
                """,
                (payload.building_id, payload.bawab_id, payload.cod_amount, f"عهدة طرد ({payload.courier_name}): {payload.tracking_Or_desc}"),
            )
        row = conn.execute("SELECT * FROM parcels WHERE id = ?;", (cur.lastrowid,)).fetchone()
        return dict(row)
