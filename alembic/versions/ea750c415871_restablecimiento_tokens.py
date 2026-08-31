"""restablecimiento_tokens

Revision ID: ea750c415871
Revises: 0418e306f363
Create Date: 2026-08-31 10:18:15.704798

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea750c415871'
down_revision: Union[str, Sequence[str], None] = '0418e306f363'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tokens_reset',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('id_usuario', sa.Integer(), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code_hash', sa.String(length=255), nullable=False),
        sa.Column('expiration_time', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('creado_en', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )


def downgrade() -> None:
    op.drop_table('tokens_reset')
