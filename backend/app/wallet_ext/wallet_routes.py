"""راوتر المحفظة الآمنة v2  (المسار: /api/v2/wallet).

الفرق عن /api/wallet القديم:
- كل المسارات محمية بالتوكن والصلاحيات.
- الدفع بالمحفظة بيخصم من الدافع فعليًا ويرفض لو الرصيد مش كفاية.
- كل حركة ليها سطر في دفتر wallet_ledger (الرصيد بعد الحركة).
- تقدر تتأكد إن الرصيد مطابق للدفتر من /reconcile.
- الدفع "وهمي": مفيش بوابة دفع حقيقية.
"""
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_db
from app.wallet_ext import ledger
from app.wallet_ext.deps import (
    assert_can_access_user, assert_same_building, ensure_ready, get_current_user,
    is_staff, load_user, require_roles,
)
from app.wallet_ext.installment_logic import today
from app.wallet_ext.models import TopupRequest, TransactionRequest
from app.wallet_ext.money import D, f, q

router = APIRouter(
    prefix="/api/v2/wallet",
    tags=["10b. Wallet v2 - محفظة آمنة بدفتر حسابات"],
    dependencies=[Depends(ensure_ready)],
)

MAX_TOPUP = 50000


def _simulated_topup_enabled() -> bool:
    """الشحن الذاتي للساكن (محاكاة). اقفله بـ WALLET_SIMULATED_TOPUP=0 ليبقى الشحن عن طريق البواب بس."""
    return os.getenv("WALLET_SIMULATED_TOPUP", "1") == "1"


@router.get("/balance")
def my_balance(user: dict = Depends(get_current_user)):
    return {"user_id": user["id"], "full_name": user["full_name"], "wallet_balance": f(user["wallet_balance"])}


@router.get("/balance/{user_id}")
def user_balance(user_id: int, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        target = load_user(conn, user_id)
    assert_can_access_user(user, target)
    return {"user_id": target["id"], "full_name": target["full_name"], "wallet_balance": f(target["wallet_balance"])}


@router.post("/topup", status_code=status.HTTP_201_CREATED)
def topup(payload: TopupRequest, user: dict = Depends(get_current_user)):
    """شحن المحفظة (محاكاة). الساكن يشحن لنفسه، والبواب/الأدمن يشحنوا لساكن بعد استلام فلوسه."""
    if payload.amount > MAX_TOPUP:
        raise HTTPException(status_code=400, detail=f"أقصى مبلغ للشحن في العملية الواحدة {MAX_TOPUP} جنيه")
    with get_db() as conn:
        ledger.begin_write(conn)
        target_id = payload.user_id or user["id"]
        target = load_user(conn, target_id)
        assert_same_building(user, target)
        if target_id != user["id"] and not is_staff(user):
            raise HTTPException(status_code=403, detail="لا يمكنك شحن محفظة مستخدم آخر")
        if not is_staff(user) and not _simulated_topup_enabled():
            raise HTTPException(status_code=403, detail="الشحن الذاتي مقفول، اطلب من البواب شحن محفظتك")
        res = ledger.move(
            conn, building_id=target["building_id"], tx_type="topup", amount=payload.amount,
            method=payload.payment_method, recipient_id=target_id,
            description="شحن رصيد المحفظة (محاكاة)",
        )
        return {"message": "تم شحن المحفظة", "new_balance": res["recipient_balance"], **res}


@router.post("/transactions", status_code=status.HTTP_201_CREATED)
def record_transaction(payload: TransactionRequest, user: dict = Depends(get_current_user)):
    """تسجيل معاملة مالية بقواعد صارمة.

    | النوع            | مين يسجل                      | الدافع | المستلم        |
    | tip              | الساكن                         | الساكن | البواب         |
    | reimbursement    | الساكن أو البواب/الأدمن        | الساكن | البواب         |
    | settlement       | البواب/الأدمن فقط               | الساكن | البواب         |
    | maintenance_fee  | الساكن أو البواب/الأدمن        | الساكن | صندوق العمارة  |
    | topup            | (استخدم /topup)                | -      | -              |

    الساكن يقدر يدفع بالمحفظة فقط (خصم حقيقي)، أما كاش/إنستاباي فالبواب/الأدمن هم اللي يؤكدوا الاستلام.
    """
    t = payload.tx_type
    if t == "topup":
        raise HTTPException(status_code=400, detail="استخدم /api/v2/wallet/topup للشحن")
    if t == "settlement" and not is_staff(user):
        raise HTTPException(status_code=403, detail="التسوية للبواب أو الأدمن فقط")
    if t == "tip" and user["role"] != "resident":
        raise HTTPException(status_code=403, detail="الإكرامية يدفعها الساكن فقط")
    if not is_staff(user) and payload.payment_method != "wallet":
        raise HTTPException(status_code=403, detail="الساكن يدفع بالمحفظة فقط، والكاش/إنستاباي يسجلها البواب")

    with get_db() as conn:
        ledger.begin_write(conn)
        # تحديد الدافع
        if is_staff(user):
            if payload.resident_id is None:
                raise HTTPException(status_code=400, detail="حدد resident_id (الساكن صاحب العملية)")
            payer = load_user(conn, payload.resident_id)
            if payer["role"] != "resident":
                raise HTTPException(status_code=400, detail="الدافع لازم يكون ساكن")
        else:
            if payload.resident_id not in (None, user["id"]):
                raise HTTPException(status_code=403, detail="لا يمكنك تسجيل معاملة باسم ساكن آخر")
            payer = user
        if user["role"] == "resident" and payer["role"] != "resident":
            raise HTTPException(status_code=403, detail="هذه العملية للسكان فقط")
        assert_same_building(user, payer)

        if payload.order_id is not None:
            order = conn.execute("SELECT * FROM orders WHERE id = ?;", (payload.order_id,)).fetchone()
            if not order or order["building_id"] != payer["building_id"]:
                raise HTTPException(status_code=404, detail="الطلب غير موجود في هذه العمارة")

        recipient_id = None
        if t != "maintenance_fee":
            bawab_pref = payload.bawab_id or (user["id"] if user["role"] == "bawab" else None)
            recipient_id = ledger.find_bawab(conn, payer["building_id"], bawab_pref)["id"]

        res = ledger.move(
            conn, building_id=payer["building_id"], tx_type=t, amount=payload.amount,
            method=payload.payment_method, description=payload.description,
            payer_id=payer["id"], recipient_id=recipient_id, order_id=payload.order_id,
        )
        return {"message": "تم تسجيل المعاملة", **res}


@router.get("/ledger")
def my_ledger(
    user_id: Optional[int] = Query(default=None, description="للبواب/الأدمن فقط"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
):
    """دفتر حركات الرصيد (دائن/مدين + الرصيد بعد كل حركة)."""
    with get_db() as conn:
        target = load_user(conn, user_id) if user_id is not None else user
        assert_can_access_user(user, target)
        rows = conn.execute(
            """
            SELECT id, tx_id, plan_id, direction, amount, balance_after, entry_type, ref_group, created_at
            FROM wallet_ledger WHERE user_id = ? ORDER BY id DESC LIMIT ? OFFSET ?;
            """,
            (target["id"], limit, offset),
        ).fetchall()
    return {"user_id": target["id"], "entries": [dict(r) for r in rows]}


@router.get("/reconcile/{user_id}")
def reconcile(user_id: int, user: dict = Depends(require_roles("admin"))):
    """مطابقة رصيد المستخدم مع الدفتر (أدمن فقط).

    drift != 0  يعني إن الرصيد اتغير من مكان خارج الدفتر (مثلاً من API القديم).
    chain_ok=false يعني إن في تغيير حصل بين حركتين مسجلتين.
    """
    with get_db() as conn:
        target = load_user(conn, user_id)
        assert_same_building(user, target)
        entries = conn.execute(
            "SELECT id, direction, amount, balance_after FROM wallet_ledger WHERE user_id = ? ORDER BY id;",
            (user_id,),
        ).fetchall()
    chain_ok, broken_at, prev = True, None, None
    for e in entries:
        signed = q(e["amount"]) if e["direction"] == "credit" else -q(e["amount"])
        if prev is not None and q(prev + signed) != q(e["balance_after"]):
            chain_ok, broken_at = False, e["id"]
            break
        prev = q(e["balance_after"])
    balance = q(target["wallet_balance"])
    return {
        "user_id": user_id,
        "wallet_balance": f(balance),
        "ledger_entries": len(entries),
        "last_ledger_balance": f(prev) if prev is not None else None,
        "drift": f(balance - prev) if prev is not None else None,
        "chain_ok": chain_ok,
        "broken_at_entry": broken_at,
    }


@router.get("/summary/{building_id}")
def financial_summary(building_id: int, user: dict = Depends(require_roles("bawab", "admin"))):
    """ملخص مالي للعمارة (بواب/أدمن)، يشمل الأقساط المستحقة والمتأخرة."""
    if user["building_id"] != building_id:
        raise HTTPException(status_code=403, detail="هذه العمارة ليست عمارتك")
    with get_db() as conn:
        unpaid = conn.execute(
            """
            SELECT COALESCE(SUM((CASE WHEN actual_items_cost > 0 THEN actual_items_cost ELSE estimated_items_cost END)
                                + service_tip), 0) AS v
            FROM orders WHERE building_id = ? AND status != 'cancelled' AND is_paid = 0;
            """,
            (building_id,),
        ).fetchone()["v"]
        bawab = conn.execute(
            "SELECT full_name, wallet_balance, rating_avg, rating_count FROM users "
            "WHERE building_id = ? AND role = 'bawab' ORDER BY id LIMIT 1;",
            (building_id,),
        ).fetchone()
        fund = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS v FROM wallet_transactions "
            "WHERE building_id = ? AND tx_type = 'maintenance_fee';",
            (building_id,),
        ).fetchone()["v"]
        outstanding = conn.execute(
            """
            SELECT COALESCE(SUM(i.amount_due - i.amount_paid), 0) AS v, COUNT(DISTINCT p.id) AS plans
            FROM installments i JOIN installment_plans p ON p.id = i.plan_id
            WHERE p.building_id = ? AND p.status = 'active' AND i.status IN ('pending', 'partial');
            """,
            (building_id,),
        ).fetchone()
        overdue = conn.execute(
            """
            SELECT COALESCE(SUM(i.amount_due - i.amount_paid), 0) AS v
            FROM installments i JOIN installment_plans p ON p.id = i.plan_id
            WHERE p.building_id = ? AND p.status = 'active' AND i.status IN ('pending', 'partial')
              AND i.due_date < ?;
            """,
            (building_id, today().isoformat()),
        ).fetchone()["v"]
    return {
        "unpaid_orders_balance": f(unpaid),
        "bawab_wallet_balance": f(bawab["wallet_balance"]) if bawab else 0.0,
        "bawab_rating_avg": bawab["rating_avg"] if bawab else 5.0,
        "bawab_rating_count": bawab["rating_count"] if bawab else 0,
        "maintenance_fund_collected": f(fund),
        "installments_outstanding": f(outstanding["v"]),
        "active_installment_plans": outstanding["plans"],
        "installments_overdue": f(overdue),
    }
