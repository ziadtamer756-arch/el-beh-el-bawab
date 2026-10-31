from fastapi import APIRouter, HTTPException, status
from app.core.database import get_db
from app.schemas.models import ReviewCreate

router = APIRouter(prefix="/api/reviews", tags=["12. Reviews & Ratings API (تقييمات ومراجعات البواب)"])


@router.get("/{bawab_id}")
def list_bawab_reviews(bawab_id: int = 1):
    """[API #12] عرض تقييمات السكان لخدمة البواب."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT rev.*, r.full_name AS resident_name, r.apartment_number, o.title AS order_title
            FROM reviews rev
            JOIN users r ON r.id = rev.resident_id
            JOIN orders o ON o.id = rev.order_id
            WHERE rev.bawab_id = ?
            ORDER BY rev.created_at DESC;
            """,
            (bawab_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_review(payload: ReviewCreate):
    """إضافة تقييم جديد وتحديث المتوسط العام للبواب."""
    with get_db() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO reviews (order_id, resident_id, bawab_id, rating, comment)
                VALUES (?, ?, ?, ?, ?);
                """,
                (payload.order_id, payload.resident_id, payload.bawab_id, payload.rating, payload.comment),
            )
            stats = conn.execute(
                "SELECT AVG(rating) AS avg_r, COUNT(*) AS cnt FROM reviews WHERE bawab_id = ?;",
                (payload.bawab_id,),
            ).fetchone()
            conn.execute(
                "UPDATE users SET rating_avg = ?, rating_count = ? WHERE id = ?;",
                (round(stats["avg_r"] or 5.0, 2), stats["cnt"], payload.bawab_id),
            )
            row = conn.execute("SELECT * FROM reviews WHERE id = ?;", (cur.lastrowid,)).fetchone()
            return dict(row)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"تعذر إضافة التقييم: {exc}")
