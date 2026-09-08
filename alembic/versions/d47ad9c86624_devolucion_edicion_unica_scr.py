"""devolucion_edicion_unica_scr

Revision ID: d47ad9c86624
Revises: 435585b64d7c
Create Date: 2026-09-05 14:43:40.534594

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd47ad9c86624'
down_revision: Union[str, Sequence[str], None] = '435585b64d7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('solicitudes', sa.Column('token_edicion', sa.String(length=64), nullable=True))
    op.add_column('solicitudes', sa.Column('token_edicion_usado', sa.Boolean(), server_default=sa.text('0'), nullable=False))
    op.add_column('solicitudes', sa.Column('motivo_devolucion', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('solicitudes', 'motivo_devolucion')
    op.drop_column('solicitudes', 'token_edicion_usado')
    op.drop_column('solicitudes', 'token_edicion')
