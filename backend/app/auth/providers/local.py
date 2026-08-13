from sqlalchemy.orm import Session

from app.auth.providers.base import AuthenticationError, IdentityProvider
from app.auth.schemas import AuthenticatedSubject
from app.core.security import hash_password, verify_password
from app.models.identity import User

# A well-formed argon2 hash of an unguessable, unused value. Verifying a real
# candidate password against this (rather than against a hand-written string)
# keeps the "no matching account" branch structurally identical to — and
# taking comparable time as — a real verification, without risking a decode
# error that would leak account existence through an exception instead of a
# timing signal.
_DUMMY_HASH = hash_password("atlas-timing-safety-placeholder-3f6c9a1e")


class LocalCredentialProvider(IdentityProvider):
    """Bootstrap and recovery identity provider.

    ATLAS-030 Section 6.3: not the preferred routine enterprise login
    method; exists for initial bootstrap and controlled recovery only.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def authenticate(self, username: str, password: str) -> AuthenticatedSubject:
        user = (
            self._db.query(User)
            .filter(User.subject_id == username, User.identity_source == "local")
            .one_or_none()
        )
        # Deliberately perform the same verify_password call shape whether or
        # not a user was found, so timing does not reveal account existence.
        candidate_hash = (
            user.local_credential.password_hash if user and user.local_credential else None
        )
        if candidate_hash is None:
            verify_password(password, _DUMMY_HASH)
            raise AuthenticationError
        assert user is not None  # candidate_hash is only set when user is not None

        if not user.is_active or not verify_password(password, candidate_hash):
            raise AuthenticationError

        return AuthenticatedSubject(
            subject_id=user.subject_id,
            display_name=user.display_name,
            email=user.email,
            identity_source="local",
        )
