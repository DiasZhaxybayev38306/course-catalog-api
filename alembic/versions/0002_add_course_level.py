"""add course level

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-24 12:35:51.457549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. add the column as nullable: the existing rows have no value yet
    op.add_column("courses", sa.Column("level", sa.Text(), nullable=True))
    # 2. fill in the existing rows (a decision about data, not about schema)
    op.execute(
        "UPDATE courses SET level = "
        "CASE WHEN is_elective THEN 'beginner' ELSE 'intermediate' END"
    )
    # 3. now the column is required
    op.alter_column("courses", "level", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("courses", "level")
