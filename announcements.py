from fastapi import APIRouter, status
from app.core.database import get_db
from app.schemas.models import AnnouncementCreate

router = APIRouter(prefix="/api/announcements", tags=["11. Building Announcements API (لوحة إعلانات العمارة)"])


@router.get("/{building_id}")
def list_building_announcements(building_id: int = 1):
    """[API #11] عرض إعلانات وتنبيهات العمارة."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT a.*, u.full_name AS author_name, u.role AS author_role
            FROM announcements a
            JOIN users u ON u.id = a.author_id
            WHERE a.building_id = ?
            ORDER BY a.is_pinned DESC, a.created_at DESC;
            """,
            (building_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def publish_announcement(payload: AnnouncementCreate):
    """نشر إعلان أو تنبيه جديد لسكان العمارة."""
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO announcements (building_id, author_id, title, content, priority, is_pinned)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (payload.building_id, payload.author_id, payload.title, payload.content, payload.priority, int(payload.is_pinned)),
        )
        row = conn.execute("SELECT * FROM announcements WHERE id = ?;", (cur.lastrowid,)).fetchone()
        return dict(row)
