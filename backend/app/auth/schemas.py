from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuthenticatedSubject:
    """A normalized identity produced by any provider.

    ATLAS-030 Section 5: "The Authentication Broker normalizes validated
    identity claims. It does not translate a successful login directly into
    permissions." Permission is resolved separately from `subject_id`.
    """

    subject_id: str
    display_name: str
    email: str | None
    identity_source: str  # "local" | "ldap" | "development"
    default_roles: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CurrentSubject:
    """The authenticated caller for the duration of one request."""

    subject_id: str
    display_name: str
    identity_source: str
    permissions: frozenset[str]
    session_id: str
