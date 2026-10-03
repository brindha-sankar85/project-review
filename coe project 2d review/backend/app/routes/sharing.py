from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.app.database import get_db
from backend.app.models.schema import User, Document, SharingRequest
from backend.app.services.sharing_service import SharingService

router = APIRouter(prefix="/api/sharing", tags=["Sharing & Approvals"])

class CreateShareRequestPayload(BaseModel):
    requester_id: str
    recipient_id: str
    document_id: str
    reason: str

class HumanDecisionPayload(BaseModel):
    reviewer_id: str
    decision: str  # APPROVE or REJECT
    override_reason: Optional[str] = None

@router.post("/evaluate")
def evaluate_sharing(payload: CreateShareRequestPayload, db: Session = Depends(get_db)):
    """Pre-evaluates sharing risk and recommendation before submitting request."""
    doc = db.query(Document).filter(Document.document_id == payload.document_id).first()
    recipient = db.query(User).filter(User.id == payload.recipient_id).first()

    if not doc or not recipient:
        raise HTTPException(status_code=404, detail="Document or recipient user not found")

    service = SharingService(db)
    risk_level, rec_dict, requires_human = service.evaluate_sharing_risk(doc, recipient)
    return {
        "risk_level": risk_level,
        "recommendation": rec_dict,
        "requires_human_confirmation": requires_human
    }

@router.post("/request")
def create_share_request(payload: CreateShareRequestPayload, db: Session = Depends(get_db)):
    requester = db.query(User).filter(User.id == payload.requester_id).first()
    recipient = db.query(User).filter(User.id == payload.recipient_id).first()
    doc = db.query(Document).filter(Document.document_id == payload.document_id).first()

    if not requester or not recipient or not doc:
        raise HTTPException(status_code=404, detail="Requester, recipient, or document not found")

    service = SharingService(db)
    req = service.create_sharing_request(requester, recipient, doc, payload.reason)

    return {
        "success": True,
        "request_id": req.request_id,
        "status": req.status,
        "risk_level": req.risk_level,
        "recommendation": req.recommendation_json,
        "message": f"Sharing request created with status {req.status}."
    }

@router.get("/requests")
def list_sharing_requests(user_id: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(SharingRequest)

    if status:
        query = query.filter(SharingRequest.status == status)

    requests = query.order_by(SharingRequest.requested_at.desc()).all()

    result = []
    for r in requests:
        req_user = db.query(User).filter(User.id == r.requester_id).first()
        rec_user = db.query(User).filter(User.id == r.recipient_id).first()
        doc = db.query(Document).filter(Document.document_id == r.document_id).first()
        rev_user = db.query(User).filter(User.id == r.reviewer_id).first() if r.reviewer_id else None

        rec_obj = r.recommendation_json
        if isinstance(rec_obj, str):
            try:
                rec_obj = json.loads(rec_obj)
            except Exception:
                rec_obj = {}

        result.append({
            "request_id": r.request_id,
            "requester": {"id": req_user.id, "name": req_user.name, "role": req_user.role} if req_user else None,
            "recipient": {"id": rec_user.id, "name": rec_user.name, "role": rec_user.role} if rec_user else None,
            "document": {"document_id": doc.document_id, "title": doc.title, "confidentiality_level": doc.confidentiality_level} if doc else None,
            "reason": r.reason,
            "requested_at": r.requested_at.isoformat(),
            "risk_level": r.risk_level,
            "recommendation": rec_obj,
            "status": r.status,
            "reviewer": {"id": rev_user.id, "name": rev_user.name, "role": rev_user.role} if rev_user else None,
            "reviewer_decision": r.reviewer_decision,
            "override_reason": r.override_reason,
            "timestamp": r.timestamp.isoformat()
        })
    return result

@router.post("/requests/{request_id}/decision")
def process_decision(request_id: str, payload: HumanDecisionPayload, db: Session = Depends(get_db)):
    reviewer = db.query(User).filter(User.id == payload.reviewer_id).first()
    if not reviewer:
        raise HTTPException(status_code=404, detail="Reviewer user not found")

    service = SharingService(db)
    success, msg, req = service.process_human_decision(
        request_id=request_id,
        reviewer=reviewer,
        decision=payload.decision.upper(),
        override_reason=payload.override_reason
    )

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "success": True,
        "message": msg,
        "request_id": req.request_id,
        "new_status": req.status,
        "override_reason": req.override_reason
    }
