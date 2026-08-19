"""Scheduled connector health checks (MVP-002).

Each enabled connector instance is checked on an interval
(`Settings.health_check_interval_seconds`). A "check" is intentionally
lightweight and read-only — for the SAN fabric domain it is a single
`/fabrics` request against the target, not a full discovery/reconcile run.
"""
import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable

import httpx

from app.audit.service import record_event
from app.core.database import SessionLocal
from app.models.connector_health import ConnectorHealthCheck
from app.models.inventory import ConnectorInstance

HealthProbe = Callable[[ConnectorInstance], Awaitable[dict[str, object]]]


async def _probe_san_fabric(instance: ConnectorInstance) -> dict[str, object]:
    async with httpx.AsyncClient(base_url=instance.target_base_url, timeout=5.0) as http:
        response = await http.get("/fabrics")
        response.raise_for_status()
        return {"fabric_count": len(response.json())}


_PROBES: dict[str, HealthProbe] = {
    "san_fabric": _probe_san_fabric,
}


async def check_instance(instance: ConnectorInstance) -> None:
    probe = _PROBES.get(instance.domain)
    if probe is None:
        return

    started = time.monotonic()
    try:
        detail = await probe(instance)
        status = "healthy"
    except Exception as exc:
        detail = {"error": str(exc)}
        status = "unhealthy"
    latency_ms = int((time.monotonic() - started) * 1000)

    db = SessionLocal()
    try:
        db.add(
            ConnectorHealthCheck(
                connector_instance_id=instance.id,
                status=status,
                latency_ms=latency_ms,
                detail=detail,
            )
        )
        if status == "unhealthy":
            record_event(
                db,
                event_type="connector.health_check",
                outcome="failure",
                correlation_id=str(uuid.uuid4()),
                detail={"connector_instance_key": instance.key, **detail},
            )
        db.commit()
    finally:
        db.close()


async def run_all_enabled() -> None:
    db = SessionLocal()
    try:
        instances = db.query(ConnectorInstance).filter(ConnectorInstance.is_enabled.is_(True)).all()
    finally:
        db.close()
    for instance in instances:
        await check_instance(instance)


async def run_forever(interval_seconds: float) -> None:
    while True:
        try:
            await run_all_enabled()
        except Exception:
            pass  # a scheduler-loop failure must not stop future checks
        await asyncio.sleep(interval_seconds)
