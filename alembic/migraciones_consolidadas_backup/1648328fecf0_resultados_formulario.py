"""resultados_formulario

Revision ID: 1648328fecf0
Revises: 8709410944ec
Create Date: 2026-10-13 14:16:31.184280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1648328fecf0'
down_revision: Union[str, Sequence[str], None] = '8709410944ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resultados_formulario',
        sa.Column('id',sa.Integer(),primary_key=True,autoincrement=True,nullable=False),
        sa.Column('id_persona', sa.Integer(), sa.ForeignKey('personas.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('id_formulario', sa.Integer(), sa.ForeignKey('formularioGesco.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        
        sa.Column('resultado', sa.String(50), nullable=False),
        sa.Column('estado', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('fecha_realizacion', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), server_onupdate=sa.func.now()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )


def downgrade() -> None:
    op.drop_table('resultados_formulario')
