"""Add reference data fields to facilities and enhance crawl history

Revision ID: 003
Revises: 002
Create Date: 2025-01-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add reference data fields to facilities table
    op.add_column('facilities', sa.Column('is_reference_facility', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('facilities', sa.Column('data_source', sa.String(100), nullable=True))
    op.add_column('facilities', sa.Column('reference_dataset_version', sa.DateTime(), nullable=True))
    op.add_column('facilities', sa.Column('reference_metadata', postgresql.JSON, nullable=True, server_default='{}'))
    
    # Create indexes for reference data fields
    op.create_index('idx_facility_reference', 'facilities', ['is_reference_facility'])
    op.create_index('idx_facility_data_source', 'facilities', ['data_source'])
    
    # Enhance crawl_history table
    op.add_column('crawl_history', sa.Column('pages_crawled', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('crawl_history', sa.Column('total_content_size', sa.Integer(), nullable=True))
    op.add_column('crawl_history', sa.Column('crawl_duration_ms', sa.Integer(), nullable=True))
    op.add_column('crawl_history', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('crawl_history', sa.Column('error_log', postgresql.JSON, nullable=True, server_default='[]'))
    op.add_column('crawl_history', sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('crawl_history', sa.Column('content_changes_detected', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('crawl_history', sa.Column('change_summary', postgresql.JSON, nullable=True, server_default='{}'))
    op.add_column('crawl_history', sa.Column('crawl_statistics', postgresql.JSON, nullable=True, server_default='{}'))
    op.add_column('crawl_history', sa.Column('completed_at', sa.DateTime(), nullable=True))
    
    # Create index for crawl status
    op.create_index('idx_crawl_status', 'crawl_history', ['status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_crawl_status', 'crawl_history')
    op.drop_index('idx_facility_data_source', 'facilities')
    op.drop_index('idx_facility_reference', 'facilities')
    
    # Remove crawl_history enhancements
    op.drop_column('crawl_history', 'completed_at')
    op.drop_column('crawl_history', 'crawl_statistics')
    op.drop_column('crawl_history', 'change_summary')
    op.drop_column('crawl_history', 'content_changes_detected')
    op.drop_column('crawl_history', 'retry_count')
    op.drop_column('crawl_history', 'error_log')
    op.drop_column('crawl_history', 'error_message')
    op.drop_column('crawl_history', 'crawl_duration_ms')
    op.drop_column('crawl_history', 'total_content_size')
    op.drop_column('crawl_history', 'pages_crawled')
    
    # Remove reference data fields from facilities
    op.drop_column('facilities', 'reference_metadata')
    op.drop_column('facilities', 'reference_dataset_version')
    op.drop_column('facilities', 'data_source')
    op.drop_column('facilities', 'is_reference_facility')

