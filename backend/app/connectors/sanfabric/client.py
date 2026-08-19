"""Read-only SAN fabric connector client.

ATLAS-020: a connector capability is read-only unless a separate, reviewed
capability class explicitly grants write authority — this client has no
mutating method. It currently targets the bundled simulator
(`app.simulators.sanfabric`); pointing `base_url` at a real vendor API (once
selected — see `docs/002_Product_Requirements.md` Section 16) requires only
a new client with the same `discover()` contract, not a change to the
reconciliation logic in `app.connectors.sanfabric.sync`.
"""
import httpx

from app.connectors.sanfabric.schemas import (
    DiscoveredFabric,
    DiscoveredPort,
    DiscoveredSwitch,
    DiscoveredZone,
    DiscoveryResult,
)


class SanFabricClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """`transport` lets tests bind directly to the simulator's ASGI app
        (`httpx.ASGITransport`) instead of requiring a live listening port.
        """
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._transport = transport

    def discover(self) -> DiscoveryResult:
        with httpx.Client(
            base_url=self._base_url, timeout=self._timeout, transport=self._transport
        ) as http:
            fabrics = http.get("/fabrics").raise_for_status().json()
            if not fabrics:
                raise ConnectionError("SAN fabric target reported no fabrics.")
            fabric_data = fabrics[0]
            fabric = DiscoveredFabric(external_id=fabric_data["id"], name=fabric_data["name"])

            switches_data = http.get(f"/fabrics/{fabric.external_id}/switches").raise_for_status().json()
            switches = tuple(
                DiscoveredSwitch(
                    external_id=s["id"], name=s["name"], wwn=s["wwn"], status=s["status"]
                )
                for s in switches_data
            )

            ports: list[DiscoveredPort] = []
            for switch in switches:
                ports_data = http.get(f"/switches/{switch.external_id}/ports").raise_for_status().json()
                ports.extend(
                    DiscoveredPort(
                        external_id=p["id"],
                        switch_external_id=p["switch_id"],
                        index=p["index"],
                        wwn=p["wwn"],
                        status=p["status"],
                    )
                    for p in ports_data
                )

            zones_data = http.get(f"/fabrics/{fabric.external_id}/zones").raise_for_status().json()
            zones = tuple(
                DiscoveredZone(
                    external_id=z["id"],
                    name=z["name"],
                    member_port_external_ids=tuple(z["member_port_ids"]),
                )
                for z in zones_data
            )

        return DiscoveryResult(fabric=fabric, switches=switches, ports=tuple(ports), zones=zones)
