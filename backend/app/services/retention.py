"""Retention policy: stored chats/profiles/results are deleted after their expiry date."""
import logging
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import ApplicantProfile, ChatMessage, ChatSession, RecommendationResult

log = logging.getLogger("retention")


def purge_expired(db: Session, now: datetime | None = None) -> dict[str, int]:
    now = now or datetime.utcnow()
    # Explicit child deletes: SQLite does not enforce ON DELETE CASCADE by default.
    sessions = select(ChatSession.id).where(ChatSession.expires_at <= now)
    msgs = db.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(sessions))).rowcount
    sess = db.execute(delete(ChatSession).where(ChatSession.expires_at <= now)).rowcount
    results = db.execute(delete(RecommendationResult).where(RecommendationResult.expires_at <= now)).rowcount
    expired_profiles = select(ApplicantProfile.id).where(ApplicantProfile.expires_at <= now)
    results += db.execute(delete(RecommendationResult).where(
        RecommendationResult.profile_id.in_(expired_profiles))).rowcount
    profiles = db.execute(delete(ApplicantProfile).where(ApplicantProfile.expires_at <= now)).rowcount
    db.commit()
    counts = {"chat_messages": msgs, "chat_sessions": sess, "recommendation_results": results,
              "applicant_profiles": profiles}
    log.info("retention purge", extra={"ctx": counts})
    return counts
