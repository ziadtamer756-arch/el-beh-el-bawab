"""قلب المحفظة: تحريك الأرصدة وتسجيل الدفتر داخل transaction واحدة.

القواعد:
- الخصم من المحفظة يحصل قبل الإضافة، ولو الرصيد مش كفاية بيترفض كل شيء (rollback).
- كل حركة رصيد ليها سطر في wallet_ledger فيه الرصيد بعد الحركة.
- بنسجّل كمان في جدول wallet_transactions الموجود عشان الواجهة الحالية تفضل تشوف الحركات.
- الدفع بالمحفظة "وهمي" (محاكاة) - مفيش بوابة دفع حقيقية.
"""
import uuid
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException

from app.wallet_ext.money import D, q, f

MAX_SINGLE_AMOUNT = Decimal("100000")


def begin_write(conn) -> None:
    """قفل الكتابة من أول العملية عشان محدش يعدل الرصيد بين القراءة والكتابة."""
    conn.execute("BEGIN IMMEDIATE;")


def new_ref_group() -> str:
    return uuid.uuid4().hex[:12]


def _change_balance(conn, user_id: int, delta: Decimal) -> Decimal:
    row = conn.execute("SELECT wallet_balance FROM users WHERE id = ?;", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    new_balance = q(D(row["wallet_balance"]) + delta)
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="الرصيد غير كافٍ لإتمام العملية")
    conn.execute("UPDATE users SET wallet_balance = ? WHERE id = ?;", (float(new_balance), user_id))
    return new_balance


def _insert_tx(conn, building_id, user_id, order_id, tx_type, amount: Decimal, method, description) -> int:
    cur = conn.execute(
        """
        INSERT INTO wallet_transactions (building_id, user_id, order_id, tx_type, amount, payment_method, description)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (building_id, user_id, order_id, tx_type, float(amount), method, description),
    )
    return cur.lastrowid


def _insert_entry(conn, building_id, user_id, tx_id, plan_id, direction, amount: Decimal,
                  balance_after: Decimal, entry_type, ref_group) -> None:
    conn.execute(
        """
        INSERT INTO wallet_ledger (building_id, user_id, tx_id, plan_id, direction, amount,
                                   balance_after, entry_type, ref_group)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (building_id, user_id, tx_id, plan_id, direction, float(amount), float(balance_after), entry_type, ref_group),
    )


def move(
    conn,
    *,
    building_id: int,
    tx_type: str,
    amount: Decimal,
    method: str,
    description: str,
    payer_id: Optional[int] = None,
    recipient_id: Optional[int] = None,
    order_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    ref_group: Optional[str] = None,
) -> dict:
    """تنفيذ حركة مالية.

    - payer_id فقط + method=wallet        -> خصم من المحفظة (مثال: رسوم الصيانة).
    - payer_id + recipient_id             -> دفع من ساكن للبواب (الخصم من محفظة الساكن لو method=wallet).
    - recipient_id فقط                    -> إضافة رصيد (شحن المحفظة).
    """
    amount = q(amount)
    if amount <= 0 or amount > MAX_SINGLE_AMOUNT:
        raise HTTPException(status_code=400, detail="المبلغ غير صالح")
    ref_group = ref_group or new_ref_group()
    result = {"ref_group": ref_group, "tx_ids": [], "payer_balance": None, "recipient_balance": None}

    # 1) الخصم أولاً
    if payer_id is not None:
        debit = method == "wallet"
        if debit:
            result["payer_balance"] = _change_balance(conn, payer_id, -amount)
        # صف المعاملة للدافع: لو الخصم من المحفظة، أو لو مفيش مستلم (رسوم صيانة)
        if debit or recipient_id is None:
            suffix = " (خصم من المحفظة)" if debit else ""
            tx = _insert_tx(conn, building_id, payer_id, order_id, tx_type, amount, method, description + suffix)
            result["tx_ids"].append(tx)
            if debit:
                _insert_entry(conn, building_id, payer_id, tx, plan_id, "debit", amount,
                              result["payer_balance"], tx_type, ref_group)

    # 2) ثم الإضافة
    if recipient_id is not None:
        result["recipient_balance"] = _change_balance(conn, recipient_id, amount)
        tx = _insert_tx(conn, building_id, recipient_id, order_id, tx_type, amount, method, description)
        result["tx_ids"].append(tx)
        _insert_entry(conn, building_id, recipient_id, tx, plan_id, "credit", amount,
                      result["recipient_balance"], tx_type, ref_group)

    return {
        "ref_group": ref_group,
        "tx_ids": result["tx_ids"],
        "payer_balance": f(result["payer_balance"]) if result["payer_balance"] is not None else None,
        "recipient_balance": f(result["recipient_balance"]) if result["recipient_balance"] is not None else None,
    }


def find_bawab(conn, building_id: int, bawab_id: Optional[int] = None) -> dict:
    """إيجاد البواب المستلم: المحدد، أو أول بواب في العمارة."""
    if bawab_id is not None:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ? AND role = 'bawab' AND building_id = ?;", (bawab_id, building_id)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM users WHERE role = 'bawab' AND building_id = ? ORDER BY id LIMIT 1;", (building_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="لا يوجد بواب مسجل في هذه العمارة")
    return dict(row)
