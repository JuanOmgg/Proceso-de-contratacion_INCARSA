"""crear_tabla_tokens_formulario_temporal

Revision ID: 6eadb14acbdb
Revises: 7d1ab7b6ba9e
Create Date: 2026-10-08 10:30:00.577672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6eadb14acbdb'
down_revision: Union[str, Sequence[str], None] = '7d1ab7b6ba9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = insp.get_table_names()

    if 'tokens_formulario_temporal' not in tables:
        op.create_table(
            'tokens_formulario_temporal',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('token', sa.String(length=128), nullable=False),
            sa.Column('id_usuario_creador', sa.Integer(), sa.ForeignKey('usuarios.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
            sa.Column('destinatario_nombre', sa.String(length=255), nullable=True),
            sa.Column('destinatario_email', sa.String(length=255), nullable=True),
            sa.Column('id_empresa_contratista', sa.Integer(), sa.ForeignKey('emp_contratista.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True),
            sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('fecha_expiracion', sa.DateTime(), nullable=False),
            sa.Column('usado', sa.Boolean(), server_default=sa.text('0'), nullable=False),
            sa.Column('revocado', sa.Boolean(), server_default=sa.text('0'), nullable=False),
            sa.Column('id_solicitud_creada', sa.Integer(), sa.ForeignKey('solicitudes.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True),
            sa.Column('fecha_uso', sa.DateTime(), nullable=True),
            sa.UniqueConstraint('token', name='uq_tokens_formulario_temporal_token'),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = insp.get_table_names()

    if 'tokens_formulario_temporal' in tables:
        op.drop_table('tokens_formulario_temporal')
