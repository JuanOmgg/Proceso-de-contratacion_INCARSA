"""documentos_persona-vigencia

Revision ID: 3058a162244e
Revises: d881a85dee99
Create Date: 2026-09-19 09:13:42.529020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3058a162244e'
down_revision: Union[str, Sequence[str], None] = 'd881a85dee99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documentos_persona', sa.Column('vigencia', sa.Date, nullable=True))


def downgrade() -> None:
    op.drop_column('documentos_persona', 'vigencia')
