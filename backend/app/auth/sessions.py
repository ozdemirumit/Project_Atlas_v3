from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session as DbSession

from app.core.config import Settings
from app.core.security import generate_session_token, hash_session_token
from app.models.identity import User
from app.models.session import UserSession


def create_session(db: DbSession, *, user: User, method: str, settings: Settings) -> tuple[str, UserSession]:
    raw_token = generate_session_token()
    now = datetime.now(timezone.utc)
    session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(raw_token),
        authentication_method=method,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(seconds=settings.session_ttl_seconds),
    )
    db.add(session)
    db.flush()
    return raw_token, session


def get_active_session(db: DbSession, raw_token: str) -> UserSession | None:
    token_hash = hash_session_token(raw_token)
    session = db.query(UserSession).filter(UserSession.token_hash == token_hash).one_or_none()
    if session is None:
        return None
    now = datetime.now(timezone.utc)
    if session.revoked_at is not None or session.expires_at <= now:
        return None
    session.last_seen_at = now
    return session


def revoke_session(db: DbSession, raw_token: str) -> None:
    session = get_active_session(db, raw_token)
    if session is not None:
        session.revoked_at = datetime.now(timezone.utc)
