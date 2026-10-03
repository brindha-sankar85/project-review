import os
import sys
import csv
import json
from datetime import datetime

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database import engine, Base, SessionLocal
from backend.app.models.schema import User, Document, DocumentSection, SharingRequest, AuditLog, Event, EventProcessing, ExperimentResult, FailureTestCase, UserValidation
from scripts.generate_data import generate_synthetic_data

def init_db(seed_data: bool = True, force_reset: bool = False):
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if re-seeding is forced or needed
        if force_reset:
            print("Resetting existing database records...")
            db.query(AuditLog).delete()
            db.query(SharingRequest).delete()
            db.query(DocumentSection).delete()
            db.query(Document).delete()
            db.query(User).delete()
            db.query(EventProcessing).delete()
            db.query(Event).delete()
            db.commit()

        if db.query(User).count() == 0 and seed_data:
            print("Seeding database with synthetic hospital data...")
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "synthetic")
            
            # Ensure synthetic data exists
            generate_synthetic_data(seed=42, output_dir=data_dir)

            # Load Users
            with open(os.path.join(data_dir, "users.csv"), "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    u = User(
                        id=row["id"],
                        username=row["username"],
                        name=row["name"],
                        role=row["role"],
                        department=row["department"],
                        created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else datetime.utcnow()
                    )
                    db.add(u)

            # Load Documents
            with open(os.path.join(data_dir, "documents.csv"), "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    d = Document(
                        document_id=row["document_id"],
                        title=row["title"],
                        department=row["department"],
                        protocol_version=row["protocol_version"],
                        effective_date=row["effective_date"],
                        expiry_date=row["expiry_date"],
                        confidentiality_level=row["confidentiality_level"],
                        allowed_roles_json=row["allowed_roles"],
                        document_content=row["document_content"],
                        created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else datetime.utcnow(),
                        updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else datetime.utcnow(),
                        status=row["status"]
                    )
                    db.add(d)

            db.commit()

            # Load Document Sections
            with open(os.path.join(data_dir, "document_sections.csv"), "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ds = DocumentSection(
                        id=row["id"],
                        document_id=row["document_id"],
                        section_title=row["section_title"],
                        content=row["content"],
                        is_sensitive=row["is_sensitive"].lower() == "true",
                        confidentiality_level=row["confidentiality_level"],
                        restricted_roles_json=row["restricted_roles"],
                        sensitivity_reason=row["sensitivity_reason"],
                        sequence_order=int(row["sequence_order"])
                    )
                    db.add(ds)

            # Load Sharing Requests
            with open(os.path.join(data_dir, "sharing_requests.csv"), "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sr = SharingRequest(
                        request_id=row["request_id"],
                        requester_id=row["requester_id"],
                        recipient_id=row["recipient_id"],
                        document_id=row["document_id"],
                        reason=row["reason"],
                        requested_at=datetime.fromisoformat(row["requested_at"]),
                        risk_level=row["risk_level"],
                        recommendation_json=row["recommendation_json"],
                        status=row["status"],
                        reviewer_id=row.get("reviewer_id") if row.get("reviewer_id") != "" else None,
                        reviewer_decision=row.get("reviewer_decision") if row.get("reviewer_decision") != "" else None,
                        override_reason=row.get("override_reason") if row.get("override_reason") != "" else None,
                        timestamp=datetime.fromisoformat(row["timestamp"])
                    )
                    db.add(sr)

            # Load Audit Logs
            with open(os.path.join(data_dir, "audit_logs.csv"), "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    al = AuditLog(
                        event_id=row["event_id"],
                        user_id=row["user_id"],
                        role=row["role"],
                        action=row["action"],
                        document_id=row["document_id"] if row.get("document_id") != "" else None,
                        recipient_id=row["recipient_id"] if row.get("recipient_id") != "" else None,
                        old_state=row["old_state"],
                        new_state=row["new_state"],
                        reason=row["reason"],
                        override_reason=row.get("override_reason") if row.get("override_reason") != "" else None,
                        timestamp=datetime.fromisoformat(row["timestamp"])
                    )
                    db.add(al)

            # Initialize event processing state tracker for DOC-MED-002
            ep = EventProcessing(
                entity_id="DOC-MED-002",
                last_processed_version=1,
                last_sequence_number=1,
                status="HEALTHY"
            )
            db.add(ep)

            db.commit()
            print("Database successfully initialized and seeded!")
        else:
            print("Database tables verified.")

    finally:
        db.close()

if __name__ == "__main__":
    init_db(seed_data=True)
