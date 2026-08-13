from abc import ABC, abstractmethod

from app.auth.schemas import AuthenticatedSubject


class AuthenticationError(Exception):
    """Raised for any failed authentication attempt.

    ATLAS-030 Section 13: invalid credentials return a generic response that
    does not reveal account existence, so this carries no detail beyond a
    fixed, non-specific message.
    """

    def __init__(self) -> None:
        super().__init__("Authentication failed.")


class IdentityProvider(ABC):
    """A pluggable authentication source.

    ATLAS-030 Section 5 / ADR-003: every provider sits behind this same
    port. Adding an enterprise adapter (LDAP today, OIDC later) never
    changes the authorization model or this interface.
    """

    @abstractmethod
    def authenticate(self, username: str, password: str) -> AuthenticatedSubject:
        """Return a normalized subject or raise AuthenticationError."""
        raise NotImplementedError
