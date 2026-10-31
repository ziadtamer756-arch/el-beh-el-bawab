import base64
import hashlib
import hmac
import json
import time
from typing import Optional, Dict, Any
from app.core.config import SECRET_KEY


def create_access_token(data: Dict[str, Any], expires_in_seconds: int = 86400 * 14) -> str:
    """إنشاء توكن مصادقة موقع (HMAC-SHA256 Token) لتطبيق الموبايل والويب."""
    payload = dict(data)
    payload["exp"] = int(time.time()) + expires_in_seconds
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        b64_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{b64_payload}.{signature}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """التحقق من صحة التوكن وتاريخ الصلاحية."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        b64_payload, signature = parts
        expected_sig = hmac.new(
            SECRET_KEY.encode("utf-8"),
            b64_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        padding = "=" * (-len(b64_payload) % 4)
        payload_json = base64.urlsafe_b64decode(b64_payload + padding).decode("utf-8")
        payload = json.loads(payload_json)
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None
