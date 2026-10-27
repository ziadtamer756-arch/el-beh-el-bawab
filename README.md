# 🛎️ مشروع البيه البواب (El-Beh El-Bawab)

تطبيق ذكي لربط **سكان العمارات** بحارس العقار (**البيه البواب**) لتسهيل طلبات السوبرماركت والمخابز، الصيدليات، غسيل السيارات، خدمات الصيانة المنزلية (سباكة/كهرباء/غاز)، وحمل الأغراض، بالإضافة إلى لوحة إعلانات داخلية لكل عمارة.

---

## 🏗️ هيكل المشروع (Repository Structure)

تم تصميم المستودع بنظام يفصل بوضوح بين **الواجهة الخلفية (Python Backend)** و **الواجهة الأمامية (Frontend)** ليتمكن باقي أعضاء الفريق من العمل بالتوازي دون تعارض:

```text
el-beh-el-bawab/
├── README.md                        # التوثيق الشامل للمشروع وخطة عمل الفريق
├── .gitignore                       # تجاهل الملفات المؤقتة وقواعد البيانات المحلية
├── .env.example                     # نموذج متغيرات البيئة
├── docker-compose.yml               # تشغيل السيرفر بضغطة واحدة عبر Docker
│
├── backend/                         # 🐍 الواجهة الخلفية (Python + FastAPI + SQLite)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                  # نقطة انطلاق السيرفر وتفعيل CORS والـ Routers
│   │   ├── core/
│   │   │   ├── config.py            # إعدادات التطبيق ومسار قاعدة البيانات
│   │   │   └── database.py          # إنشاء جداول SQLite + بيانات تجريبية جاهزة (Seed Data)
│   │   ├── schemas/
│   │   │   └── models.py            # نماذج التحقق من البيانات (Pydantic Schemas)
│   │   └── routers/
│   │       ├── buildings.py         # إدارة العمارات ولوحة الإعلانات (/api/buildings)
│   │       ├── users.py             # إدارة السكان والبوابين وحالة التواجد (/api/users)
│   │       └── orders.py            # إدارة الطلبات، المشاوير، والإحصائيات (/api/orders)
│   └── tests/
│       └── test_api.py              # اختبارات آلية (Pytest) لجميع مسارات الـ API
│
└── frontend/                        # 🎨 هيكل الواجهة الأمامية لباقي الفريق
    ├── README_FRONTEND.md           # إرشادات خاصة بمطوري الـ Frontend
    ├── index.html                   # شاشة تأسيسية تفاعلية (للساكن والبواب)
    └── src/
        ├── app.js                   # منطق ربط الشاشات بالـ API
        ├── services/
        │   └── api.js               # عميل API جاهز (Fetch Wrapper) لكل الـ Endpoints
        └── styles/
            └── main.css             # تنسيقات الهوية البصرية العربية (RTL)
```

---

## 🚀 طريقة تشغيل المشروع (Quick Start)

### 1️⃣ تشغيل الـ Backend (Python FastAPI)

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

* بمجرد التشغيل، سيقوم النظام تلقائياً بإنشاء قاعدة البيانات `el_beh_el_bawab.db` وإضافة **بيانات تجريبية جاهزة** (عمارة النيل الذهبية، عم عبد السميع البواب، سكان، وطلبات متنوعة) حتى يتمكن فريق الـ Frontend من التجربة فوراً.
* **توثيق Swagger التفاعلي (لتجربة الـ API من المتصفح):**
  افتح الرابط: `http://localhost:8000/docs`

### 2️⃣ تشغيل اختبارات الـ Backend (Tests)

```bash
cd backend
pytest
```

### 3️⃣ تشغيل الـ Frontend التأسيسي

يمكن لفريق الـ Frontend فتح ملف `frontend/index.html` عبر Live Server (أو استبدال مجلد `frontend/` بمشروع React / Next.js / Flutter مع استخدام ملف `frontend/src/services/api.js` الجاهز للربط).

---

## 🔌 أهم مسارات الـ API الجاهزة (API Endpoints)

| الطريقة (Method) | المسار (Endpoint) | الوظيفة |
| :--- | :--- | :--- |
| `GET` | `/api/buildings` | جلب قائمة العمارات المسجلة وإحصائيات كل عمارة |
| `POST` | `/api/buildings` | تسجيل عمارة جديدة بكود دعوة خاص (`invite_code`) |
| `GET` | `/api/buildings/{id}/announcements` | عرض إعلانات وتنبيهات العمارة (مثل مواعيد صيانة الأسانسير) |
| `POST` | `/api/buildings/{id}/announcements` | نشر تنبيه جديد لسكان العمارة |
| `GET` | `/api/users?building_id=1` | جلب السكان والبوابين في العمارة |
| `POST` | `/api/users` | تسجيل ساكن جديد أو بواب |
| `PATCH` | `/api/users/{id}/availability` | تغيير حالة تواجد البواب (متاح / مشغول خارج العمارة) |
| `GET` | `/api/orders/categories` | قائمة أنواع الخدمات بالعربية (سوبرماركت، صيدلية، غسيل سيارات، صيانة...) |
| `GET` | `/api/orders?building_id=1` | عرض الطلبات مرتبة تلقائياً حسب الأولوية (`urgent` أولاً) |
| `POST` | `/api/orders` | إرسال طلب جديد من الساكن إلى البواب |
| `PATCH` | `/api/orders/{id}/status` | تحديث حالة الطلب (`pending` ⬅️ `accepted` ⬅️ `in_progress` ⬅️ `delivered`) |
| `GET` | `/api/orders/stats/{building_id}` | إحصائيات العمارة وإجمالي إكراميات البواب |

---

## 👥 تقسيم المهام المقترح لباقي الفريق (Next Steps for the Team)

1. **فريق الواجهة الأمامية (Frontend / Mobile):**
   - استخدام `frontend/src/services/api.js` لبناء شاشات الساكن وشاشة البواب.
   - إضافة شاشة تسجيل الدخول برقم الهاتف وكود العمارة (`NILE-15`).
   - تصميم بطاقات حالة الطلب مع ألوان واضحة للطلبات المستعجلة.
2. **فريق الواجهة الخلفية (Backend Extensions):**
   - إضافة مصادقة JWT / OTP لرقم الموبايل.
   - إضافة WebSockets للإشعارات اللحظية بمجرد إرسال طلب جديد.
