from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration.

    Values are supplied through environment variables or a local `.env` file
    (see `.env.example`). Nothing here is a client-controlled identity input.
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ATLAS_", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"

    database_url: str = "postgresql+psycopg://atlas3:atlas3@localhost:5432/atlas3"

    session_secret: str = "change-me-in-every-non-development-environment"
    session_ttl_seconds: int = 60 * 60 * 8
    session_cookie_name: str = "atlas3_session"

    # ADR-003: development identity provider. Disabled by default; can only be
    # honored in development/test. See app.auth.providers.development.
    enable_development_identity: bool = False

    # ATLAS-030 Section 6.1: LDAP/Active Directory provider (optional; unset
    # means the LDAP provider is inactive).
    ldap_url: str | None = None
    ldap_base_dn: str | None = None
    ldap_bind_dn: str | None = None
    ldap_bind_password: str | None = None
    ldap_user_search_filter: str = "(uid={username})"
    ldap_use_tls: bool = True

    # MVP-002: scheduled connector health checks. 0 disables the scheduler
    # (useful for tests, which drive checks explicitly).
    health_check_interval_seconds: float = 300.0

    @model_validator(mode="after")
    def _development_identity_requires_non_production(self) -> "Settings":
        # ADR-003: enabling the development identity provider in production is
        # a configuration error that must prevent startup, not a soft warning.
        if self.enable_development_identity and self.environment == "production":
            raise ValueError(
                "ATLAS_ENABLE_DEVELOPMENT_IDENTITY must not be true when "
                "ATLAS_ENVIRONMENT=production (ADR-003)."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
