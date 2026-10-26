"""persona_correo

Revision ID: d881a85dee99
Revises: cf38e95623af
Create Date: 2026-09-19 07:57:38.246648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd881a85dee99'
down_revision: Union[str, Sequence[str], None] = 'cf38e95623af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('personas', sa.Column('correo', sa.String(255), nullable=False))


def downgrade() -> None:
    op.drop_column('personas', 'correo')
