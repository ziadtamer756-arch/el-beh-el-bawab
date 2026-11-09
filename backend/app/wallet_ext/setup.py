"""ربط وحدة المحفظة والتقسيط بتطبيق FastAPI من غير تعديل main.py.

الجداول الجديدة بتتنشأ تلقائيًا عند أول طلب لأي endpoint من الوحدة (ensure_ready)،
فمفيش حاجة إضافية لازم تتضاف في startup.
"""
from fastapi import FastAPI


def install(app: FastAPI) -> FastAPI:
    from app.wallet_ext.installment_routes import router as installments_router
    from app.wallet_ext.wallet_routes import router as wallet_router

    app.include_router(wallet_router)
    app.include_router(installments_router)
    return app
