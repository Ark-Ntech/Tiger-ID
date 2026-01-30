"""Add coordinates to facilities and methodology to investigations

Revision ID: 005
Revises: 004
Create Date: 2026-01-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add coordinates field to facilities table
    op.add_column(
        'facilities',
        sa.Column('coordinates', postgresql.JSON, nullable=True)
    )

    # Add methodology field to investigations table
    op.add_column(
        'investigations',
        sa.Column('methodology', postgresql.JSON, nullable=True)
    )

    # Create index on coordinates for spatial queries (JSON path index)
    # This allows faster filtering of facilities with coordinates
    op.execute(
        """
        CREATE INDEX idx_facilities_coordinates
        ON facilities ((coordinates IS NOT NULL))
        """
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_facilities_coordinates', table_name='facilities')

    # Remove columns
    op.drop_column('investigations', 'methodology')
    op.drop_column('facilities', 'coordinates')
