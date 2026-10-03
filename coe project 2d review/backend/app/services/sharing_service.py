import json
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.schema import SharingRequest, User, Document, AuditLog
from backend.app.security.rbac import check_document_access, CONFIDENTIALITY_LEVELS

class SharingService:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_sharing_risk(self, document: Document, recipient: User) -> Tuple[str, Dict[str, Any], bool]:
        """
        Evaluates risk level and generates structured recommendations for sharing a document with recipient.
        Returns (risk_level, recommendation_dict, requires_human_confirmation)
        """
        is_allowed, msg, explanation = check_document_access(recipient.role, recipient.department, document)

        doc_level = document.confidentiality_level
        recipient_role = recipient.role

        if doc_level == "HIGHLY_CONFIDENTIAL":
            risk_level = "CRITICAL"
            requires_human = True
            recommendation = {
                "recommendation": "Access not recommended. Sharing blocked pending executive review.",
                "reason": f"Recipient role ({recipient_role}) is attempting to access a HIGHLY_CONFIDENTIAL protocol.",
                "rule": "HIGHLY_CONFIDENTIAL documents cannot be shared automatically and require mandatory human confirmation and written override justification.",
                "evidence": f"Document ID = {document.document_id}, Classification = HIGHLY_CONFIDENTIAL. Recipient Role = {recipient_role}.",
                "confidence_status": "CRITICAL_RISK",
                "required_action": "Mandatory Human Confirmation & Override Reason Required"
            }
        elif doc_level == "CONFIDENTIAL":
            if not is_allowed:
                risk_level = "HIGH"
                requires_human = True
                recommendation = {
                    "recommendation": "Access not recommended. Recipient role lacks required permission level.",
                    "reason": f"The recipient's role ({recipient_role}) does not normally have permission to view Confidential documents.",
                    "rule": "Confidential documents can only be shared with authorized roles unless an explicit human override is recorded.",
                    "evidence": f"Document Classification = CONFIDENTIAL. Recipient role = {recipient_role}.",
                    "confidence_status": "HIGH_RISK",
                    "required_action": "Human Review Required"
                }
            else:
                risk_level = "MEDIUM"
                requires_human = True
                recommendation = {
                    "recommendation": "Sharing permitted with human confirmation.",
                    "reason": f"Recipient role ({recipient_role}) is authorized, but document is Confidential.",
                    "rule": "All sharing of Confidential protocols requires reviewer confirmation.",
                    "evidence": f"Document Classification = CONFIDENTIAL. Recipient role = {recipient_role}.",
                    "confidence_status": "CONFIRMED_AUTHORIZED",
                    "required_action": "Human Review Required"
                }
        else:  # PUBLIC or INTERNAL
            if not is_allowed:
                risk_level = "MEDIUM"
                requires_human = True
                recommendation = {
                    "recommendation": "Access not recommended for recipient role.",
                    "reason": explanation["reason"],
                    "rule": explanation["rule"],
                    "evidence": explanation["evidence"],
                    "confidence_status": "RESTRICTED",
                    "required_action": "Human Review Required"
                }
            else:
                risk_level = "LOW"
                requires_human = False
                recommendation = {
                    "recommendation": "Sharing Recommended.",
                    "reason": f"Recipient role ({recipient_role}) is authorized for {doc_level} documents.",
                    "rule": "Standard internal sharing policy applies.",
                    "evidence": f"Document Classification = {doc_level}. Recipient role = {recipient_role}.",
                    "confidence_status": "LOW_RISK",
                    "required_action": "Auto-Approve / Standard Share"
                }

        return risk_level, recommendation, requires_human

    def create_sharing_request(self, requester: User, recipient: User, document: Document, reason: str) -> SharingRequest:
        risk_level, rec_dict, requires_human = self.evaluate_sharing_risk(document, recipient)

        status = "PENDING" if requires_human else "APPROVED"

        request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        req = SharingRequest(
            request_id=request_id,
            requester_id=requester.id,
            recipient_id=recipient.id,
            document_id=document.document_id,
            reason=reason,
            requested_at=datetime.utcnow(),
            risk_level=risk_level,
            recommendation_json=json.dumps(rec_dict),
            status=status,
            timestamp=datetime.utcnow()
        )
        self.db.add(req)

        # Audit log creation
        audit = AuditLog(
            event_id=str(uuid.uuid4()),
            user_id=requester.id,
            role=requester.role,
            action="CREATE_SHARE_REQUEST",
            document_id=document.document_id,
            recipient_id=recipient.id,
            old_state="NONE",
            new_state=status,
            reason=f"Share request created for {recipient.name} ({recipient.role}). Risk Level: {risk_level}",
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(req)
        return req

    def process_human_decision(
        self, 
        request_id: str, 
        reviewer: User, 
        decision: str,  # "APPROVE" or "REJECT"
        override_reason: str = None
    ) -> Tuple[bool, str, SharingRequest]:
        """
        Processes human confirmation decision on a pending sharing request.
        Mandates override_reason when approving high-impact/unauthorized sharing.
        """
        req = self.db.query(SharingRequest).filter(SharingRequest.request_id == request_id).first()
        if not req:
            return False, "Sharing request not found.", None

        if req.status not in ["PENDING"]:
            return False, f"Request already processed with status: {req.status}", req

        document = self.db.query(Document).filter(Document.document_id == req.document_id).first()
        recipient = self.db.query(User).filter(User.id == req.recipient_id).first()

        is_allowed, _, _ = check_document_access(recipient.role, recipient.department, document)

        # Check if this is an override of standard restrictions
        is_override = not is_allowed or document.confidentiality_level in ["CONFIDENTIAL", "HIGHLY_CONFIDENTIAL"]

        if decision == "APPROVE":
            if is_override and (not override_reason or not override_reason.strip()):
                return False, "Human confirmation error: An override reason is MANDATORY when approving restricted sharing requests. Empty override reasons are not allowed.", req

            req.status = "OVERRIDDEN" if is_override else "APPROVED"
            req.reviewer_id = reviewer.id
            req.reviewer_decision = "APPROVE"
            req.override_reason = override_reason if is_override else None

            # Audit logs
            audit_action = "OVERRIDE_RESTRICTION" if is_override else "APPROVE_SHARE"
            audit = AuditLog(
                event_id=str(uuid.uuid4()),
                user_id=reviewer.id,
                role=reviewer.role,
                action=audit_action,
                document_id=req.document_id,
                recipient_id=req.recipient_id,
                old_state="PENDING",
                new_state=req.status,
                reason=f"Human reviewer ({reviewer.name}) approved request.",
                override_reason=override_reason,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
        
        elif decision == "REJECT":
            req.status = "REJECTED"
            req.reviewer_id = reviewer.id
            req.reviewer_decision = "REJECT"
            req.override_reason = override_reason

            audit = AuditLog(
                event_id=str(uuid.uuid4()),
                user_id=reviewer.id,
                role=reviewer.role,
                action="REJECT_SHARE",
                document_id=req.document_id,
                recipient_id=req.recipient_id,
                old_state="PENDING",
                new_state="REJECTED",
                reason=f"Human reviewer ({reviewer.name}) rejected request.",
                override_reason=override_reason,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
        else:
            return False, "Invalid decision. Must be APPROVE or REJECT.", req

        self.db.commit()
        self.db.refresh(req)
        return True, f"Request successfully updated to {req.status}", req
