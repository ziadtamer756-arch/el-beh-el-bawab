from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION
from app.core.database import init_db
from app.routers import (
    auth,
    buildings,
    users,
    orders,
    maintenance,
    visitors,
    parcels,
    garage,
    utilities,
    wallet,
    announcements,
    reviews,
    chat,
    emergency,
    ai_agents,
)

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from pathlib import Path
from fastapi.responses import FileResponse

INDEX_HTML_PATH = Path(__file__).resolve().parent.parent.parent / "index.html"


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", include_in_schema=False)
def serve_home_app():
    if INDEX_HTML_PATH.exists():
        return FileResponse(str(INDEX_HTML_PATH), media_type="text/html")
    return api_overview()


@app.get("/api", tags=["Health Check & Overview"])
@app.get("/api/health", tags=["Health Check & Overview"])
def api_overview():
    return {
        "project": "البيه البواب - El-Beh El-Bawab v3.0 (Mobile + 15 AI Agents + 15 APIs)",
        "status": "online",
        "version": APP_VERSION,
        "docs_url": "/docs",
        "web_app": "/",
        "total_ai_agents": 15,
        "total_api_modules": 15,
        "api_modules": [
            "01. /api/auth (المصادقة وتسجيل الدخول)",
            "02. /api/buildings (إدارة العمارات واتحاد الملاك)",
            "03. /api/users (إدارة السكان والبوابين وحالة التواجد)",
            "04. /api/orders (الطلبات والمشاوير والخدمات)",
            "05. /api/maintenance (الصيانة والأعطال المنزلية)",
            "06. /api/visitors (تصاريح الزوار والدليفري وأمن البوابة)",
            "07. /api/parcels (استلام الطرود وأمانات البوابة)",
            "08. /api/garage (الجراج واشتراكات غسيل السيارات)",
            "09. /api/utilities (فواتير المرافق المشتركة والعدادات)",
            "10. /api/wallet (محفظة الإكراميات وحساب العهدة)",
            "11. /api/announcements (لوحة إعلانات وتنبيهات العمارة)",
            "12. /api/reviews (تقييمات ومراجعات البواب)",
            "13. /api/chat (المحادثة الفورية والرسائل الصوتية)",
            "14. /api/emergency (بلاغات الطوارئ والاستغاثة SOS)",
            "15. /api/ai-agents (محرك وكلاء الذكاء الاصطناعي الـ ١٥)",
        ],
    }


# تسجيل الـ 15 API Routers بالكامل
app.include_router(auth.router)
app.include_router(buildings.router)
app.include_router(users.router)
app.include_router(orders.router)
app.include_router(maintenance.router)
app.include_router(visitors.router)
app.include_router(parcels.router)
app.include_router(garage.router)
app.include_router(utilities.router)
app.include_router(wallet.router)
app.include_router(announcements.router)
app.include_router(reviews.router)
app.include_router(chat.router)
app.include_router(emergency.router)
app.include_router(ai_agents.router)
