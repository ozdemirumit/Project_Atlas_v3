import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.service import record_event
from app.auth.dependencies import require_permission
from app.auth.schemas import CurrentSubject
from app.core.database import get_db
from app.decision.impact import assess_impact
from app.decision.rca import generate_hypotheses
from app.decision.recommendation import draft_recommendation
from app.guardrails.dlp import find_violations
from app.models.governance import RecommendationApproval
from app.models.investigation import (
    ChangeImpactAssessment,
    Investigation,
    InvestigationEvent,
    RcaHypothesis,
    Recommendation,
)
from app.rbac.permissions import APPROVAL_DECIDE, INVESTIGATION_READ, INVESTIGATION_WRITE

router = APIRouter(prefix="/investigations", tags=["investigations"])


class CreateInvestigationRequest(BaseModel):
    key: str
    title: str
    model_config = {"extra": "forbid"}


class InvestigationResponse(BaseModel):
    id: uuid.UUID
    key: str
    title: str
    status: str
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AddEventRequest(BaseModel):
    event_type: str
    description: str
    related_entity_id: uuid.UUID | None = None
    model_config = {"extra": "forbid"}


class EventResponse(BaseModel):
    id: uuid.UUID
    occurred_at: datetime
    event_type: str
    description: str
    related_entity_id: uuid.UUID | None
    source: str

    model_config = {"from_attributes": True}


class GenerateHypothesesRequest(BaseModel):
    target_entity_id: uuid.UUID
    model_config = {"extra": "forbid"}


class HypothesisResponse(BaseModel):
    id: uuid.UUID
    fault_family: str
    description: str
    confidence: str
    supporting_evidence: list[str]
    contradicting_evidence: list[str]
    status: str
    generated_by: str

    model_config = {"from_attributes": True}


class UpdateHypothesisRequest(BaseModel):
    status: str
    model_config = {"extra": "forbid"}


class AssessImpactRequest(BaseModel):
    target_entity_id: uuid.UUID
    model_config = {"extra": "forbid"}


class ImpactResponse(BaseModel):
    id: uuid.UUID
    target_entity_id: uuid.UUID
    affected_entity_ids: list[str]
    graph_gaps: list[str]
    summary: str

    model_config = {"from_attributes": True}


class DraftRecommendationRequest(BaseModel):
    hypothesis_id: uuid.UUID
    model_config = {"extra": "forbid"}


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    title: str
    summary: str
    risk_level: str
    estimated_duration_minutes: int
    preconditions: list[str]
    rollback_plan: str
    status: str
    generated_by: str

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    investigation: InvestigationResponse
    events: list[EventResponse]
    hypotheses: list[HypothesisResponse]
    impact_assessments: list[ImpactResponse]
    recommendations: list[RecommendationResponse]


def _get_investigation_or_404(db: Session, key: str) -> Investigation:
    investigation = db.query(Investigation).filter(Investigation.key == key).one_or_none()
    if investigation is None:
        raise HTTPException(status_code=404, detail="Unknown investigation.")
    return investigation


@router.post("", response_model=InvestigationResponse, status_code=201)
def create_investigation(
    payload: CreateInvestigationRequest,
    db: Session = Depends(get_db),
    current: CurrentSubject = Depends(require_permission(INVESTIGATION_WRITE)),
) -> Investigation:
    try:
        investigation = Investigation(key=payload.key, title=payload.title, created_by=current.subject_id)
        db.add(investigation)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An investigation with this key already exists.") from exc
    return investigation


@router.get("", response_model=list[InvestigationResponse])
def list_investigations(
    db: Session = Depends(get_db),
    _current: CurrentSubject = Depends(require_permission(INVESTIGATION_READ)),
) -> list[Investigation]:
    return db.query(Investigation).order_by(Investigation.created_at.desc()).all()


@router.get("/{key}/report", response_model=ReportResponse)
def get_report(
    key: str,
    db: Session = Depends(get_db),
    _current: CurrentSubject = Depends(require_permission(INVESTIGATION_READ)),
) -> ReportResponse:
    investigation = _get_investigation_or_404(db, key)
    return ReportResponse(
        investigation=InvestigationResponse.model_validate(investigation),
        events=[EventResponse.model_validate(e) for e in investigation.events],
        hypotheses=[HypothesisResponse.model_validate(h) for h in investigation.hypotheses],
        impact_assessments=[ImpactResponse.model_validate(i) for i in investigation.impact_assessments],
        recommendations=[RecommendationResponse.model_validate(r) for r in investigation.recommendations],
    )


@router.post("/{key}/events", response_model=EventResponse, status_code=201)
def add_event(
    key: str,
    payload: AddEventRequest,
    db: Session = Depends(get_db),
    current: CurrentSubject = Depends(require_permission(INVESTIGATION_WRITE)),
) -> InvestigationEvent:
    investigation = _get_investigation_or_404(db, key)

    violations = find_violations(payload.description)
    if violations:
        record_event(
            db,
            event_type="guardrail.dlp_violation",
            outcome="denied",
            correlation_id=str(uuid.uuid4()),
            subject_id=current.subject_id,
            detail={"investigation_key": key, "patterns": violations},
        )
        db.commit()
        raise HTTPException(
            status_code=422, detail="Event description was blocked by a DLP guardrail (ATLAS-047)."
        )

    event = InvestigationEvent(
        investigation_id=investigation.id,
        event_type=payload.event_type,
        description=payload.description,
        related_entity_id=payload.related_entity_id,
        source="manual",
    )
    db.add(event)
    db.commit()
    return event


@router.post("/{key}/hypotheses/generate", response_model=list[HypothesisResponse], status_code=201)
def generate_investigation_hypotheses(
    key: str,
    payload: GenerateHypothesesRequest,
    db: Session = Depends(get_db),
    _current: CurrentSubject = Depends(require_permission(INVESTIGATION_WRITE)),
) -> list[RcaHypothesis]:
    investigation = _get_investigation_or_404(db, key)
    drafts = generate_hypotheses(db, target_entity_id=payload.target_entity_id)
    hypotheses = [
        RcaHypothesis(
            investigation_id=investigation.id,
            fault_family=draft["fault_family"],
            description=draft["description"],
            confidence=draft["confidence"],
            supporting_evidence=draft["supporting_evidence"],
            contradicting_evidence=draft["contradicting_evidence"],
        )
        for draft in drafts
    ]
    db.add_all(hypotheses)
    db.commit()
    return hypotheses


@router.patch("/{key}/hypotheses/{hypothesis_id}", response_model=HypothesisResponse)
def update_hypothesis_status(
    key: str,
    hypothesis_id: uuid.UUID,
    payload: UpdateHypothesisRequest,
    db: Session = Depends(get_db),
    _current: CurrentSubject = Depends(require_permission(INVESTIGATION_WRITE)),
) -> RcaHypothesis:
    if payload.status not in {"proposed", "confirmed", "rejected"}:
        raise HTTPException(status_code=422, detail="status must be proposed, confirmed, or rejected.")
    investigation = _get_investigation_or_404(db, key)
    hypothesis = (
        db.query(RcaHypothesis)
        .filter(RcaHypothesis.id == hypothesis_id, RcaHypothesis.investigation_id == investigation.id)
        .one_or_none()
    )
    if hypothesis is None:
        raise HTTPException(status_code=404, detail="Unknown hypothesis.")
    hypothesis.status = payload.status
    db.commit()
    return hypothesis


@router.post("/{key}/impact", response_model=ImpactResponse, status_code=201)
def assess_investigation_impact(
    key: str,
    payload: AssessImpactRequest,
    db: Session = Depends(get_db),
    _current: CurrentSubject = Depends(require_permission(INVESTIGATION_WRITE)),
) -> ChangeImpactAssessment:
    investigation = _get_investigation_or_404(db, key)
    result = assess_impact(db, target_entity_id=payload.target_entity_id)
    assessment = ChangeImpactAssessment(
        investigation_id=investigation.id,
        target_entity_id=payload.target_entity_id,
        affected_entity_ids=result["affected_entity_ids"],
        graph_gaps=result["graph_gaps"],
        summary=result["summary"],
    )
    db.add(assessment)
    db.commit()
    return assessment


@router.post("/{key}/recommendations", response_model=RecommendationResponse, status_code=201)
def draft_investigation_recommendation(
    key: str,
    payload: DraftRecommendationRequest,
    db: Session = Depends(get_db),
    _current: CurrentSubject = Depends(require_permission(INVESTIGATION_WRITE)),
) -> Recommendation:
    investigation = _get_investigation_or_404(db, key)
    hypothesis = (
        db.query(RcaHypothesis)
        .filter(RcaHypothesis.id == payload.hypothesis_id, RcaHypothesis.investigation_id == investigation.id)
        .one_or_none()
    )
    if hypothesis is None:
        raise HTTPException(status_code=404, detail="Unknown hypothesis.")

    draft = draft_recommendation(hypothesis)
    recommendation = Recommendation(
        investigation_id=investigation.id,
        title=draft["title"],
        summary=draft["summary"],
        risk_level=draft["risk_level"],
        estimated_duration_minutes=draft["estimated_duration_minutes"],
        preconditions=draft["preconditions"],
        rollback_plan=draft["rollback_plan"],
    )
    db.add(recommendation)
    db.commit()
    return recommendation


class DecideApprovalRequest(BaseModel):
    decision: str
    comment: str = ""
    model_config = {"extra": "forbid"}


class ApprovalResponse(BaseModel):
    id: uuid.UUID
    approver_subject_id: str
    decision: str
    comment: str
    decided_at: datetime

    model_config = {"from_attributes": True}


def _get_recommendation_or_404(db: Session, investigation: Investigation, recommendation_id: uuid.UUID) -> Recommendation:
    recommendation = (
        db.query(Recommendation)
        .filter(Recommendation.id == recommendation_id, Recommendation.investigation_id == investigation.id)
        .one_or_none()
    )
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Unknown recommendation.")
    return recommendation


@router.post("/{key}/recommendations/{recommendation_id}/submit", response_model=RecommendationResponse)
def submit_recommendation_for_approval(
    key: str,
    recommendation_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current: CurrentSubject = Depends(require_permission(INVESTIGATION_WRITE)),
) -> Recommendation:
    investigation = _get_investigation_or_404(db, key)
    recommendation = _get_recommendation_or_404(db, investigation, recommendation_id)
    if recommendation.status != "proposed":
        raise HTTPException(status_code=409, detail=f"Recommendation is already {recommendation.status}.")
    recommendation.status = "pending_approval"
    db.commit()
    return recommendation


@router.post(
    "/{key}/recommendations/{recommendation_id}/decide", response_model=RecommendationResponse
)
def decide_recommendation_approval(
    key: str,
    recommendation_id: uuid.UUID,
    payload: DecideApprovalRequest,
    db: Session = Depends(get_db),
    current: CurrentSubject = Depends(require_permission(APPROVAL_DECIDE)),
) -> Recommendation:
    if payload.decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=422, detail="decision must be approved or rejected.")

    investigation = _get_investigation_or_404(db, key)
    recommendation = _get_recommendation_or_404(db, investigation, recommendation_id)
    if recommendation.status != "pending_approval":
        raise HTTPException(
            status_code=409, detail="Recommendation must be pending_approval before it can be decided."
        )

    # ATLAS-037 separation of duties: the investigation's opener cannot also
    # approve its own recommendation. No AI actor can approve at all — this
    # endpoint requires an authenticated human session like any other.
    if current.subject_id == investigation.created_by:
        raise HTTPException(
            status_code=403,
            detail="The investigation's opener cannot approve their own recommendation (separation of duties).",
        )

    db.add(
        RecommendationApproval(
            recommendation_id=recommendation.id,
            approver_subject_id=current.subject_id,
            decision=payload.decision,
            comment=payload.comment,
        )
    )
    recommendation.status = payload.decision

    record_event(
        db,
        event_type="approval.decision",
        outcome="success",
        correlation_id=str(uuid.uuid4()),
        subject_id=current.subject_id,
        detail={
            "investigation_key": key,
            "recommendation_id": str(recommendation.id),
            "decision": payload.decision,
        },
    )
    db.commit()
    return recommendation


@router.get(
    "/{key}/recommendations/{recommendation_id}/approvals", response_model=list[ApprovalResponse]
)
def list_recommendation_approvals(
    key: str,
    recommendation_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current: CurrentSubject = Depends(require_permission(INVESTIGATION_READ)),
) -> list[RecommendationApproval]:
    investigation = _get_investigation_or_404(db, key)
    _get_recommendation_or_404(db, investigation, recommendation_id)
    return (
        db.query(RecommendationApproval)
        .filter(RecommendationApproval.recommendation_id == recommendation_id)
        .order_by(RecommendationApproval.decided_at.desc())
        .all()
    )
