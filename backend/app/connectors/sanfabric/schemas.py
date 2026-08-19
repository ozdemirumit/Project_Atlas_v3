from dataclasses import dataclass


@dataclass(frozen=True)
class DiscoveredFabric:
    external_id: str
    name: str


@dataclass(frozen=True)
class DiscoveredSwitch:
    external_id: str
    name: str
    wwn: str
    status: str


@dataclass(frozen=True)
class DiscoveredPort:
    external_id: str
    switch_external_id: str
    index: int
    wwn: str
    status: str


@dataclass(frozen=True)
class DiscoveredZone:
    external_id: str
    name: str
    member_port_external_ids: tuple[str, ...]


@dataclass(frozen=True)
class DiscoveryResult:
    fabric: DiscoveredFabric
    switches: tuple[DiscoveredSwitch, ...]
    ports: tuple[DiscoveredPort, ...]
    zones: tuple[DiscoveredZone, ...]
