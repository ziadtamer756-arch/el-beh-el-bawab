"""أدوات التعامل مع الفلوس بدقة (Decimal) بدل float لتجنب أخطاء التقريب."""
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def D(value) -> Decimal:
    """تحويل أي رقم (float من SQLite أو int أو str) إلى Decimal بدون أخطاء الفاصلة العائمة."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value if value is not None else 0))


def q(value) -> Decimal:
    """تقريب لأقرب قرش (منزلتين عشريتين)."""
    return D(value).quantize(CENT, rounding=ROUND_HALF_UP)


def f(value) -> float:
    """تحويل لـ float للإرجاع في JSON."""
    return float(q(value))
