import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.audit.service import record_event
from app.auth.dependencies import require_permission
from app.auth.schemas import CurrentSubject
from app.connectors.sanfabric.client import SanFabricClient
from app.connectors.sanfabric.sync import reconcile
from app.core.database import get_db
from app.models.connector_health import ConnectorHealthCheck
from app.models.inventory import ConnectorInstance, InventoryEntity, InventoryRelationship
from app.rbac.permissions import CONNECTOR_HEALTH_READ, CONNECTOR_SYNC, INVENTORY_READ

router = APIRouter(tags=["inventory"])


class ConnectorHealthCheckResponse(BaseModel):
    id: uuid.UUID
    connector_instance_id: uuid.UUID
    checked_at: datetime
    status: str
    latency_ms: int
    detail: dict[str, object]

    model_config = {"from_attributes": True}


class InventoryEntityResponse(BaseModel):
    id: uuid.UUID
    connector_instance_id: uuid.UUID
    entity_type: str
    external_id: str
    display_name: str
    attributes: dict[str, object]
    last_observed_at: datetime

    model_config = {"from_attributes": True}


class InventoryRelationshipResponse(BaseModel):
    id: uuid.UUID
    from_entity_id: uuid.UUID
    to_entity_id: uuid.UUID
    relationship_type: str

    model_config = {"from_attributes": True}


class SyncResult(BaseModel):
    connector_instance_key: str
    entities_written: int
    relationships_written: int


@router.get("/inventory/entities", response_model=list[InventoryEntityResponse])
def list_entities(
    db: Session = Depends(get_db),
    _current: CurrentSubject = Depends(require_permission(INVENTORY_READ)),
) -> list[InventoryEntity]:
    return db.query(InventoryEntity).order_by(InventoryEntity.entity_type, InventoryEntity.display_name).all()


@router.get("/inventory/relationships", response_model=list[InventoryRelationshipResponse])
def list_relationships(
    db: Session = Depends(get_db),
    _current: CurrentSubject = Depends(require_permission(INVENTORY_READ)),
) -> list[InventoryRelationship]:
    return db.query(InventoryRelationship).all()


@router.post("/connectors/{connector_key}/sync", response_model=SyncResult)
def sync_connector(
    connector_key: str,
    db: Session = Depends(get_db),
    current: CurrentSubject = Depends(require_permission(CONNECTOR_SYNC)),
) -> SyncResult:
    instance = db.query(ConnectorInstance).filter(ConnectorInstance.key == connector_key).one_or_none()
    if instance is None or not instance.is_enabled:
        raise HTTPException(status_code=404, detail="Unknown or disabled connector.")

    correlation_id = str(uuid.uuid4())
    try:
        client = SanFabricClient(base_url=instance.target_base_url)
        result = client.discover()
        counts = reconcile(db, instance=instance, result=result)
    except Exception as exc:
        record_event(
            db,
            event_type="connector.sync",
            outcome="failure",
            correlation_id=correlation_id,
            subject_id=current.subject_id,
            detail={"connector_instance_key": connector_key, "error": str(exc)},
        )
        db.commit()
        raise HTTPException(status_code=502, detail="Connector discovery failed.") from exc

    record_event(
        db,
        event_type="connector.sync",
        outcome="success",
        correlation_id=correlation_id,
        subject_id=current.subject_id,
        detail={"connector_instance_key": connector_key, **counts},
    )
    db.commit()
    return SyncResult(connector_instance_key=connector_key, **counts)


@router.get("/connectors/{connector_key}/health-checks", response_model=list[ConnectorHealthCheckResponse])
def list_health_checks(
    connector_key: str,
    db: Session = Depends(get_db),
    limit: int = 20,
    _current: CurrentSubject = Depends(require_permission(CONNECTOR_HEALTH_READ)),
) -> list[ConnectorHealthCheck]:
    instance = db.query(ConnectorInstance).filter(ConnectorInstance.key == connector_key).one_or_none()
    if instance is None:
        raise HTTPException(status_code=404, detail="Unknown connector.")
    checks: list[ConnectorHealthCheck] = (
        db.query(ConnectorHealthCheck)
        .filter(ConnectorHealthCheck.connector_instance_id == instance.id)
        .order_by(ConnectorHealthCheck.checked_at.desc())
        .limit(limit)
        .all()
    )
    return checks
