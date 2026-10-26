"""opciones

Revision ID: 8709410944ec
Revises: 0b02a04dfd31
Create Date: 2026-10-13 14:03:48.948654

"""
from sqlalchemy import null
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8709410944ec'
down_revision: Union[str, Sequence[str], None] = '0b02a04dfd31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        'opciones_formulario',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True, nullable=False),
        sa.Column('id_pregunta', sa.Integer(), sa.ForeignKey('preguntas.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('opcion', sa.String(255), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), server_onupdate=sa.func.now()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )


def downgrade() -> None:
    op.drop_table('opciones_formulario')
