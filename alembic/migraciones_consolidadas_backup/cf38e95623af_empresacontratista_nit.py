"""empresaContratista_NIT

Revision ID: cf38e95623af
Revises: b2c3d4e5f6g7
Create Date: 2026-09-18 15:26:44.484888

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf38e95623af'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("emp_contratista", sa.Column("nit", sa.String(20), nullable=True, unique=True))

def downgrade() -> None:
    op.drop_column("emp_contratista", "nit")
