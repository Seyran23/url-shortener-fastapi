"""add telegram_chat_id to users

Revision ID: af996662a9bf
Revises: 925935a288bb
Create Date: 2026-08-30 01:12:21.363911

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af996662a9bf'
down_revision: Union[str, Sequence[str], None] = '925935a288bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('telegram_chat_id', sa.BigInteger(), nullable=True))
    op.create_unique_constraint('uq_users_telegram_chat_id', 'users', ['telegram_chat_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_users_telegram_chat_id', 'users', type_='unique')
    op.drop_column('users', 'telegram_chat_id')
