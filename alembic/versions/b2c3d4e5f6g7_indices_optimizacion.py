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
    indices = [
        ("idx_personas_identificacion", "personas", ["identificacion"]),
        ("idx_solicitudes_estado", "solicitudes", ["estado"]),
        ("idx_solicitudes_fecha_creacion", "solicitudes", ["fecha_creacion"]),
        ("idx_solicitudes_pre_aprobado", "solicitudes", ["pre_aprobado"]),
        ("idx_inducciones_fecha_vigencia", "inducciones", ["fecha_vigencia"]),
    ]
    for nombre_indice, tabla, columnas in indices:
        try:
            op.create_index(nombre_indice, tabla, columnas)
        except Exception as e:
            print(f"Aviso al crear índice {nombre_indice} en {tabla}: {e}")


def downgrade() -> None:
    """Eliminar índices añadidos."""
    indices = [
        ("idx_personas_identificacion", "personas"),
        ("idx_solicitudes_estado", "solicitudes"),
        ("idx_solicitudes_fecha_creacion", "solicitudes"),
        ("idx_solicitudes_pre_aprobado", "solicitudes"),
        ("idx_inducciones_fecha_vigencia", "inducciones"),
    ]
    for nombre_indice, tabla in indices:
        try:
            op.drop_index(nombre_indice, table_name=tabla)
        except Exception as e:
            print(f"Aviso al eliminar índice {nombre_indice} de {tabla}: {e}")
