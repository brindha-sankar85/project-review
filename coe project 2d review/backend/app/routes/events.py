from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.app.database import get_db
from backend.app.models.schema import Event, EventProcessing
from backend.app.events.processor import EventStreamProcessor

router = APIRouter(prefix="/api/events", tags=["Event Stream Processor"])

class EventInjectPayload(BaseModel):
    event_id: Optional[str] = None
    event_type: str  # PERMISSION_CHANGED, PROTOCOL_SUPERSEDED
    entity_id: str
    event_version: int
    sequence_number: int
    payload: Dict[str, Any]

@router.post("/inject")
def inject_event(payload: EventInjectPayload, db: Session = Depends(get_db)):
    """
    Injects an event into the stream to test duplicate, delayed, and out-of-order handling.
    """
    processor = EventStreamProcessor(db)
    
    status, msg, details = processor.process_event(
        event_id=payload.event_id or f"EVT-{payload.event_type[:3]}-{payload.sequence_number}",
        event_type=payload.event_type,
        entity_id=payload.entity_id,
        event_version=payload.event_version,
        sequence_number=payload.sequence_number,
        payload=payload.payload
    )

    return {
        "success": True,
        "processing_status": status,
        "message": msg,
        "details": details
    }

@router.get("/stream")
def list_event_stream(entity_id: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    """Returns the recorded event log and entity state version trackers."""
    query = db.query(Event)
    if entity_id:
        query = query.filter(Event.entity_id == entity_id)

    events = query.order_by(Event.timestamp.desc()).limit(limit).all()

    trackers = db.query(EventProcessing).all()

    return {
        "events": [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "entity_id": e.entity_id,
                "event_version": e.event_version,
                "sequence_number": e.sequence_number,
                "timestamp": e.timestamp.isoformat(),
                "payload": e.payload_json,
                "processing_status": e.processing_status
            } for e in events
        ],
        "entity_trackers": [
            {
                "entity_id": t.entity_id,
                "last_processed_version": t.last_processed_version,
                "last_sequence_number": t.last_sequence_number,
                "status": t.status,
                "updated_at": t.updated_at.isoformat()
            } for t in trackers
        ]
    }
