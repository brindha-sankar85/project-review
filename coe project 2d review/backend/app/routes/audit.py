from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models.schema import AuditLog, User, Document

router = APIRouter(prefix="/api/audit", tags=["Audit Log"])

@router.get("/logs")
def list_audit_logs(
    action: Optional[str] = None,
    role: Optional[str] = None,
    document_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Returns audit log entries for Admin review.
    Tracks VIEW_DOCUMENT, GENERATE_SUMMARY, CREATE_SHARE_REQUEST, APPROVE_SHARE, REJECT_SHARE, OVERRIDE_RESTRICTION, CHANGE_PERMISSION, REDACT_CONTENT.
    """
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if role:
        query = query.filter(AuditLog.role == role)
    if document_id:
        query = query.filter(AuditLog.document_id == document_id)

    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

    result = []
    for l in logs:
        user = db.query(User).filter(User.id == l.user_id).first()
        doc = db.query(Document).filter(Document.document_id == l.document_id).first() if l.document_id else None
        rec_user = db.query(User).filter(User.id == l.recipient_id).first() if l.recipient_id else None

        result.append({
            "event_id": l.event_id,
            "user_id": l.user_id,
            "user_name": user.name if user else l.user_id,
            "role": l.role,
            "action": l.action,
            "document_id": l.document_id,
            "document_title": doc.title if doc else None,
            "recipient_id": l.recipient_id,
            "recipient_name": rec_user.name if rec_user else None,
            "old_state": l.old_state,
            "new_state": l.new_state,
            "reason": l.reason,
            "override_reason": l.override_reason,
            "timestamp": l.timestamp.isoformat()
        })

    return result
