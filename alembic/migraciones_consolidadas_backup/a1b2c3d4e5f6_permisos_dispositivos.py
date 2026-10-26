"""permisos_dispositivos

Revision ID: a1b2c3d4e5f6
Revises: fba5d41ec52e
Create Date: 2026-09-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fba5d41ec52e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Sembrar permisos de solo lectura para consulta de dispositivos."""
    op.execute("""
        INSERT INTO rol_permisos (id_rol, modulo, accion, permitido) VALUES
        (1, 'dispositivos', 'ver', 1),  -- ADMINISTRADOR
        (2, 'dispositivos', 'ver', 1),  -- SUPERADMIN
        (4, 'dispositivos', 'ver', 1),  -- EQUIPO SCR - RADICADOS
        (5, 'dispositivos', 'ver', 1),  -- SOLICITANTE
        (6, 'dispositivos', 'ver', 1),  -- SST
        (7, 'dispositivos', 'ver', 1),  -- GESCO
        (8, 'dispositivos', 'ver', 1)   -- SCR
        ON DUPLICATE KEY UPDATE permitido = VALUES(permitido);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        DELETE FROM rol_permisos WHERE modulo = 'dispositivos';
    """)
