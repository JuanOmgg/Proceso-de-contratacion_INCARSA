"""agregar_adjuntos_notificaciones

Revision ID: fa83b4549ea1
Revises: 69dabb8fd0ef
Create Date: 2026-09-08 11:30:06.225496

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa83b4549ea1'
down_revision: Union[str, Sequence[str], None] = '69dabb8fd0ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('notificaciones', sa.Column('archivo_url', sa.String(length=500), nullable=True))
    op.add_column('notificaciones', sa.Column('archivo_nombre', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('notificaciones', 'archivo_nombre')
    op.drop_column('notificaciones', 'archivo_url')
