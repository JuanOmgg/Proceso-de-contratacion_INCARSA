"""add_cantidad_preguntas_to_formulario_gesco

Revision ID: 5b821f6b141a
Revises: 1648328fecf0
Create Date: 2026-10-16 10:34:56.431657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b821f6b141a'
down_revision: Union[str, Sequence[str], None] = '1648328fecf0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'formularioGesco',
        sa.Column('cantidad_preguntas', sa.Integer(), nullable=False, default=1),
        sa.Column('Tipo_pregunta', sa.String(45), nullable=False, default='Multiple choice'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('formularioGesco', 'cantidad_preguntas'),
    op.drop_column('formularioGesco', 'Tipo_pregunta')
