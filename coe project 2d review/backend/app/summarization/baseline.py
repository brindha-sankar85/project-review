from typing import Dict, Any
from backend.app.models.schema import Document

class BaselineSummarizer:
    """
    Experimental Baseline Summarization Engine.
    Does NOT apply document-level or section-level confidentiality filtering before summarization.
    Used exclusively for baseline metrics comparison and leakage measurement.
    """
    def generate_unfiltered_summary(self, document: Document) -> Dict[str, Any]:
        sections = sorted(document.sections, key=lambda s: s.sequence_order) if document.sections else []

        summary_paragraphs = [
            f"### [BASELINE UNFILTERED SUMMARY] {document.title} (Protocol v{document.protocol_version})",
            f"**Department:** {document.department}",
            "\n**Full Protocol Content (Unfiltered):**"
        ]

        for sec in sections:
            summary_paragraphs.append(f"- **{sec.section_title}**: {sec.content}")

        if not sections and document.document_content:
            summary_paragraphs.append(document.document_content)

        raw_summary = "\n".join(summary_paragraphs)

        return {
            "is_baseline": True,
            "document_id": document.document_id,
            "summary": raw_summary,
            "included_sections_count": len(sections),
            "applied_redactions": 0,
            "filtered": False
        }
