import os
import sys
import json
import uuid
from datetime import datetime

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database import SessionLocal
from backend.app.events.processor import EventStreamProcessor

def inject_event(
    event_type: str,
    entity_id: str,
    event_version: int,
    sequence_number: int,
    payload: dict,
    event_id: str = None
):
    if not event_id:
        event_id = f"EVT-INJ-{uuid.uuid4().hex[:6].upper()}"

    db = SessionLocal()
    try:
        processor = EventStreamProcessor(db)
        status, msg, details = processor.process_event(
            event_id=event_id,
            event_type=event_type,
            entity_id=entity_id,
            event_version=event_version,
            sequence_number=sequence_number,
            payload=payload
        )
        print(f"[EVENT INJECTION] Status: {status} | Message: {msg}")
        print(f"Details: {json.dumps(details, indent=2)}")
        return {"status": status, "message": msg, "details": details}
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 4:
        e_type = sys.argv[1]
        ent_id = sys.argv[2]
        e_ver = int(sys.argv[3])
        seq_num = int(sys.argv[4])
        payload = json.loads(sys.argv[5]) if len(sys.argv) > 5 else {}
        inject_event(e_type, ent_id, e_ver, seq_num, payload)
    else:
        print("Usage: python inject_events.py <event_type> <entity_id> <event_version> <sequence_number> [payload_json]")
        print("Example duplicate test:")
        inject_event("PERMISSION_CHANGED", "DOC-MED-002", 1, 1, {"confidentiality_level": "INTERNAL"}, event_id="EVT-DUP-DEMO")
        inject_event("PERMISSION_CHANGED", "DOC-MED-002", 1, 1, {"confidentiality_level": "INTERNAL"}, event_id="EVT-DUP-DEMO")
