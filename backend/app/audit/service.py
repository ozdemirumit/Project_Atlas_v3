from sqlalchemy.orm import Session

from app.models.audit import AuditEvent

_REDACTED_KEYS = {"password", "password_hash", "token", "token_hash", "secret"}


def _redact(detail: dict[str, object]) -> dict[str, object]:
    return {k: ("<redacted>" if k.lower() in _REDACTED_KEYS else v) for k, v in detail.items()}


def record_event(
    db: Session,
    *,
    event_type: str,
    outcome: str,
    correlation_id: str,
    subject_id: str | None = None,
    source_ip: str | None = None,
    detail: dict[str, object] | None = None,
) -> AuditEvent:
    """Persist one append-only audit event.

    This is the only function permitted to write to `audit_events`. Callers
    must not pass raw passwords, tokens, or secret values in `detail` — this
    function redacts commonly-named secret fields as a backstop, but callers
    are still responsible for not including secret values under other names.
    """
    event = AuditEvent(
        event_type=event_type,
        outcome=outcome,
        correlation_id=correlation_id,
        subject_id=subject_id,
        source_ip=source_ip,
        detail=_redact(detail or {}),
    )
    db.add(event)
    db.flush()
    return event
