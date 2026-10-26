"""formularioGesco

Revision ID: 6b12e616f6b6
Revises: 6eadb14acbdb
Create Date: 2026-10-09 12:08:40.918530

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b12e616f6b6'
down_revision: Union[str, Sequence[str], None] = '6eadb14acbdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Incompleto / pendiente de definición
    # op.create_table(
    #     'formularioGesco',
    #     sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
    #     sa.Column('nombreform', sa.VARCHAR(200), nullable=False)
    # )
    pass


def downgrade() -> None:
    op.drop_table('formularioGesco')
    pass
