"""indices_optimizacion

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-18 07:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crear índices de alto rendimiento para filtros, búsquedas y ordenamientos frecuentes."""
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_personas_identificacion ON personas (identificacion);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_solicitudes_estado ON solicitudes (estado);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_solicitudes_fecha_creacion ON solicitudes (fecha_creacion);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_solicitudes_pre_aprobado ON solicitudes (pre_aprobado);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_inducciones_fecha_vigencia ON inducciones (fecha_vigencia);
    """)


def downgrade() -> None:
    """Eliminar índices añadidos."""
    op.execute("DROP INDEX IF EXISTS idx_personas_identificacion ON personas;")
    op.execute("DROP INDEX IF EXISTS idx_solicitudes_estado ON solicitudes;")
    op.execute("DROP INDEX IF EXISTS idx_solicitudes_fecha_creacion ON solicitudes;")
    op.execute("DROP INDEX IF EXISTS idx_solicitudes_pre_aprobado ON solicitudes;")
    op.execute("DROP INDEX IF EXISTS idx_inducciones_fecha_vigencia ON inducciones;")
