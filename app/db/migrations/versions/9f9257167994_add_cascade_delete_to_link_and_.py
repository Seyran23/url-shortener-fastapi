"""add cascade delete to link and analytics foreign keys

Revision ID: 9f9257167994
Revises: 73c04bd4e2d4
Create Date: 2026-08-27 19:45:45.148485

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f9257167994'
down_revision: Union[str, Sequence[str], None] = '73c04bd4e2d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # corrected: named both new constraints explicitly (autogenerate left them as None,
    # relying on Postgres's auto-generated name) so downgrade() can actually reference them
    op.drop_constraint(op.f('analytics_link_id_fkey'), 'analytics', type_='foreignkey')
    op.create_foreign_key(
        'analytics_link_id_fkey', 'analytics', 'links', ['link_id'], ['id'], ondelete='CASCADE'
    )
    op.drop_constraint(op.f('links_user_id_fkey'), 'links', type_='foreignkey')
    op.create_foreign_key(
        'links_user_id_fkey', 'links', 'users', ['user_id'], ['id'], ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('links_user_id_fkey', 'links', type_='foreignkey')
    op.create_foreign_key(op.f('links_user_id_fkey'), 'links', 'users', ['user_id'], ['id'])
    op.drop_constraint('analytics_link_id_fkey', 'analytics', type_='foreignkey')
    op.create_foreign_key(op.f('analytics_link_id_fkey'), 'analytics', 'links', ['link_id'], ['id'])
