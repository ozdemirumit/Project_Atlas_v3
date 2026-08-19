"""Standalone read-only SAN fabric simulator.

Run with: `uvicorn app.simulators.sanfabric.app:app --port 9101`

This stands in for a vendor SAN fabric manager (e.g. Brocade SAN Nav, Cisco
MDS) so `app.connectors.sanfabric.client` can be developed and tested
without live switch hardware, per ATLAS-020's simulator requirement. It is
read-only by construction — there is no mutation endpoint.
"""
from fastapi import FastAPI, HTTPException

from app.simulators.sanfabric import fixtures

app = FastAPI(title="SAN Fabric Simulator (read-only)")


@app.get("/fabrics")
def list_fabrics() -> list[dict[str, object]]:
    return [fixtures.FABRIC]


@app.get("/fabrics/{fabric_id}/switches")
def list_switches(fabric_id: str) -> list[dict[str, object]]:
    if fabric_id != fixtures.FABRIC["id"]:
        raise HTTPException(status_code=404, detail="Unknown fabric.")
    return fixtures.SWITCHES


@app.get("/switches/{switch_id}/ports")
def list_ports(switch_id: str) -> list[dict[str, object]]:
    ports = [p for p in fixtures.PORTS if p["switch_id"] == switch_id]
    if not ports and switch_id not in {s["id"] for s in fixtures.SWITCHES}:
        raise HTTPException(status_code=404, detail="Unknown switch.")
    return ports


@app.get("/fabrics/{fabric_id}/zones")
def list_zones(fabric_id: str) -> list[dict[str, object]]:
    if fabric_id != fixtures.FABRIC["id"]:
        raise HTTPException(status_code=404, detail="Unknown fabric.")
    return fixtures.ZONES
