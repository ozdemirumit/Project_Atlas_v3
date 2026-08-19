"""Rule-based recommendation drafting (ATLAS-043).

Same placeholder status as `app.decision.rca`: no AI reasoning engine is
configured, so this maps a confirmed hypothesis's fault family to a fixed
recommendation template. Per AGENTS.md Section 7, every recommendation
involving operational change must carry risk, duration, preconditions, and
a rollback plan — those fields are mandatory here, not optional prose.
"""
from app.models.investigation import RcaHypothesis

_TEMPLATES: dict[str, dict[str, object]] = {
    "san_port_offline": {
        "title": "Verify and restore the offline SAN switch port",
        "risk_level": "low",
        "estimated_duration_minutes": 30,
        "preconditions": [
            "Confirm no active I/O is expected on the affected zone during the check.",
            "Physical or remote console access to the switch is available.",
        ],
        "rollback_plan": (
            "If re-enabling the port does not restore connectivity, leave it disabled and escalate "
            "to the storage/network on-call rotation — no configuration change is made by this step."
        ),
    },
    "san_fabric_unreachable": {
        "title": "Investigate SAN fabric manager connectivity",
        "risk_level": "medium",
        "estimated_duration_minutes": 45,
        "preconditions": [
            "Confirm whether the fabric manager itself, or only the monitoring path to it, is down.",
            "Notify stakeholders of any storage services dependent on this fabric before acting.",
        ],
        "rollback_plan": (
            "This is a read-only investigation step; no infrastructure change is proposed until a "
            "human confirms root cause and a separate change is planned and approved."
        ),
    },
}

_DEFAULT_TEMPLATE: dict[str, object] = {
    "title": "Manual investigation required",
    "risk_level": "low",
    "estimated_duration_minutes": 60,
    "preconditions": ["No automated fault pattern matched; a human must classify the fault first."],
    "rollback_plan": "No action is proposed; this is an investigation-only recommendation.",
}


def draft_recommendation(hypothesis: RcaHypothesis) -> dict[str, object]:
    template = _TEMPLATES.get(hypothesis.fault_family, _DEFAULT_TEMPLATE)
    return {
        "title": template["title"],
        "summary": (
            f"Based on hypothesis: {hypothesis.description} (confidence: {hypothesis.confidence})."
        ),
        "risk_level": template["risk_level"],
        "estimated_duration_minutes": template["estimated_duration_minutes"],
        "preconditions": template["preconditions"],
        "rollback_plan": template["rollback_plan"],
    }
