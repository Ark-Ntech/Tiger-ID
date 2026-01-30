"""Add discovery tracking and reference flags

Revision ID: 006
Revises: 005
Create Date: 2026-01-13

Adds fields to support investigation-driven tiger discovery:
- is_reference flag to distinguish reference data (ATRW) from real tigers
- discovery tracking fields to record when/how tigers and facilities were discovered
- Enables auto-population of database through investigations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add discovery tracking to tigers table
    op.add_column(
        'tigers',
        sa.Column('is_reference', sa.Boolean, nullable=False, server_default='false')
    )
    op.add_column(
        'tigers',
        sa.Column('discovered_at', sa.DateTime, nullable=True)
    )
    op.add_column(
        'tigers',
        sa.Column('discovered_by_investigation_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        'tigers',
        sa.Column('discovery_confidence', sa.Float, nullable=True)
    )

    # Add foreign key for discovered_by_investigation_id
    op.create_foreign_key(
        'fk_tigers_discovered_by_investigation',
        'tigers',
        'investigations',
        ['discovered_by_investigation_id'],
        ['investigation_id']
    )

    # Add index for is_reference (frequently queried)
    op.create_index(
        'idx_tigers_is_reference',
        'tigers',
        ['is_reference']
    )

    # Add discovery tracking to tiger_images table
    op.add_column(
        'tiger_images',
        sa.Column('is_reference', sa.Boolean, nullable=False, server_default='false')
    )
    op.add_column(
        'tiger_images',
        sa.Column('discovered_by_investigation_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key for discovered_by_investigation_id
    op.create_foreign_key(
        'fk_tiger_images_discovered_by_investigation',
        'tiger_images',
        'investigations',
        ['discovered_by_investigation_id'],
        ['investigation_id']
    )

    # Add index for is_reference
    op.create_index(
        'idx_tiger_images_is_reference',
        'tiger_images',
        ['is_reference']
    )

    # Add discovery tracking to facilities table
    op.add_column(
        'facilities',
        sa.Column('discovered_at', sa.DateTime, nullable=True)
    )
    op.add_column(
        'facilities',
        sa.Column('discovered_by_investigation_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key for discovered_by_investigation_id
    op.create_foreign_key(
        'fk_facilities_discovered_by_investigation',
        'facilities',
        'investigations',
        ['discovered_by_investigation_id'],
        ['investigation_id']
    )


def downgrade() -> None:
    # Remove foreign keys
    op.drop_constraint('fk_facilities_discovered_by_investigation', 'facilities', type_='foreignkey')
    op.drop_constraint('fk_tiger_images_discovered_by_investigation', 'tiger_images', type_='foreignkey')
    op.drop_constraint('fk_tigers_discovered_by_investigation', 'tigers', type_='foreignkey')

    # Remove indexes
    op.drop_index('idx_tiger_images_is_reference', table_name='tiger_images')
    op.drop_index('idx_tigers_is_reference', table_name='tigers')

    # Remove columns from facilities
    op.drop_column('facilities', 'discovered_by_investigation_id')
    op.drop_column('facilities', 'discovered_at')

    # Remove columns from tiger_images
    op.drop_column('tiger_images', 'discovered_by_investigation_id')
    op.drop_column('tiger_images', 'is_reference')

    # Remove columns from tigers
    op.drop_column('tigers', 'discovery_confidence')
    op.drop_column('tigers', 'discovered_by_investigation_id')
    op.drop_column('tigers', 'discovered_at')
    op.drop_column('tigers', 'is_reference')
