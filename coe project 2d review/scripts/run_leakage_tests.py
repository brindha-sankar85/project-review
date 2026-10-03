import os
import sys
import json

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database import SessionLocal
from backend.app.models.schema import User, Document
from backend.app.summarization.engine import SummarizationEngine
from backend.app.summarization.baseline import BaselineSummarizer

SENSITIVE_MARKERS = [
    "SENSITIVE_TEST_001",
    "RESTRICTED_TEST_002",
    "HIGHLY_CONFIDENTIAL_TEST_003",
    "CONFIDENTIAL SENSITIVE",
    "CONFIDENTIAL PATIENT DATA",
    "HIGHLY CONFIDENTIAL"
]

def run_synthetic_leakage_tests():
    """
    Evaluates baseline vs proposed summarization engine for sensitive content leakage
    when requested by unauthorized user roles.
    """
    db = SessionLocal()
    summarizer = SummarizationEngine(db)
    baseline_summarizer = BaselineSummarizer()

    try:
        documents = db.query(Document).all()
        # Unauthorized roles for confidential documents
        unauthorized_users = db.query(User).filter(User.role.in_(["Nurse", "Receptionist", "Intern"])).all()

        baseline_total_requests = 0
        baseline_leakage_count = 0

        proposed_total_requests = 0
        proposed_leakage_count = 0

        test_details = []

        for doc in documents:
            for user in unauthorized_users:
                # 1. Run Baseline
                baseline_res = baseline_summarizer.generate_unfiltered_summary(doc)
                b_text = baseline_res["summary"]
                b_leaked = any(marker in b_text for marker in SENSITIVE_MARKERS)
                
                # We count as unauthorized scenario if document has sensitive sections restricted from this user
                has_sensitive_restricted = any(
                    sec.is_sensitive and (user.role in sec.restricted_roles or sec.confidentiality_level in ["CONFIDENTIAL", "HIGHLY_CONFIDENTIAL"])
                    for sec in doc.sections
                )

                if has_sensitive_restricted:
                    baseline_total_requests += 1
                    if b_leaked:
                        baseline_leakage_count += 1

                    # 2. Run Proposed System
                    prop_res = summarizer.generate_confidentiality_aware_summary(user, doc)
                    p_text = prop_res.get("summary", "")
                    p_leaked = any(marker in p_text for marker in SENSITIVE_MARKERS)

                    proposed_total_requests += 1
                    if p_leaked:
                        proposed_leakage_count += 1

                    test_details.append({
                        "document_id": doc.document_id,
                        "title": doc.title,
                        "user": user.name,
                        "role": user.role,
                        "baseline_leaked": b_leaked,
                        "proposed_leaked": p_leaked,
                        "redactions_applied": prop_res.get("redacted_count", 0),
                        "status": "PASSED" if not p_leaked else "FAILED"
                    })

        b_leak_rate = (baseline_leakage_count / baseline_total_requests * 100.0) if baseline_total_requests > 0 else 0.0
        p_leak_rate = (proposed_leakage_count / proposed_total_requests * 100.0) if proposed_total_requests > 0 else 0.0

        results = {
            "baseline": {
                "total_unauthorized_requests": baseline_total_requests,
                "leaked_requests_count": baseline_leakage_count,
                "leakage_rate_pct": round(b_leak_rate, 2)
            },
            "proposed": {
                "total_unauthorized_requests": proposed_total_requests,
                "leaked_requests_count": proposed_leakage_count,
                "leakage_rate_pct": round(p_leak_rate, 2)
            },
            "target_leakage_rate_pct": 0.0,
            "success": proposed_leakage_count == 0,
            "test_runs": test_details
        }

        print("=== SYNTHETIC LEAKAGE TEST RESULTS ===")
        print(f"Baseline Sensitive Leakage Rate: {results['baseline']['leakage_rate_pct']}% ({baseline_leakage_count}/{baseline_total_requests})")
        print(f"Proposed System Leakage Rate:  {results['proposed']['leakage_rate_pct']}% ({proposed_leakage_count}/{proposed_total_requests})")
        print(f"Target Leakage Rate:           {results['target_leakage_rate_pct']}%")
        print(f"Leakage Test Status:           {'PASSED (0% Leakage)' if results['success'] else 'FAILED'}")

        return results

    finally:
        db.close()

if __name__ == "__main__":
    run_synthetic_leakage_tests()
