from ldap3 import ALL, Connection, Server
from ldap3.core.exceptions import LDAPException

from app.auth.providers.base import AuthenticationError, IdentityProvider
from app.auth.schemas import AuthenticatedSubject
from app.core.config import Settings


class LDAPProvider(IdentityProvider):
    """ATLAS-030 Section 6.1: LDAP / Active Directory provider.

    Uses a service-bind search followed by a direct user bind, so the user's
    password is only ever sent to the directory, never compared locally.
    Plain LDAP (no TLS) is refused outside explicit local-development
    configuration, per Section 6.1.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.ldap_url or not settings.ldap_base_dn:
            raise RuntimeError("LDAP provider requires ldap_url and ldap_base_dn to be configured.")
        if not settings.ldap_use_tls and settings.environment != "development":
            raise RuntimeError("Plain LDAP is prohibited outside an explicitly isolated development environment.")
        self._settings = settings
        self._server = Server(settings.ldap_url, use_ssl=settings.ldap_use_tls, get_info=ALL)

    def authenticate(self, username: str, password: str) -> AuthenticatedSubject:
        settings = self._settings
        try:
            with Connection(
                self._server,
                user=settings.ldap_bind_dn,
                password=settings.ldap_bind_password,
                auto_bind=True,
                receive_timeout=5,
            ) as service_conn:
                search_filter = settings.ldap_user_search_filter.format(username=_escape(username))
                service_conn.search(
                    search_base=settings.ldap_base_dn,
                    search_filter=search_filter,
                    attributes=["cn", "mail"],
                )
                if len(service_conn.entries) != 1:
                    raise AuthenticationError
                entry = service_conn.entries[0]
                user_dn = entry.entry_dn

            with Connection(
                self._server, user=user_dn, password=password, auto_bind=True, receive_timeout=5
            ):
                pass

        except LDAPException as exc:
            raise AuthenticationError from exc

        display_name = str(entry.cn) if "cn" in entry else username
        email = str(entry.mail) if "mail" in entry else None
        return AuthenticatedSubject(
            subject_id=username,
            display_name=display_name,
            email=email,
            identity_source="ldap",
        )


def _escape(value: str) -> str:
    # Minimal LDAP filter metacharacter escaping (RFC 4515).
    replacements = {"\\": r"\5c", "*": r"\2a", "(": r"\28", ")": r"\29", "\x00": r"\00"}
    for char, escaped in replacements.items():
        value = value.replace(char, escaped)
    return value
