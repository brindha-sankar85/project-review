import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Admin, Hospital Manager, Doctor, Nurse, Receptionist, Intern
    department = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    protocol_version = Column(String, nullable=False)
    effective_date = Column(String, nullable=False)
    expiry_date = Column(String, nullable=False)
    confidentiality_level = Column(String, nullable=False)  # PUBLIC, INTERNAL, CONFIDENTIAL, HIGHLY_CONFIDENTIAL
    allowed_roles_json = Column(Text, default="[]")  # JSON array of roles allowed
    document_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="ACTIVE")  # ACTIVE, SUPERSEDED, ARCHIVED
    previous_version_id = Column(String, nullable=True)
    current_active_version_id = Column(String, nullable=True)

    sections = relationship("DocumentSection", back_populates="document", cascade="all, delete-orphan")

    @property
    def allowed_roles(self):
        return json.loads(self.allowed_roles_json or "[]")

    @allowed_roles.setter
    def allowed_roles(self, val):
        self.allowed_roles_json = json.dumps(val)

class DocumentSection(Base):
    __tablename__ = "document_sections"

    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.document_id"), nullable=False)
    section_title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    is_sensitive = Column(Boolean, default=False)
    confidentiality_level = Column(String, default="INTERNAL")
    restricted_roles_json = Column(Text, default="[]")  # JSON array of forbidden roles
    sensitivity_reason = Column(String, nullable=True)
    sequence_order = Column(Integer, default=0)

    document = relationship("Document", back_populates="sections")

    @property
    def restricted_roles(self):
        return json.loads(self.restricted_roles_json or "[]")

    @restricted_roles.setter
    def restricted_roles(self, val):
        self.restricted_roles_json = json.dumps(val)

class SharingRequest(Base):
    __tablename__ = "sharing_requests"

    request_id = Column(String, primary_key=True)
    requester_id = Column(String, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(String, ForeignKey("users.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.document_id"), nullable=False)
    reason = Column(Text, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    risk_level = Column(String, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    recommendation_json = Column(Text, default="{}")  # JSON object with recommendation details
    status = Column(String, default="PENDING")  # PENDING, APPROVED, REJECTED, OVERRIDDEN, EXPIRED
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=True)
    reviewer_decision = Column(String, nullable=True)
    override_reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    requester = relationship("User", foreign_keys=[requester_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
    document = relationship("Document", foreign_keys=[document_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

class AuditLog(Base):
    __tablename__ = "audit_logs"

    event_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    action = Column(String, nullable=False)  # VIEW_DOCUMENT, GENERATE_SUMMARY, CREATE_SHARE_REQUEST, APPROVE_SHARE, REJECT_SHARE, OVERRIDE_RESTRICTION, CHANGE_PERMISSION, REDACT_CONTENT
    document_id = Column(String, nullable=True)
    recipient_id = Column(String, nullable=True)
    old_state = Column(Text, nullable=True)
    new_state = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    override_reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    event_version = Column(Integer, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    payload_json = Column(Text, nullable=False)
    processing_status = Column(String, default="PROCESSED")  # PROCESSED, IGNORED_DUPLICATE, OUT_OF_ORDER_BUFFERED, DISCARDED_STALE

class EventProcessing(Base):
    __tablename__ = "event_processing"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String, unique=True, nullable=False)
    last_processed_version = Column(Integer, default=0)
    last_sequence_number = Column(Integer, default=0)
    status = Column(String, default="HEALTHY")
    updated_at = Column(DateTime, default=datetime.utcnow)

class ExperimentResult(Base):
    __tablename__ = "experiment_results"

    id = Column(String, primary_key=True)
    run_name = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    baseline_value = Column(Float, nullable=False)
    target_value = Column(Float, nullable=False)
    proposed_value = Column(Float, nullable=False)
    unit = Column(String, default="%")
    status = Column(String, default="PASSED")
    timestamp = Column(DateTime, default=datetime.utcnow)

class FailureTestCase(Base):
    __tablename__ = "test_results"

    test_id = Column(String, primary_key=True)
    scenario = Column(String, nullable=False)
    expected_result = Column(Text, nullable=False)
    actual_result = Column(Text, nullable=False)
    failure_reason = Column(Text, nullable=True)
    corrective_action = Column(Text, nullable=True)
    status = Column(String, nullable=False)  # PASSED, FAILED, RESOLVED
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserValidation(Base):
    __tablename__ = "user_validations"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    recommendation_clear = Column(Boolean, default=True)
    reason_clear = Column(Boolean, default=True)
    access_decision_clear = Column(Boolean, default=True)
    summary_useful = Column(Boolean, default=True)
    approval_workflow_clear = Column(Boolean, default=True)
    evidence_sufficient = Column(Boolean, default=True)
    usability_rating = Column(Integer, default=5)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
