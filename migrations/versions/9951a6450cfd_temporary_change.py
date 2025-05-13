from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '9951a6450cfd'
down_revision = '9951a6450ccd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('firstName', sa.String(50)),
        sa.Column('lastName', sa.String(50)),
        sa.Column('phoneNumber', sa.String(20)),
        sa.Column('image', sa.String(100)),
        sa.Column('email', sa.String(100), unique=True, nullable=False),
        sa.Column('password', sa.String(255)),
        sa.Column('city', sa.String(30)),
        sa.Column('company', sa.String(50)),
        sa.Column('country', sa.String(50)),
        sa.Column('role', sa.String(20), server_default='Admin'),
        sa.Column('subscriptionType', sa.String(20)),
        sa.Column('numberOfTeamMembers', sa.Integer, server_default='1'),
        sa.Column('paymentId', sa.String(100)),
        sa.Column('activeProfile', sa.Boolean, server_default=sa.sql.expression.false()),
        sa.Column('isProfileComplete', sa.Boolean, server_default=sa.sql.expression.false()),
        sa.Column('stripeCustomerId', sa.String(50)),
        sa.Column('subscriptionStatus', sa.String(50)),
        sa.Column('subscriptionId', sa.String(100)),
        sa.Column('refreshToken', sa.String(255)),
        sa.Column('otp', sa.String(6)),
        sa.Column('subscriptionEndDate', sa.DateTime()),
        sa.Column('subscriptionStartDate', sa.DateTime()),
        sa.Column('subscriptionUpdatedAt', sa.DateTime()),
        sa.Column('teamId', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # password_reset_tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('token', sa.String(255), unique=True, nullable=False),
        sa.Column('expiresAt', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # teammembers table
    op.create_table(
        'teammembers',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('memberId', sa.Integer, nullable=False),
        sa.Column('adminId', sa.Integer, nullable=False),
        sa.Column('isAdmin', sa.Boolean, server_default=sa.sql.expression.false()),
        sa.Column('role', sa.String(20)),
        sa.Column('teamId', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # invite_tokens table
    op.create_table(
        'invite_tokens',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('token', sa.String(255), unique=True, nullable=False),
        sa.Column('adminId', sa.Integer, nullable=False),
        sa.Column('teamId', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20)),
        sa.Column('expiresAt', sa.DateTime, nullable=False),
        sa.Column('accepted', sa.Boolean, server_default=sa.sql.expression.false()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # transaction_history table
    op.create_table(
        'transaction_history',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('userId', sa.Integer, nullable=False),
        sa.Column('paymentId', sa.String(100), nullable=False),
        sa.Column('amountPaid', sa.Float, nullable=False),
        sa.Column('email', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('paymentMethod', sa.String(50)),
        sa.Column('subscriptionType', sa.String(20)),
        sa.Column('receiptUrl', sa.String(255)),
        sa.Column('currency', sa.String()),
        sa.Column('transactionDate', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('transaction_history')
    op.drop_table('invite_tokens')
    op.drop_table('teammembers')
    op.drop_table('password_reset_tokens')
    op.drop_table('users')