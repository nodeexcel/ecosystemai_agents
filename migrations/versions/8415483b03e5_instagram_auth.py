"""instagram auth

Revision ID: 8415483b03e5
Revises: 82e0af75e300
Create Date: 2025-06-09 10:45:50.462273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8415483b03e5'
down_revision: Union[str, None] = '82e0af75e300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('instagram_connection_details',
    sa.Column('instagram_user_id', sa.String(), nullable=False),
    sa.Column('instagram_id', sa.String(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('access_token', sa.String(), nullable=False),
    sa.Column('refresh_token', sa.String(), nullable=True),
    sa.Column('expiry_time', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('instagram_user_id', 'instagram_id')
    )
    op.add_column('appointment_setter', sa.Column('lead_id', sa.String(), nullable=False))
    op.create_unique_constraint(None, 'appointment_setter', ['lead_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'appointment_setter', type_='unique')
    op.drop_column('appointment_setter', 'lead_id')
    op.drop_table('instagram_connection_details')
    # ### end Alembic commands ###
