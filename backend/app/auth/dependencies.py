from collections.abc import Callable

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app.auth.schemas import CurrentSubject
from app.auth.sessions import get_active_session
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models.identity import Permission, RolePermission, User, UserRole


def get_current_subject(
    db: DbSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    session_token: str | None = Cookie(default=None, alias="atlas_session"),
) -> CurrentSubject:
    if session_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    session = get_active_session(db, session_token)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    permissions = (
        db.query(Permission.key)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .filter(UserRole.user_id == user.id)
        .distinct()
        .all()
    )
    db.commit()  # persists the session.last_seen_at touch from get_active_session

    return CurrentSubject(
        subject_id=user.subject_id,
        display_name=user.display_name,
        identity_source=user.identity_source,
        permissions=frozenset(p[0] for p in permissions),
        session_id=str(session.id),
    )


def require_permission(permission: str) -> Callable[[CurrentSubject], CurrentSubject]:
    """ATLAS-031: a successful authentication grants no permission by
    itself. This dependency is the single default-deny enforcement point —
    every protected route must declare the exact permission it needs.
    """

    def _check(current: CurrentSubject = Depends(get_current_subject)) -> CurrentSubject:
        if permission not in current.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted.")
        return current

    return _check
