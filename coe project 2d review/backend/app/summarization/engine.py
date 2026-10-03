import uuid
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.schema import Document, DocumentSection, AuditLog, User
from backend.app.security.rbac import check_document_access, check_section_access

class SummarizationEngine:
    def __init__(self, db: Session):
        self.db = db

    def generate_confidentiality_aware_summary(self, user: User, document: Document) -> Dict[str, Any]:
        """
        Generates a safe protocol summary filtered strictly according to the requesting user's role.
        Protects sensitive sections and provides human-readable explanations.
        """
        # 1. Document Level Access Check
        is_allowed, access_msg, explanation = check_document_access(user.role, user.department, document)

        if not is_allowed:
            # Audit log unauthorized attempt
            audit = AuditLog(
                event_id=str(uuid.uuid4()),
                user_id=user.id,
                role=user.role,
                action="GENERATE_SUMMARY",
                document_id=document.document_id,
                old_state="UNAUTHORIZED_REQUEST",
                new_state="ACCESS_DENIED",
                reason=explanation["reason"],
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
            self.db.commit()

            return {
                "success": False,
                "error": "Access Denied",
                "summary": "Summary generation blocked due to confidentiality restrictions.",
                "what_you_can_see": [],
                "information_withheld": ["Entire document contents withheld due to role permissions."],
                "why_explanation": explanation,
                "has_redactions": True,
                "redacted_count": len(document.sections) if document.sections else 1
            }

        # 2. Section Level Confidentiality Filtering
        visible_sections = []
        withheld_sections = []
        redaction_count = 0
        withheld_reasons = []

        # Sort sections by order
        sections = sorted(document.sections, key=lambda s: s.sequence_order)

        for sec in sections:
            sec_allowed, sec_reason = check_section_access(user.role, sec)
            if sec_allowed:
                visible_sections.append({
                    "id": sec.id,
                    "title": sec.section_title,
                    "content": sec.content,
                    "is_sensitive": sec.is_sensitive
                })
            else:
                redaction_count += 1
                withheld_sections.append({
                    "id": sec.id,
                    "title": sec.section_title,
                    "confidentiality_level": sec.confidentiality_level,
                    "reason": sec_reason
                })
                withheld_reasons.append(f"Section '{sec.section_title}': {sec_reason}")

        # 3. Generate Summary Text from Permitted Sections
        summary_paragraphs = []
        summary_paragraphs.append(f"### Safe Summary: {document.title} (Protocol v{document.protocol_version})")
        summary_paragraphs.append(f"**Department:** {document.department} | **Effective Date:** {document.effective_date}")
        summary_paragraphs.append("\n**Key Protocol Guidelines:**")

        for sec in visible_sections:
            # Extract key sentences or points
            content_preview = sec["content"]
            if len(content_preview) > 200:
                content_preview = content_preview[:197] + "..."
            summary_paragraphs.append(f"- **{sec['title']}**: {content_preview}")

        if not visible_sections:
            summary_paragraphs.append("- *No viewable sections available for your role level.*")

        summary_text = "\n".join(summary_paragraphs)

        # 4. Create Explanation for UI
        if redaction_count > 0:
            why_text = f"Your role is '{user.role}'. This document contains {redaction_count} sensitive/confidential sections restricted to higher authority roles."
            explanation_obj = {
                "recommendation": "Redacted Summary Generated",
                "reason": why_text,
                "rule": "Sensitive hospital investigation notes, patient identifiers, and restricted security items are automatically removed for unauthorized roles.",
                "evidence": f"Document ID = {document.document_id}. User Role = {user.role}. Sections Filtered = {redaction_count}/{len(sections)}.",
                "confidence_status": "FILTERED_SAFE",
                "required_action": "None (Safe to read)"
            }
        else:
            why_text = f"All sections of this document are fully authorized for viewing by '{user.role}'."
            explanation_obj = {
                "recommendation": "Full Summary Generated",
                "reason": why_text,
                "rule": "Standard document access allowed based on user role matrix.",
                "evidence": f"Document ID = {document.document_id}. User Role = {user.role}. All sections accessible.",
                "confidence_status": "FULL_ACCESS",
                "required_action": "None"
            }

        # 5. Record Audit Logs
        audit_summary = AuditLog(
            event_id=str(uuid.uuid4()),
            user_id=user.id,
            role=user.role,
            action="GENERATE_SUMMARY",
            document_id=document.document_id,
            old_state="REQUESTED",
            new_state="SUCCESS",
            reason=f"Generated summary with {redaction_count} redacted sections",
            timestamp=datetime.utcnow()
        )
        self.db.add(audit_summary)

        if redaction_count > 0:
            audit_redact = AuditLog(
                event_id=str(uuid.uuid4()),
                user_id=user.id,
                role=user.role,
                action="REDACT_CONTENT",
                document_id=document.document_id,
                old_state="RAW_SECTIONS",
                new_state=f"REDACTED_{redaction_count}_SECTIONS",
                reason="; ".join(withheld_reasons),
                timestamp=datetime.utcnow()
            )
            self.db.add(audit_redact)

        self.db.commit()

        return {
            "success": True,
            "document_id": document.document_id,
            "title": document.title,
            "protocol_version": document.protocol_version,
            "user_role": user.role,
            "summary": summary_text,
            "what_you_can_see": [f"{s['title']}: {s['content'][:120]}..." for s in visible_sections],
            "information_withheld": [f"Section '{s['title']}' ({s['confidentiality_level']}) - Withheld because your role ({user.role}) is not authorized." for s in withheld_sections],
            "why_explanation": explanation_obj,
            "has_redactions": redaction_count > 0,
            "redacted_count": redaction_count,
            "total_sections": len(sections)
        }
