"""راوتر تقسيط العهدة «حالاً عالنوتة»  (المسار: /api/v2/installments).

الفكرة: البواب بيشتري للساكن من جيبه (العهدة)، والساكن بيسدد على أقساط.
- البواب/الأدمن بس هم اللي يفتحوا الخطة (هم الدائنين).
- الساكن يشوف خططه ويسدد بالمحفظة (خصم حقيقي من رصيده).
- كاش/إنستاباي بيسجلها البواب/الأدمن بعد استلام الفلوس.
- الدفع بالمحفظة وهمي (محاكاة) - مفيش بوابة دفع حقيقية.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_db
from app.wallet_ext import ledger
from app.wallet_ext.deps import (
    assert_can_access_user, assert_same_building, ensure_ready, get_current_user,
    is_staff, load_user, require_roles,
)
from app.wallet_ext.installment_logic import build_schedule, default_first_due, today
from app.wallet_ext.models import PayRequest, PlanCreate
from app.wallet_ext.money import D, f, q

router = APIRouter(
    prefix="/api/v2/installments",
    tags=["10c. Installments - تقسيط العهدة (حالاً عالنوتة)"],
    dependencies=[Depends(ensure_ready)],
)


# ---------------------------------------------------------------- helpers
def _order_total_due(order) -> Decimal:
    base = D(order["actual_items_cost"]) if D(order["actual_items_cost"]) > 0 else D(order["estimated_items_cost"])
    return q(base + D(order["service_tip"]))


def _plan_view(conn, plan) -> dict:
    rows = conn.execute(
        "SELECT id, seq, due_date, amount_due, amount_paid, status, paid_at FROM installments "
        "WHERE plan_id = ? ORDER BY seq;",
        (plan["id"],),
    ).fetchall()
    t = today().isoformat()
    items, paid, remaining, overdue = [], Decimal("0"), Decimal("0"), Decimal("0")
    for r in rows:
        due, got = q(r["amount_due"]), q(r["amount_paid"])
        left = due - got if r["status"] in ("pending", "partial") else Decimal("0")
        is_overdue = r["status"] in ("pending", "partial") and r["due_date"] < t and plan["status"] == "active"
        paid += got
        remaining += left
        if is_overdue:
            overdue += left
        items.append({
            "id": r["id"], "seq": r["seq"], "due_date": r["due_date"], "amount_due": f(due),
            "amount_paid": f(got), "remaining": f(left), "status": r["status"],
            "is_overdue": is_overdue, "paid_at": r["paid_at"],
        })
    return {
        "id": plan["id"], "building_id": plan["building_id"], "resident_id": plan["resident_id"],
        "bawab_id": plan["bawab_id"], "order_id": plan["order_id"],
        "total_amount": f(plan["total_amount"]), "down_payment": f(plan["down_payment"]),
        "financed_amount": f(plan["financed_amount"]), "installments_count": plan["installments_count"],
        "frequency": plan["frequency"], "start_date": plan["start_date"], "status": plan["status"],
        "notes": plan["notes"], "created_at": plan["created_at"],
        "paid_so_far": f(paid), "remaining": f(remaining), "overdue_amount": f(overdue),
        "installments": items,
    }


def _get_plan_for(conn, plan_id: int, caller: dict):
    plan = conn.execute("SELECT * FROM installment_plans WHERE id = ?;", (plan_id,)).fetchone()
    if not plan:
        raise HTTPException(status_code=404, detail="خطة التقسيط غير موجودة")
    if plan["building_id"] != caller["building_id"]:
        raise HTTPException(status_code=403, detail="هذه الخطة تخص عمارة أخرى")
    if not is_staff(caller) and plan["resident_id"] != caller["id"]:
        raise HTTPException(status_code=403, detail="لا يمكنك الاطلاع على خطة ساكن آخر")
    return plan


# ---------------------------------------------------------------- endpoints
@router.post("/plans", status_code=status.HTTP_201_CREATED)
def create_plan(payload: PlanCreate, user: dict = Depends(require_roles("bawab", "admin"))):
    """فتح خطة تقسيط لساكن (بواب/أدمن). لو في مقدم، بيتحصل فورًا."""
    total, down = q(payload.total_amount), q(payload.down_payment)
    financed = total - down
    if financed <= 0:
        raise HTTPException(status_code=400, detail="المقدم لازم يكون أقل من الإجمالي (لو هتدفع كله ادفع مباشرة)")
    if int(financed * 100) < payload.installments_count:
        raise HTTPException(status_code=400, detail="المبلغ المقسَّط صغير جدًا على عدد الأقساط ده")

    with get_db() as conn:
        ledger.begin_write(conn)
        resident = load_user(conn, payload.resident_id)
        assert_same_building(user, resident)
        if resident["role"] != "resident":
            raise HTTPException(status_code=400, detail="التقسيط للسكان فقط")

        order, bawab_id = None, None
        if payload.order_id is not None:
            order = conn.execute("SELECT * FROM orders WHERE id = ?;", (payload.order_id,)).fetchone()
            if not order or order["building_id"] != resident["building_id"] or order["resident_id"] != resident["id"]:
                raise HTTPException(status_code=404, detail="الطلب غير موجود أو لا يخص هذا الساكن")
            if order["status"] == "cancelled":
                raise HTTPException(status_code=400, detail="الطلب ملغي")
            if order["is_paid"]:
                raise HTTPException(status_code=400, detail="الطلب مدفوع بالفعل")
            if total > _order_total_due(order):
                raise HTTPException(
                    status_code=400,
                    detail=f"إجمالي التقسيط أكبر من المستحق على الطلب ({f(_order_total_due(order))} جنيه)",
                )
            exists = conn.execute(
                "SELECT id FROM installment_plans WHERE order_id = ? AND status = 'active';", (order["id"],)
            ).fetchone()
            if exists:
                raise HTTPException(status_code=409, detail=f"الطلب عليه خطة تقسيط نشطة بالفعل (#{exists['id']})")
            bawab_id = order["bawab_id"]

        if bawab_id is None:
            bawab_id = user["id"] if user["role"] == "bawab" else None
        bawab = ledger.find_bawab(conn, resident["building_id"], bawab_id)

        first_due = payload.start_date or default_first_due(payload.frequency, today())
        if first_due < today():
            raise HTTPException(status_code=400, detail="تاريخ أول قسط لا يمكن أن يكون في الماضي")
        schedule = build_schedule(financed, payload.installments_count, payload.frequency, first_due)

        cur = conn.execute(
            """
            INSERT INTO installment_plans (building_id, resident_id, bawab_id, order_id, total_amount, down_payment,
                financed_amount, installments_count, frequency, start_date, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (resident["building_id"], resident["id"], bawab["id"], payload.order_id, float(total), float(down),
             float(financed), payload.installments_count, payload.frequency, first_due.isoformat(),
             payload.notes, user["id"]),
        )
        plan_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO installments (plan_id, seq, due_date, amount_due) VALUES (?, ?, ?, ?);",
            [(plan_id, seq, due.isoformat(), float(amt)) for seq, due, amt in schedule],
        )

        down_tx = None
        if down > 0:
            down_tx = ledger.move(
                conn, building_id=resident["building_id"], tx_type="settlement", amount=down,
                method=payload.down_payment_method, payer_id=resident["id"], recipient_id=bawab["id"],
                order_id=payload.order_id, plan_id=plan_id,
                description=f"دفعة مقدمة لخطة تقسيط #{plan_id}",
            )

        plan = conn.execute("SELECT * FROM installment_plans WHERE id = ?;", (plan_id,)).fetchone()
        view = _plan_view(conn, plan)
    return {"plan": view, "down_payment_tx": down_tx}


@router.get("/plans")
def list_plans(
    resident_id: Optional[int] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status", pattern="^(active|completed|cancelled)$"),
    user: dict = Depends(get_current_user),
):
    """الساكن يشوف خططه فقط، والبواب/الأدمن يشوفوا كل خطط العمارة."""
    query = "SELECT * FROM installment_plans WHERE building_id = ?"
    params = [user["building_id"]]
    if not is_staff(user):
        query += " AND resident_id = ?"
        params.append(user["id"])
    elif resident_id is not None:
        query += " AND resident_id = ?"
        params.append(resident_id)
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    query += " ORDER BY id DESC;"
    with get_db() as conn:
        plans = conn.execute(query, params).fetchall()
        return [_plan_view(conn, p) for p in plans]


@router.get("/overdue")
def overdue_installments(user: dict = Depends(require_roles("bawab", "admin"))):
    """الأقساط المتأخرة في العمارة (بواب/أدمن)."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT i.id AS installment_id, i.plan_id, i.seq, i.due_date, i.amount_due, i.amount_paid,
                   u.id AS resident_id, u.full_name, u.apartment_number, u.phone
            FROM installments i
            JOIN installment_plans p ON p.id = i.plan_id
            JOIN users u ON u.id = p.resident_id
            WHERE p.building_id = ? AND p.status = 'active' AND i.status IN ('pending', 'partial') AND i.due_date < ?
            ORDER BY i.due_date, i.id;
            """,
            (user["building_id"], today().isoformat()),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["remaining"] = f(D(d["amount_due"]) - D(d["amount_paid"]))
        d["days_late"] = (today() - datetime.strptime(d["due_date"], "%Y-%m-%d").date()).days
        out.append(d)
    return {"count": len(out), "total_overdue": f(sum((D(x["remaining"]) for x in out), Decimal("0"))), "items": out}


@router.get("/ledger/{resident_id}")
def resident_notebook(resident_id: int, user: dict = Depends(get_current_user)):
    """«النوتة»: كل اللي على الساكن، المسدد والمتبقي والمتأخر وأقرب قسط."""
    with get_db() as conn:
        resident = load_user(conn, resident_id)
        assert_can_access_user(user, resident)
        plans = conn.execute(
            "SELECT * FROM installment_plans WHERE resident_id = ? ORDER BY id DESC;", (resident_id,)
        ).fetchall()
        views = [_plan_view(conn, p) for p in plans]
    active = [v for v in views if v["status"] == "active"]
    upcoming = sorted(
        (i for v in active for i in v["installments"] if i["status"] in ("pending", "partial")),
        key=lambda i: (i["due_date"], i["id"]),
    )
    return {
        "resident_id": resident_id,
        "resident_name": resident["full_name"],
        "apartment_number": resident["apartment_number"],
        "active_plans": len(active),
        "total_financed": f(sum((D(v["financed_amount"]) for v in active), Decimal("0"))),
        "total_paid": f(sum((D(v["paid_so_far"]) for v in active), Decimal("0"))),
        "total_remaining": f(sum((D(v["remaining"]) for v in active), Decimal("0"))),
        "total_overdue": f(sum((D(v["overdue_amount"]) for v in active), Decimal("0"))),
        "next_installment": upcoming[0] if upcoming else None,
        "plans": [{k: v[k] for k in ("id", "status", "total_amount", "financed_amount", "paid_so_far", "remaining",
                                      "overdue_amount", "installments_count", "frequency", "order_id")} for v in views],
    }


@router.get("/plans/{plan_id}")
def get_plan(plan_id: int, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        plan = _get_plan_for(conn, plan_id, user)
        return _plan_view(conn, plan)


@router.post("/plans/{plan_id}/pay")
def pay_plan(plan_id: int, payload: PayRequest, user: dict = Depends(get_current_user)):
    """سداد جزء أو كل الأقساط. من غير installment_id بيتوزع من الأقدم للأحدث."""
    amount = q(payload.amount)
    if not is_staff(user) and payload.payment_method != "wallet":
        raise HTTPException(status_code=403, detail="الساكن يسدد بالمحفظة فقط، والكاش/إنستاباي يسجلها البواب")

    with get_db() as conn:
        ledger.begin_write(conn)
        plan = _get_plan_for(conn, plan_id, user)
        if plan["status"] != "active":
            raise HTTPException(status_code=400, detail="الخطة غير نشطة (مكتملة أو ملغاة)")

        if payload.installment_id is not None:
            targets = conn.execute(
                "SELECT * FROM installments WHERE id = ? AND plan_id = ? AND status IN ('pending', 'partial');",
                (payload.installment_id, plan_id),
            ).fetchall()
            if not targets:
                raise HTTPException(status_code=404, detail="القسط غير موجود أو تم سداده")
        else:
            targets = conn.execute(
                "SELECT * FROM installments WHERE plan_id = ? AND status IN ('pending', 'partial') ORDER BY seq;",
                (plan_id,),
            ).fetchall()

        total_left = sum((q(t["amount_due"]) - q(t["amount_paid"]) for t in targets), Decimal("0"))
        if amount > total_left:
            raise HTTPException(status_code=400, detail=f"المبلغ أكبر من المتبقي ({f(total_left)} جنيه)")

        # توزيع المبلغ
        allocations, left = [], amount
        for t in targets:
            if left <= 0:
                break
            room = q(t["amount_due"]) - q(t["amount_paid"])
            take = min(room, left)
            allocations.append((t, take))
            left -= take

        label = ", ".join(f"#{t['seq']}" for t, _ in allocations)
        tx = ledger.move(
            conn, building_id=plan["building_id"], tx_type="settlement", amount=amount,
            method=payload.payment_method, payer_id=plan["resident_id"], recipient_id=plan["bawab_id"],
            order_id=plan["order_id"], plan_id=plan_id,
            description=f"سداد قسط/أقساط ({label}) - خطة تقسيط #{plan_id}",
        )

        now = datetime.now().isoformat(timespec="seconds")
        for t, take in allocations:
            new_paid = q(t["amount_paid"]) + take
            fully = new_paid >= q(t["amount_due"])
            conn.execute(
                "UPDATE installments SET amount_paid = ?, status = ?, paid_at = ? WHERE id = ?;",
                (float(new_paid), "paid" if fully else "partial", now if fully else t["paid_at"], t["id"]),
            )

        open_left = conn.execute(
            "SELECT COUNT(*) AS c FROM installments WHERE plan_id = ? AND status IN ('pending', 'partial');",
            (plan_id,),
        ).fetchone()["c"]
        completed = open_left == 0
        if completed:
            conn.execute(
                "UPDATE installment_plans SET status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (plan_id,),
            )
            if plan["order_id"]:
                order = conn.execute("SELECT * FROM orders WHERE id = ?;", (plan["order_id"],)).fetchone()
                # الطلب يتقفل كمدفوع لو الخطة غطّت كامل المستحق عليه
                if order and q(plan["total_amount"]) >= _order_total_due(order):
                    conn.execute(
                        "UPDATE orders SET is_paid = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                        (order["id"],),
                    )
        plan = conn.execute("SELECT * FROM installment_plans WHERE id = ?;", (plan_id,)).fetchone()
        view = _plan_view(conn, plan)
    return {
        "message": "تم تسجيل السداد" + (" - الخطة اكتملت 🎉" if completed else ""),
        "paid_amount": f(amount),
        "allocations": [{"installment_id": t["id"], "seq": t["seq"], "amount": f(take)} for t, take in allocations],
        "transaction": tx,
        "plan": view,
    }


@router.post("/plans/{plan_id}/cancel")
def cancel_plan(plan_id: int, user: dict = Depends(require_roles("bawab", "admin"))):
    """إلغاء خطة نشطة (بواب/أدمن). الأقساط المسددة تفضل مسددة، والباقي بيتلغي."""
    with get_db() as conn:
        ledger.begin_write(conn)
        plan = _get_plan_for(conn, plan_id, user)
        if plan["status"] != "active":
            raise HTTPException(status_code=400, detail="الخطة غير نشطة")
        conn.execute(
            "UPDATE installments SET status = 'cancelled' WHERE plan_id = ? AND status IN ('pending', 'partial');",
            (plan_id,),
        )
        conn.execute(
            "UPDATE installment_plans SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
            (plan_id,),
        )
        plan = conn.execute("SELECT * FROM installment_plans WHERE id = ?;", (plan_id,)).fetchone()
        return {"message": "تم إلغاء الخطة", "plan": _plan_view(conn, plan)}
