# المحفظة الآمنة v2 + تقسيط العهدة («حالاً عالنوتة»)

وحدة مستقلة بالكامل: **كل ملفاتها جديدة ولا تعدّل أي ملف موجود في المشروع.**
الدفع بالمحفظة **وهمي (محاكاة)**، مفيش بوابة دفع حقيقية.

## الملفات

| الملف | وظيفته |
|---|---|
| `backend/app/wallet_ext/schema.py` | إنشاء 3 جداول جديدة (`wallet_ledger`, `installment_plans`, `installments`) تلقائيًا عند أول طلب |
| `backend/app/wallet_ext/deps.py` | التحقق من التوكن والأدوار (resident / bawab / admin) |
| `backend/app/wallet_ext/ledger.py` | تحريك الأرصدة داخل transaction واحدة + تسجيل الدفتر |
| `backend/app/wallet_ext/wallet_routes.py` | `/api/v2/wallet/*` |
| `backend/app/wallet_ext/installment_routes.py` | `/api/v2/installments/*` |
| `backend/app/wallet_ext/installment_logic.py` | جدولة الأقساط (بالقروش بدون فقد ولا زيادة) |
| `backend/app/wallet_ext/models.py`, `money.py`, `setup.py`, `__init__.py` | نماذج الإدخال، حساب Decimal، ربط الراوترات |
| `backend/app/wallet_main.py` | نقطة التشغيل: التطبيق الأصلي + الوحدة الجديدة |
| `backend/tests/test_wallet_installments.py` | 97 اختبار |

## التشغيل (من داخل `backend/` على هيكل فرع `hatem`)

```bash
pip install -r requirements.txt
python -m pytest tests/test_wallet_installments.py -v
uvicorn app.wallet_main:app --reload --port 8000     # ثم افتح /docs
```

الـ endpoints القديمة (`/api/...`) شغالة زي ما هي. الجديدة تحت `/api/v2/...`.
لو عايز تدمجها في التطبيق الأصلي بدل `wallet_main.py`، أضف في `main.py` سطرين:
`from app.wallet_ext.setup import install` ثم `install(app)`.

## الـ endpoints (كلها تتطلب `Authorization: Bearer <token>`)

**المحفظة `/api/v2/wallet`**

| Method | Path | مين | الوصف |
|---|---|---|---|
| GET | `/balance`, `/balance/{user_id}` | الكل (الساكن لنفسه فقط) | الرصيد |
| POST | `/topup` | الكل | شحن المحفظة (محاكاة). البواب/الأدمن يشحنوا لساكن بـ `user_id` |
| POST | `/transactions` | حسب النوع | `tip` / `reimbursement` / `settlement` / `maintenance_fee` |
| GET | `/ledger` | الكل | دفتر الحركات مع الرصيد بعد كل حركة |
| GET | `/reconcile/{user_id}` | أدمن | مطابقة الرصيد مع الدفتر وكشف أي تغيير من خارجه |
| GET | `/summary/{building_id}` | بواب/أدمن | ملخص مالي يشمل الأقساط |

**التقسيط `/api/v2/installments`**

| Method | Path | مين | الوصف |
|---|---|---|---|
| POST | `/plans` | بواب/أدمن | فتح خطة (إجمالي، مقدم، عدد أقساط 1-12، أسبوعي/نص شهري/شهري) |
| GET | `/plans`, `/plans/{id}` | الساكن لخططه، البواب للكل | الخطط والأقساط |
| POST | `/plans/{id}/pay` | الساكن (محفظة) / البواب (أي وسيلة) | سداد، من الأقدم للأحدث أو قسط محدد |
| POST | `/plans/{id}/cancel` | بواب/أدمن | إلغاء الخطة (المسدد يفضل مسدد) |
| GET | `/overdue` | بواب/أدمن | المتأخرات |
| GET | `/ledger/{resident_id}` | الساكن لنفسه، البواب للكل | «النوتة»: المسدد والمتبقي والمتأخر وأقرب قسط |

## القواعد الأساسية

- الخصم من المحفظة حقيقي ويُرفض لو الرصيد مش كفاية، والعملية كلها تتلغي (لا خصم بدون إضافة).
- الساكن يدفع **بالمحفظة فقط**. الكاش/إنستاباي يسجلها البواب بعد ما يستلم الفلوس (عشان الساكن ميكتبش دفع وهمي).
- الإكرامية يدفعها الساكن فقط، والتسوية للبواب/الأدمن فقط.
- كل مستخدم محصور في عمارته، والساكن لا يرى بيانات ساكن آخر.
- المبالغ بحد أقصى منزلتين عشريتين، والحسابات بـ Decimal (مفيش أخطاء تقريب).
- لما آخر قسط يتسدد: الخطة تتقفل، والطلب المرتبط يبقى `is_paid = 1` لو الخطة غطّت كامل مستحقه.
- متغير بيئة اختياري: `WALLET_SIMULATED_TOPUP=0` يقفل الشحن الذاتي، ويخلي البواب هو اللي يشحن.

## ملاحظات مهمة

- الـ endpoints القديمة `/api/wallet/*` **لم تتغير** وما زالت بلا حماية. الواجهة (`api.js`) محتاجة تنادي الـ v2.
- الرصيد القديم (قبل الدفتر) ليس له سطور في الدفتر، و`/reconcile` بيقيس من أول حركة مسجلة.
- التسوية بين الساكن والبواب تعتمد على أمانة البواب في تسجيل الكاش، والدفتر بيخلي أي حاجة قابلة للمراجعة من الأدمن.
