"""اختبارات المحفظة الآمنة وتقسيط العهدة (wallet_ext).

التشغيل من داخل مجلد backend:
    python -m pytest tests/test_wallet_installments.py -v

كل اختبار يشتغل على قاعدة بيانات مؤقتة جديدة (فيها البيانات التجريبية الأصلية)،
فمفيش أي تأثير على ملف القاعدة الحقيقي.
"""
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import database
from app.core.security import create_access_token
from app.wallet_ext import installment_logic, installment_routes, wallet_routes
from app.wallet_ext.installment_logic import add_months, build_schedule
from app.wallet_ext.schema import ensure_schema
from app.wallet_ext.setup import install

# معرّفات البيانات التجريبية الأصلية (database._seed_initial_data)
BAWAB, AHMED, SOAD, TAREK = 1, 2, 3, 4
ORDER_AHMED = 1   # طلب أحمد: 225 + 25 إكرامية = 250 (غير مدفوع)
ORDER_SOAD = 2    # طلب سعاد: 150 + 35 إكرامية = 185 (غير مدفوع)
ORDER_TAREK = 4   # مدفوع بالفعل


# ------------------------------------------------------------------ fixtures
@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    database.init_db()
    ensure_schema()
    app = FastAPI()
    install(app)
    client = TestClient(app)

    class Env:
        pass

    e = Env()
    e.client = client
    e.db_path = str(tmp_path / "test.db")

    def sql(query, params=()):
        conn = sqlite3.connect(e.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(query, params)
            rows = cur.fetchall()
            conn.commit()
            return rows
        finally:
            conn.close()

    e.sql = sql
    e.balance = lambda uid: sql("SELECT wallet_balance FROM users WHERE id=?", (uid,))[0][0]
    e.count = lambda table: sql(f"SELECT COUNT(*) FROM {table}")[0][0]

    def headers(uid):
        return {"Authorization": "Bearer " + create_access_token({"sub": uid})}

    e.h = headers

    # أدمن للعمارة الأولى
    sql("INSERT INTO users (full_name, phone, role, building_id) VALUES ('مدير العمارة', '01099999999', 'admin', 1)")
    e.admin = sql("SELECT id FROM users WHERE phone='01099999999'")[0][0]
    # عمارة تانية فيها بواب وساكن
    sql("INSERT INTO buildings (name, address, invite_code) VALUES ('عمارة تانية', 'عنوان', 'OTHER-1')")
    b2 = sql("SELECT id FROM buildings WHERE invite_code='OTHER-1'")[0][0]
    sql("INSERT INTO users (full_name, phone, role, building_id, wallet_balance) VALUES ('بواب تاني','01111111111','bawab',?,0)", (b2,))
    sql("INSERT INTO users (full_name, phone, role, building_id, wallet_balance) VALUES ('ساكن تاني','01122222222','resident',?,1000)", (b2,))
    e.bawab2 = sql("SELECT id FROM users WHERE phone='01111111111'")[0][0]
    e.res2 = sql("SELECT id FROM users WHERE phone='01122222222'")[0][0]
    return e


def set_today(monkeypatch, d: date):
    for mod in (installment_logic, installment_routes, wallet_routes):
        monkeypatch.setattr(mod, "today", lambda d=d: d)


def make_plan(env, **overrides):
    body = dict(resident_id=AHMED, order_id=ORDER_AHMED, total_amount=250, down_payment=50,
                down_payment_method="cash", installments_count=2, frequency="weekly")
    body.update(overrides)
    return env.client.post("/api/v2/installments/plans", json=body, headers=env.h(BAWAB))


# ------------------------------------------------------------------ auth
@pytest.mark.parametrize("method,path", [
    ("get", "/api/v2/wallet/balance"),
    ("get", "/api/v2/wallet/ledger"),
    ("post", "/api/v2/wallet/topup"),
    ("post", "/api/v2/wallet/transactions"),
    ("get", "/api/v2/wallet/summary/1"),
    ("get", "/api/v2/installments/plans"),
    ("post", "/api/v2/installments/plans"),
    ("get", "/api/v2/installments/overdue"),
])
def test_all_endpoints_require_token(env, method, path):
    assert getattr(env.client, method)(path).status_code == 401
    bad = {"Authorization": "Bearer not.a.token"}
    assert getattr(env.client, method)(path, headers=bad).status_code == 401


def test_token_of_deleted_user_rejected(env):
    h = env.h(9999)
    assert env.client.get("/api/v2/wallet/balance", headers=h).status_code == 401


# ------------------------------------------------------------------ topup
def test_topup_self_updates_balance_ledger_and_legacy_table(env):
    before_tx = env.count("wallet_transactions")
    r = env.client.post("/api/v2/wallet/topup", json={"amount": 100.5}, headers=env.h(AHMED))
    assert r.status_code == 201
    assert r.json()["new_balance"] == 450.5
    assert env.balance(AHMED) == 450.5
    assert env.count("wallet_transactions") == before_tx + 1          # الواجهة القديمة تشوفها
    entry = env.sql("SELECT * FROM wallet_ledger WHERE user_id=?", (AHMED,))[0]
    assert entry["direction"] == "credit" and entry["balance_after"] == 450.5


def test_topup_decimal_precision_no_float_drift(env):
    for _ in range(3):
        assert env.client.post("/api/v2/wallet/topup", json={"amount": 0.1}, headers=env.h(AHMED)).status_code == 201
    assert env.balance(AHMED) == 350.3          # مش 350.30000000000001


@pytest.mark.parametrize("amount", [0, -5, 10.123, "abc"])
def test_topup_rejects_invalid_amounts(env, amount):
    r = env.client.post("/api/v2/wallet/topup", json={"amount": amount}, headers=env.h(AHMED))
    assert r.status_code == 422


def test_topup_over_max_rejected(env):
    r = env.client.post("/api/v2/wallet/topup", json={"amount": 50000.01}, headers=env.h(AHMED))
    assert r.status_code == 400


def test_resident_cannot_topup_someone_else(env):
    r = env.client.post("/api/v2/wallet/topup", json={"amount": 10, "user_id": SOAD}, headers=env.h(AHMED))
    assert r.status_code == 403
    assert env.balance(SOAD) == 180


def test_bawab_can_topup_resident_in_same_building_only(env):
    ok = env.client.post("/api/v2/wallet/topup", json={"amount": 20, "user_id": SOAD, "payment_method": "cash"},
                         headers=env.h(BAWAB))
    assert ok.status_code == 201 and env.balance(SOAD) == 200
    other = env.client.post("/api/v2/wallet/topup", json={"amount": 20, "user_id": env.res2}, headers=env.h(BAWAB))
    assert other.status_code == 403


def test_self_topup_can_be_disabled(env, monkeypatch):
    monkeypatch.setenv("WALLET_SIMULATED_TOPUP", "0")
    assert env.client.post("/api/v2/wallet/topup", json={"amount": 10}, headers=env.h(AHMED)).status_code == 403
    assert env.client.post("/api/v2/wallet/topup", json={"amount": 10, "user_id": AHMED},
                           headers=env.h(BAWAB)).status_code == 201


# ------------------------------------------------------------------ transactions
def test_tip_via_wallet_debits_resident_and_credits_bawab(env):
    r = env.client.post("/api/v2/wallet/transactions", headers=env.h(AHMED),
                        json={"tx_type": "tip", "amount": 30, "description": "إكرامية توصيل"})
    assert r.status_code == 201
    assert env.balance(AHMED) == 320 and env.balance(BAWAB) == 570
    entries = env.sql("SELECT direction FROM wallet_ledger ORDER BY id")
    assert [x[0] for x in entries] == ["debit", "credit"]


def test_insufficient_balance_is_atomic(env):
    tx_before, led_before = env.count("wallet_transactions"), env.count("wallet_ledger")
    r = env.client.post("/api/v2/wallet/transactions", headers=env.h(SOAD),
                        json={"tx_type": "tip", "amount": 500, "description": "أكتر من الرصيد"})
    assert r.status_code == 400
    assert env.balance(SOAD) == 180 and env.balance(BAWAB) == 540
    assert env.count("wallet_transactions") == tx_before and env.count("wallet_ledger") == led_before


def test_resident_cannot_self_report_cash_or_settlement_or_impersonate(env):
    base = {"amount": 20, "description": "محاولة غش"}
    cash = env.client.post("/api/v2/wallet/transactions", headers=env.h(AHMED),
                           json={**base, "tx_type": "tip", "payment_method": "cash"})
    settle = env.client.post("/api/v2/wallet/transactions", headers=env.h(AHMED),
                             json={**base, "tx_type": "settlement"})
    imp = env.client.post("/api/v2/wallet/transactions", headers=env.h(AHMED),
                          json={**base, "tx_type": "reimbursement", "resident_id": SOAD})
    assert cash.status_code == 403 and settle.status_code == 403 and imp.status_code == 403
    assert env.balance(BAWAB) == 540


def test_bawab_cannot_record_tip_for_himself(env):
    r = env.client.post("/api/v2/wallet/transactions", headers=env.h(BAWAB),
                        json={"tx_type": "tip", "amount": 100, "description": "إكرامية وهمية", "resident_id": AHMED,
                              "payment_method": "cash"})
    assert r.status_code == 403
    assert env.balance(BAWAB) == 540


def test_staff_must_name_resident(env):
    r = env.client.post("/api/v2/wallet/transactions", headers=env.h(BAWAB),
                        json={"tx_type": "reimbursement", "amount": 20, "description": "سداد عهدة", "payment_method": "cash"})
    assert r.status_code == 400


def test_bawab_records_cash_reimbursement_credit_only(env):
    r = env.client.post("/api/v2/wallet/transactions", headers=env.h(BAWAB),
                        json={"tx_type": "reimbursement", "amount": 140, "description": "سداد فاتورة صيدلية",
                              "payment_method": "cash", "resident_id": TAREK, "order_id": ORDER_TAREK})
    assert r.status_code == 201
    assert env.balance(TAREK) == 500 and env.balance(BAWAB) == 680      # الساكن ما اتخصمش (دفع كاش)


def test_maintenance_fee_wallet_and_cash(env):
    wal = env.client.post("/api/v2/wallet/transactions", headers=env.h(AHMED),
                          json={"tx_type": "maintenance_fee", "amount": 300, "description": "اشتراك الصيانة"})
    assert wal.status_code == 201 and env.balance(AHMED) == 50
    assert env.balance(BAWAB) == 540                                    # صندوق العمارة مش محفظة البواب
    before = env.count("wallet_ledger")
    cash = env.client.post("/api/v2/wallet/transactions", headers=env.h(BAWAB),
                           json={"tx_type": "maintenance_fee", "amount": 300, "description": "صيانة كاش",
                                 "payment_method": "cash", "resident_id": SOAD})
    assert cash.status_code == 201 and env.balance(SOAD) == 180
    assert env.count("wallet_ledger") == before                         # مفيش حركة رصيد
    fund = env.sql("SELECT SUM(amount) FROM wallet_transactions WHERE tx_type='maintenance_fee'")[0][0]
    assert fund == 300 + 300 + 300                                       # الصف التجريبي + الاتنين


def test_topup_through_transactions_endpoint_is_refused(env):
    r = env.client.post("/api/v2/wallet/transactions", headers=env.h(AHMED),
                        json={"tx_type": "topup", "amount": 10, "description": "محاولة شحن"})
    assert r.status_code == 400


def test_concurrent_payments_cannot_overspend(env):
    def pay():
        return env.client.post("/api/v2/wallet/transactions", headers=env.h(SOAD),
                               json={"tx_type": "tip", "amount": 120, "description": "إكرامية متزامنة"}).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = sorted(pool.map(lambda _: pay(), range(2)))
    assert codes == [201, 400]
    assert env.balance(SOAD) == 60 and env.balance(BAWAB) == 660


# ------------------------------------------------------------------ ledger / reconcile / summary
def test_ledger_visibility(env):
    env.client.post("/api/v2/wallet/topup", json={"amount": 10}, headers=env.h(AHMED))
    mine = env.client.get("/api/v2/wallet/ledger", headers=env.h(AHMED)).json()
    assert len(mine["entries"]) == 1 and mine["entries"][0]["balance_after"] == 360
    assert env.client.get(f"/api/v2/wallet/ledger?user_id={AHMED}", headers=env.h(SOAD)).status_code == 403
    assert env.client.get(f"/api/v2/wallet/ledger?user_id={AHMED}", headers=env.h(BAWAB)).status_code == 200


def test_reconcile_detects_changes_outside_ledger(env):
    env.client.post("/api/v2/wallet/topup", json={"amount": 10}, headers=env.h(AHMED))
    ok = env.client.get(f"/api/v2/wallet/reconcile/{AHMED}", headers=env.h(env.admin)).json()
    assert ok["drift"] == 0 and ok["chain_ok"] is True
    env.sql("UPDATE users SET wallet_balance = wallet_balance + 10 WHERE id=?", (AHMED,))   # تعديل بره الدفتر
    bad = env.client.get(f"/api/v2/wallet/reconcile/{AHMED}", headers=env.h(env.admin)).json()
    assert bad["drift"] == 10
    assert env.client.get(f"/api/v2/wallet/reconcile/{AHMED}", headers=env.h(BAWAB)).status_code == 403
    assert env.client.get(f"/api/v2/wallet/reconcile/{env.res2}", headers=env.h(env.admin)).status_code == 403


def test_summary_staff_only_and_same_building(env):
    assert env.client.get("/api/v2/wallet/summary/1", headers=env.h(AHMED)).status_code == 403
    assert env.client.get("/api/v2/wallet/summary/2", headers=env.h(BAWAB)).status_code == 403
    s = env.client.get("/api/v2/wallet/summary/1", headers=env.h(BAWAB)).json()
    assert s["bawab_wallet_balance"] == 540 and s["installments_outstanding"] == 0


# ------------------------------------------------------------------ schedule logic
@pytest.mark.parametrize("amount", ["100", "100.01", "0.12", "999.99", "1000", "12345.67"])
@pytest.mark.parametrize("count", [1, 2, 3, 5, 7, 12])
def test_schedule_sums_exactly(amount, count):
    amt = Decimal(amount)
    if int(amt * 100) < count:
        pytest.skip("مبلغ أصغر من عدد الأقساط")
    s = build_schedule(amt, count, "monthly", date(2026, 1, 15))
    assert sum(x[2] for x in s) == amt and len(s) == count
    assert all(x[2] > 0 for x in s)


def test_schedule_dates_and_remainder_goes_to_last():
    s = build_schedule(Decimal("100"), 3, "monthly", date(2026, 1, 31))
    assert [x[1] for x in s] == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31)]
    assert [x[2] for x in s] == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
    w = build_schedule(Decimal("90"), 3, "weekly", date(2026, 5, 1))
    assert [x[1] for x in w] == [date(2026, 5, 1), date(2026, 5, 8), date(2026, 5, 15)]
    assert add_months(date(2028, 1, 31), 1) == date(2028, 2, 29)         # سنة كبيسة


def test_schedule_rejects_tiny_amount():
    with pytest.raises(ValueError):
        build_schedule(Decimal("0.05"), 12, "weekly", date(2026, 1, 1))


# ------------------------------------------------------------------ plans
def test_create_plan_with_order_and_cash_down_payment(env):
    r = make_plan(env)
    assert r.status_code == 201, r.text
    plan = r.json()["plan"]
    assert plan["financed_amount"] == 200 and plan["remaining"] == 200
    assert [i["amount_due"] for i in plan["installments"]] == [100, 100]
    assert env.balance(BAWAB) == 590 and env.balance(AHMED) == 350      # مقدم كاش: البواب بس اتزود


def test_down_payment_via_wallet_debits_resident(env):
    r = make_plan(env, resident_id=SOAD, order_id=ORDER_SOAD, total_amount=185, down_payment=100,
                  down_payment_method="wallet")
    assert r.status_code == 201, r.text
    assert env.balance(SOAD) == 80 and env.balance(BAWAB) == 640
    assert [i["amount_due"] for i in r.json()["plan"]["installments"]] == [42.5, 42.5]


def test_down_payment_wallet_insufficient_rolls_back_the_whole_plan(env):
    r = make_plan(env, resident_id=SOAD, order_id=ORDER_SOAD, total_amount=185, down_payment=181,
                  down_payment_method="wallet", installments_count=1)
    assert r.status_code == 400
    assert env.count("installment_plans") == 0 and env.count("installments") == 0
    assert env.balance(SOAD) == 180


@pytest.mark.parametrize("override,code", [
    ({"total_amount": 300}, 400),                                   # أكتر من المستحق على الطلب
    ({"order_id": ORDER_SOAD}, 404),                                # طلب ساكن تاني
    ({"order_id": ORDER_TAREK, "resident_id": TAREK}, 400),         # طلب مدفوع بالفعل
    ({"order_id": 999}, 404),
    ({"down_payment": 250}, 400),                                   # المقدم = الإجمالي
    ({"start_date": (date.today() - timedelta(days=1)).isoformat()}, 400),
    ({"installments_count": 13}, 422),
    ({"installments_count": 0}, 422),
    ({"total_amount": 0.05, "down_payment": 0, "installments_count": 12, "order_id": None}, 400),
    ({"resident_id": BAWAB}, 400),                                  # التقسيط للسكان بس
    ({"resident_id": 12345}, 404),
])
def test_create_plan_validation(env, override, code):
    assert make_plan(env, **override).status_code == code


def test_duplicate_active_plan_on_same_order_rejected(env):
    assert make_plan(env).status_code == 201
    assert make_plan(env).status_code == 409


def test_only_staff_create_plans_and_building_isolation(env):
    body = dict(resident_id=AHMED, total_amount=100, installments_count=2)
    assert env.client.post("/api/v2/installments/plans", json=body, headers=env.h(AHMED)).status_code == 403
    assert env.client.post("/api/v2/installments/plans", json=body, headers=env.h(env.bawab2)).status_code == 403
    assert env.client.post("/api/v2/installments/plans", json=body, headers=env.h(env.admin)).status_code == 201


def test_plan_visibility(env):
    pid = make_plan(env).json()["plan"]["id"]
    assert env.client.get(f"/api/v2/installments/plans/{pid}", headers=env.h(AHMED)).status_code == 200
    assert env.client.get(f"/api/v2/installments/plans/{pid}", headers=env.h(SOAD)).status_code == 403
    assert env.client.get(f"/api/v2/installments/plans/{pid}", headers=env.h(env.bawab2)).status_code == 403
    assert env.client.get("/api/v2/installments/plans/999", headers=env.h(BAWAB)).status_code == 404
    assert len(env.client.get("/api/v2/installments/plans", headers=env.h(AHMED)).json()) == 1
    assert env.client.get("/api/v2/installments/plans", headers=env.h(SOAD)).json() == []
    assert len(env.client.get("/api/v2/installments/plans", headers=env.h(BAWAB)).json()) == 1


# ------------------------------------------------------------------ payments
def pay(env, uid, pid, **body):
    body.setdefault("payment_method", "wallet")
    return env.client.post(f"/api/v2/installments/plans/{pid}/pay", json=body, headers=env.h(uid))


def test_pay_full_flow_completes_plan_and_marks_order_paid(env):
    pid = make_plan(env).json()["plan"]["id"]
    r1 = pay(env, AHMED, pid, amount=100)
    assert r1.status_code == 200 and r1.json()["plan"]["remaining"] == 100
    assert env.balance(AHMED) == 250 and env.balance(BAWAB) == 690
    r2 = pay(env, AHMED, pid, amount=100)
    assert r2.status_code == 200 and r2.json()["plan"]["status"] == "completed"
    assert env.sql("SELECT is_paid FROM orders WHERE id=?", (ORDER_AHMED,))[0][0] == 1
    assert pay(env, AHMED, pid, amount=1).status_code == 400            # الخطة اتقفلت


def test_partial_and_oldest_first_allocation(env):
    pid = make_plan(env, installments_count=2).json()["plan"]["id"]
    r = pay(env, AHMED, pid, amount=30)
    inst = r.json()["plan"]["installments"]
    assert inst[0]["status"] == "partial" and inst[0]["remaining"] == 70
    r = pay(env, AHMED, pid, amount=100)                                 # 70 للأول + 30 للتاني
    alloc = r.json()["allocations"]
    assert [a["amount"] for a in alloc] == [70, 30]
    inst = r.json()["plan"]["installments"]
    assert inst[0]["status"] == "paid" and inst[1]["status"] == "partial"


def test_pay_specific_installment(env):
    pid = make_plan(env).json()["plan"]["id"]
    second = env.client.get(f"/api/v2/installments/plans/{pid}", headers=env.h(AHMED)).json()["installments"][1]["id"]
    r = pay(env, AHMED, pid, amount=100, installment_id=second)
    assert r.status_code == 200
    inst = r.json()["plan"]["installments"]
    assert inst[0]["status"] == "pending" and inst[1]["status"] == "paid"
    assert pay(env, AHMED, pid, amount=10, installment_id=second).status_code == 404   # اتسدد


def test_overpay_rejected_without_side_effects(env):
    pid = make_plan(env).json()["plan"]["id"]
    before = (env.balance(AHMED), env.balance(BAWAB), env.count("wallet_ledger"))
    assert pay(env, AHMED, pid, amount=200.01).status_code == 400
    assert (env.balance(AHMED), env.balance(BAWAB), env.count("wallet_ledger")) == before


def test_wallet_payment_with_low_balance_fails_atomically(env):
    pid = make_plan(env, resident_id=SOAD, order_id=ORDER_SOAD, total_amount=185, down_payment=0,
                    installments_count=1).json()["plan"]["id"]
    r = pay(env, SOAD, pid, amount=185)                                  # رصيدها 180
    assert r.status_code == 400
    assert env.balance(SOAD) == 180 and env.balance(BAWAB) == 540
    plan = env.client.get(f"/api/v2/installments/plans/{pid}", headers=env.h(SOAD)).json()
    assert plan["paid_so_far"] == 0 and plan["status"] == "active"


def test_resident_cannot_pay_cash_but_bawab_can(env):
    pid = make_plan(env).json()["plan"]["id"]
    assert pay(env, AHMED, pid, amount=100, payment_method="cash").status_code == 403
    r = pay(env, BAWAB, pid, amount=100, payment_method="cash")
    assert r.status_code == 200
    assert env.balance(AHMED) == 350 and env.balance(BAWAB) == 690       # الساكن ما اتخصمش


def test_cannot_pay_other_residents_plan(env):
    pid = make_plan(env).json()["plan"]["id"]
    assert pay(env, SOAD, pid, amount=10).status_code == 403
    assert pay(env, env.bawab2, pid, amount=10, payment_method="cash").status_code == 403


def test_cancel_plan(env):
    pid = make_plan(env).json()["plan"]["id"]
    pay(env, AHMED, pid, amount=100)
    assert env.client.post(f"/api/v2/installments/plans/{pid}/cancel", headers=env.h(AHMED)).status_code == 403
    r = env.client.post(f"/api/v2/installments/plans/{pid}/cancel", headers=env.h(BAWAB))
    assert r.status_code == 200
    statuses = [i["status"] for i in r.json()["plan"]["installments"]]
    assert statuses == ["paid", "cancelled"] and r.json()["plan"]["remaining"] == 0
    assert pay(env, AHMED, pid, amount=10).status_code == 400
    assert env.client.post(f"/api/v2/installments/plans/{pid}/cancel", headers=env.h(BAWAB)).status_code == 400
    assert make_plan(env).status_code == 201                              # الطلب اتحرر لخطة جديدة


# ------------------------------------------------------------------ overdue / notebook
def test_overdue_and_notebook(env, monkeypatch):
    make_plan(env, frequency="weekly")                                    # أول قسط بعد 7 أيام
    make_plan(env, resident_id=SOAD, order_id=ORDER_SOAD, total_amount=185, down_payment=0, installments_count=1,
              frequency="monthly")                                        # أول قسط بعد شهر
    assert env.client.get("/api/v2/installments/overdue", headers=env.h(BAWAB)).json()["count"] == 0
    assert env.client.get("/api/v2/installments/overdue", headers=env.h(AHMED)).status_code == 403

    set_today(monkeypatch, date.today() + timedelta(days=9))             # دلوقتي أول قسط لأحمد متأخر يومين
    od = env.client.get("/api/v2/installments/overdue", headers=env.h(BAWAB)).json()
    assert od["count"] == 1 and od["items"][0]["resident_id"] == AHMED
    assert od["items"][0]["days_late"] == 2 and od["total_overdue"] == 100

    book = env.client.get(f"/api/v2/installments/ledger/{AHMED}", headers=env.h(AHMED)).json()
    assert book["total_financed"] == 200 and book["total_remaining"] == 200 and book["total_overdue"] == 100
    assert book["next_installment"]["is_overdue"] is True
    assert env.client.get(f"/api/v2/installments/ledger/{AHMED}", headers=env.h(SOAD)).status_code == 403
    assert env.client.get(f"/api/v2/installments/ledger/{AHMED}", headers=env.h(env.bawab2)).status_code == 403

    s = env.client.get("/api/v2/wallet/summary/1", headers=env.h(BAWAB)).json()
    assert s["active_installment_plans"] == 2 and s["installments_overdue"] == 100
    assert s["installments_outstanding"] == 200 + 185


def test_ledger_reconciles_after_a_full_scenario(env):
    pid = make_plan(env).json()["plan"]["id"]
    pay(env, AHMED, pid, amount=100)
    env.client.post("/api/v2/wallet/topup", json={"amount": 25}, headers=env.h(AHMED))
    for uid in (AHMED, BAWAB):
        r = env.client.get(f"/api/v2/wallet/reconcile/{uid}", headers=env.h(env.admin)).json()
        assert r["chain_ok"] is True and r["drift"] == 0, (uid, r)


# ------------------------------------------------------------------ smoke: التطبيق الكامل
def test_full_app_includes_legacy_and_v2_routes():
    pytest.importorskip("openai")
    from app.wallet_main import app
    paths = app.openapi()["paths"]
    assert "/api/orders" in paths and "/api/wallet/transactions" in paths    # القديم زي ما هو
    assert "/api/v2/wallet/topup" in paths and "/api/v2/installments/plans" in paths
