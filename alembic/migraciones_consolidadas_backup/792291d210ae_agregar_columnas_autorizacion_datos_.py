"""agregar_columnas_autorizacion_datos_ingresantes

Revision ID: 792291d210ae
Revises: 0caa7c00d45c
Create Date: 2026-10-02 10:17:50.205040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '792291d210ae'
down_revision: Union[str, Sequence[str], None] = '0caa7c00d45c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: agregar columnas de autorizacion de datos personales a la tabla ingresantes."""
    op.add_column('ingresantes', sa.Column('token_autorizacion', sa.String(length=100), nullable=True))
    op.add_column('ingresantes', sa.Column('estado_datos', sa.String(length=20), nullable=False, server_default='PENDIENTE'))
    op.add_column('ingresantes', sa.Column('fecha_respuesta_datos', sa.DateTime(), nullable=True))
    op.add_column('ingresantes', sa.Column('ip_datos', sa.String(length=50), nullable=True))
    op.add_column('ingresantes', sa.Column('motivo_rechazo_datos', sa.Text(), nullable=True))
    op.create_index('idx_ingresantes_token', 'ingresantes', ['token_autorizacion'])


def downgrade() -> None:
    """Downgrade schema: remover columnas de autorizacion de datos."""
    op.drop_index('idx_ingresantes_token', table_name='ingresantes')
    op.drop_column('ingresantes', 'motivo_rechazo_datos')
    op.drop_column('ingresantes', 'ip_datos')
    op.drop_column('ingresantes', 'fecha_respuesta_datos')
    op.drop_column('ingresantes', 'estado_datos')
    op.drop_column('ingresantes', 'token_autorizacion')
