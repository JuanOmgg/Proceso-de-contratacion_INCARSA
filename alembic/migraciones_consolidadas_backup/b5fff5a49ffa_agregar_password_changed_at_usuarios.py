"""agregar_password_changed_at_usuarios

Revision ID: b5fff5a49ffa
Revises: f2a7b1c89012
Create Date: 2026-10-07 20:50:54.373479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5fff5a49ffa'
down_revision: Union[str, Sequence[str], None] = 'f2a7b1c89012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('usuarios')]
    if 'password_changed_at' not in cols:
        op.add_column('usuarios', sa.Column('password_changed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('usuarios')]
    if 'password_changed_at' in cols:
        op.drop_column('usuarios', 'password_changed_at')
