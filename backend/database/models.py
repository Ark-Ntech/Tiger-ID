"""SQLAlchemy database models for Tiger ID"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid
import enum


# Create declarative base
Base = declarative_base()


# Enum types (using Python enums for type hints, database uses PostgreSQL enums)
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
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.investigator, index=True)
    permissions = Column(JSON, default=dict)
    department = Column(String(100))
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    api_key_hash = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    investigations = relationship("Investigation", back_populates="creator")
    sessions = relationship("UserSession", back_populates="user")


# Facility model
class Facility(Base):
    """Facility/exhibitor model"""
    __tablename__ = "facilities"
    
    facility_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exhibitor_name = Column(String(255), nullable=False, index=True)
    usda_license = Column(String(100), index=True)
    state = Column(String(50), index=True)
    city = Column(String(100))
    address = Column(Text)
    tiger_count = Column(Integer, default=0)
    tiger_capacity = Column(Integer)
    social_media_links = Column(JSON, default=dict)
    website = Column(String(500))
    ir_date = Column(DateTime)
    last_inspection_date = Column(DateTime)
    accreditation_status = Column(String(100))
    violation_history = Column(JSON, default=list)
    last_crawled_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Reference data fields (from migration 003)
    is_reference_facility = Column(Boolean, default=False, nullable=False, index=True)
    data_source = Column(String(100), index=True)
    reference_dataset_version = Column(DateTime)
    reference_metadata = Column(JSON, default=dict)  # This is fine as it's not a direct attribute name conflict

    # Location fields (from migration 005)
    coordinates = Column(JSON)  # {"latitude": float, "longitude": float, "geocoded_at": timestamp, "confidence": str}

    # Discovery tracking (from migration 006)
    discovered_at = Column(DateTime)  # When facility was auto-discovered
    discovered_by_investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.investigation_id"))

    # Relationships
    tigers = relationship("Tiger", back_populates="origin_facility")
    crawl_history = relationship("CrawlHistory", back_populates="facility")


# Tiger model
class Tiger(Base):
    """Tiger individual model"""
    __tablename__ = "tigers"
    
    tiger_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), index=True)
    alias = Column(String(255))
    origin_facility_id = Column(UUID(as_uuid=True), ForeignKey("facilities.facility_id"))
    last_seen_location = Column(String(255))
    last_seen_date = Column(DateTime)
    status = Column(SQLEnum(TigerStatus), default=TigerStatus.active, index=True)
    tags = Column(JSON, default=list)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Discovery tracking (from migration 006)
    is_reference = Column(Boolean, default=False, nullable=False, index=True)  # True = ATRW reference data only
    discovered_at = Column(DateTime)  # When tiger was discovered through investigation
    discovered_by_investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.investigation_id"))
    discovery_confidence = Column(Float)  # Gemini confidence in discovery

    # Relationships
    origin_facility = relationship("Facility", back_populates="tigers")
    images = relationship("TigerImage", back_populates="tiger")


# TigerImage model
class TigerImage(Base):
    """Tiger image with vector embedding"""
    __tablename__ = "tiger_images"
    
    image_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tiger_id = Column(UUID(as_uuid=True), ForeignKey("tigers.tiger_id"), index=True)
    image_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500))
    embedding = Column(Vector(2048))  # ResNet50 embeddings are 2048-dimensional
    side_view = Column(SQLEnum(SideView), default=SideView.unknown)
    pose_keypoints = Column(JSON)
    meta_data = Column("metadata", JSON, default=dict)  # Use meta_data as Python attr, metadata as DB column
    quality_score = Column(Float)
    verified = Column(Boolean, default=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime, server_default=func.now())

    # Discovery tracking (from migration 006)
    is_reference = Column(Boolean, default=False, nullable=False, index=True)  # True = ATRW/reference, False = real tiger
    discovered_by_investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.investigation_id"))

    # Relationships
    tiger = relationship("Tiger", back_populates="images")


# Investigation model
class Investigation(Base):
    """Investigation model"""
    __tablename__ = "investigations"
    
    investigation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    status = Column(SQLEnum(InvestigationStatus), default=InvestigationStatus.draft, index=True)
    priority = Column(SQLEnum(Priority), default=Priority.medium, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    summary = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    assigned_to = Column(JSON, default=list)
    related_tigers = Column(JSON, default=list)
    related_facilities = Column(JSON, default=list)
    methodology = Column(JSON, default=list)  # Reasoning chain steps from Investigation 2.0 workflow (from migration 005)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
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
    
    step_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.investigation_id"), nullable=False, index=True)
    step_type = Column(String(100), nullable=False)
    agent_name = Column(String(100))
    status = Column(String(50), nullable=False)
    result = Column(JSON, default=dict)
    error_message = Column(Text)
    duration_ms = Column(Integer)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    parent_step_id = Column(UUID(as_uuid=True), ForeignKey("investigation_steps.step_id"))
    
    # Relationships
    investigation = relationship("Investigation", back_populates="steps")


# Evidence model
class Evidence(Base):
    """Evidence model"""
    __tablename__ = "evidence"
    
    evidence_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.investigation_id"), nullable=False, index=True)
    source_type = Column(SQLEnum(EvidenceSourceType), nullable=False, index=True)
    source_url = Column(String(500))
    content = Column(JSON, default=dict)
    extracted_text = Column(Text)
    relevance_score = Column(Float)
    verified = Column(Boolean, default=False, index=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    verification_date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    investigation = relationship("Investigation", back_populates="evidence")
    annotations = relationship("InvestigationAnnotation", back_populates="evidence")


# VerificationQueue model
class VerificationQueue(Base):
    """Verification queue model"""
    __tablename__ = "verification_queue"
    
    queue_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(SQLEnum(EntityType), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    priority = Column(SQLEnum(Priority), default=Priority.medium, index=True)
    requires_human_review = Column(Boolean, default=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.pending, index=True)
    review_notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    reviewed_at = Column(DateTime)
    
    __table_args__ = (
        Index("idx_queue_entity", "entity_type", "entity_id"),
    )


# UserSession model
class UserSession(Base):
    """User session model"""
    __tablename__ = "user_sessions"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")


# InvestigationTemplate model
class InvestigationTemplate(Base):
    """Investigation template model"""
    __tablename__ = "investigation_templates"
    
    template_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    workflow_steps = Column(JSON, default=list)
    default_agents = Column(JSON, default=list)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime, server_default=func.now())


# SavedSearch model
class SavedSearch(Base):
    """Saved search model"""
    __tablename__ = "saved_searches"
    
    search_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    name = Column(String(255), nullable=False)
    search_criteria = Column(JSON, default=dict)
    alert_enabled = Column(Boolean, default=False)
    last_executed = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


# InvestigationComment model
class InvestigationComment(Base):
    """Investigation comment model"""
    __tablename__ = "investigation_comments"
    
    comment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.investigation_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("investigation_comments.comment_id"))
    created_at = Column(DateTime, server_default=func.now())
    edited_at = Column(DateTime)
    
    # Relationships
    investigation = relationship("Investigation", back_populates="comments")


# InvestigationAnnotation model
class InvestigationAnnotation(Base):
    """Investigation annotation model"""
    __tablename__ = "investigation_annotations"
    
    annotation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.investigation_id"), nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.evidence_id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    annotation_type = Column(String(100), nullable=False)
    coordinates = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    investigation = relationship("Investigation", back_populates="annotations")
    evidence = relationship("Evidence", back_populates="annotations")


# EvidenceLink model
class EvidenceLink(Base):
    """Evidence link model"""
    __tablename__ = "evidence_links"
    
    link_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.evidence_id"), nullable=False)
    target_evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.evidence_id"), nullable=False)
    link_type = Column(String(100), nullable=False)
    strength = Column(Float)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime, server_default=func.now())


# ModelVersion model
class ModelVersion(Base):
    """Model version model"""
    __tablename__ = "model_versions"
    
    model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False, index=True)  # e.g., 'wildlife_tools', 'tiger_reid'
    model_type = Column(SQLEnum(ModelType), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    path = Column(String(500), nullable=False)
    training_data_hash = Column(String(100))
    metrics = Column(JSON, default=dict)
    is_active = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now())


# ModelInference model
class ModelInference(Base):
    """Model inference model"""
    __tablename__ = "model_inferences"
    
    inference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.model_id"), nullable=False, index=True)
    input_data_hash = Column(String(100))
    output = Column(JSON, default=dict)
    confidence = Column(Float)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, server_default=func.now(), index=True)


# Notification model
class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    related_entity_type = Column(String(100))
    related_entity_id = Column(UUID(as_uuid=True))
    read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)


# BackgroundJob model
class BackgroundJob(Base):
    """Background job model"""
    __tablename__ = "background_jobs"
    
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    parameters = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    error_message = Column(Text)
    started_at = Column(DateTime, index=True)
    completed_at = Column(DateTime)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


# DataExport model
class DataExport(Base):
    """Data export model"""
    __tablename__ = "data_exports"
    
    export_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    export_type = Column(String(100), nullable=False)
    filters = Column(JSON, default=dict)
    file_path = Column(String(500))
    status = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, index=True)


# SystemMetric model
class SystemMetric(Base):
    """System metric model"""
    __tablename__ = "system_metrics"
    
    metric_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    tags = Column(JSON, default=dict)


# Feedback model
class Feedback(Base):
    """Feedback model"""
    __tablename__ = "feedback"
    
    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.investigation_id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    feedback_type = Column(String(100), nullable=False)
    content = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())


# CrawlHistory model
class CrawlHistory(Base):
    """Crawl history model"""
    __tablename__ = "crawl_history"
    
    crawl_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facilities.facility_id"), index=True)
    source_url = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    images_found = Column(Integer, default=0)
    tigers_identified = Column(Integer, default=0)
    crawled_at = Column(DateTime, server_default=func.now(), index=True)
    
    # Enhanced fields from migration 003
    pages_crawled = Column(Integer, default=0)
    total_content_size = Column(Integer)
    crawl_duration_ms = Column(Integer)
    error_message = Column(Text)
    error_log = Column(JSON, default=list)
    retry_count = Column(Integer, default=0)
    content_changes_detected = Column(Boolean, default=False)
    change_summary = Column(JSON, default=dict)
    crawl_statistics = Column(JSON, default=dict)
    completed_at = Column(DateTime)
    
    # Relationships
    facility = relationship("Facility", back_populates="crawl_history")


# Password reset token model
class PasswordResetToken(Base):
    """Password reset token model"""
    __tablename__ = "password_reset_tokens"
    
    token_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="password_reset_tokens")