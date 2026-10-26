"""agregar_columna_denegado_por_ingresantes

Revision ID: eec99bb44287
Revises: 792291d210ae
Create Date: 2026-10-03 08:20:08.744084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eec99bb44287'
down_revision: Union[str, Sequence[str], None] = '792291d210ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: agregar columna denegado_por a la tabla ingresantes."""
    op.add_column('ingresantes', sa.Column('denegado_por', sa.Integer(), nullable=True))
    op.create_index('idx_ingresantes_denegado_por', 'ingresantes', ['denegado_por'])


def downgrade() -> None:
    """Downgrade schema: remover columna denegado_por."""
    op.drop_index('idx_ingresantes_denegado_por', table_name='ingresantes')
    op.drop_column('ingresantes', 'denegado_por')
