"""SQLAlchemy database models for Tiger ID (SQLite-only)"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, ForeignKey, Index, text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.types import TypeDecorator
from datetime import datetime
import uuid
import enum
import json


# Create declarative base
Base = declarative_base()


# Helper functions for UUID and JSON handling
def generate_uuid():
    """Generate a new UUID string"""
    return str(uuid.uuid4())


def json_default(value):
    """Return JSON string default for SQLite Text columns"""
    return json.dumps(value) if value else '{}'


class JSONEncodedValue(TypeDecorator):
    """
    Custom type for storing JSON-serializable values (lists/dicts) in SQLite Text columns.
    Automatically handles serialization to JSON strings on write and deserialization on read.
    """
    impl = Text
    cache_ok = True

    def __init__(self, default_factory=list):
        super().__init__()
        self._default_factory = default_factory

    def process_bind_param(self, value, dialect):
        """Serialize Python value to JSON string for database storage"""
        if value is None:
            return json.dumps(self._default_factory())
        if isinstance(value, str):
            # Already a JSON string, validate and return
            try:
                json.loads(value)
                return value
            except json.JSONDecodeError:
                # Invalid JSON string, wrap in quotes
                return json.dumps(value)
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        """Deserialize JSON string from database to Python value"""
        if value is None:
            return self._default_factory()
        if isinstance(value, (list, dict)):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return self._default_factory()


# Convenience aliases
JSONList = lambda: JSONEncodedValue(default_factory=list)
JSONDict = lambda: JSONEncodedValue(default_factory=dict)


# Enum types (using Python enums for type hints, stored as strings in SQLite)
class TigerStatus(enum.Enum):
    active = "active"
    monitored = "monitored"
    seized = "seized"
    deceased = "deceased"


class SideView(enum.Enum):
    left = "left"
    right = "right"
    both = "both"
    unknown = "unknown"


class InvestigationStatus(enum.Enum):
    draft = "draft"
    active = "active"
    pending_verification = "pending_verification"
    completed = "completed"
    archived = "archived"
    cancelled = "cancelled"


class Priority(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class EvidenceSourceType(enum.Enum):
    image = "image"
    web_search = "web_search"
    document = "document"
    user_input = "user_input"


class EntityType(enum.Enum):
    tiger = "tiger"
    facility = "facility"
    evidence = "evidence"
    investigation = "investigation"


class VerificationStatus(enum.Enum):
    pending = "pending"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"


class UserRole(enum.Enum):
    investigator = "investigator"
    analyst = "analyst"
    supervisor = "supervisor"
    admin = "admin"


class ModelType(enum.Enum):
    detection = "detection"
    reid = "reid"
    pose = "pose"


# User model
class User(Base):
    """User account model"""
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.investigator.value, index=True)
    permissions = Column(Text, default='{}')
    department = Column(String(100))
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    api_key_hash = Column(String(255))
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    investigations = relationship("Investigation", back_populates="creator")
    sessions = relationship("UserSession", back_populates="user")


# Facility model
class Facility(Base):
    """Facility/exhibitor model"""
    __tablename__ = "facilities"

    facility_id = Column(String(36), primary_key=True, default=generate_uuid)
    exhibitor_name = Column(String(255), nullable=False, index=True)
    usda_license = Column(String(100), index=True)
    state = Column(String(50), index=True)
    city = Column(String(100))
    address = Column(Text)
    tiger_count = Column(Integer, default=0)
    tiger_capacity = Column(Integer)
    social_media_links = Column(JSONDict())  # JSON dict for social media links
    website = Column(String(500))
    ir_date = Column(DateTime)
    last_inspection_date = Column(DateTime)
    accreditation_status = Column(String(100))
    violation_history = Column(JSONList())  # JSON list of violations
    last_crawled_at = Column(DateTime)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), onupdate=datetime.utcnow)

    # Reference data fields (from migration 003)
    is_reference_facility = Column(Boolean, default=False, nullable=False, index=True)
    data_source = Column(String(100), index=True)
    reference_dataset_version = Column(DateTime)
    reference_metadata = Column(Text, default='{}')

    # Location fields (from migration 005)
    coordinates = Column(Text)  # JSON: {"latitude": float, "longitude": float, "geocoded_at": timestamp, "confidence": str}

    # Discovery tracking (from migration 006)
    discovered_at = Column(DateTime)  # When facility was auto-discovered
    discovered_by_investigation_id = Column(String(36), ForeignKey("investigations.investigation_id"))

    # Relationships
    tigers = relationship("Tiger", back_populates="origin_facility")
    crawl_history = relationship("CrawlHistory", back_populates="facility")


# Tiger model
class Tiger(Base):
    """Tiger individual model"""
    __tablename__ = "tigers"

    tiger_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), index=True)
    alias = Column(String(255))
    origin_facility_id = Column(String(36), ForeignKey("facilities.facility_id"))
    last_seen_location = Column(String(255))
    last_seen_date = Column(DateTime)
    status = Column(String(50), default=TigerStatus.active.value, index=True)
    tags = Column(JSONList())  # JSON list of tags
    notes = Column(Text)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), onupdate=datetime.utcnow)

    # Discovery tracking (from migration 006)
    is_reference = Column(Boolean, default=False, nullable=False, index=True)  # True = ATRW reference data only
    discovered_at = Column(DateTime)  # When tiger was discovered through investigation
    discovered_by_investigation_id = Column(String(36), ForeignKey("investigations.investigation_id"))
    discovery_confidence = Column(Float)  # Gemini confidence in discovery

    # Relationships
    origin_facility = relationship("Facility", back_populates="tigers")
    images = relationship("TigerImage", back_populates="tiger")


# TigerImage model
class TigerImage(Base):
    """Tiger image - embeddings stored in sqlite-vec virtual table"""
    __tablename__ = "tiger_images"

    image_id = Column(String(36), primary_key=True, default=generate_uuid)
    tiger_id = Column(String(36), ForeignKey("tigers.tiger_id"), index=True)
    image_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500))
    # Note: embeddings stored in vec_embeddings virtual table, not here
    side_view = Column(String(50), default=SideView.unknown.value)
    pose_keypoints = Column(Text)
    meta_data = Column("metadata", Text, default='{}')  # Use meta_data as Python attr, metadata as DB column
    quality_score = Column(Float)
    verified = Column(Boolean, default=False, index=True)
    uploaded_by = Column(String(36), ForeignKey("users.user_id"))
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # Discovery tracking (from migration 006)
    is_reference = Column(Boolean, default=False, nullable=False, index=True)  # True = ATRW/reference, False = real tiger
    discovered_by_investigation_id = Column(String(36), ForeignKey("investigations.investigation_id"))

    # Deduplication (SHA256 content hash)
    content_hash = Column(String(64), index=True, nullable=True)
    is_duplicate_of = Column(String(36), ForeignKey("tiger_images.image_id"), nullable=True)

    # Relationships
    tiger = relationship("Tiger", back_populates="images")
    duplicate_of = relationship("TigerImage", remote_side=[image_id], foreign_keys=[is_duplicate_of])


# Investigation model
class Investigation(Base):
    """Investigation model"""
    __tablename__ = "investigations"

    investigation_id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    status = Column(String(50), default=InvestigationStatus.draft.value, index=True)
    priority = Column(String(50), default=Priority.medium.value, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    summary = Column(JSONDict())  # JSON dict for investigation summary
    tags = Column(JSONList())  # JSON list of tags
    assigned_to = Column(JSONList())  # JSON list of assigned user IDs
    related_tigers = Column(JSONList())  # JSON list of related tiger IDs
    related_facilities = Column(JSONList())  # JSON list of related facility IDs
    methodology = Column(JSONList())  # Reasoning chain steps from Investigation 2.0 workflow
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), onupdate=datetime.utcnow)

    # Source tracking for auto-discovery integration
    source = Column(String(50), default="user_upload", index=True)  # "user_upload" or "auto_discovery"
    source_tiger_id = Column(String(36), index=True)  # Tiger ID that triggered auto-investigation
    source_image_id = Column(String(36), index=True)  # Image ID that triggered auto-investigation
    
    # Relationships
    creator = relationship("User", back_populates="investigations")
    steps = relationship("InvestigationStep", back_populates="investigation")
    evidence = relationship("Evidence", back_populates="investigation")
    comments = relationship("InvestigationComment", back_populates="investigation")
    annotations = relationship("InvestigationAnnotation", back_populates="investigation")


# InvestigationStep model
class InvestigationStep(Base):
    """Investigation step/agent activity model"""
    __tablename__ = "investigation_steps"

    step_id = Column(String(36), primary_key=True, default=generate_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.investigation_id"), nullable=False, index=True)
    step_type = Column(String(100), nullable=False)
    agent_name = Column(String(100))
    status = Column(String(50), nullable=False)
    result = Column(JSONDict())  # JSON dict for step result
    error_message = Column(Text)
    duration_ms = Column(Integer)
    timestamp = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), index=True)
    parent_step_id = Column(String(36), ForeignKey("investigation_steps.step_id"))
    
    # Relationships
    investigation = relationship("Investigation", back_populates="steps")


# Evidence model
class Evidence(Base):
    """Evidence model"""
    __tablename__ = "evidence"

    evidence_id = Column(String(36), primary_key=True, default=generate_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.investigation_id"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, index=True)
    source_url = Column(String(500))
    content = Column(JSONDict())  # JSON dict for evidence content
    extracted_text = Column(Text)
    relevance_score = Column(Float)
    verified = Column(Boolean, default=False, index=True)
    verified_by = Column(String(36), ForeignKey("users.user_id"))
    verification_date = Column(DateTime)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    investigation = relationship("Investigation", back_populates="evidence")
    annotations = relationship("InvestigationAnnotation", back_populates="evidence")


# VerificationQueue model
class VerificationQueue(Base):
    """Verification queue model"""
    __tablename__ = "verification_queue"

    queue_id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)
    priority = Column(String(50), default=Priority.medium.value, index=True)
    requires_human_review = Column(Boolean, default=True)
    assigned_to = Column(String(36), ForeignKey("users.user_id"))
    reviewed_by = Column(String(36), ForeignKey("users.user_id"))
    status = Column(String(50), default=VerificationStatus.pending.value, index=True)
    review_notes = Column(Text)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    reviewed_at = Column(DateTime)

    # Source tracking for auto-discovery integration
    source = Column(String(50), index=True)  # "auto_discovery" or "user_upload"
    investigation_id = Column(String(36), ForeignKey("investigations.investigation_id"))  # Source investigation

    __table_args__ = (
        Index("idx_queue_entity", "entity_type", "entity_id"),
        Index("idx_queue_source", "source"),
    )


# UserSession model
class UserSession(Base):
    """User session model"""
    __tablename__ = "user_sessions"

    session_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    user = relationship("User", back_populates="sessions")


# InvestigationTemplate model
class InvestigationTemplate(Base):
    """Investigation template model"""
    __tablename__ = "investigation_templates"

    template_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    workflow_steps = Column(JSONList())  # JSON list of workflow steps
    default_agents = Column(JSONList())  # JSON list of default agents
    created_by = Column(String(36), ForeignKey("users.user_id"))
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


# SavedSearch model
class SavedSearch(Base):
    """Saved search model"""
    __tablename__ = "saved_searches"

    search_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    name = Column(String(255), nullable=False)
    search_criteria = Column(Text, default='{}')
    alert_enabled = Column(Boolean, default=False)
    last_executed = Column(DateTime)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


# InvestigationComment model
class InvestigationComment(Base):
    """Investigation comment model"""
    __tablename__ = "investigation_comments"

    comment_id = Column(String(36), primary_key=True, default=generate_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.investigation_id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_comment_id = Column(String(36), ForeignKey("investigation_comments.comment_id"))
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    edited_at = Column(DateTime)
    
    # Relationships
    investigation = relationship("Investigation", back_populates="comments")


# InvestigationAnnotation model
class InvestigationAnnotation(Base):
    """Investigation annotation model"""
    __tablename__ = "investigation_annotations"

    annotation_id = Column(String(36), primary_key=True, default=generate_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.investigation_id"), nullable=False)
    evidence_id = Column(String(36), ForeignKey("evidence.evidence_id"))
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    annotation_type = Column(String(100), nullable=False)
    coordinates = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    investigation = relationship("Investigation", back_populates="annotations")
    evidence = relationship("Evidence", back_populates="annotations")


# EvidenceLink model
class EvidenceLink(Base):
    """Evidence link model"""
    __tablename__ = "evidence_links"

    link_id = Column(String(36), primary_key=True, default=generate_uuid)
    source_evidence_id = Column(String(36), ForeignKey("evidence.evidence_id"), nullable=False)
    target_evidence_id = Column(String(36), ForeignKey("evidence.evidence_id"), nullable=False)
    link_type = Column(String(100), nullable=False)
    strength = Column(Float)
    created_by = Column(String(36), ForeignKey("users.user_id"))
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


# ModelVersion model
class ModelVersion(Base):
    """Model version model"""
    __tablename__ = "model_versions"

    model_id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(100), nullable=False, index=True)  # e.g., 'wildlife_tools', 'tiger_reid'
    model_type = Column(String(50), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    path = Column(String(500), nullable=False)
    training_data_hash = Column(String(100))
    metrics = Column(Text, default='{}')
    is_active = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


# ModelInference model
class ModelInference(Base):
    """Model inference model"""
    __tablename__ = "model_inferences"

    inference_id = Column(String(36), primary_key=True, default=generate_uuid)
    model_id = Column(String(36), ForeignKey("model_versions.model_id"), nullable=False, index=True)
    input_data_hash = Column(String(100))
    output = Column(Text, default='{}')
    confidence = Column(Float)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), index=True)


# Notification model
class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"

    notification_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    related_entity_type = Column(String(100))
    related_entity_id = Column(String(36))
    read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), index=True)


# BackgroundJob model
class BackgroundJob(Base):
    """Background job model"""
    __tablename__ = "background_jobs"

    job_id = Column(String(36), primary_key=True, default=generate_uuid)
    job_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    parameters = Column(Text, default='{}')
    result = Column(Text, default='{}')
    error_message = Column(Text)
    started_at = Column(DateTime, index=True)
    completed_at = Column(DateTime)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


# DataExport model
class DataExport(Base):
    """Data export model"""
    __tablename__ = "data_exports"

    export_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    export_type = Column(String(100), nullable=False)
    filters = Column(Text, default='{}')
    file_path = Column(String(500))
    status = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    expires_at = Column(DateTime, index=True)


# SystemMetric model
class SystemMetric(Base):
    """System metric model"""
    __tablename__ = "system_metrics"

    metric_id = Column(String(36), primary_key=True, default=generate_uuid)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), index=True)
    tags = Column(Text, default='{}')


# Feedback model
class Feedback(Base):
    """Feedback model"""
    __tablename__ = "feedback"

    feedback_id = Column(String(36), primary_key=True, default=generate_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.investigation_id"))
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    feedback_type = Column(String(100), nullable=False)
    content = Column(Text, default='{}')
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


# CrawlHistory model
class CrawlHistory(Base):
    """Crawl history model"""
    __tablename__ = "crawl_history"

    crawl_id = Column(String(36), primary_key=True, default=generate_uuid)
    facility_id = Column(String(36), ForeignKey("facilities.facility_id"), index=True)
    source_url = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    images_found = Column(Integer, default=0)
    tigers_identified = Column(Integer, default=0)
    crawled_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), index=True)

    # Enhanced fields from migration 003
    pages_crawled = Column(Integer, default=0)
    total_content_size = Column(Integer)
    crawl_duration_ms = Column(Integer)
    error_message = Column(Text)
    error_log = Column(JSONList())  # JSON list of error logs
    retry_count = Column(Integer, default=0)
    content_changes_detected = Column(Boolean, default=False)
    change_summary = Column(Text, default='{}')
    crawl_statistics = Column(Text, default='{}')
    completed_at = Column(DateTime)
    
    # Relationships
    facility = relationship("Facility", back_populates="crawl_history")


# Password reset token model
class PasswordResetToken(Base):
    """Password reset token model"""
    __tablename__ = "password_reset_tokens"

    token_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    # Relationships
    user = relationship("User", backref="password_reset_tokens")