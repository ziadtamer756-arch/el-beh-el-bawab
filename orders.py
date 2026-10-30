from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.core.database import get_db
from app.schemas.models import OrderCreate, OrderStatusUpdate

router = APIRouter(prefix="/api/orders", tags=["04. Orders & Errands API (الطلبات والمشاوير)"])

CATEGORY_LABELS_AR = {
    "groceries": "طلبات سوبرماركت وخضار",
    "pharmacy": "صيدلية وأدوية",
    "errand": "مشوار خاص / استلام طرد",
    "cleaning": "تنظيف ومسح سلم/شقة",
    "car_wash": "غسيل سيارات",
    "plumbing_electrical": "صيانة (سباكة / كهرباء / غاز)",
    "luggage_help": "حمل شنط وأغراض ثقيلة",
    "other": "أخرى",
}


@router.get("/categories")
def get_service_categories():
    """إرجاع فئات الطلبات والخدمات المتاحة."""
    return [{"key": k, "label_ar": v} for k, v in CATEGORY_LABELS_AR.items()]


@router.get("")
def list_orders(
    building_id: Optional[int] = Query(default=None),
    resident_id: Optional[int] = Query(default=None),
    bawab_id: Optional[int] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
):
    """[API #4] جلب الطلبات مرتبة حسب الأولوية (المستعجل أولاً)."""
    query = """
        SELECT o.*,
               r.full_name AS resident_name,
               r.apartment_number AS resident_apartment,
               r.floor_number AS resident_floor,
               r.phone AS resident_phone,
               b.full_name AS bawab_name
        FROM orders o
        JOIN users r ON r.id = o.resident_id
        LEFT JOIN users b ON b.id = o.bawab_id
        WHERE 1=1
    """
    params = []
    if building_id is not None:
        query += " AND o.building_id = ?"
        params.append(building_id)
    if resident_id is not None:
        query += " AND o.resident_id = ?"
        params.append(resident_id)
    if bawab_id is not None:
        query += " AND o.bawab_id = ?"
        params.append(bawab_id)
    if status_filter is not None:
        query += " AND o.status = ?"
        params.append(status_filter)

    query += " ORDER BY CASE o.urgency WHEN 'urgent' THEN 1 WHEN 'scheduled' THEN 2 ELSE 3 END, o.created_at DESC;"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        results = []
        for r in rows:
            item = dict(r)
            item["category_label_ar"] = CATEGORY_LABELS_AR.get(item["category"], item["category"])
            base_cost = item["actual_items_cost"] if (item["actual_items_cost"] or 0) > 0 else (item["estimated_items_cost"] or 0.0)
            item["total_due"] = round(base_cost + (item["service_tip"] or 0.0), 2)
            results.append(item)
        return results


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate):
    """إرسال طلب جديد من الساكن إلى البواب مع إشعار فوري."""
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO orders (
                building_id, resident_id, category, title, details,
                urgency, scheduled_time, estimated_items_cost, service_tip, payment_method, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                payload.building_id,
                payload.resident_id,
                payload.category,
                payload.title,
                payload.details,
                payload.urgency,
                payload.scheduled_time,
                payload.estimated_items_cost,
                payload.service_tip,
                payload.payment_method,
                payload.notes,
            ),
        )
        order_id = cur.lastrowid
        row = conn.execute("SELECT * FROM orders WHERE id = ?;", (order_id,)).fetchone()
        return dict(row)


@router.patch("/{order_id}/status")
def update_order_status(order_id: int, payload: OrderStatusUpdate):
    """تحديث حالة الطلب وإضافة الإكرامية لمحفظة البواب عند التوصيل."""
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM orders WHERE id = ?;", (order_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="الطلب غير موجود")

        bawab_id = payload.bawab_id if payload.bawab_id is not None else (existing["bawab_id"] or 1)
        actual_cost = payload.actual_items_cost if payload.actual_items_cost is not None else existing["actual_items_cost"]
        is_paid = int(payload.is_paid) if payload.is_paid is not None else existing["is_paid"]
        notes = payload.notes if payload.notes is not None else existing["notes"]

        conn.execute(
            """
            UPDATE orders
            SET status = ?, bawab_id = ?, actual_items_cost = ?, is_paid = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (payload.status, bawab_id, actual_cost, is_paid, notes, order_id),
        )

        if payload.status == "delivered" and existing["status"] != "delivered":
            tip = existing["service_tip"] or 0.0
            if tip > 0 and bawab_id:
                conn.execute("UPDATE users SET wallet_balance = wallet_balance + ? WHERE id = ?;", (tip, bawab_id))
                conn.execute(
                    """
                    INSERT INTO wallet_transactions (building_id, user_id, order_id, tx_type, amount, payment_method, description)
                    VALUES (?, ?, ?, 'tip', ?, ?, ?);
                    """,
                    (existing["building_id"], bawab_id, order_id, tip, existing["payment_method"], f"إكرامية توصيل: {existing['title']}"),
                )

        updated = conn.execute("SELECT * FROM orders WHERE id = ?;", (order_id,)).fetchone()
        return dict(updated)


@router.get("/stats/{building_id}")
def get_building_order_stats(building_id: int):
    """إحصائيات الطلبات للعمارة."""
    with get_db() as conn:
        stats = conn.execute(
            """
            SELECT
                COUNT(*) AS total_orders,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_orders,
                SUM(CASE WHEN status IN ('accepted', 'in_progress') THEN 1 ELSE 0 END) AS active_orders,
                SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) AS completed_orders,
                COALESCE(SUM(CASE WHEN status = 'delivered' THEN service_tip ELSE 0 END), 0) AS total_bawab_tips
            FROM orders WHERE building_id = ?;
            """,
            (building_id,),
        ).fetchone()
        return dict(stats)
