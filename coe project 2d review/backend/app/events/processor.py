import json
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from backend.app.models.schema import Event, EventProcessing, Document, AuditLog

class EventStreamProcessor:
    """
    Resilient Event Processing System handling delayed, duplicate, and out-of-order events
    without state corruption.
    """
    def __init__(self, db: Session):
        self.db = db

    def process_event(
        self, 
        event_id: str,
        event_type: str,
        entity_id: str,
        event_version: int,
        sequence_number: int,
        payload: Dict[str, Any],
        timestamp: datetime = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Processes an incoming event with strict idempotency and version control checks.
        Returns (processing_status, message, details)
        """
        if not timestamp:
            timestamp = datetime.utcnow()

        payload_str = json.dumps(payload)

        # 1. Check if event_id already exists (Duplicate event check)
        existing_event = self.db.query(Event).filter(Event.event_id == event_id).first()
        if existing_event:
            return "IGNORED_DUPLICATE", f"Duplicate event ID {event_id} ignored. State preserved.", {
                "event_id": event_id,
                "reason": "Duplicate event ID detected.",
                "action_taken": "No state change."
            }

        # 2. Fetch or initialize Entity Processing Record
        tracker = self.db.query(EventProcessing).filter(EventProcessing.entity_id == entity_id).first()
        if not tracker:
            tracker = EventProcessing(
                entity_id=entity_id,
                last_processed_version=0,
                last_sequence_number=0,
                status="HEALTHY",
                updated_at=datetime.utcnow()
            )
            self.db.add(tracker)
            self.db.flush()

        last_v = tracker.last_processed_version

        # 3. Check for Stale / Delayed Event (out-of-date version)
        if event_version <= last_v:
            # Event is delayed/stale - entity state has already advanced beyond this version
            evt = Event(
                event_id=event_id,
                event_type=event_type,
                entity_id=entity_id,
                event_version=event_version,
                sequence_number=sequence_number,
                timestamp=timestamp,
                payload_json=payload_str,
                processing_status="DISCARDED_STALE"
            )
            self.db.add(evt)
            self.db.commit()

            return "DISCARDED_STALE", f"Delayed event version {event_version} discarded. Entity state already at version {last_v}.", {
                "event_id": event_id,
                "current_version": last_v,
                "incoming_version": event_version,
                "action_taken": "Discarded stale update to prevent state corruption."
            }

        # 4. Check for Out-of-Order Event (gap in version numbers)
        if event_version > last_v + 1:
            # Missing intermediate events - buffer this out-of-order event
            evt = Event(
                event_id=event_id,
                event_type=event_type,
                entity_id=entity_id,
                event_version=event_version,
                sequence_number=sequence_number,
                timestamp=timestamp,
                payload_json=payload_str,
                processing_status="OUT_OF_ORDER_BUFFERED"
            )
            self.db.add(evt)
            self.db.commit()

            return "OUT_OF_ORDER_BUFFERED", f"Out-of-order event version {event_version} buffered. Waiting for missing version {last_v + 1}.", {
                "event_id": event_id,
                "expected_version": last_v + 1,
                "incoming_version": event_version,
                "action_taken": "Buffered in state queue. Current state unchanged."
            }

        # 5. Event is strictly in sequence (event_version == last_v + 1): Process State Change
        evt = Event(
            event_id=event_id,
            event_type=event_type,
            entity_id=entity_id,
            event_version=event_version,
            sequence_number=sequence_number,
            timestamp=timestamp,
            payload_json=payload_str,
            processing_status="PROCESSED"
        )
        self.db.add(evt)

        # Apply state transition logic based on event type
        self._apply_event_state(event_type, entity_id, payload)

        # Update tracker
        tracker.last_processed_version = event_version
        tracker.last_sequence_number = sequence_number
        tracker.updated_at = datetime.utcnow()

        # Audit log for event processing
        audit = AuditLog(
            event_id=str(uuid.uuid4()),
            user_id="SYSTEM_EVENT_PROCESSOR",
            role="SYSTEM",
            action="CHANGE_PERMISSION" if "PERMISSION" in event_type else "UPDATE_STATE",
            document_id=entity_id if "DOC" in event_type or "PERMISSION" in event_type else None,
            old_state=f"VERSION_{last_v}",
            new_state=f"VERSION_{event_version}",
            reason=f"Processed in-sequence event {event_type} (v{event_version})",
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)
        self.db.commit()

        # 6. Check if any buffered out-of-order events can now be drain-processed in sequence
        drained_count = self._drain_buffered_events(entity_id)

        return "PROCESSED", f"Event v{event_version} processed successfully. State updated.", {
            "event_id": event_id,
            "new_version": event_version,
            "drained_buffered_events": drained_count,
            "action_taken": "State updated cleanly."
        }

    def _apply_event_state(self, event_type: str, entity_id: str, payload: Dict[str, Any]):
        """Applies state mutation to database models."""
        if event_type == "PERMISSION_CHANGED":
            doc = self.db.query(Document).filter(Document.document_id == entity_id).first()
            if doc:
                if "confidentiality_level" in payload:
                    doc.confidentiality_level = payload["confidentiality_level"]
                if "allowed_roles" in payload:
                    doc.allowed_roles = payload["allowed_roles"]

        elif event_type == "PROTOCOL_SUPERSEDED":
            doc = self.db.query(Document).filter(Document.document_id == entity_id).first()
            if doc:
                doc.status = "SUPERSEDED"
                if "current_active_version_id" in payload:
                    doc.current_active_version_id = payload["current_active_version_id"]

    def _drain_buffered_events(self, entity_id: str) -> int:
        """Processes any buffered out-of-order events that now match sequence."""
        drained = 0
        while True:
            tracker = self.db.query(EventProcessing).filter(EventProcessing.entity_id == entity_id).first()
            next_v = tracker.last_processed_version + 1

            next_buffered = self.db.query(Event).filter(
                Event.entity_id == entity_id,
                Event.event_version == next_v,
                Event.processing_status == "OUT_OF_ORDER_BUFFERED"
            ).first()

            if not next_buffered:
                break

            # Process buffered event
            payload = json.loads(next_buffered.payload_json or "{}")
            self._apply_event_state(next_buffered.event_type, entity_id, payload)
            next_buffered.processing_status = "PROCESSED"
            tracker.last_processed_version = next_v
            drained += 1

        if drained > 0:
            self.db.commit()
        return drained
