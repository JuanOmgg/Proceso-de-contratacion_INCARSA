"""ampliar_longitud_asunto_correspondencia

Revision ID: 0caa7c00d45c
Revises: 3058a162244e
Create Date: 2026-09-21 09:14:36.680571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0caa7c00d45c'
down_revision: Union[str, Sequence[str], None] = '3058a162244e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('correspondencia', 'asunto',
               existing_type=sa.String(length=50),
               type_=sa.Text(),
               existing_nullable=False,
               nullable=False)
    op.alter_column('correspondencia', 'procedencia',
               existing_type=sa.String(length=100),
               type_=sa.String(length=255),
               existing_nullable=False,
               nullable=False)
    op.alter_column('correspondencia', 'destino',
               existing_type=sa.String(length=100),
               type_=sa.String(length=255),
               existing_nullable=False,
               nullable=False)
    op.alter_column('correspondencia', 'tipo_correspondencia',
               existing_type=sa.String(length=40),
               type_=sa.String(length=100),
               existing_nullable=False,
               nullable=False)


def downgrade() -> None:
    op.alter_column('correspondencia', 'tipo_correspondencia',
               existing_type=sa.String(length=100),
               type_=sa.String(length=40),
               existing_nullable=False,
               nullable=False)
    op.alter_column('correspondencia', 'destino',
               existing_type=sa.String(length=255),
               type_=sa.String(length=100),
               existing_nullable=False,
               nullable=False)
    op.alter_column('correspondencia', 'procedencia',
               existing_type=sa.String(length=255),
               type_=sa.String(length=100),
               existing_nullable=False,
               nullable=False)
    op.alter_column('correspondencia', 'asunto',
               existing_type=sa.Text(),
               type_=sa.String(length=50),
               existing_nullable=False,
               nullable=False)

