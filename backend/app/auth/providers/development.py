from app.auth.providers.base import AuthenticationError, IdentityProvider
from app.auth.schemas import AuthenticatedSubject
from app.core.config import Settings
from app.rbac.permissions import DEVELOPMENT_OPERATOR_ROLE


class DevelopmentIdentityProvider(IdentityProvider):
    """ADR-003: the pre-directory development identity provider.

    Subject, roles, and scope come only from trusted server configuration —
    never from request input. This provider grants a fixed, minimal-scope
    subject (`identity.self.read` only); it is not a bootstrap administrator
    and accepts no username/password.

    `Settings._development_identity_requires_non_production` already fails
    startup if this is enabled with ATLAS_ENVIRONMENT=production; the check
    here is a second, defense-in-depth gate at the point of use.
    """

    FIXED_SUBJECT_ID = "local-operator"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def authenticate(self, username: str, password: str) -> AuthenticatedSubject:
        # No credential this provider accepts is ever valid — it does not
        # authenticate by username/password. Call `issue()` instead.
        raise AuthenticationError

    def issue(self) -> AuthenticatedSubject:
        if self._settings.environment == "production" or not self._settings.enable_development_identity:
            raise AuthenticationError
        return AuthenticatedSubject(
            subject_id=self.FIXED_SUBJECT_ID,
            display_name="Local Operator",
            email=None,
            identity_source="development",
            default_roles=(DEVELOPMENT_OPERATOR_ROLE,),
        )
