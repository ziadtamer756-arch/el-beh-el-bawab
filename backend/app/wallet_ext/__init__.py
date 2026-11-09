"""وحدة المحفظة الآمنة وتقسيط العهدة (حالاً عالنوتة) - البيه البواب.

وحدة مستقلة تمامًا: كل ملفاتها جديدة ولا تعدّل أي ملف موجود في المشروع.
للتفعيل شغّل:  uvicorn app.wallet_main:app --reload
أو أضف سطرين في main.py:
    from app.wallet_ext.setup import install
    install(app)
"""
