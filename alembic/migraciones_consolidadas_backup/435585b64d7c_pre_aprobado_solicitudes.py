"""pre-aprobado_solicitudes

Revision ID: 435585b64d7c
Revises: baee671ba15a
Create Date: 2026-09-05 08:56:39.882215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '435585b64d7c'
down_revision: Union[str, Sequence[str], None] = 'baee671ba15a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'solicitudes',
        sa.Column('pre_aprobado', sa.Boolean(), server_default=sa.text('0'), nullable=False)
    )


def downgrade() -> None:
    op.drop_column('solicitudes', 'pre_aprobado')
