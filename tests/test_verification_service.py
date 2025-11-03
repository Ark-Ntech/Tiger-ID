"""Tests for verification service"""

import pytest
from uuid import uuid4

from backend.database import get_db_session, VerificationQueue
from backend.services.verification_service import VerificationService

# Note: db_session and sample_user_id fixtures are now in conftest.py

@pytest.fixture
def verification_service(db_session):
    """Verification service fixture"""
    return VerificationService(db_session)


class TestVerificationService:
    """Tests for VerificationService"""
    
    def test_create_verification_request(self, verification_service, sample_user_id):
        """Test creating a verification request"""
        queue_item = verification_service.create_verification_request(
            entity_type="tiger",
            entity_id=uuid4(),
            priority="high",
            assigned_to=sample_user_id
        )
        
        assert queue_item.entity_type.value == "tiger" if hasattr(queue_item.entity_type, 'value') else queue_item.entity_type == "tiger"
        assert queue_item.priority.value == "high" if hasattr(queue_item.priority, 'value') else queue_item.priority == "high"
        assert queue_item.assigned_to == sample_user_id
        assert queue_item.status.value == "pending" if hasattr(queue_item.status, 'value') else queue_item.status == "pending"
        assert queue_item.requires_human_review is True
    
    def test_get_verification_queue(self, verification_service, sample_user_id):
        """Test getting verification queue"""
        # Create multiple queue items
        verification_service.create_verification_request(
            entity_type="tiger",
            entity_id=uuid4(),
            priority="high"
        )
        verification_service.create_verification_request(
            entity_type="facility",
            entity_id=uuid4(),
            priority="medium"
        )
        
        queue = verification_service.get_verification_queue(status="pending")
        
        assert len(queue) >= 2
        assert all((item.status.value if hasattr(item.status, 'value') else item.status) == "pending" for item in queue)
    
    def test_assign_verification(self, verification_service, sample_user_id):
        """Test assigning a verification request"""
        queue_item = verification_service.create_verification_request(
            entity_type="tiger",
            entity_id=uuid4()
        )
        
        assigned = verification_service.assign_verification(
            queue_item.queue_id,
            sample_user_id
        )
        
        assert assigned.assigned_to == sample_user_id
        assert assigned.status.value == "in_review" if hasattr(assigned.status, 'value') else assigned.status == "in_review"
    
    def test_approve_verification(self, verification_service, sample_user_id):
        """Test approving a verification request"""
        queue_item = verification_service.create_verification_request(
            entity_type="tiger",
            entity_id=uuid4(),
            assigned_to=sample_user_id
        )
        
        # Assign first
        verification_service.assign_verification(queue_item.queue_id, sample_user_id)
        
        # Approve
        approved = verification_service.approve_verification(
            queue_item.queue_id,
            sample_user_id,
            review_notes="Looks good"
        )
        
        assert approved.status.value == "approved" if hasattr(approved.status, 'value') else approved.status == "approved"
        assert approved.reviewed_by == sample_user_id
        assert approved.review_notes == "Looks good"
        assert approved.reviewed_at is not None
    
    def test_reject_verification(self, verification_service, sample_user_id):
        """Test rejecting a verification request"""
        queue_item = verification_service.create_verification_request(
            entity_type="tiger",
            entity_id=uuid4(),
            assigned_to=sample_user_id
        )
        
        # Assign first
        verification_service.assign_verification(queue_item.queue_id, sample_user_id)
        
        # Reject
        rejected = verification_service.reject_verification(
            queue_item.queue_id,
            sample_user_id,
            review_notes="Invalid data"
        )
        
        assert rejected.status.value == "rejected" if hasattr(rejected.status, 'value') else rejected.status == "rejected"
        assert rejected.reviewed_by == sample_user_id
        assert rejected.review_notes == "Invalid data"
        assert rejected.reviewed_at is not None
    
    def test_get_verification_queue_with_filters(self, verification_service, sample_user_id):
        """Test getting verification queue with filters"""
        # Create items with different priorities
        verification_service.create_verification_request(
            entity_type="tiger",
            entity_id=uuid4(),
            priority="critical"
        )
        verification_service.create_verification_request(
            entity_type="facility",
            entity_id=uuid4(),
            priority="low"
        )
        
        # Filter by priority
        critical_items = verification_service.get_verification_queue(priority="critical")
        assert len(critical_items) >= 1
        assert all((item.priority.value if hasattr(item.priority, 'value') else item.priority) == "critical" for item in critical_items)
        
        # Filter by assigned user
        assigned_items = verification_service.get_verification_queue(
            assigned_to=sample_user_id
        )
        # May be empty if no items assigned to this user
        assert isinstance(assigned_items, list)

