"""نقطة تشغيل التطبيق مع وحدة المحفظة والتقسيط.

التشغيل (من داخل مجلد backend):
    uvicorn app.wallet_main:app --reload --port 8000

الـ endpoints القديمة كما هي، والجديدة تحت /api/v2/wallet و /api/v2/installments.
"""
from app.main import app
from app.wallet_ext.setup import install

install(app)
