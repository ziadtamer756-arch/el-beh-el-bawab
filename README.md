# 🛎️ مشروع البيه البواب (El-Beh El-Bawab v2.0 - النسخة الكاملة)

منصة متكاملة لربط **سكان العمارات** بحارس العقار (**البيه البواب**) لتسهيل طلبات السوبرماركت والمخابز، الصيدليات، غسيل السيارات، خدمات الصيانة المنزلية (سباكة/كهرباء/غاز)، وحمل الأغراض، بالإضافة إلى **محفظة الإكراميات وحساب العهدة**، **نظام التقييمات**، و**لوحة إعلانات العمارة الفورية**.

---

## 🏗️ هيكل المشروع المكتمل (Full Repository Structure)

```text
el-beh-el-bawab/
├── README.md                        # التوثيق الشامل للمشروع ومسارات الـ API
├── .gitignore                       # تجاهل الملفات المؤقتة وقواعد البيانات المحلية
├── .env.example                     # نموذج متغيرات البيئة وإعدادات السيرفر
├── docker-compose.yml               # تشغيل السيرفر بضغطة واحدة عبر Docker
├── setup_el_beh_el_bawab.py         # سكربت التوليد التلقائي لجميع ملفات المشروع
│
├── backend/                         # 🐍 الواجهة الخلفية الكاملة (Python + FastAPI + SQLite + WebSockets)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                  # نقطة انطلاق السيرفر وتفعيل CORS والـ 7 Routers
│   │   ├── core/
│   │   │   ├── config.py            # إعدادات التطبيق ومسار قاعدة البيانات
│   │   │   ├── security.py          # توليد والتحقق من توكن المصادقة (HMAC-SHA256 Token)
│   │   │   └── database.py          # إنشاء 7 جداول SQLite + بيانات تجريبية غنية (Seed Data)
│   │   ├── schemas/
│   │   │   └── models.py            # نماذج التحقق من البيانات (Pydantic v2 Schemas)
│   │   └── routers/
│   │       ├── auth.py              # تسجيل الدخول برقم الهاتف وكود العمارة (/api/auth)
│   │       ├── buildings.py         # إدارة العمارات ولوحة الإعلانات (/api/buildings)
│   │       ├── users.py             # إدارة السكان والبوابين وحالة التواجد (/api/users)
│   │       ├── orders.py            # إدارة الطلبات، الأولويات، والإحصائيات (/api/orders)
│   │       ├── wallet.py            # محفظة الإكراميات، العهدة، وصندوق الصيانة (/api/wallet)
│   │       ├── reviews.py           # تقييمات ومراجعات البواب (/api/reviews)
│   │       └── notifications.py     # الإشعارات اللحظية وقناة WebSocket (/api/notifications)
│   └── tests/
│       └── test_api.py              # اختبارات آلية شاملة لدورة حياة الطلب والمحفظة والتقييم
│
└── frontend/                        # 🎨 الواجهة الأمامية التفاعلية الكاملة (RTL Arabic UI)
    ├── README_FRONTEND.md           # دليل مطوري الواجهة الأمامية
    ├── index.html                   # التطبيق التفاعلي الكامل (يعمل مع السيرفر أو بشكل مستقل)
    └── src/
        └── services/
            └── api.js               # عميل API كامل لجميع المسارات (Auth, Orders, Wallet, Reviews)
```

---

## 🚀 طريقة التشغيل السريع (Quick Start)

### 1️⃣ توليد الملفات ورفعها إلى GitHub
ضع ملف `setup_el_beh_el_bawab.py` داخل مجلد الريبو لديك ثم نفّذ:

```bash
python setup_el_beh_el_bawab.py
git add .
git commit -m "feat: complete El-Beh El-Bawab v2.0 full-stack backend and interactive frontend"
git push origin main
```

### 2️⃣ تشغيل الـ Backend (Python FastAPI)

```bash
cd backend
python -m venv venv
# في ويندوز:
venv\Scripts\activate
# في ماك أو لينكس:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

* افتح توثيق **Swagger UI** التفاعلي لتجربة كل المسارات: `http://localhost:8000/docs`

### 3️⃣ تشغيل الواجهة الأمامية الكاملة (`frontend/index.html`)
افتح ملف `frontend/index.html` مباشرة في المتصفح أو عبر Live Server، وستجد كافة الشاشات (واجهة الساكن، لوحة تحكم عم عبد السميع، محفظة الإكراميات والعهدة، لوحة الإعلانات، التقييمات، ودليل الشقق) تعمل بشكل فوري.

---

## 🔌 جدول مسارات الـ API الكامل (v2.0 Endpoints)

| القسم | الطريقة | المسار (Endpoint) | الوظيفة |
| :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/auth/login` | تسجيل الدخول برقم الموبايل وكود العمارة (`NILE-15`) ورمز OTP (`1234`) |
| **Auth** | `POST` | `/api/auth/register` | إنشاء حساب ساكن جديد وإصدار `access_token` |
| **Auth** | `GET` | `/api/auth/me` | جلب بيانات المستخدم الحالي من التوكن |
| **Buildings** | `GET` | `/api/buildings` | جلب قائمة العمارات وإحصائيات السكان والطلبات |
| **Buildings** | `GET/POST` | `/api/buildings/{id}/announcements` | عرض ونشر إعلانات وتنبيهات العمارة |
| **Users** | `GET/POST` | `/api/users` | عرض أو إضافة سكان وبوابين |
| **Users** | `PATCH` | `/api/users/{id}/availability` | تحديث حالة تواجد البواب (متاح الآن / في مشوار خارج العمارة) |
| **Orders** | `GET/POST` | `/api/orders` | عرض الطلبات (مرتبة حسب الأولوية) أو إرسال طلب جديد |
| **Orders** | `PATCH` | `/api/orders/{id}/status` | تحديث حالة الطلب وتسجيل الفاتورة الفعلية وإضافة الإكرامية للمحفظة |
| **Orders** | `GET` | `/api/orders/stats/{building_id}` | إحصائيات العمارة (الكل، قيد الانتظار، جاري التنفيذ، المكتملة) |
| **Wallet** | `GET/POST` | `/api/wallet/transactions` | سجل المعاملات المالية (إكراميات، سداد عهدة، صيانة العمارة) |
| **Wallet** | `GET` | `/api/wallet/summary/{building_id}` | ملخص أرصدة محفظة البواب، العهدة غير المسددة، وصندوق الصيانة |
| **Reviews** | `GET/POST` | `/api/reviews` | إضافة وعرض تقييمات السكان لخدمة البواب |
| **Realtime** | `WS` | `/api/notifications/ws/{building_id}` | قناة WebSocket للإشعارات اللحظية للعمارة |
