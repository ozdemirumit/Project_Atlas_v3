from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.broker import AuthenticationBroker
from app.auth.dependencies import get_current_subject
from app.auth.providers.base import AuthenticationError
from app.auth.schemas import CurrentSubject
from app.auth.sessions import revoke_session
from app.core.config import Settings, get_settings
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str
    model_config = {"extra": "forbid"}


class CurrentSubjectResponse(BaseModel):
    subject_id: str
    display_name: str
    identity_source: str
    permissions: list[str]


def _set_session_cookie(response: Response, raw_token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        # "test" is the automated-test execution context (ADR-003) and, like
        # "development", runs over plain HTTP — a Secure cookie there would
        # be silently dropped by any HTTP client, breaking every session.
        secure=settings.environment == "production",
        samesite="lax",
        path="/",
    )


@router.post("/login/local", status_code=status.HTTP_204_NO_CONTENT)
def login_local(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    broker = AuthenticationBroker(db, settings)
    try:
        raw_token, _user = broker.login_local(
            payload.username, payload.password, source_ip=request.client.host if request.client else None
        )
    except AuthenticationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    _set_session_cookie(response, raw_token, settings)


@router.post("/login/ldap", status_code=status.HTTP_204_NO_CONTENT)
def login_ldap(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    broker = AuthenticationBroker(db, settings)
    try:
        raw_token, _user = broker.login_ldap(
            payload.username, payload.password, source_ip=request.client.host if request.client else None
        )
    except AuthenticationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    _set_session_cookie(response, raw_token, settings)


@router.post("/login/development", status_code=status.HTTP_204_NO_CONTENT)
def login_development(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    """ADR-003: only reachable when ATLAS_ENABLE_DEVELOPMENT_IDENTITY=true
    and ATLAS_ENVIRONMENT is development or test."""
    if settings.environment == "production" or not settings.enable_development_identity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    broker = AuthenticationBroker(db, settings)
    try:
        raw_token, _user = broker.login_development(
            source_ip=request.client.host if request.client else None
        )
    except AuthenticationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Development identity unavailable.")
    _set_session_cookie(response, raw_token, settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> None:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if raw_token:
        revoke_session(db, raw_token)
        db.commit()
    response.delete_cookie(settings.session_cookie_name, path="/")


@router.get("/me", response_model=CurrentSubjectResponse)
def read_current_subject(current: CurrentSubject = Depends(get_current_subject)) -> CurrentSubjectResponse:
    return CurrentSubjectResponse(
        subject_id=current.subject_id,
        display_name=current.display_name,
        identity_source=current.identity_source,
        permissions=sorted(current.permissions),
    )
