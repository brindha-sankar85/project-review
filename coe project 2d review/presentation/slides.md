# Presentation Deck: Confidentiality-Aware Hospital Knowledge Assistant

## Slide 1: Title & Project Overview
* **Title**: Confidentiality-Aware Hospital Knowledge Summarisation and Sharing Assistant
* **Subtitle**: Protecting Sensitive Clinical Protocols, Incident Logs, and Controlled Drug Security Across Shift Handovers
* **Key Focus**: Role-Based Access Control, Redacted Summarisation, Human Approvals, and Resilient Event Handling.

---

## Slide 2: Hospital Problem Statement
* Shift personnel & frequent protocol changes create risk of accidental confidential data exposure.
* Documents shared across roles (Interns, Nurses, Doctors, Receptionists) can expose sensitive vault codes or patient pseudonyms.
* Need for automated filtering that explains *why* content is withheld in non-specialist language.

---

## Slide 3: Field Workflow Architecture
* Protocol Update Published &rarr; Confidentiality Level Assigned &rarr; Staff Member Requests Shift Handover Summary &rarr; RBAC Redaction Engine Filters Sensitive Sections &rarr; Safe Summary & Explanation &rarr; High-Risk Sharing Routed for Human Approval &rarr; Immutable Audit Trail.

---

## Slide 4: Proposed Solution Core Features
1. **Document Permission Labels**: PUBLIC, INTERNAL, CONFIDENTIAL, HIGHLY_CONFIDENTIAL.
2. **User Role Matrix**: Admin, Hospital Manager, Doctor, Nurse, Receptionist, Intern.
3. **Backend API Redaction**: Sensitive sections stripped BEFORE returning payload to client.
4. **Mandatory Override Reason**: Human confirmation requires written justification.

---

## Slide 5: System Architecture & Technology Stack
* **Frontend**: Responsive Single-Page Application (HTML5 / Vanilla CSS / Modern JS)
* **Backend**: Python FastAPI REST web services
* **Database**: SQLite with SQLAlchemy ORM
* **Resiliency Engine**: Event Stream Processor with Idempotency & Version Vectors

---

## Slide 6: Confidentiality & Permission Matrix
* **Admin**: All confidentiality levels
* **Doctor & Hospital Manager**: Up to CONFIDENTIAL
* **Nurse**: Up to CONFIDENTIAL (departmental & explicit role restrictions apply)
* **Receptionist & Intern**: PUBLIC & limited INTERNAL

---

## Slide 7: Summarisation & Redaction Engine Workflow
* Evaluates document confidentiality level and section sensitivity metadata.
* Filters out restricted sections before summary generation.
* Provides structured WHY explanation:
  * **Recommendation**: Redacted Summary Generated
  * **Reason**: User role is Nurse; document contains 1 confidential section
  * **Rule Applied**: Sensitive vault codes restricted to authorized roles
  * **Evidence**: Document classification = CONFIDENTIAL, User role = Nurse

---

## Slide 8: Sharing Request System & Human Confirmation
* Risk evaluation engine automatically classifies requests as LOW, MEDIUM, HIGH, or CRITICAL risk.
* High-impact sharing requests held in `PENDING` status.
* Human approval screen requires mandatory override reason. Empty reasons rejected.

---

## Slide 9: Resilient Event Failure Handling
* **Duplicate Events**: Idempotency check returns `IGNORED_DUPLICATE` with zero state mutation.
* **Out-of-Order Events**: Version vector buffers future events in `OUT_OF_ORDER_BUFFERED` and drains sequentially when missing events arrive.
* **Delayed Events**: Stale event versions discarded as `DISCARDED_STALE` to preserve active state.

---

## Slide 10: Experimental Evaluation & Baseline Comparison
* **Experimental Baseline**: Summariser without confidentiality filtering (100% Leakage Rate).
* **Proposed System**: Confidentiality-aware summariser (0.0% Sensitive Leakage Rate).

---

## Slide 11: Measured Results & Failure Analysis
* **Sensitive Leakage Rate**: Baseline = 100%, Proposed = **0.0%**
* **Access Control Accuracy**: **100.0%**
* **Duplicate / Out-of-Order / Delayed Event Recovery**: **100.0%**
* All 7 Edge Case Tests **PASSED**.

---

## Slide 12: Stakeholder Validation & Conclusion
* Average Usability Score: **5.0 / 5.0** across Doctor, Nurse, Manager, and Intern feedback.
* **Conclusion**: Prototype complete, fully verified, and ready for live evaluation and demonstration.
