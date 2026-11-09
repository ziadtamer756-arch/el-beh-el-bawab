"""منطق جدولة الأقساط (دوال نقية سهلة الاختبار)."""
import calendar
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Tuple

from app.wallet_ext.money import q


def today() -> date:
    """منفصلة في دالة عشان الاختبارات تقدر تتحكم في التاريخ."""
    return date.today()


def add_months(d: date, months: int) -> date:
    """إضافة شهور مع الحفاظ على اليوم قدر الإمكان (31 يناير + شهر = 28/29 فبراير)."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def default_first_due(frequency: str, start: date) -> date:
    if frequency == "weekly":
        return start + timedelta(days=7)
    if frequency == "biweekly":
        return start + timedelta(days=14)
    return add_months(start, 1)


def due_date_for(first_due: date, frequency: str, index: int) -> date:
    if frequency == "weekly":
        return first_due + timedelta(days=7 * index)
    if frequency == "biweekly":
        return first_due + timedelta(days=14 * index)
    return add_months(first_due, index)


def build_schedule(financed: Decimal, count: int, frequency: str, first_due: date) -> List[Tuple[int, date, Decimal]]:
    """تقسيم المبلغ المموَّل على الأقساط بالقروش بدون فقد ولا زيادة.

    الكسر الناتج عن القسمة بيروح في آخر قسط. مثال: 100 على 3 = 33.33 + 33.33 + 33.34
    """
    cents = int(q(financed) * 100)
    if count < 1 or cents < count:
        raise ValueError("المبلغ صغير جدًا مقارنة بعدد الأقساط")
    base, remainder = divmod(cents, count)
    schedule = []
    for i in range(count):
        c = base + (remainder if i == count - 1 else 0)
        schedule.append((i + 1, due_date_for(first_due, frequency, i), Decimal(c) / 100))
    return schedule
