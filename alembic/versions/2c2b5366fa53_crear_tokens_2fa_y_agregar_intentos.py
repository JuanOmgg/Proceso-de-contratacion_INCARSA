"""crear_tokens_2fa_y_agregar_intentos

Revision ID: 2c2b5366fa53
Revises: b5fff5a49ffa
Create Date: 2026-10-07 21:03:10.330310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c2b5366fa53'
down_revision: Union[str, Sequence[str], None] = 'b5fff5a49ffa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = insp.get_table_names()
    if 'tokens_2fa' not in tables:
        op.create_table(
            'tokens_2fa',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('id_usuario', sa.Integer(), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
            sa.Column('code_hash', sa.String(length=255), nullable=False),
            sa.Column('expiration_time', sa.DateTime(), nullable=False),
            sa.Column('used', sa.Boolean(), server_default=sa.text('0'), nullable=False),
            sa.Column('intentos', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('creado_en', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )
    if 'tokens_reset' in tables:
        cols = [c['name'] for c in insp.get_columns('tokens_reset')]
        if 'intentos' not in cols:
            op.add_column('tokens_reset', sa.Column('intentos', sa.Integer(), server_default=sa.text('0'), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tables = insp.get_table_names()
    if 'tokens_2fa' in tables:
        op.drop_table('tokens_2fa')
    if 'tokens_reset' in tables:
        cols = [c['name'] for c in insp.get_columns('tokens_reset')]
        if 'intentos' in cols:
            op.drop_column('tokens_reset', 'intentos')
