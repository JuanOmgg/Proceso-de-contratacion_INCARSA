"""notificaciones

Revision ID: 3cf7b0da6cd9
Revises: ea750c415871
Create Date: 2026-09-02 08:56:16.565295

"""
from sqlalchemy import false
from sqlalchemy import true
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3cf7b0da6cd9'
down_revision: Union[str, Sequence[str], None] = 'ea750c415871'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notificaciones',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('id_usuario', sa.Integer(), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=True),
        sa.Column('rol_destino', sa.Integer(), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=True),
        sa.Column('titulo', sa.VARCHAR(100), nullable=False),
        sa.Column('mensaje', sa.Text(), nullable=False),
        sa.Column('tipo', sa.String(length=30), server_default='info', nullable=False),
        sa.Column('enlace', sa.VARCHAR(250), nullable=True),
        sa.Column('leido', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )


def downgrade() -> None:
    op.drop_table('notificaciones')
