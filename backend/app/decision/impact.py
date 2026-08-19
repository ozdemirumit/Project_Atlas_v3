"""Change-impact analysis via inventory graph reachability (ATLAS-044).

MVP must describe this as dependency and scenario analysis, not a validated
digital twin (`docs/002_Product_Requirements.md` Section 10): this walks
`InventoryRelationship` edges from a target entity in both directions
(what it depends on, and what depends on it) up to a bounded depth. It
reports entities it could not classify as a graph gap rather than silently
omitting them, per ATLAS-044's "graph or evidence gaps" requirement.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.inventory import InventoryEntity, InventoryRelationship

_MAX_DEPTH = 4


def assess_impact(db: Session, *, target_entity_id: uuid.UUID) -> dict[str, object]:
    target = db.get(InventoryEntity, target_entity_id)
    if target is None:
        return {"affected_entity_ids": [], "graph_gaps": ["Target entity not found."], "summary": ""}

    visited: set[uuid.UUID] = {target.id}
    frontier: set[uuid.UUID] = {target.id}
    gaps: list[str] = []

    for _ in range(_MAX_DEPTH):
        if not frontier:
            break
        edges = (
            db.query(InventoryRelationship)
            .filter(
                (InventoryRelationship.from_entity_id.in_(frontier))
                | (InventoryRelationship.to_entity_id.in_(frontier))
            )
            .all()
        )
        next_frontier: set[uuid.UUID] = set()
        for edge in edges:
            for candidate in (edge.from_entity_id, edge.to_entity_id):
                if candidate not in visited:
                    next_frontier.add(candidate)
        visited |= next_frontier
        frontier = next_frontier

    affected = visited - {target.id}
    affected_entities = db.query(InventoryEntity).filter(InventoryEntity.id.in_(affected)).all()
    for entity in affected_entities:
        if not entity.attributes:
            gaps.append(f"{entity.entity_type} {entity.display_name} has no recorded attributes.")

    by_type: dict[str, int] = {}
    for entity in affected_entities:
        by_type[entity.entity_type] = by_type.get(entity.entity_type, 0) + 1
    summary_parts = [f"{count} {etype}(s)" for etype, count in sorted(by_type.items())]
    summary = (
        f"{target.entity_type} {target.display_name}: {len(affected_entities)} potentially affected "
        f"entities within {_MAX_DEPTH} relationship hops ({', '.join(summary_parts) or 'none'})."
    )

    return {
        "affected_entity_ids": [str(e.id) for e in affected_entities],
        "graph_gaps": gaps,
        "summary": summary,
    }
