"""Parqueo

Revision ID: 493199191027
Revises: d2e5a1b3c4f7
Create Date: 2026-10-27 10:28:45.702660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '493199191027'
down_revision: Union[str, Sequence[str], None] = 'd2e5a1b3c4f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tablas_existentes = insp.get_table_names()

    # 1. Tabla de vehículos internos y su zona asignada
    if 'vehiculo_int' not in tablas_existentes:
        op.create_table(
            'vehiculo_int',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('placa', sa.String(20), unique=True, nullable=False),
            sa.Column('zona', sa.String(50), nullable=False),
            sa.Column('descripcion', sa.String(255), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )

    # 2. Tabla de reportes nocturnos por zona (enlista fecha, zona y reportador)
    if 'reportes_parqueo' not in tablas_existentes:
        op.create_table(
            'reportes_parqueo',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('zona', sa.String(50), nullable=False),
            sa.Column('reportador', sa.String(100), nullable=False),
            sa.Column('observaciones', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Index('idx_reportes_parqueo_zona', 'zona'),
            sa.Index('idx_reportes_parqueo_reportador', 'reportador'),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )

    # 3. Tabla de detalle de parqueos (vehículos reportados en cada zona ese día)
    if 'parqueos' not in tablas_existentes:
        op.create_table(
            'parqueos',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('id_reporte', sa.Integer(), sa.ForeignKey('reportes_parqueo.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
            sa.Column('id_vehiculo', sa.Integer(), sa.ForeignKey('vehiculo_int.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True),
            sa.Column('vehiculo', sa.String(20), nullable=False),
            sa.Column('zona_asignada', sa.String(50), nullable=False),
            sa.Column('se_quedo', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('observacion', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Index('idx_parqueos_reporte', 'id_reporte'),
            sa.Index('idx_parqueos_vehiculo', 'vehiculo'),
            sa.Index('idx_parqueos_se_quedo', 'se_quedo'),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )


def downgrade() -> None:
    try:
        op.drop_table('parqueos')
    except Exception:
        pass
    try:
        op.drop_table('reportes_parqueo')
    except Exception:
        pass
    try:
        op.drop_table('vehiculo_int')
    except Exception:
        pass
