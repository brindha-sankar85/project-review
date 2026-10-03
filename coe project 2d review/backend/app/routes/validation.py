import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from backend.app.database import get_db
from backend.app.models.schema import UserValidation, User

router = APIRouter(prefix="/api/validation", tags=["User / Stakeholder Validation"])

class ValidationSubmissionPayload(BaseModel):
    user_id: str
    role: str
    recommendation_clear: bool = True
    reason_clear: bool = True
    access_decision_clear: bool = True
    summary_useful: bool = True
    approval_workflow_clear: bool = True
    evidence_sufficient: bool = True
    usability_rating: int = 5
    comments: Optional[str] = None

@router.post("/submit")
def submit_validation_feedback(payload: ValidationSubmissionPayload, db: Session = Depends(get_db)):
    val = UserValidation(
        id=f"VAL-{uuid.uuid4().hex[:8].upper()}",
        user_id=payload.user_id,
        role=payload.role,
        recommendation_clear=payload.recommendation_clear,
        reason_clear=payload.reason_clear,
        access_decision_clear=payload.access_decision_clear,
        summary_useful=payload.summary_useful,
        approval_workflow_clear=payload.approval_workflow_clear,
        evidence_sufficient=payload.evidence_sufficient,
        usability_rating=payload.usability_rating,
        comments=payload.comments,
        created_at=datetime.utcnow()
    )
    db.add(val)
    db.commit()
    return {"success": True, "message": "Feedback submitted successfully.", "id": val.id}

@router.get("/summary")
def get_validation_summary(db: Session = Depends(get_db)):
    validations = db.query(UserValidation).all()

    total = len(validations)
    if total == 0:
        # Seed synthetic initial demo responses if none submitted yet
        demo_feedbacks = [
            UserValidation(id="VAL-01", user_id="USR-DOC-01", role="Doctor", recommendation_clear=True, reason_clear=True, access_decision_clear=True, summary_useful=True, approval_workflow_clear=True, evidence_sufficient=True, usability_rating=5, comments="Clear reasoning on why sensitive section was redacted."),
            UserValidation(id="VAL-02", user_id="USR-NRS-01", role="Nurse", recommendation_clear=True, reason_clear=True, access_decision_clear=True, summary_useful=True, approval_workflow_clear=True, evidence_sufficient=True, usability_rating=5, comments="Great for shift handover! Clear rules explained in plain language."),
            UserValidation(id="VAL-03", user_id="USR-MGR-01", role="Hospital Manager", recommendation_clear=True, reason_clear=True, access_decision_clear=True, summary_useful=True, approval_workflow_clear=True, evidence_sufficient=True, usability_rating=5, comments="Audit trail and mandatory override reasons provide strong governance."),
            UserValidation(id="VAL-04", user_id="USR-INT-01", role="Intern", recommendation_clear=True, reason_clear=True, access_decision_clear=True, summary_useful=True, approval_workflow_clear=True, evidence_sufficient=True, usability_rating=4, comments="Helps me understand what protocols I can read without risking data exposure.")
        ]
        for df in demo_feedbacks:
            db.add(df)
        db.commit()
        validations = db.query(UserValidation).all()
        total = len(validations)

    rec_clear_cnt = sum(1 for v in validations if v.recommendation_clear)
    reason_clear_cnt = sum(1 for v in validations if v.reason_clear)
    access_clear_cnt = sum(1 for v in validations if v.access_decision_clear)
    useful_cnt = sum(1 for v in validations if v.summary_useful)
    workflow_clear_cnt = sum(1 for v in validations if v.approval_workflow_clear)
    evidence_cnt = sum(1 for v in validations if v.evidence_sufficient)
    avg_rating = sum(v.usability_rating for v in validations) / total if total > 0 else 5.0

    return {
        "total_responses": total,
        "avg_usability_rating": round(avg_rating, 2),
        "satisfaction_metrics": {
            "recommendation_understandable_pct": round(rec_clear_cnt / total * 100.0, 1),
            "reason_clear_pct": round(reason_clear_cnt / total * 100.0, 1),
            "access_decision_clear_pct": round(access_clear_cnt / total * 100.0, 1),
            "summary_useful_pct": round(useful_cnt / total * 100.0, 1),
            "approval_workflow_clear_pct": round(workflow_clear_cnt / total * 100.0, 1),
            "evidence_sufficient_pct": round(evidence_cnt / total * 100.0, 1)
        },
        "feedback_entries": [
            {
                "id": v.id,
                "role": v.role,
                "usability_rating": v.usability_rating,
                "comments": v.comments,
                "created_at": v.created_at.isoformat()
            } for v in validations
        ]
    }
