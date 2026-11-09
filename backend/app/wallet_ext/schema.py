"""إنشاء الجداول الجديدة (آمن للتكرار: CREATE TABLE IF NOT EXISTS).

لا يلمس أي جدول موجود. الجداول الجديدة:
- wallet_ledger        : دفتر حركة الأرصدة (دائن/مدين + الرصيد بعد كل حركة)
- installment_plans    : خطط التقسيط (العهدة)
- installments         : الأقساط
"""
from app.core import database

_ready_paths: set = set()

_DDL = """
CREATE TABLE IF NOT EXISTS wallet_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    tx_id INTEGER,
    plan_id INTEGER,
    direction TEXT NOT NULL CHECK(direction IN ('credit', 'debit')),
    amount REAL NOT NULL CHECK(amount > 0),
    balance_after REAL NOT NULL,
    entry_type TEXT NOT NULL,
    ref_group TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (tx_id) REFERENCES wallet_transactions(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_wallet_ledger_user ON wallet_ledger(user_id, id);

CREATE TABLE IF NOT EXISTS installment_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    bawab_id INTEGER NOT NULL,
    order_id INTEGER,
    total_amount REAL NOT NULL CHECK(total_amount > 0),
    down_payment REAL NOT NULL DEFAULT 0 CHECK(down_payment >= 0),
    financed_amount REAL NOT NULL CHECK(financed_amount > 0),
    installments_count INTEGER NOT NULL CHECK(installments_count BETWEEN 1 AND 12),
    frequency TEXT NOT NULL CHECK(frequency IN ('weekly', 'biweekly', 'monthly')),
    start_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'completed', 'cancelled')),
    notes TEXT,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (bawab_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_plans_resident ON installment_plans(resident_id, status);

CREATE TABLE IF NOT EXISTS installments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    seq INTEGER NOT NULL,
    due_date TEXT NOT NULL,
    amount_due REAL NOT NULL CHECK(amount_due > 0),
    amount_paid REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'partial', 'paid', 'cancelled')),
    paid_at TEXT,
    UNIQUE(plan_id, seq),
    FOREIGN KEY (plan_id) REFERENCES installment_plans(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_installments_plan ON installments(plan_id, seq);
"""


def ensure_schema() -> None:
    """ينشئ الجداول الجديدة مرة واحدة لكل ملف قاعدة بيانات."""
    path = str(database.DB_PATH)
    if path in _ready_paths:
        return
    with database.get_db() as conn:
        conn.executescript(_DDL)
    _ready_paths.add(path)
