import hashlib
import hmac
import secrets

from passlib.context import CryptContext

# ATLAS-030 Section 6.3: local password verifiers use an approved adaptive
# password-hashing algorithm with a per-credential salt. Argon2 is the
# adaptive algorithm selected here; passlib manages the per-hash salt.
_password_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return str(_password_context.hash(plain_password))


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bool(_password_context.verify(plain_password, password_hash))


def generate_session_token() -> str:
    """Return an unpredictable, high-entropy session token.

    The raw token is only ever sent to the client in the session cookie. Only
    its hash is persisted (see `hash_session_token`), so a database read
    alone cannot forge a valid session.
    """
    return secrets.token_urlsafe(48)


def hash_session_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
