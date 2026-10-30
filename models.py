from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


OrderCategory = Literal[
    "groceries",
    "pharmacy",
    "errand",
    "cleaning",
    "car_wash",
    "plumbing_electrical",
    "luggage_help",
    "other",
]

OrderUrgency = Literal["normal", "urgent", "scheduled"]
OrderStatus = Literal["pending", "accepted", "in_progress", "delivered", "cancelled"]
PaymentMethod = Literal["cash", "instapay", "wallet"]
UserRole = Literal["resident", "bawab", "admin"]
TransactionType = Literal["tip", "reimbursement", "topup", "maintenance_fee", "settlement"]


class LoginRequest(BaseModel):
    phone: str = Field(..., examples=["01000000002"])
    invite_code: str = Field(default="NILE-15", examples=["NILE-15"])
    otp_code: str = Field(default="1234", examples=["1234"])


class BuildingCreate(BaseModel):
    name: str = Field(..., examples=["عمارة الزمالك الشرقية"])
    address: str = Field(..., examples=["٢٢ شارع البرازيل - الزمالك"])
    city: str = Field(default="القاهرة")
    invite_code: str = Field(..., examples=["ZAMALEK-22"])
    floors_count: int = Field(default=10, ge=1)
    monthly_maintenance_fee: float = Field(default=300.0, ge=0)


class UserCreate(BaseModel):
    full_name: str = Field(..., examples=["محمد إبراهيم"])
    phone: str = Field(..., examples=["01012345678"])
    role: UserRole = Field(default="resident")
    building_id: int = Field(default=1, examples=[1])
    apartment_number: Optional[str] = Field(default=None, examples=["شقة 8"])
    floor_number: Optional[int] = Field(default=None, examples=[3])


class OrderCreate(BaseModel):
    building_id: int = Field(default=1, examples=[1])
    resident_id: int = Field(..., examples=[2])
    category: OrderCategory = Field(default="groceries")
    title: str = Field(..., examples=["طلبات من السوبرماركت"])
    details: str = Field(..., examples=["٢ كيلو سكر + شاي العروسة + زجاجة زيت"])
    urgency: OrderUrgency = Field(default="normal")
    scheduled_time: Optional[str] = Field(default=None, examples=["09:00 صباحاً"])
    estimated_items_cost: float = Field(default=0.0, ge=0)
    service_tip: float = Field(default=15.0, ge=0)
    payment_method: PaymentMethod = Field(default="cash")
    notes: Optional[str] = Field(default=None, examples=["رن الجرس مرة واحدة"])


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    bawab_id: Optional[int] = None
    actual_items_cost: Optional[float] = Field(default=None, ge=0)
    is_paid: Optional[bool] = None
    notes: Optional[str] = None


class AnnouncementCreate(BaseModel):
    building_id: int = Field(default=1, examples=[1])
    author_id: int = Field(default=1, examples=[1])
    title: str = Field(..., examples=["تحصيل صيانة الشهر"])
    content: str = Field(..., examples=["يرجى سداد اشتراك الصيانة الشهري مع عم عبد السميع."])
    priority: str = Field(default="normal")
    is_pinned: bool = Field(default=False)


class WalletTransactionCreate(BaseModel):
    building_id: int = Field(default=1)
    user_id: int = Field(..., examples=[1])
    order_id: Optional[int] = Field(default=None)
    tx_type: TransactionType = Field(default="tip")
    amount: float = Field(..., gt=0)
    payment_method: PaymentMethod = Field(default="instapay")
    description: str = Field(..., examples=["إكرامية توصيل طلبات سوبرماركت"])


class ReviewCreate(BaseModel):
    order_id: int = Field(..., examples=[4])
    resident_id: int = Field(..., examples=[4])
    bawab_id: int = Field(default=1, examples=[1])
    rating: int = Field(..., ge=1, le=5, examples=[5])
    comment: Optional[str] = Field(default="", examples=["خدمة ممتازة وسريعة جداً يا عم عبد السميع"])


class MaintenanceTicketCreate(BaseModel):
    building_id: int = Field(default=1)
    resident_id: int = Field(default=2)
    specialty: Literal["plumbing", "electrical", "carpentry", "gas", "elevator", "satellite_internet", "ac"] = "plumbing"
    issue_title: str = Field(..., examples=["تسريب في حوض المطبخ"])
    description: str = Field(..., examples=["المحبس البارد بينقط باستمرار"])
    urgency: str = Field(default="urgent")
    estimated_cost: float = Field(default=150.0)


class VisitorPassCreate(BaseModel):
    building_id: int = Field(default=1)
    resident_id: int = Field(default=2)
    visitor_name: str = Field(..., examples=["مندوب طلبات"])
    visitor_type: Literal["guest", "delivery", "technician", "broker"] = "delivery"
    expected_time: str = Field(default="خلال ٣٠ دقيقة")
    notes: Optional[str] = Field(default="اسمح له بالصعود للدور الرابع")


class ParcelCreate(BaseModel):
    building_id: int = Field(default=1)
    resident_id: int = Field(default=2)
    bawab_id: int = Field(default=1)
    courier_name: str = Field(..., examples=["أمازون مصر"])
    tracking_Or_desc: str = Field(..., examples=["طرد ملابس - شقة 12"])
    cod_amount: float = Field(default=0.0, ge=0)
    paid_by_bawab: bool = Field(default=False)


class VehicleCreate(BaseModel):
    building_id: int = Field(default=1)
    resident_id: int = Field(default=2)
    car_model: str = Field(..., examples=["نيسان صني كحلي"])
    plate_number: str = Field(..., examples=["م ن هـ ٢٣٤١"])
    parking_spot: str = Field(default="باكية 7")
    wash_schedule: str = Field(default="الأحد والأربعاء ٧:٣٠ ص")
    key_with_bawab: bool = Field(default=True)


class UtilityBillCreate(BaseModel):
    building_id: int = Field(default=1)
    utility_type: Literal["water_shared", "elevator_electricity", "stairs_cleaning", "gas_cylinder", "garbage_collection"] = "water_shared"
    month_label: str = Field(..., examples=["نوفمبر ٢٠٢٦ - فاتورة المياه"])
    total_amount: float = Field(..., gt=0)
    apartments_count: int = Field(default=24, ge=1)


class ChatMessageCreate(BaseModel):
    building_id: int = Field(default=1)
    sender_id: int = Field(default=2)
    receiver_id: int = Field(default=1)
    message_text: str = Field(..., examples=["عم عبد السميع هاتلي عيش سخن وأنت طالع"])
    is_voice_note: bool = Field(default=False)


class EmergencySOSCreate(BaseModel):
    building_id: int = Field(default=1)
    reporter_id: int = Field(default=2)
    emergency_type: Literal["elevator_stuck", "gas_leak", "water_burst", "medical_help", "security_alert"] = "elevator_stuck"
    apartment_or_location: str = Field(..., examples=["الأسانسير بالدور الرابع"])


class AIAgentInvokeRequest(BaseModel):
    agent_id: str = Field(..., examples=["agent_01_order_parser"])
    prompt: str = Field(..., examples=["عايز ٢ لبن جهينة وكرتونة بيض وعيش سخن بسرعة"])
    building_id: int = Field(default=1)
    context: Optional[Dict[str, Any]] = Field(default=None)
