import uuid
from collections.abc import Callable

from sqlalchemy.orm import Session as DbSession

from app.audit.service import record_event
from app.auth.providers.base import AuthenticationError
from app.auth.providers.development import DevelopmentIdentityProvider
from app.auth.providers.ldap import LDAPProvider
from app.auth.providers.local import LocalCredentialProvider
from app.auth.schemas import AuthenticatedSubject
from app.auth.sessions import create_session
from app.core.config import Settings
from app.models.identity import Role, User, UserRole


class AuthenticationBroker:
    """ATLAS-030 Section 5: normalizes provider output into one session model.

    A successful `authenticate()` call never grants permission by itself
    (ADR-003) — it only produces a normalized subject. Role assignment below
    is limited to the provider's own `default_roles`; it does not evaluate
    or grant any additional permission.
    """

    def __init__(self, db: DbSession, settings: Settings) -> None:
        self._db = db
        self._settings = settings

    def login_local(self, username: str, password: str, *, source_ip: str | None) -> tuple[str, User]:
        provider = LocalCredentialProvider(self._db)
        return self._complete(provider.authenticate, username, password, source_ip=source_ip)

    def login_ldap(self, username: str, password: str, *, source_ip: str | None) -> tuple[str, User]:
        provider = LDAPProvider(self._settings)
        return self._complete(provider.authenticate, username, password, source_ip=source_ip)

    def login_development(self, *, source_ip: str | None) -> tuple[str, User]:
        provider = DevelopmentIdentityProvider(self._settings)
        correlation_id = str(uuid.uuid4())
        try:
            subject = provider.issue()
        except AuthenticationError:
            record_event(
                self._db,
                event_type="auth.development.login",
                outcome="denied",
                correlation_id=correlation_id,
                source_ip=source_ip,
            )
            self._db.commit()
            raise
        return self._issue_session(subject, correlation_id=correlation_id, source_ip=source_ip)

    def _complete(
        self,
        authenticate: Callable[[str, str], AuthenticatedSubject],
        username: str,
        password: str,
        *,
        source_ip: str | None,
    ) -> tuple[str, User]:
        correlation_id = str(uuid.uuid4())
        try:
            subject = authenticate(username, password)
        except AuthenticationError:
            record_event(
                self._db,
                event_type="auth.login",
                outcome="failure",
                correlation_id=correlation_id,
                subject_id=username,
                source_ip=source_ip,
            )
            self._db.commit()
            raise
        return self._issue_session(subject, correlation_id=correlation_id, source_ip=source_ip)

    def _issue_session(
        self, subject: AuthenticatedSubject, *, correlation_id: str, source_ip: str | None
    ) -> tuple[str, User]:
        user = self._get_or_provision_user(subject)
        raw_token, _session = create_session(
            self._db, user=user, method=subject.identity_source, settings=self._settings
        )
        record_event(
            self._db,
            event_type="auth.login",
            outcome="success",
            correlation_id=correlation_id,
            subject_id=subject.subject_id,
            source_ip=source_ip,
            detail={"identity_source": subject.identity_source},
        )
        self._db.commit()
        return raw_token, user

    def _get_or_provision_user(self, subject: AuthenticatedSubject) -> User:
        user = (
            self._db.query(User)
            .filter(
                User.subject_id == subject.subject_id,
                User.identity_source == subject.identity_source,
            )
            .one_or_none()
        )
        if user is None:
            user = User(
                subject_id=subject.subject_id,
                display_name=subject.display_name,
                email=subject.email,
                identity_source=subject.identity_source,
            )
            self._db.add(user)
            self._db.flush()
            for role_name in subject.default_roles:
                role = self._db.query(Role).filter(Role.name == role_name).one_or_none()
                if role is not None:
                    self._db.add(UserRole(user_id=user.id, role_id=role.id))
        else:
            user.display_name = subject.display_name
            user.email = subject.email
        return user
