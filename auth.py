from fastapi import APIRouter, HTTPException, Header, status
from typing import Optional
from app.core.database import get_db
from app.core.security import create_access_token, verify_access_token
from app.schemas.models import LoginRequest, UserCreate

router = APIRouter(prefix="/api/auth", tags=["01. Authentication API (المصادقة وتسجيل الدخول)"])


@router.post("/login")
def login_with_phone_and_invite_code(payload: LoginRequest):
    """[API #1] تسجيل دخول الساكن أو البواب برقم الموبايل وكود العمارة ورمز التحقق."""
    with get_db() as conn:
        building = conn.execute(
            "SELECT * FROM buildings WHERE UPPER(invite_code) = UPPER(?);",
            (payload.invite_code.strip(),),
        ).fetchone()
        if not building:
            raise HTTPException(status_code=404, detail="كود العمارة غير صحيح (جرب NILE-15)")

        user = conn.execute(
            "SELECT * FROM users WHERE phone = ? AND building_id = ?;",
            (payload.phone.strip(), building["id"]),
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="رقم الهاتف غير مسجل في هذه العمارة")

        if payload.otp_code != (user["otp_code"] or "1234"):
            raise HTTPException(status_code=401, detail="رمز التحقق OTP غير صحيح (استخدم 1234)")

        token = create_access_token({
            "sub": user["id"],
            "phone": user["phone"],
            "role": user["role"],
            "building_id": user["building_id"],
        })
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": dict(user),
            "building": dict(building),
        }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_and_login(payload: UserCreate, invite_code: str = "NILE-15"):
    """إنشاء حساب ساكن جديد بكود العمارة وتسجيل الدخول فوراً."""
    with get_db() as conn:
        building = conn.execute(
            "SELECT * FROM buildings WHERE UPPER(invite_code) = UPPER(?);",
            (invite_code.strip(),),
        ).fetchone()
        b_id = building["id"] if building else payload.building_id
        try:
            cur = conn.execute(
                """
                INSERT INTO users (full_name, phone, role, building_id, apartment_number, floor_number)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (payload.full_name, payload.phone.strip(), payload.role, b_id, payload.apartment_number, payload.floor_number),
            )
            user = conn.execute("SELECT * FROM users WHERE id = ?;", (cur.lastrowid,)).fetchone()
            token = create_access_token({"sub": user["id"], "phone": user["phone"], "role": user["role"], "building_id": b_id})
            return {"access_token": token, "token_type": "bearer", "user": dict(user)}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"تعذر تسجيل الحساب: {exc}")


@router.get("/me")
def get_current_user_profile(authorization: Optional[str] = Header(default=None)):
    """جلب بيانات المستخدم الحالي من التوكن."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="يرجى إرسال Bearer Token")
    claims = verify_access_token(authorization.split(" ", 1)[1].strip())
    if not claims:
        raise HTTPException(status_code=401, detail="التوكن غير صالح")
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?;", (claims["sub"],)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
        return dict(user)
