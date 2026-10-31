from typing import Optional
from fastapi import APIRouter, Query, status
from app.core.database import get_db
from app.schemas.models import WalletTransactionCreate

router = APIRouter(prefix="/api/wallet", tags=["10. Wallet & Custody Ledger API (محفظة الإكراميات وحساب العهدة)"])


@router.get("/transactions")
def list_wallet_transactions(building_id: int = Query(default=1), user_id: Optional[int] = Query(default=None)):
    """[API #10] عرض دفتر المعاملات المالية (إكراميات، سداد فواتير مشتريات، صيانة العمارة)."""
    query = """
        SELECT wt.*, u.full_name AS user_name, u.apartment_number, u.role
        FROM wallet_transactions wt
        JOIN users u ON u.id = wt.user_id
        WHERE wt.building_id = ?
    """
    params = [building_id]
    if user_id is not None:
        query += " AND wt.user_id = ?"
        params.append(user_id)
    query += " ORDER BY wt.created_at DESC;"
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


@router.post("/transactions", status_code=status.HTTP_201_CREATED)
def record_wallet_transaction(payload: WalletTransactionCreate):
    """تسجيل معاملة مالية جديدة."""
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO wallet_transactions (building_id, user_id, order_id, tx_type, amount, payment_method, description)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (payload.building_id, payload.user_id, payload.order_id, payload.tx_type, payload.amount, payload.payment_method, payload.description),
        )
        if payload.tx_type in ("tip", "topup", "reimbursement"):
            conn.execute("UPDATE users SET wallet_balance = wallet_balance + ? WHERE id = ?;", (payload.amount, payload.user_id))
        row = conn.execute("SELECT * FROM wallet_transactions WHERE id = ?;", (cur.lastrowid,)).fetchone()
        return dict(row)


@router.get("/summary/{building_id}")
def get_financial_summary(building_id: int):
    """ملخص الأرصدة المالية للعمارة والبواب."""
    with get_db() as conn:
        unpaid = conn.execute(
            """
            SELECT COALESCE(SUM((CASE WHEN actual_items_cost > 0 THEN actual_items_cost ELSE estimated_items_cost END) + service_tip), 0) AS unpaid_balance
            FROM orders WHERE building_id = ? AND status != 'cancelled' AND is_paid = 0;
            """,
            (building_id,),
        ).fetchone()["unpaid_balance"]

        bawab = conn.execute(
            "SELECT full_name, wallet_balance, rating_avg, rating_count FROM users WHERE building_id = ? AND role = 'bawab' LIMIT 1;",
            (building_id,),
        ).fetchone()

        maintenance_collected = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM wallet_transactions WHERE building_id = ? AND tx_type = 'maintenance_fee';",
            (building_id,),
        ).fetchone()["total"]

        return {
            "unpaid_orders_balance": round(unpaid, 2),
            "bawab_wallet_balance": round(bawab["wallet_balance"], 2) if bawab else 0.0,
            "bawab_rating_avg": bawab["rating_avg"] if bawab else 5.0,
            "bawab_rating_count": bawab["rating_count"] if bawab else 0,
            "maintenance_fund_collected": round(maintenance_collected, 2),
        }
