"""crear_tablas_seguridad_social

Revision ID: 7d1ab7b6ba9e
Revises: 2c2b5366fa53
Create Date: 2026-10-08 10:09:08.413492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d1ab7b6ba9e'
down_revision: Union[str, Sequence[str], None] = '2c2b5366fa53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = insp.get_table_names()

    if 'seguridad_social' not in tables:
        op.create_table(
            'seguridad_social',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('id_persona', sa.Integer(), sa.ForeignKey('personas.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
            sa.Column('responsable', sa.String(length=100), nullable=True),
            sa.Column('anotaciones', sa.Text(), nullable=True),
            sa.Column('id_empresa', sa.Integer(), sa.ForeignKey('empresa.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True),
            sa.Column('ultima_revision', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('fecha_vigencia', sa.Date(), nullable=True),
            sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.UniqueConstraint('id_persona', name='uq_seguridad_social_persona'),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )

    if 'seguridad_social_historial_solicitudes' not in tables:
        op.create_table(
            'seguridad_social_historial_solicitudes',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('id_seguridad_social', sa.Integer(), sa.ForeignKey('seguridad_social.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
            sa.Column('id_solicitud', sa.Integer(), sa.ForeignKey('solicitudes.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True),
            sa.Column('id_empresa', sa.Integer(), sa.ForeignKey('empresa.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True),
            sa.Column('fecha_solicitud', sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column('observacion', sa.Text(), nullable=True),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = insp.get_table_names()

    if 'seguridad_social_historial_solicitudes' in tables:
        op.drop_table('seguridad_social_historial_solicitudes')
    if 'seguridad_social' in tables:
        op.drop_table('seguridad_social')
