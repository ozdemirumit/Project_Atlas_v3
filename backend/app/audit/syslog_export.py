"""RFC 5424 syslog formatting for audit events (ATLAS-034 / ATLAS-035).

MVP-004 requires "Syslog or SIEM security-event export." No SIEM product is
selected yet (open question, `docs/002_Product_Requirements.md` Section
16), so this implements the export *format* plus an optional UDP forwarder
gated by configuration — pointing it at a real syslog/SIEM collector later
needs no code change, only `ATLAS_SYSLOG_HOST`/`ATLAS_SYSLOG_PORT`.
"""
import socket
from datetime import timezone

from app.models.audit import AuditEvent

_FACILITY_LOCAL0 = 16
_SEVERITY_INFO = 6
_SEVERITY_WARNING = 4


def _severity(outcome: str) -> int:
    return _SEVERITY_INFO if outcome == "success" else _SEVERITY_WARNING


def format_syslog(event: AuditEvent, *, hostname: str = "atlas") -> str:
    priority = _FACILITY_LOCAL0 * 8 + _severity(event.outcome)
    timestamp = event.occurred_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    subject = event.subject_id or "-"
    structured_data = (
        f'[atlas@0 event_type="{event.event_type}" outcome="{event.outcome}" '
        f'subject_id="{subject}" correlation_id="{event.correlation_id}"]'
    )
    return f"<{priority}>1 {timestamp} {hostname} atlas - {event.correlation_id} {structured_data}"


def send_udp(events: list[AuditEvent], *, host: str, port: int, hostname: str = "atlas") -> int:
    """Best-effort UDP syslog send. Returns the number of messages sent.

    Syslog-over-UDP is inherently unreliable delivery — callers must treat
    this as a forwarding convenience, not a durable audit trail. The
    database `audit_events` table remains the canonical record.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sent = 0
        for event in events:
            message = format_syslog(event, hostname=hostname).encode("utf-8")
            sock.sendto(message, (host, port))
            sent += 1
        return sent
    finally:
        sock.close()
