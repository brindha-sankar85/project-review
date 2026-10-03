import os
import csv
import json
import random
import uuid
from datetime import datetime, timedelta

def generate_synthetic_data(seed: int = 42, output_dir: str = None):
    random.seed(seed)

    if not output_dir:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic")

    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating synthetic hospital data with seed={seed} into {output_dir}...")

    # 1. Users Data
    users = [
        {"id": "USR-ADM-01", "username": "admin_chief", "name": "Dr. Arthur Vance (Chief Admin)", "role": "Admin", "department": "Administration"},
        {"id": "USR-ADM-02", "username": "admin_sec", "name": "Claire Redfield (Systems Admin)", "role": "Admin", "department": "IT & Operations"},
        {"id": "USR-MGR-01", "username": "mgr_hand", "name": "Eleanor Vance (Hospital Director)", "role": "Hospital Manager", "department": "Executive Management"},
        {"id": "USR-MGR-02", "username": "mgr_clinical", "name": "Marcus Wright (Clinical Manager)", "role": "Hospital Manager", "department": "Clinical Governance"},
        {"id": "USR-DOC-01", "username": "doc_house", "name": "Dr. Gregory House (Head Physician)", "role": "Doctor", "department": "General Medicine"},
        {"id": "USR-DOC-02", "username": "doc_shepherd", "name": "Dr. Derek Shepherd (Neurosurgeon)", "role": "Doctor", "department": "Surgery"},
        {"id": "USR-NRS-01", "username": "nurse_joy", "name": "Joy Hathaway (Head ICU Nurse)", "role": "Nurse", "department": "ICU"},
        {"id": "USR-NRS-02", "username": "nurse_jack", "name": "Jack Dawson (ER Staff Nurse)", "role": "Nurse", "department": "Emergency"},
        {"id": "USR-REC-01", "username": "rec_pam", "name": "Pam Beesly (Lead Receptionist)", "role": "Receptionist", "department": "Front Desk & Admissions"},
        {"id": "USR-INT-01", "username": "intern_jd", "name": "John Dorian (Medical Intern)", "role": "Intern", "department": "General Medicine"},
        {"id": "USR-INT-02", "username": "intern_turk", "name": "Christopher Turk (Surgical Intern)", "role": "Intern", "department": "Surgery"},
    ]

    users_file = os.path.join(output_dir, "users.csv")
    with open(users_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "username", "name", "role", "department", "created_at"])
        writer.writeheader()
        now_str = datetime.utcnow().isoformat()
        for u in users:
            u_dict = dict(u)
            u_dict["created_at"] = now_str
            writer.writerow(u_dict)

    # 2. Documents Data
    documents = [
        {
            "document_id": "DOC-INF-001",
            "title": "Infection Control & Disinfection Protocol",
            "department": "Infectious Diseases",
            "protocol_version": "2.1",
            "effective_date": "2026-01-15",
            "expiry_date": "2027-01-15",
            "confidentiality_level": "PUBLIC",
            "allowed_roles": ["Admin", "Hospital Manager", "Doctor", "Nurse", "Receptionist", "Intern"],
            "status": "ACTIVE",
            "document_content": "Standard operating procedures for hand hygiene, surface sterilization, personal protective equipment (PPE) donning/doffing, and isolation chamber sanitization across all clinical wards."
        },
        {
            "document_id": "DOC-MED-002",
            "title": "Medication Administration & Controlled Substances Protocol",
            "department": "Pharmacy & Nursing",
            "protocol_version": "3.0",
            "effective_date": "2026-02-01",
            "expiry_date": "2027-02-01",
            "confidentiality_level": "INTERNAL",
            "allowed_roles": ["Admin", "Hospital Manager", "Doctor", "Nurse"],
            "status": "ACTIVE",
            "document_content": "Guidelines for double-signoff verification on Schedule II narcotic dispensing, automated Pyxis medstation access credentials, and pediatric dosage calculation safeguards."
        },
        {
            "document_id": "DOC-EMG-003",
            "title": "Emergency Disaster Response & Trauma Activation Protocol",
            "department": "Emergency",
            "protocol_version": "1.8",
            "effective_date": "2025-11-10",
            "expiry_date": "2026-11-10",
            "confidentiality_level": "PUBLIC",
            "allowed_roles": ["Admin", "Hospital Manager", "Doctor", "Nurse", "Receptionist", "Intern"],
            "status": "ACTIVE",
            "document_content": "Mass casualty triage code responses (Code Blue, Code Red, Code Amber), trauma surge capacity allocation, and emergency inter-facility patient transport coordination."
        },
        {
            "document_id": "DOC-TRN-004",
            "title": "Inter-Ward Patient Transfer & Handover Protocol",
            "department": "Nursing Operations",
            "protocol_version": "2.0",
            "effective_date": "2026-03-01",
            "expiry_date": "2027-03-01",
            "confidentiality_level": "INTERNAL",
            "allowed_roles": ["Admin", "Hospital Manager", "Doctor", "Nurse"],
            "status": "ACTIVE",
            "document_content": "SBAR (Situation, Background, Assessment, Recommendation) framework for transferring telemetry and ICU patients to step-down care units."
        },
        {
            "document_id": "DOC-HND-005",
            "title": "Shift Handover & Critical Patient Sentinel Report",
            "department": "ICU & Surgery",
            "protocol_version": "4.2",
            "effective_date": "2026-04-10",
            "expiry_date": "2026-10-10",
            "confidentiality_level": "CONFIDENTIAL",
            "allowed_roles": ["Admin", "Hospital Manager", "Doctor"],
            "status": "ACTIVE",
            "document_content": "End-of-shift handover procedures containing sensitive clinical alerts, pending lab culture notifications, and critical patient status reviews."
        },
        {
            "document_id": "DOC-ICU-006",
            "title": "ICU Sepsis Management & Ventilator Bundle Protocol",
            "department": "ICU",
            "protocol_version": "3.5",
            "effective_date": "2026-05-01",
            "expiry_date": "2027-05-01",
            "confidentiality_level": "CONFIDENTIAL",
            "allowed_roles": ["Admin", "Hospital Manager", "Doctor", "Nurse"],
            "status": "ACTIVE",
            "document_content": "Intensive Care protocol for severe sepsis resuscitation, central line-associated bloodstream infection (CLABSI) prevention, and mechanical ventilation weaning criteria."
        },
        {
            "document_id": "DOC-LAB-007",
            "title": "Laboratory Sample Handling & Biohazard Security Protocol",
            "department": "Pathology",
            "protocol_version": "1.5",
            "effective_date": "2026-01-20",
            "expiry_date": "2027-01-20",
            "confidentiality_level": "INTERNAL",
            "allowed_roles": ["Admin", "Hospital Manager", "Doctor", "Nurse", "Receptionist"],
            "status": "ACTIVE",
            "document_content": "Standard chain of custody for high-consequence pathogen samples, pneumatic tube transport restrictions, and centrifuging containment safety."
        },
        {
            "document_id": "DOC-AUD-008",
            "title": "Internal Incident Investigation & Sentinel Malpractice Review",
            "department": "Clinical Risk Management",
            "protocol_version": "1.0",
            "effective_date": "2026-06-01",
            "expiry_date": "2027-06-01",
            "confidentiality_level": "HIGHLY_CONFIDENTIAL",
            "allowed_roles": ["Admin"],
            "status": "ACTIVE",
            "document_content": "Root cause analysis report on internal medication administration errors, staff peer review depositions, and legal risk assessment documentation."
        },
        # Outdated protocol version for testing versioning rule!
        {
            "document_id": "DOC-INF-000",
            "title": "Infection Control & Disinfection Protocol",
            "department": "Infectious Diseases",
            "protocol_version": "1.0",
            "effective_date": "2024-01-01",
            "expiry_date": "2025-12-31",
            "confidentiality_level": "PUBLIC",
            "allowed_roles": ["Admin", "Hospital Manager", "Doctor", "Nurse", "Receptionist", "Intern"],
            "status": "SUPERSEDED",
            "document_content": "Outdated disinfection standards superseded by protocol DOC-INF-001 (v2.1)."
        }
    ]

    docs_file = os.path.join(output_dir, "documents.csv")
    with open(docs_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "document_id", "title", "department", "protocol_version", 
            "effective_date", "expiry_date", "confidentiality_level", 
            "allowed_roles", "document_content", "created_at", "updated_at", "status"
        ])
        writer.writeheader()
        for d in documents:
            d_dict = dict(d)
            d_dict["allowed_roles"] = json.dumps(d_dict["allowed_roles"])
            d_dict["created_at"] = now_str
            d_dict["updated_at"] = now_str
            writer.writerow(d_dict)

    # 3. Document Sections (with explicit sensitive sections & synthetic leakage test markers)
    document_sections = [
        # DOC-INF-001
        {
            "id": "SEC-INF-01",
            "document_id": "DOC-INF-001",
            "section_title": "1. Hand Hygiene & Sanitation",
            "content": "All clinical staff must wash hands using WHO 6-step technique before and after patient contact. Alcohol rub stations are situated at ward entrances.",
            "is_sensitive": False,
            "confidentiality_level": "PUBLIC",
            "restricted_roles": [],
            "sensitivity_reason": None,
            "sequence_order": 1
        },
        {
            "id": "SEC-INF-02",
            "document_id": "DOC-INF-001",
            "section_title": "2. Ward Isolation Procedures",
            "content": "Negative pressure isolation rooms must maintain -2.5 Pa gradient for airborne contagion management.",
            "is_sensitive": False,
            "confidentiality_level": "PUBLIC",
            "restricted_roles": [],
            "sensitivity_reason": None,
            "sequence_order": 2
        },
        # DOC-MED-002
        {
            "id": "SEC-MED-01",
            "document_id": "DOC-MED-002",
            "section_title": "1. General Dispensing Rules",
            "content": "Prescriptions require licensed physician signature and electronic record entry prior to nursing administration.",
            "is_sensitive": False,
            "confidentiality_level": "INTERNAL",
            "restricted_roles": [],
            "sensitivity_reason": None,
            "sequence_order": 1
        },
        {
            "id": "SEC-MED-02",
            "document_id": "DOC-MED-002",
            "section_title": "2. High-Alert Medication Security Codes",
            "content": "[CONFIDENTIAL SENSITIVE] Master vault override pin code is 8842. Fentanyl and Morphine dual-witness inventory key storage location is Pyxis Vault B (Code: SENSITIVE_TEST_001).",
            "is_sensitive": True,
            "confidentiality_level": "CONFIDENTIAL",
            "restricted_roles": ["Nurse", "Receptionist", "Intern"],
            "sensitivity_reason": "Contains secure vault codes and restricted narcotic handling protocols.",
            "sequence_order": 2
        },
        # DOC-HND-005
        {
            "id": "SEC-HND-01",
            "document_id": "DOC-HND-005",
            "section_title": "1. General Shift Handoff Summary",
            "content": "Bed census at 92% capacity. Shift handover completed at 07:00 and 19:00 daily with attending physician present.",
            "is_sensitive": False,
            "confidentiality_level": "INTERNAL",
            "restricted_roles": [],
            "sensitivity_reason": None,
            "sequence_order": 1
        },
        {
            "id": "SEC-HND-02",
            "document_id": "DOC-HND-005",
            "section_title": "2. VIP & Incident Patient Clinical Notes",
            "content": "[CONFIDENTIAL PATIENT DATA] Patient #9948 (Senator J. Doe) admitted under pseudonym 'John Smith'. Internal investigation ongoing regarding potential adverse drug reaction during night shift (Marker: RESTRICTED_TEST_002).",
            "is_sensitive": True,
            "confidentiality_level": "CONFIDENTIAL",
            "restricted_roles": ["Nurse", "Receptionist", "Intern"],
            "sensitivity_reason": "Contains fake patient pseudonym identifier and ongoing internal investigation details.",
            "sequence_order": 2
        },
        # DOC-AUD-008
        {
            "id": "SEC-AUD-01",
            "document_id": "DOC-AUD-008",
            "section_title": "1. Malpractice Risk Assessment",
            "content": "[HIGHLY CONFIDENTIAL] Executive review of pending malpractice claim #2026-88. Peer review witness statements confidential to hospital legal counsel (Marker: HIGHLY_CONFIDENTIAL_TEST_003).",
            "is_sensitive": True,
            "confidentiality_level": "HIGHLY_CONFIDENTIAL",
            "restricted_roles": ["Hospital Manager", "Doctor", "Nurse", "Receptionist", "Intern"],
            "sensitivity_reason": "Contains legal liability depositions and internal sentinel incident investigations.",
            "sequence_order": 1
        }
    ]

    secs_file = os.path.join(output_dir, "document_sections.csv")
    with open(secs_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "document_id", "section_title", "content", 
            "is_sensitive", "confidentiality_level", "restricted_roles", 
            "sensitivity_reason", "sequence_order"
        ])
        writer.writeheader()
        for s in document_sections:
            s_dict = dict(s)
            s_dict["restricted_roles"] = json.dumps(s_dict["restricted_roles"])
            writer.writerow(s_dict)

    # 4. Sharing Requests
    sharing_requests = [
        {
            "request_id": "REQ-SHR-001",
            "requester_id": "USR-NRS-01",
            "recipient_id": "USR-INT-01",
            "document_id": "DOC-HND-005",
            "reason": "Requesting shift handover protocol for intern orientation.",
            "risk_level": "HIGH",
            "status": "PENDING",
            "reviewer_id": None,
            "reviewer_decision": None,
            "override_reason": None
        },
        {
            "request_id": "REQ-SHR-002",
            "requester_id": "USR-DOC-01",
            "recipient_id": "USR-NRS-01",
            "document_id": "DOC-ICU-006",
            "reason": "ICU sepsis protocol sharing for shift assignment.",
            "risk_level": "MEDIUM",
            "status": "APPROVED",
            "reviewer_id": "USR-MGR-01",
            "reviewer_decision": "APPROVE",
            "override_reason": "Authorized clinical access needed for ICU patient care."
        }
    ]

    shares_file = os.path.join(output_dir, "sharing_requests.csv")
    with open(shares_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "request_id", "requester_id", "recipient_id", "document_id", 
            "reason", "requested_at", "risk_level", "recommendation_json", 
            "status", "reviewer_id", "reviewer_decision", "override_reason", "timestamp"
        ])
        writer.writeheader()
        for sr in sharing_requests:
            sr_dict = dict(sr)
            sr_dict["requested_at"] = (datetime.utcnow() - timedelta(hours=2)).isoformat()
            sr_dict["timestamp"] = datetime.utcnow().isoformat()
            sr_dict["recommendation_json"] = json.dumps({
                "recommendation": "Access not recommended." if sr_dict["risk_level"] == "HIGH" else "Sharing permitted.",
                "reason": "Recipient role does not normally have permission." if sr_dict["risk_level"] == "HIGH" else "Authorized.",
                "rule": "Confidential documents require approval.",
                "evidence": f"Risk Level: {sr_dict['risk_level']}",
                "confidence_status": "HIGH_RISK" if sr_dict["risk_level"] == "HIGH" else "AUTHORIZED"
            })
            writer.writerow(sr_dict)

    # 5. Audit Logs
    audit_logs = [
        {
            "event_id": str(uuid.uuid4()),
            "user_id": "USR-DOC-01",
            "role": "Doctor",
            "action": "VIEW_DOCUMENT",
            "document_id": "DOC-MED-002",
            "recipient_id": None,
            "old_state": "CLOSED",
            "new_state": "VIEWED",
            "reason": "Routine clinical protocol review",
            "override_reason": None,
            "timestamp": (datetime.utcnow() - timedelta(hours=4)).isoformat()
        },
        {
            "event_id": str(uuid.uuid4()),
            "user_id": "USR-NRS-01",
            "role": "Nurse",
            "action": "GENERATE_SUMMARY",
            "document_id": "DOC-HND-005",
            "recipient_id": None,
            "old_state": "REQUESTED",
            "new_state": "REDACTED_SUMMARY",
            "reason": "Summarized DOC-HND-005 with 1 sensitive section withheld",
            "override_reason": None,
            "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat()
        }
    ]

    audit_file = os.path.join(output_dir, "audit_logs.csv")
    with open(audit_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "event_id", "user_id", "role", "action", "document_id", 
            "recipient_id", "old_state", "new_state", "reason", "override_reason", "timestamp"
        ])
        writer.writeheader()
        for al in audit_logs:
            writer.writerow(al)

    # 6. Synthetic Event Stream (for duplicate, out-of-order, delayed event testing)
    events = [
        {
            "event_id": "EVT-DOC-101",
            "event_type": "PERMISSION_CHANGED",
            "entity_id": "DOC-MED-002",
            "event_version": 1,
            "sequence_number": 1,
            "timestamp": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
            "payload_json": json.dumps({"confidentiality_level": "INTERNAL"}),
            "processing_status": "PROCESSED"
        },
        # Duplicate of EVT-DOC-101
        {
            "event_id": "EVT-DOC-101",
            "event_type": "PERMISSION_CHANGED",
            "entity_id": "DOC-MED-002",
            "event_version": 1,
            "sequence_number": 1,
            "timestamp": (datetime.utcnow() - timedelta(minutes=29)).isoformat(),
            "payload_json": json.dumps({"confidentiality_level": "INTERNAL"}),
            "processing_status": "IGNORED_DUPLICATE"
        }
    ]

    events_file = os.path.join(output_dir, "events.csv")
    with open(events_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "event_id", "event_type", "entity_id", "event_version", 
            "sequence_number", "timestamp", "payload_json", "processing_status"
        ])
        writer.writeheader()
        for ev in events:
            writer.writerow(ev)

    print("Synthetic data generation finished successfully!")

if __name__ == "__main__":
    generate_synthetic_data(seed=42)
