"""Fixed, synthetic SAN fabric data for the MVP-002 connector simulator.

ATLAS-020 Section 6 ("MCP Framework") requires every connector to have a
simulator target so it can be exercised without live infrastructure. This
fixture is intentionally vendor-neutral: MVP-002's real SAN switch vendor
(Brocade, Cisco MDS, etc.) is still an open product decision
(`docs/002_Product_Requirements.md` Section 16). The connector and its
normalization logic are written against this generic port/zone/fabric shape
so swapping in a real vendor client later only requires a new client module,
not a new inventory model.
"""

FABRIC: dict[str, object] = {"id": "fab-01", "name": "Fabric A"}

SWITCHES: list[dict[str, object]] = [
    {"id": "sw-01", "name": "edge-switch-01", "wwn": "10:00:00:05:1e:0a:00:01", "status": "ok"},
    {"id": "sw-02", "name": "edge-switch-02", "wwn": "10:00:00:05:1e:0a:00:02", "status": "ok"},
]

PORTS: list[dict[str, object]] = [
    {"id": "sw-01-p1", "switch_id": "sw-01", "index": 1, "wwn": "20:01:00:05:1e:0a:00:01", "status": "online"},
    {"id": "sw-01-p2", "switch_id": "sw-01", "index": 2, "wwn": "20:02:00:05:1e:0a:00:01", "status": "online"},
    {"id": "sw-01-p3", "switch_id": "sw-01", "index": 3, "wwn": "20:03:00:05:1e:0a:00:01", "status": "offline"},
    {"id": "sw-02-p1", "switch_id": "sw-02", "index": 1, "wwn": "20:01:00:05:1e:0a:00:02", "status": "online"},
    {"id": "sw-02-p2", "switch_id": "sw-02", "index": 2, "wwn": "20:02:00:05:1e:0a:00:02", "status": "online"},
]

ZONES: list[dict[str, object]] = [
    {"id": "zone-prod-storage-01", "name": "prod_storage_01", "member_port_ids": ["sw-01-p1", "sw-02-p1"]},
    {"id": "zone-backup-01", "name": "backup_01", "member_port_ids": ["sw-01-p2", "sw-02-p2"]},
]
