"""التحقق من التوكن والصلاحيات (يُطبَّق على راوترات المحفظة والتقسيط فقط)."""
from typing import Optional

from fastapi import Depends, Header, HTTPException

from app.core.database import get_db
from app.core.security import verify_access_token
from app.wallet_ext.schema import ensure_schema

STAFF_ROLES = ("bawab", "admin")


def ensure_ready() -> None:
    ensure_schema()


def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """يرجع بيانات المستخدم الحالية من قاعدة البيانات (الدور والعمارة من القاعدة مش من التوكن)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="يرجى إرسال Bearer Token")
    claims = verify_access_token(authorization.split(" ", 1)[1].strip())
    if not claims or "sub" not in claims:
        raise HTTPException(status_code=401, detail="التوكن غير صالح أو منتهي")
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?;", (claims["sub"],)).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="المستخدم غير موجود")
    return dict(row)


def require_roles(*roles: str):
    def _dep(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="ليس لديك صلاحية لهذه العملية")
        return user

    return _dep


def is_staff(user: dict) -> bool:
    return user["role"] in STAFF_ROLES


def load_user(conn, user_id: int) -> dict:
    row = conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return dict(row)


def assert_same_building(caller: dict, target: dict) -> None:
    if caller["building_id"] != target["building_id"]:
        raise HTTPException(status_code=403, detail="هذا المستخدم ينتمي لعمارة أخرى")


def assert_can_access_user(caller: dict, target: dict) -> None:
    """الساكن يصل لبياناته فقط، والبواب/الأدمن لكل سكان عمارتهم."""
    assert_same_building(caller, target)
    if caller["id"] != target["id"] and not is_staff(caller):
        raise HTTPException(status_code=403, detail="لا يمكنك الاطلاع على بيانات مستخدم آخر")
