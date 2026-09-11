"""agregar_autorizado_motivo_veh_ingreso

Revision ID: e30871535d20
Revises: fa83b4549ea1
Create Date: 2026-09-08 12:18:51.527897

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e30871535d20'
down_revision: Union[str, Sequence[str], None] = 'fa83b4549ea1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('Veh_ingreso', sa.Column('autorizado', sa.Boolean(), server_default=sa.text('1'), nullable=False))
    op.add_column('Veh_ingreso', sa.Column('motivo', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('Veh_ingreso', 'motivo')
    op.drop_column('Veh_ingreso', 'autorizado')
