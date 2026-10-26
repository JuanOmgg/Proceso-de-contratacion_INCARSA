"""add_tipo_pregunta_preguntas_and_config_cuotas

Revision ID: 8a96c8185468
Revises: 5b821f6b141a
Create Date: 2026-10-16 11:32:55.739052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a96c8185468'
down_revision: Union[str, Sequence[str], None] = '5b821f6b141a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Columnas agregadas de forma segura si no existen
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols_preguntas = [c['name'] for c in insp.get_columns('preguntas')]
    if 'tipo_pregunta' not in cols_preguntas:
        op.add_column(
            'preguntas',
            sa.Column('tipo_pregunta', sa.String(50), nullable=False, server_default='GENERAL')
        )
    cols_form = [c['name'] for c in insp.get_columns('formularioGesco')]
    if 'config_cuotas' not in cols_form:
        op.add_column(
            'formularioGesco',
            sa.Column('config_cuotas', sa.JSON(), nullable=True)
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('preguntas', 'tipo_pregunta')
    op.drop_column('formularioGesco', 'config_cuotas')
