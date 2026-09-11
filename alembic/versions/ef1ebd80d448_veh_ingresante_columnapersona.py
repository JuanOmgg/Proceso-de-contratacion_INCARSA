"""veh_ingresante-columnapersona

Revision ID: ef1ebd80d448
Revises: e30871535d20
Create Date: 2026-09-11 16:00:50.191655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef1ebd80d448'
down_revision: Union[str, Sequence[str], None] = 'e30871535d20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Agregar columna persona_id a vehiculos_ingresantes
    op.add_column('vehiculos_ingresantes', sa.Column('persona_id', sa.String(20), nullable=False))

    # Crear constraint de clave foránea
    op.create_foreign_key(
        'fk_vehiculos_ingresantes_persona',
        'vehiculos_ingresantes',
        'personas',
        ['persona_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Eliminar constraint de clave foránea
    op.drop_constraint('fk_vehiculos_ingresantes_persona', 'vehiculos_ingresantes', type_='foreignkey')

    # Eliminar columna persona_id
    op.drop_column('vehiculos_ingresantes', 'persona_id')
