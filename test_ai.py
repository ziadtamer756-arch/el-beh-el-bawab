"""
Groq AI Agent Connection & Model Verification Script
فحص واختبار الاتصال المباشر بـ Groq API والموديل
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Safe utf-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load .env
env_path = Path(__file__).resolve().parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("GROQ_API_KEY", "").strip()
raw_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
model_name = "openai/gpt-oss-20b" if raw_model in ("openai/oss-20b", "oss-20b") else raw_model

print("=" * 65)
print("🔍 فحص الاتصال بوكيل الذكاء الاصطناعي (Groq AI Verification)")
print("=" * 65)
print(f"📁 مسار ملف .env: {env_path}")
print(f"🤖 الموديل المحدد: {model_name}")

if not api_key:
    print("\n❌ تنبيه: لم تقم بكتابة المفتاح بعد في ملف .env!")
    print("👉 افتح ملف .env وضع مفتاحك بجانب GROQ_API_KEY=")
    print("   مثال: GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx")
    print("   احصل على مفتاح مجاني من: https://console.groq.com/keys")
    sys.exit(1)

masked_key = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
print(f"🔑 المفتاح المستخدم: {masked_key}")
print("\n⏳ جاري إرسال طلب تجريبي لـ Groq API...")

try:
    from openai import OpenAI
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
        timeout=15.0
    )

    start_time = time.time()
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "أنت عم عبد السميع بواب عمارة النيل الذكي في مصر. رد بجملة ترحيبية واحدة فقط بالمصري."},
            {"role": "user", "content": "مساء الخير يا عم عبد السميع، إيه الأخبار؟"}
        ],
        max_tokens=500,
        temperature=0.3
    )
    elapsed_ms = int((time.time() - start_time) * 1000)
    msg = response.choices[0].message
    reply = (msg.content or "").strip() or getattr(msg, "reasoning", "")[:120]

    print("\n" + "=" * 65)
    print("✅ تم الاتصال بنجاح تام! الموديل يعمل بكفاءة وسرعة فائقة 🚀")
    print(f"⚡ زمن الاستجابة: {elapsed_ms} مللي ثانية")
    print(f"💬 رد الموديل الحي:")
    print(f"   «{reply}»")
    print("=" * 65)
    print("🎉 يمكنك الآن تشغيل السيرفر بأمان عبر: python run.py")

except Exception as e:
    err_str = str(e)
    print("\n" + "=" * 65)
    print("❌ حدث خطأ أثناء الاتصال بـ Groq:")
    print(f"   {err_str}")
    print("\n💡 نصائح للحل:")
    if "model_not_found" in err_str or "does not exist" in err_str:
        print(f"   اسم الموديل '{model_name}' غير متاح على Groq.")
        print("   الموديل الموصى به والرسمي هو: llama-3.3-70b-versatile أو llama-3.1-8b-instant")
    elif "Invalid API Key" in err_str or "authentication" in err_str.lower() or "401" in err_str:
        print("   المفتاح غير صحيح أو منتهي الصلاحية. تأكد من نسخه كاملاً من: https://console.groq.com/keys")
    else:
        print("   تأكد من الاتصال بالإنترنت وصحة المفتاح.")
    print("=" * 65)
