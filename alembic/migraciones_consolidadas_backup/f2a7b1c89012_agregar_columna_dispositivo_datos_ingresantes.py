"""agregar_columna_dispositivo_datos_ingresantes

Revision ID: f2a7b1c89012
Revises: eec99bb44287
Create Date: 2026-10-05 16:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a7b1c89012'
down_revision: Union[str, Sequence[str], None] = 'eec99bb44287'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: agregar columna dispositivo_datos a la tabla ingresantes."""
    try:
        op.add_column('ingresantes', sa.Column('dispositivo_datos', sa.String(length=255), nullable=True))
    except Exception:
        pass


def downgrade() -> None:
    """Downgrade schema: remover columna dispositivo_datos."""
    op.drop_column('ingresantes', 'dispositivo_datos')
