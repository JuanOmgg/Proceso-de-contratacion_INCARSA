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
    # 1. Agregar columna id_persona a Veh_ingreso (Integer y Nullable)
    op.add_column('Veh_ingreso', sa.Column('id_persona', sa.Integer(), nullable=True))

    # 2. Crear constraint de clave foránea hacia personas(id)
    op.create_foreign_key(
        'fk_veh_ingreso_persona',
        'Veh_ingreso',
        'personas',
        ['id_persona'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Eliminar constraint de clave foránea
    op.drop_constraint('fk_veh_ingreso_persona', 'Veh_ingreso', type_='foreignkey')

    # Eliminar columna id_persona
    op.drop_column('Veh_ingreso', 'id_persona')
