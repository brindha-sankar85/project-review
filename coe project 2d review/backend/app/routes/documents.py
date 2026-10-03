from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend.app.database import get_db
from backend.app.models.schema import User, Document, AuditLog
from backend.app.security.rbac import check_document_access, check_section_access
from backend.app.summarization.engine import SummarizationEngine
from backend.app.summarization.baseline import BaselineSummarizer
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/documents", tags=["Documents & Protocols"])

def get_current_user(user_id: str, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail=f"User ID '{user_id}' not found. Please log in.")
    return user

@router.get("/")
def list_documents(user_id: str, db: Session = Depends(get_db)):
    """
    Returns list of protocol documents.
    Enforces role-based visibility markers.
    """
    user = get_current_user(user_id, db)
    documents = db.query(Document).all()

    result = []
    for doc in documents:
        is_allowed, msg, explanation = check_document_access(user.role, user.department, doc)
        result.append({
            "document_id": doc.document_id,
            "title": doc.title,
            "department": doc.department,
            "protocol_version": doc.protocol_version,
            "effective_date": doc.effective_date,
            "confidentiality_level": doc.confidentiality_level,
            "status": doc.status,
            "is_accessible": is_allowed,
            "access_message": msg,
            "explanation": explanation
        })
    return result

@router.get("/{document_id}")
def get_document_detail(document_id: str, user_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full document detail.
    SECURITY ENFORCED: Unauthorized sensitive sections are REMOVED from the API payload!
    """
    user = get_current_user(user_id, db)
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    is_allowed, msg, explanation = check_document_access(user.role, user.department, doc)

    # Log document view audit
    audit = AuditLog(
        event_id=str(uuid.uuid4()),
        user_id=user.id,
        role=user.role,
        action="VIEW_DOCUMENT",
        document_id=doc.document_id,
        old_state="CLOSED",
        new_state="VIEWED" if is_allowed else "DENIED",
        reason=msg,
        timestamp=datetime.utcnow()
    )
    db.add(audit)
    db.commit()

    if not is_allowed:
        raise HTTPException(status_code=403, detail={
            "error": "Access Denied",
            "message": f"Your role ({user.role}) is not authorized to view {doc.confidentiality_level} documents.",
            "explanation": explanation
        })

    # Filter section content strictly in backend API
    safe_sections = []
    withheld_count = 0

    for sec in sorted(doc.sections, key=lambda s: s.sequence_order):
        sec_allowed, sec_reason = check_section_access(user.role, sec)
        if sec_allowed:
            safe_sections.append({
                "id": sec.id,
                "section_title": sec.section_title,
                "content": sec.content,
                "is_sensitive": sec.is_sensitive,
                "confidentiality_level": sec.confidentiality_level
            })
        else:
            withheld_count += 1
            safe_sections.append({
                "id": sec.id,
                "section_title": sec.section_title,
                "content": "[REDACTED - SENSITIVE CONTENT WITHHELD FOR YOUR ROLE]",
                "is_sensitive": True,
                "is_redacted": True,
                "confidentiality_level": sec.confidentiality_level,
                "redaction_reason": sec_reason
            })

    version_warning = None
    if doc.status == "SUPERSEDED":
        active_doc = db.query(Document).filter(Document.title == doc.title, Document.status == "ACTIVE").first()
        version_warning = {
            "warning": "This protocol version has been superseded.",
            "current_requested": doc.protocol_version,
            "recommended_active_version": active_doc.protocol_version if active_doc else "Latest Active",
            "recommended_document_id": active_doc.document_id if active_doc else None,
            "rule": "Staff must use current active protocol versions for patient safety."
        }

    return {
        "document_id": doc.document_id,
        "title": doc.title,
        "department": doc.department,
        "protocol_version": doc.protocol_version,
        "effective_date": doc.effective_date,
        "expiry_date": doc.expiry_date,
        "confidentiality_level": doc.confidentiality_level,
        "allowed_roles": doc.allowed_roles,
        "status": doc.status,
        "sections": safe_sections,
        "withheld_sections_count": withheld_count,
        "version_warning": version_warning,
        "explanation": explanation
    }

@router.post("/{document_id}/summarize")
def summarize_document(document_id: str, user_id: str, use_baseline: bool = False, db: Session = Depends(get_db)):
    """
    Generates a protocol summary.
    If use_baseline=True, runs baseline unfiltered summarizer (for baseline comparison).
    Otherwise runs proposed confidentiality-aware summarizer.
    """
    user = get_current_user(user_id, db)
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if use_baseline:
        baseline_engine = BaselineSummarizer()
        res = baseline_engine.generate_unfiltered_summary(doc)
        res["warning"] = "EXPERIMENTAL BASELINE RESULT - UNFILTERED SUMMARIZATION"
        return res

    engine = SummarizationEngine(db)
    res = engine.generate_confidentiality_aware_summary(user, doc)
    return res
