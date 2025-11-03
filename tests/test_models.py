"""Tests for database models"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from backend.database.models import (
    User, Tiger, TigerImage, Facility, Investigation,
    InvestigationStep, Evidence, VerificationQueue,
    UserSession, InvestigationTemplate, SavedSearch,
    InvestigationComment, InvestigationAnnotation,
    EvidenceLink, ModelVersion, ModelInference,
    Notification, BackgroundJob,
    DataExport, SystemMetric, Feedback, CrawlHistory
)
from backend.database.audit_models import AuditLog


class TestUser:
    """Tests for User model"""
    
    def test_create_user(self, db_session, sample_user_id):
        """Test creating a user"""
        user = User(
            user_id=sample_user_id,  # Already a UUID object from fixture
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role="investigator"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.user_id == sample_user_id
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role.value == "investigator" if hasattr(user.role, 'value') else user.role == "investigator"
        assert user.is_active is True
        assert user.mfa_enabled is False
    
    def test_user_unique_username(self, db_session):
        """Test that username must be unique"""
        user1 = User(
            username="testuser",
            email="test1@example.com",
            password_hash="hash1",
            role="investigator"
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="testuser",  # Same username
            email="test2@example.com",
            password_hash="hash2",
            role="investigator"
        )
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_unique_email(self, db_session):
        """Test that email must be unique"""
        user1 = User(
            username="user1",
            email="test@example.com",
            password_hash="hash1",
            role="investigator"
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="user2",
            email="test@example.com",  # Same email
            password_hash="hash2",
            role="investigator"
        )
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestTiger:
    """Tests for Tiger model"""
    
    def test_create_tiger(self, db_session, sample_tiger_id):
        """Test creating a tiger"""
        tiger = Tiger(
            tiger_id=sample_tiger_id,  # Already a UUID object
            name="Test Tiger",
            alias="TT-001",
            last_seen_location="Test Facility",
            status="active"
        )
        db_session.add(tiger)
        db_session.commit()
        
        assert tiger.tiger_id == sample_tiger_id
        assert tiger.name == "Test Tiger"
        assert tiger.alias == "TT-001"
        assert tiger.status.value == "active" if hasattr(tiger.status, 'value') else tiger.status == "active"
        assert tiger.tags == []
        assert tiger.created_at is not None
    
    def test_tiger_status_enum(self, db_session):
        """Test tiger status enum values"""
        valid_statuses = ["active", "monitored", "seized", "deceased"]
        
        for status in valid_statuses:
            tiger = Tiger(
                tiger_id=uuid.uuid4(),
                name=f"Tiger-{status}",
                status=status
            )
            db_session.add(tiger)
        
        db_session.commit()
        
        tigers = db_session.query(Tiger).all()
        assert len(tigers) == len(valid_statuses)


class TestTigerImage:
    """Tests for TigerImage model"""
    
    def test_create_tiger_image(self, db_session, sample_image_id, sample_tiger_id):
        """Test creating a tiger image"""
        image = TigerImage(
            image_id=sample_image_id,  # Already a UUID object
            tiger_id=sample_tiger_id,  # Already a UUID object
            image_path="/path/to/image.jpg",
            side_view="left",
            verified=True
        )
        db_session.add(image)
        db_session.commit()
        
        assert image.image_id == sample_image_id
        assert image.tiger_id == sample_tiger_id
        assert image.image_path == "/path/to/image.jpg"
        assert image.side_view.value == "left" if hasattr(image.side_view, 'value') else image.side_view == "left"
        assert image.verified is True
        # image_metadata might not exist on the model, check if it exists
        if hasattr(image, 'image_metadata'):
            assert image.image_metadata == {}
    
    def test_tiger_image_side_view_enum(self, db_session):
        """Test tiger image side_view enum values"""
        valid_views = ["left", "right", "both", "unknown"]
        
        for view in valid_views:
            image = TigerImage(
                image_id=uuid.uuid4(),
                image_path=f"/path/{view}.jpg",
                side_view=view
            )
            db_session.add(image)
        
        db_session.commit()
        
        images = db_session.query(TigerImage).all()
        assert len(images) == len(valid_views)


class TestFacility:
    """Tests for Facility model"""
    
    def test_create_facility(self, db_session, sample_facility_id):
        """Test creating a facility"""
        facility = Facility(
            facility_id=sample_facility_id,  # Already a UUID object
            exhibitor_name="Test Facility",
            usda_license="USDA-123",
            state="CA",
            city="Los Angeles",
            tiger_count=5
        )
        db_session.add(facility)
        db_session.commit()
        
        assert facility.facility_id == sample_facility_id
        assert facility.exhibitor_name == "Test Facility"
        assert facility.usda_license == "USDA-123"
        assert facility.state == "CA"
        assert facility.tiger_count == 5
        assert facility.violation_history == []


class TestInvestigation:
    """Tests for Investigation model"""
    
    def test_create_investigation(self, db_session, sample_investigation_id, sample_user_id):
        """Test creating an investigation"""
        investigation = Investigation(
            investigation_id=sample_investigation_id,  # Already a UUID object
            title="Test Investigation",
            description="A test investigation",
            created_by=sample_user_id,  # Already a UUID object
            status="draft",
            priority="high"
        )
        db_session.add(investigation)
        db_session.commit()
        
        assert investigation.investigation_id == sample_investigation_id
        assert investigation.title == "Test Investigation"
        assert investigation.status.value == "draft" if hasattr(investigation.status, 'value') else investigation.status == "draft"
        assert investigation.priority.value == "high" if hasattr(investigation.priority, 'value') else investigation.priority == "high"
        assert investigation.related_tigers == []
        assert investigation.summary == {}
    
    def test_investigation_status_enum(self, db_session, sample_user_id):
        """Test investigation status enum values"""
        valid_statuses = ["draft", "active", "pending_verification", "completed", "archived"]
        
        for status in valid_statuses:
            investigation = Investigation(
                investigation_id=uuid.uuid4(),
                title=f"Investigation-{status}",
                created_by=sample_user_id,  # Already a UUID object
                status=status
            )
            db_session.add(investigation)
        
        db_session.commit()
        
        investigations = db_session.query(Investigation).all()
        assert len(investigations) == len(valid_statuses)


class TestInvestigationStep:
    """Tests for InvestigationStep model"""
    
    def test_create_investigation_step(self, db_session, sample_investigation_id):
        """Test creating an investigation step"""
        step = InvestigationStep(
            step_id=uuid.uuid4(),
            investigation_id=sample_investigation_id,  # Already a UUID object
            step_type="image_analysis",
            agent_name="vision_agent",
            status="completed",
            result={"confidence": 0.95},
            duration_ms=500
        )
        db_session.add(step)
        db_session.commit()
        
        assert step.step_type == "image_analysis"
        assert step.agent_name == "vision_agent"
        assert step.status == "completed"
        assert step.result == {"confidence": 0.95}
        assert step.duration_ms == 500


class TestEvidence:
    """Tests for Evidence model"""
    
    def test_create_evidence(self, db_session, sample_investigation_id):
        """Test creating evidence"""
        evidence = Evidence(
            evidence_id=uuid.uuid4(),
            investigation_id=sample_investigation_id,  # Already a UUID object
            source_type="image",
            source_url="https://example.com/image.jpg",
            content={"data": "test"},
            relevance_score=0.9
        )
        db_session.add(evidence)
        db_session.commit()
        
        assert evidence.source_type.value == "image" if hasattr(evidence.source_type, 'value') else evidence.source_type == "image"
        assert evidence.source_url == "https://example.com/image.jpg"
        assert evidence.relevance_score == 0.9
        assert evidence.verified is False
    
    def test_evidence_source_type_enum(self, db_session, sample_investigation_id):
        """Test evidence source_type enum values"""
        valid_types = ["image", "web_search", "document", "user_input"]
        
        for source_type in valid_types:
            evidence = Evidence(
                evidence_id=uuid.uuid4(),
                investigation_id=sample_investigation_id,  # Already a UUID object
                source_type=source_type
            )
            db_session.add(evidence)
        
        db_session.commit()
        
        evidence_list = db_session.query(Evidence).all()
        assert len(evidence_list) == len(valid_types)


class TestVerificationQueue:
    """Tests for VerificationQueue model"""
    
    def test_create_verification_queue(self, db_session, sample_tiger_id):
        """Test creating a verification queue item"""
        queue_item = VerificationQueue(
            queue_id=uuid.uuid4(),
            entity_type="tiger",
            entity_id=sample_tiger_id,  # Already a UUID object
            priority="high",
            status="pending"
        )
        db_session.add(queue_item)
        db_session.commit()
        
        assert queue_item.entity_type.value == "tiger" if hasattr(queue_item.entity_type, 'value') else queue_item.entity_type == "tiger"
        assert queue_item.entity_id == sample_tiger_id
        assert queue_item.priority.value == "high" if hasattr(queue_item.priority, 'value') else queue_item.priority == "high"
        assert queue_item.status.value == "pending" if hasattr(queue_item.status, 'value') else queue_item.status == "pending"
        assert queue_item.requires_human_review is True


class TestRelationships:
    """Tests for model relationships"""
    
    def test_tiger_image_relationship(self, db_session, sample_tiger_id):
        """Test relationship between Tiger and TigerImage"""
        tiger = Tiger(
            tiger_id=sample_tiger_id,  # Already a UUID object
            name="Test Tiger"
        )
        db_session.add(tiger)
        
        image = TigerImage(
            image_id=uuid.uuid4(),
            tiger_id=sample_tiger_id,  # Already a UUID object
            image_path="/path/to/image.jpg"
        )
        db_session.add(image)
        db_session.commit()
        
        # Test relationship
        assert len(tiger.images) == 1
        assert tiger.images[0].image_id == image.image_id
        assert image.tiger.tiger_id == tiger.tiger_id
    
    def test_investigation_steps_relationship(self, db_session, sample_user_id):
        """Test relationship between Investigation and InvestigationStep"""
        investigation = Investigation(
            investigation_id=uuid.uuid4(),
            title="Test Investigation",
            created_by=sample_user_id  # Already a UUID object
        )
        db_session.add(investigation)
        
        step1 = InvestigationStep(
            step_id=uuid.uuid4(),
            investigation_id=investigation.investigation_id,
            step_type="step1",
            status="completed"
        )
        step2 = InvestigationStep(
            step_id=uuid.uuid4(),
            investigation_id=investigation.investigation_id,
            step_type="step2",
            status="pending"
        )
        db_session.add_all([step1, step2])
        db_session.commit()
        
        assert len(investigation.steps) == 2
        assert investigation.steps[0].step_id == step1.step_id
        assert investigation.steps[1].step_id == step2.step_id

