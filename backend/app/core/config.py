import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent

# Load .env from workspace root or backend dir
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

db_env = os.getenv("DATABASE_PATH", "el_beh_el_bawab.db")
if not os.path.isabs(db_env):
    if db_env.startswith("backend/") or db_env.startswith("backend\\"):
        DB_PATH = str((ROOT_DIR / db_env).resolve())
    else:
        DB_PATH = str((BASE_DIR / db_env).resolve())
else:
    DB_PATH = db_env

Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
SECRET_KEY = os.getenv("SECRET_KEY", "el-beh-el-bawab-secret-key-2026-v3")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
_raw_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_MODEL = "openai/gpt-oss-20b" if _raw_model in ("openai/oss-20b", "oss-20b") else _raw_model
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

APP_TITLE = "البيه البواب API - El-Beh El-Bawab v3.0 (15 AI Agents + 15 APIs)"
APP_DESCRIPTION = """
الواجهة الخلفية الكاملة (Full-Stack Mobile & Web Backend) لمشروع **البيه البواب (El-Beh El-Bawab v3.0)** 📱🏢🛎️
تضم:
- **15 AI Agents (وكيل ذكاء اصطناعي متخصص)** لتحليل الطلبات باللهجة المصرية، تسعير المشتريات، كشف التلاعب في الفواتير، تجميع المشاوير، تشخيص أعطال الصيانة، إدارة طوارئ العمارة، وصياغة الإعلانات.
- **15 API Routers (١٥ وحدة API متكاملة)** تغطي كل احتياجات تطبيق الموبايل والويب للسكان والبوابين واتحاد الملاك.
"""
APP_VERSION = "3.0.0"
