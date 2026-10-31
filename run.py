"""
El-Beh El-Bawab Application Launcher
Starts FastAPI backend server on http://localhost:8000
"""
import sys
from pathlib import Path

# Safe utf-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

if __name__ == "__main__":
    import uvicorn
    print("=" * 65)
    print("🛎️  مشروع البيه البواب (El-Beh El-Bawab v3.0) - السيرفر قيد التشغيل")
    print("🌐 رابط التطبيق والواجهة التفاعلية: http://localhost:8000")
    print("📍 رابط الـ API و Swagger UI: http://localhost:8000/docs")
    print("🤖 وكيل الذكاء الاصطناعي (Groq AI Agent): مفعّل ومستعد")
    print("=" * 65)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
