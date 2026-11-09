"""نماذج الإدخال (Pydantic) للمحفظة والتقسيط."""
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field

# مبلغ موجب بحد أقصى منزلتين عشريتين
Money = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2, examples=[150.5])]
MoneyOrZero = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2, examples=[0])]

PayMethod = Literal["cash", "instapay", "wallet"]
TxType = Literal["tip", "reimbursement", "topup", "maintenance_fee", "settlement"]
Frequency = Literal["weekly", "biweekly", "monthly"]


class TopupRequest(BaseModel):
    amount: Money
    payment_method: Literal["cash", "instapay"] = Field(
        default="instapay", description="وسيلة الشحن (محاكاة - لا توجد بوابة دفع حقيقية)"
    )
    user_id: Optional[int] = Field(default=None, description="للبواب/الأدمن فقط: شحن محفظة ساكن بعد استلام فلوسه")


class TransactionRequest(BaseModel):
    tx_type: TxType
    amount: Money
    payment_method: PayMethod = "wallet"
    description: str = Field(..., min_length=3, max_length=200, examples=["إكرامية توصيل الطلبات"])
    resident_id: Optional[int] = Field(default=None, description="للبواب/الأدمن: الساكن صاحب العملية")
    bawab_id: Optional[int] = Field(default=None, description="البواب المستلم (اختياري)")
    order_id: Optional[int] = None


class PlanCreate(BaseModel):
    resident_id: int = Field(..., examples=[2])
    order_id: Optional[int] = Field(default=None, description="الطلب المرتبط بالعهدة (اختياري)")
    total_amount: Money
    down_payment: MoneyOrZero = Decimal("0")
    down_payment_method: PayMethod = "cash"
    installments_count: int = Field(..., ge=1, le=12, examples=[3])
    frequency: Frequency = "monthly"
    start_date: Optional[date] = Field(default=None, description="تاريخ أول قسط (الافتراضي: بعد فترة واحدة من اليوم)")
    notes: Optional[str] = Field(default=None, max_length=300)


class PayRequest(BaseModel):
    amount: Money
    payment_method: PayMethod = "wallet"
    installment_id: Optional[int] = Field(default=None, description="قسط محدد، وإلا يتم السداد من الأقدم للأحدث")
