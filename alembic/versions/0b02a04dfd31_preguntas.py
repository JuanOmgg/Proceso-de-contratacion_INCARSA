"""preguntas

Revision ID: 0b02a04dfd31
Revises: 28e20c185481
Create Date: 2026-10-13 12:08:19.757401

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b02a04dfd31'
down_revision: Union[str, Sequence[str], None] = '28e20c185481'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'preguntas',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True, nullable=False),
        sa.Column('id_formulario', sa.Integer(), sa.ForeignKey('formularioGesco.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('pregunta', sa.String(500), nullable=False),
        sa.Column('tipo_respuesta', sa.String(20), nullable=False),
        sa.Column('estado', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), server_onupdate=sa.func.now()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'

    )


def downgrade() -> None:
    op.drop_table('preguntas')
