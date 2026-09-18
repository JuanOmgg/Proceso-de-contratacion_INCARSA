"""inducciones

Revision ID: fba5d41ec52e
Revises: ef1ebd80d448
Create Date: 2026-09-16 15:29:57.128590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fba5d41ec52e'
down_revision: Union[str, Sequence[str], None] = 'ef1ebd80d448'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'inducciones',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('id_persona', sa.Integer(), sa.ForeignKey('personas.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
        sa.Column('responsable', sa.String(length=100), nullable=True),
        sa.Column('anotaciones', sa.Text(), nullable=True),
        sa.Column('id_empresa', sa.Integer(), sa.ForeignKey('empresa.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True),
        sa.Column('ultima_revision', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('fecha_induccion', sa.Date(), nullable=True),
        sa.Column('fecha_vigencia', sa.Date(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.UniqueConstraint('id_persona', name='uq_inducciones_persona'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('inducciones')
