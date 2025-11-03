"""Initial schema creation

Revision ID: 001
Revises: 
Create Date: 2025-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create enum types
    op.execute("""
        CREATE TYPE tiger_status AS ENUM ('active', 'monitored', 'seized', 'deceased');
        CREATE TYPE side_view AS ENUM ('left', 'right', 'both', 'unknown');
        CREATE TYPE investigation_status AS ENUM ('draft', 'active', 'pending_verification', 'completed', 'archived');
        CREATE TYPE priority AS ENUM ('low', 'medium', 'high', 'critical');
        CREATE TYPE evidence_source_type AS ENUM ('image', 'web_search', 'document', 'user_input');
        CREATE TYPE entity_type AS ENUM ('tiger', 'facility', 'evidence', 'investigation');
        CREATE TYPE verification_status AS ENUM ('pending', 'in_review', 'approved', 'rejected');
        CREATE TYPE user_role AS ENUM ('investigator', 'analyst', 'supervisor', 'admin');
        CREATE TYPE model_type AS ENUM ('detection', 'reid', 'pose');
    """)
    
    # Create users table (needed for foreign keys)
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('investigator', 'analyst', 'supervisor', 'admin', name='user_role'), default='investigator'),
        sa.Column('permissions', postgresql.JSON, default=dict),
        sa.Column('department', sa.String(100)),
        sa.Column('last_login', sa.DateTime),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('mfa_enabled', sa.Boolean, default=False),
        sa.Column('api_key_hash', sa.String(255)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Index('idx_user_username', 'username'),
        sa.Index('idx_user_email', 'email'),
        sa.Index('idx_user_role', 'role'),
    )
    
    # Create facilities table
    op.create_table(
        'facilities',
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('exhibitor_name', sa.String(255), nullable=False),
        sa.Column('usda_license', sa.String(100)),
        sa.Column('state', sa.String(50)),
        sa.Column('city', sa.String(100)),
        sa.Column('address', sa.Text),
        sa.Column('tiger_count', sa.Integer, default=0),
        sa.Column('tiger_capacity', sa.Integer),
        sa.Column('social_media_links', postgresql.JSON, default=dict),
        sa.Column('website', sa.String(500)),
        sa.Column('ir_date', sa.DateTime),
        sa.Column('last_inspection_date', sa.DateTime),
        sa.Column('accreditation_status', sa.String(100)),
        sa.Column('violation_history', postgresql.JSON, default=list),
        sa.Column('last_crawled_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Index('idx_facility_state', 'state'),
        sa.Index('idx_facility_usda', 'usda_license'),
        sa.Index('idx_facility_name', 'exhibitor_name'),
    )
    
    # Create tigers table
    op.create_table(
        'tigers',
        sa.Column('tiger_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255)),
        sa.Column('alias', sa.String(255)),
        sa.Column('origin_facility_id', postgresql.UUID(as_uuid=True)),
        sa.Column('last_seen_location', sa.String(255)),
        sa.Column('last_seen_date', sa.DateTime),
        sa.Column('status', sa.Enum('active', 'monitored', 'seized', 'deceased', name='tiger_status'), default='active'),
        sa.Column('tags', postgresql.JSON, default=list),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['origin_facility_id'], ['facilities.facility_id']),
        sa.Index('idx_tiger_status', 'status'),
        sa.Index('idx_tiger_name', 'name'),
    )
    
    # Create tiger_images table with vector embedding
    op.create_table(
        'tiger_images',
        sa.Column('image_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tiger_id', postgresql.UUID(as_uuid=True)),
        sa.Column('image_path', sa.String(500), nullable=False),
        sa.Column('thumbnail_path', sa.String(500)),
        sa.Column('embedding', Vector(512)),
        sa.Column('side_view', sa.Enum('left', 'right', 'both', 'unknown', name='side_view'), default='unknown'),
        sa.Column('pose_keypoints', postgresql.JSON),
        sa.Column('metadata', postgresql.JSON, default=dict),
        sa.Column('quality_score', sa.Float),
        sa.Column('verified', sa.Boolean, default=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tiger_id'], ['tigers.tiger_id']),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.user_id']),
        sa.Index('idx_image_tiger', 'tiger_id'),
        sa.Index('idx_image_verified', 'verified'),
    )
    
    # Create HNSW index for vector search (after table creation)
    op.execute("""
        CREATE INDEX idx_image_embedding_hnsw
        ON tiger_images USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
    
    # Create investigations table
    op.create_table(
        'investigations',
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('draft', 'active', 'pending_verification', 'completed', 'archived', name='investigation_status'), default='draft'),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='priority'), default='medium'),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('summary', postgresql.JSON, default=dict),
        sa.Column('tags', postgresql.JSON, default=list),
        sa.Column('assigned_to', postgresql.JSON, default=list),
        sa.Column('related_tigers', postgresql.JSON, default=list),
        sa.Column('related_facilities', postgresql.JSON, default=list),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id']),
        sa.Index('idx_investigation_status', 'status'),
        sa.Index('idx_investigation_created_by', 'created_by'),
        sa.Index('idx_investigation_priority', 'priority'),
    )
    
    # Create investigation_steps table
    op.create_table(
        'investigation_steps',
        sa.Column('step_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_type', sa.String(100), nullable=False),
        sa.Column('agent_name', sa.String(100)),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('result', postgresql.JSON, default=dict),
        sa.Column('error_message', sa.Text),
        sa.Column('duration_ms', sa.Integer),
        sa.Column('timestamp', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('parent_step_id', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.investigation_id']),
        sa.ForeignKeyConstraint(['parent_step_id'], ['investigation_steps.step_id']),
        sa.Index('idx_step_investigation', 'investigation_id'),
        sa.Index('idx_step_timestamp', 'timestamp'),
    )
    
    # Create evidence table
    op.create_table(
        'evidence',
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.Enum('image', 'web_search', 'document', 'user_input', name='evidence_source_type'), nullable=False),
        sa.Column('source_url', sa.String(500)),
        sa.Column('content', postgresql.JSON, default=dict),
        sa.Column('extracted_text', sa.Text),
        sa.Column('relevance_score', sa.Float),
        sa.Column('verified', sa.Boolean, default=False),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True)),
        sa.Column('verification_date', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.investigation_id']),
        sa.ForeignKeyConstraint(['verified_by'], ['users.user_id']),
        sa.Index('idx_evidence_investigation', 'investigation_id'),
        sa.Index('idx_evidence_source_type', 'source_type'),
        sa.Index('idx_evidence_verified', 'verified'),
    )
    
    # Create verification_queue table
    op.create_table(
        'verification_queue',
        sa.Column('queue_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.Enum('tiger', 'facility', 'evidence', 'investigation', name='entity_type'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='priority'), default='medium'),
        sa.Column('requires_human_review', sa.Boolean, default=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True)),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True)),
        sa.Column('status', sa.Enum('pending', 'in_review', 'approved', 'rejected', name='verification_status'), default='pending'),
        sa.Column('review_notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('reviewed_at', sa.DateTime),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.user_id']),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.user_id']),
        sa.Index('idx_queue_status', 'status'),
        sa.Index('idx_queue_priority', 'priority'),
        sa.Index('idx_queue_entity', 'entity_type', 'entity_id'),
    )
    
    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ip_address', sa.String(50)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.Index('idx_session_user', 'user_id'),
        sa.Index('idx_session_expires', 'expires_at'),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('user_sessions')
    op.drop_table('verification_queue')
    op.drop_table('evidence')
    op.drop_table('investigation_steps')
    op.drop_table('investigations')
    op.drop_table('tiger_images')
    op.drop_table('tigers')
    op.drop_table('facilities')
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS model_type")
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP TYPE IF EXISTS verification_status")
    op.execute("DROP TYPE IF EXISTS entity_type")
    op.execute("DROP TYPE IF EXISTS evidence_source_type")
    op.execute("DROP TYPE IF EXISTS priority")
    op.execute("DROP TYPE IF EXISTS investigation_status")
    op.execute("DROP TYPE IF EXISTS side_view")
    op.execute("DROP TYPE IF EXISTS tiger_status")
    
    # Note: pgvector extension is not dropped as it might be used by other databases

