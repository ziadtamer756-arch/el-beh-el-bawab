import json
from fastapi import APIRouter, status
from app.core.database import get_db
from app.schemas.models import ChatMessageCreate
from app.ai.ai_agents_engine import run_ai_agent

router = APIRouter(prefix="/api/chat", tags=["13. Resident-Bawab Chat & Voice API (المحادثة الفورية والردود الذكية)"])


@router.get("/{building_id}")
def list_chat_messages(building_id: int = 1):
    """[API #13] جلب رسائل المحادثة بين السكان وعم عبد السميع مع الردود الذكية المقترحة."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT c.*, s.full_name AS sender_name, s.role AS sender_role, s.apartment_number
            FROM chat_messages c
            JOIN users s ON s.id = c.sender_id
            WHERE c.building_id = ?
            ORDER BY c.created_at ASC;
            """,
            (building_id,),
        ).fetchall()
        results = []
        for r in rows:
            item = dict(r)
            try:
                item["quick_replies"] = json.loads(item["ai_quick_replies"] or "[]")
            except Exception:
                item["quick_replies"] = []
            results.append(item)
        return results


@router.post("", status_code=status.HTTP_201_CREATED)
def send_chat_message(payload: ChatMessageCreate):
    """إرسال رسالة نصية أو صوتية وتوليد ٣ ردود ذكية تلقائياً عبر AI Agent #11."""
    ai_res = run_ai_agent("agent_11_voice_chat_assistant", payload.message_text, payload.building_id)
    quick_replies = ai_res.get("structured_data", {}).get("Quick_Replies", ["حاضر يا فندم", "تمام فوراً", "تسلم"])
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO chat_messages (building_id, sender_id, receiver_id, message_text, is_voice_note, ai_quick_replies)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                payload.building_id,
                payload.sender_id,
                payload.receiver_id,
                payload.message_text,
                int(payload.is_voice_note),
                json.dumps(quick_replies, ensure_ascii=False),
            ),
        )
        row = conn.execute("SELECT * FROM chat_messages WHERE id = ?;", (cur.lastrowid,)).fetchone()
        return dict(row)
