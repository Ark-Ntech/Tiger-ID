"""Add additional tables for templates, comments, annotations, etc.

Revision ID: 002
Revises: 001
Create Date: 2025-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create investigation_templates table
    op.create_table(
        'investigation_templates',
        sa.Column('template_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('workflow_steps', postgresql.JSON, default=list),
        sa.Column('default_agents', postgresql.JSON, default=list),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id']),
    )
    
    # Create saved_searches table
    op.create_table(
        'saved_searches',
        sa.Column('search_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('search_criteria', postgresql.JSON, default=dict),
        sa.Column('alert_enabled', sa.Boolean, default=False),
        sa.Column('last_executed', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
    )
    
    # Create investigation_comments table
    op.create_table(
        'investigation_comments',
        sa.Column('comment_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('parent_comment_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('edited_at', sa.DateTime),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.investigation_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['investigation_comments.comment_id']),
    )
    
    # Create investigation_annotations table
    op.create_table(
        'investigation_annotations',
        sa.Column('annotation_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True)),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('annotation_type', sa.String(100), nullable=False),
        sa.Column('coordinates', postgresql.JSON),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.investigation_id']),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidence.evidence_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
    )
    
    # Create evidence_links table
    op.create_table(
        'evidence_links',
        sa.Column('link_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('link_type', sa.String(100), nullable=False),
        sa.Column('strength', sa.Float),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['source_evidence_id'], ['evidence.evidence_id']),
        sa.ForeignKeyConstraint(['target_evidence_id'], ['evidence.evidence_id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id']),
    )
    
    # Create model_versions table
    op.create_table(
        'model_versions',
        sa.Column('model_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_type', sa.Enum('detection', 'reid', 'pose', name='model_type'), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('training_data_hash', sa.String(100)),
        sa.Column('metrics', postgresql.JSON, default=dict),
        sa.Column('is_active', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Index('idx_model_type', 'model_type'),
        sa.Index('idx_model_active', 'is_active'),
    )
    
    # Create model_inferences table
    op.create_table(
        'model_inferences',
        sa.Column('inference_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('input_data_hash', sa.String(100)),
        sa.Column('output', postgresql.JSON, default=dict),
        sa.Column('confidence', sa.Float),
        sa.Column('execution_time_ms', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['model_id'], ['model_versions.model_id']),
        sa.Index('idx_inference_model', 'model_id'),
        sa.Index('idx_inference_timestamp', 'created_at'),
    )
    
    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('log_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True)),
        sa.Column('changes', postgresql.JSON, default=dict),
        sa.Column('ip_address', sa.String(50)),
        sa.Column('timestamp', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.Index('idx_audit_user', 'user_id'),
        sa.Index('idx_audit_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_audit_timestamp', 'timestamp'),
    )
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('notification_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('related_entity_type', sa.String(100)),
        sa.Column('related_entity_id', postgresql.UUID(as_uuid=True)),
        sa.Column('read', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.Index('idx_notification_user', 'user_id'),
        sa.Index('idx_notification_read', 'read'),
        sa.Index('idx_notification_created', 'created_at'),
    )
    
    # Create background_jobs table
    op.create_table(
        'background_jobs',
        sa.Column('job_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('parameters', postgresql.JSON, default=dict),
        sa.Column('result', postgresql.JSON, default=dict),
        sa.Column('error_message', sa.Text),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Index('idx_job_type', 'job_type'),
        sa.Index('idx_job_status', 'status'),
        sa.Index('idx_job_started', 'started_at'),
    )
    
    # Create data_exports table
    op.create_table(
        'data_exports',
        sa.Column('export_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('export_type', sa.String(100), nullable=False),
        sa.Column('filters', postgresql.JSON, default=dict),
        sa.Column('file_path', sa.String(500)),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.Index('idx_export_user', 'user_id'),
        sa.Index('idx_export_status', 'status'),
        sa.Index('idx_export_expires', 'expires_at'),
    )
    
    # Create system_metrics table
    op.create_table(
        'system_metrics',
        sa.Column('metric_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float, nullable=False),
        sa.Column('timestamp', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('tags', postgresql.JSON, default=dict),
        sa.Index('idx_metric_name', 'metric_name'),
        sa.Index('idx_metric_timestamp', 'timestamp'),
    )
    
    # Create feedback table
    op.create_table(
        'feedback',
        sa.Column('feedback_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True)),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_type', sa.String(100), nullable=False),
        sa.Column('content', postgresql.JSON, default=dict),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['investigation_id'], ['investigations.investigation_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
    )
    
    # Create crawl_history table
    op.create_table(
        'crawl_history',
        sa.Column('crawl_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True)),
        sa.Column('source_url', sa.String(500), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('images_found', sa.Integer, default=0),
        sa.Column('tigers_identified', sa.Integer, default=0),
        sa.Column('crawled_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['facility_id'], ['facilities.facility_id']),
        sa.Index('idx_crawl_facility', 'facility_id'),
        sa.Index('idx_crawl_timestamp', 'crawled_at'),
    )


def downgrade() -> None:
    op.drop_table('crawl_history')
    op.drop_table('feedback')
    op.drop_table('system_metrics')
    op.drop_table('data_exports')
    op.drop_table('background_jobs')
    op.drop_table('notifications')
    op.drop_table('audit_log')
    op.drop_table('model_inferences')
    op.drop_table('model_versions')
    op.drop_table('evidence_links')
    op.drop_table('investigation_annotations')
    op.drop_table('investigation_comments')
    op.drop_table('saved_searches')
    op.drop_table('investigation_templates')

