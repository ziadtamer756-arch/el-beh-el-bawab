from fastapi import APIRouter, status
from app.core.database import get_db
from app.schemas.models import VehicleCreate

router = APIRouter(prefix="/api/garage", tags=["08. Car Wash & Garage API (الجراج واشتراكات غسيل السيارات)"])


@router.get("")
def list_garage_vehicles(building_id: int = 1):
    """[API #8] عرض سيارات السكان، أرقام الباكيات، وجدول الغسيل الصباحي."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT v.*, u.full_name AS owner_name, u.apartment_number
            FROM vehicles v
            JOIN users u ON u.id = v.resident_id
            WHERE v.building_id = ?
            ORDER BY v.id ASC;
            """,
            (building_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def register_vehicle(payload: VehicleCreate):
    """إضافة سيارة جديدة في جدول الجراج والغسيل الدوري."""
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO vehicles (building_id, resident_id, car_model, plate_number, parking_spot, wash_schedule, key_with_bawab)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                payload.building_id,
                payload.resident_id,
                payload.car_model,
                payload.plate_number,
                payload.parking_spot,
                payload.wash_schedule,
                int(payload.key_with_bawab),
            ),
        )
        row = conn.execute("SELECT * FROM vehicles WHERE id = ?;", (cur.lastrowid,)).fetchone()
        return dict(row)
