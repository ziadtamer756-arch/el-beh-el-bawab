# 🛎️ مشروع البيه البواب (El-Beh El-Bawab v8.0 — GitHub Pro Ultimate Edition)

![CI/CD Pipeline](https://img.shields.io/badge/GitHub_Actions_CI%2FCD-Passing-C8102E?style=for-the-badge&logo=githubactions&logoColor=white)
![GitHub Codespaces](https://img.shields.io/badge/GitHub_Codespaces-Ready_in_1_Click-0F172A?style=for-the-badge&logo=github&logoColor=white)
![Smart Agents](https://img.shields.io/badge/AI_Concierge_Agents-15_Active_Modules-D97706?style=for-the-badge)
![Backend APIs](https://img.shields.io/badge/Unified_APIs-15_Endpoints_on_:8000-10B981?style=for-the-badge)

منصة «سوبر أب» متكاملة بالهوية الرسمية (**الأحمر الملكي `#C8102E` والأبيض النقي `#FFFFFF`**) لربط **سكان العمارات** بحارس العقار (**البيه البواب**) واتحاد الملاك؛ تجمع بين **شاشة الترحيب وبوابة التسجيل**، **تعديل الطلبات التفاعلي داخل الشات قبل الإرسال**، **رادار التتبع اللحظي**، **محفظة تقسيط العهدة (حالاً عالنوتة)**، و**١٥ وكيلاً ذكياً** مع **١٥ مسار خدمة خلفية**.

---

## 🌟 كيف يستفيد هذا المستودع من مميزات **GitHub Pro**؟

1. **خط أنابيب الفحص والتشغيل التلقائي (`.github/workflows/ci_cd_pipeline.yml`):**
   عند كل `git push` أو `Pull Request`، يقوم GitHub Actions تلقائياً ببناء محرك العمليات السريع واختبار جميع الـ 15 مسارات والتأكد من سلامة ملفات الواجهة.
2. **الفحص الأمني المتقدم للثغرات (`.github/workflows/codeql_security.yml`):**
   يفعل ميزة **GitHub Advanced Security (CodeQL)** لفحص الكود أسبوعياً وعند كل تحديث.
3. **التشغيل السحابي الفوري بضغطة واحدة (`.devcontainer/devcontainer.json`):**
   يتيح لك وللبشمهندس فتح المشروع وتشغيله بالكامل من المتصفح عبر **GitHub Codespaces** بدون تثبيت أي برامج محلياً.
4. **التحديث الذكي للمكتبات (`.github/dependabot.yml`) وحماية الفروع (`CODEOWNERS`):**
   يراقب تحديثات المكتبات تلقائياً وينظم مراجعة الكود بين أعضاء الفريق.

---

## 📂 هيكلة المشروع الشاملة

```text
el-beh-el-bawab/
├── .github/                         # 🚀 أتمتة GitHub Pro (CI/CD + CodeQL + Dependabot + Templates)
├── .devcontainer/                   # ☁️ تشغيل سحابي فوري عبر GitHub Codespaces
├── assets/                          # 🎨 الشعار الرسمي بالأحمر والأبيض (el_beh_logo.jpg)
├── android-app/                     # 📱 تطبيق الموبايل الأصلي (ElBehElBawabApp.kt)
├── mobile-react-app/                # 📱 نسخة التليفون التفاعلية المستقلة (شاشة الترحيب + بوابة التسجيل + تعديل الشات)
├── desktop-react-app/               # 🖥️ نسخة الكمبيوتر وغرفة العمليات المركزية والرسومات البيانية
├── backend/                         # ⚡ الخادم الموحد (15 مسار خدمة + 15 وكيل ذكي + 15 جدول بيانات)
├── c_engine/                        # ⚙️ محرك الحسابات السريع للمسافات والتسعير وتدقيق الفواتير
├── enterprise_core/                 # 🏦 خدمات الفوترة، قواعد البيانات، وبوابات الدفع والمزامنة
└── json_schemas/                    # 📄 المخططات القياسية للبيانات
```

---

## 🚀 طريقة التشغيل السريع (محلياً أو عبر GitHub Codespaces)

```bash
# 1. تثبيت المكتبات وتشغيل الخادم الموحد على المنفذ 8000
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
* **التطبيق الموحد:** `http://localhost:8000`
* **توثيق المسارات التفاعلي (Swagger):** `http://localhost:8000/docs`
