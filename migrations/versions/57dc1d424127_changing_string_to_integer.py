"""changing string to integer

Revision ID: 57dc1d424127
Revises: 52b2c5cde128
Create Date: 2025-06-27 10:51:44.332281
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '57dc1d424127'
down_revision: Union[str, None] = '52b2c5cde128'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema: change list_of_target from VARCHAR[] to INTEGER[]"""
    op.execute(
        """
        ALTER TABLE email_campaign
        ALTER COLUMN list_of_target
        TYPE INTEGER[]
        USING list_of_target::INTEGER[];
        """
    )

def downgrade() -> None:
    """Downgrade schema: revert list_of_target from INTEGER[] to VARCHAR[]"""
    op.execute(
        """
        ALTER TABLE email_campaign
        ALTER COLUMN list_of_target
        TYPE VARCHAR[]
        USING list_of_target::VARCHAR[];
        """
    )
