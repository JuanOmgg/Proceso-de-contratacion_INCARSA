"""superadmin_y_permisos_rbac

Revision ID: baee671ba15a
Revises: 3cf7b0da6cd9
Create Date: 2026-09-04 09:28:32.555525

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'baee671ba15a'
down_revision: Union[str, Sequence[str], None] = '3cf7b0da6cd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Crear tabla sistema_config (Directivas globales y modo mantenimiento 503)
    op.execute("""
        CREATE TABLE IF NOT EXISTS sistema_config (
            clave VARCHAR(64) PRIMARY KEY,
            valor TEXT NOT NULL,
            descripcion VARCHAR(255) NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 3. Semilla para modo mantenimiento
    op.execute("""
        INSERT INTO sistema_config (clave, valor, descripcion) VALUES
        ('modo_mantenimiento', '0', 'Estado de mantenimiento del sistema: 0=Inactivo, 1=Activo'),
        ('mantenimiento_mensaje', 'Estamos realizando labores de optimización y mantenimiento programado.', 'Mensaje mostrado al usuario en error 503'),
        ('mantenimiento_tiempo', '30 minutos aprox.', 'Tiempo estimado de finalización')
        ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion);
    """)

    # 4. Crear tabla rol_permisos (Matriz de permisos RBAC por módulo y acción)
    op.execute("""
        CREATE TABLE IF NOT EXISTS rol_permisos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_rol INT NOT NULL,
            modulo VARCHAR(64) NOT NULL,
            accion VARCHAR(64) NOT NULL DEFAULT 'ver',
            permitido TINYINT(1) NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_rol_modulo_accion (id_rol, modulo, accion),
            CONSTRAINT fk_rol_permisos_roles FOREIGN KEY (id_rol) REFERENCES roles(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 5. Semilla de permisos iniciales
    modulos = [
        "dashboard",
        "solicitudes",
        "nueva_solicitud",
        "usuarios",
        "nuevo_usuario",
        "plantas",
        "contratistas",
        "vehiculos",
        "personas",
        "procesamiento",
        "antecedentes",
        "revision_solicitud"
    ]
    acciones = ["ver", "crear", "editar", "eliminar", "aprobar"]

    permisos_por_rol = {
        "SUPERADMIN": {"todos": True},
        "ADMINISTRADOR": {
            "dashboard": True, "solicitudes": True, "nueva_solicitud": True, "usuarios": True,
            "nuevo_usuario": True, "plantas": True, "contratistas": True, "vehiculos": True,
            "personas": True, "procesamiento": True, "antecedentes": True, "revision_solicitud": True,
            "crear": True, "editar": True, "eliminar": True, "aprobar": True
        },
        "GESTION DOCUMENTAL": {
            "dashboard": True, "solicitudes": True, "nueva_solicitud": True, "usuarios": False,
            "nuevo_usuario": False, "plantas": False, "contratistas": True, "vehiculos": True,
            "personas": True, "procesamiento": True, "antecedentes": False, "revision_solicitud": True,
            "crear": True, "editar": True, "eliminar": False, "aprobar": False
        },
        "SST": {
            "dashboard": True, "solicitudes": True, "nueva_solicitud": True, "usuarios": False,
            "nuevo_usuario": False, "plantas": False, "contratistas": False, "vehiculos": False,
            "personas": True, "procesamiento": True, "antecedentes": True, "revision_solicitud": True,
            "crear": False, "editar": False, "eliminar": False, "aprobar": True
        },
        "GESCO": {
            "dashboard": True, "solicitudes": True, "nueva_solicitud": True, "usuarios": False,
            "nuevo_usuario": False, "plantas": False, "contratistas": False, "vehiculos": False,
            "personas": True, "procesamiento": True, "antecedentes": False, "revision_solicitud": True,
            "crear": False, "editar": False, "eliminar": False, "aprobar": True
        },
        "SCR": {
            "dashboard": True, "solicitudes": True, "nueva_solicitud": True, "usuarios": False,
            "nuevo_usuario": False, "plantas": True, "contratistas": True, "vehiculos": True,
            "personas": True, "procesamiento": True, "antecedentes": True, "revision_solicitud": True,
            "crear": True, "editar": True, "eliminar": False, "aprobar": True
        },
        "VIGILANTE": {
            "dashboard": True, "solicitudes": True, "nueva_solicitud": False, "usuarios": False,
            "nuevo_usuario": False, "plantas": False, "contratistas": False, "vehiculos": False,
            "personas": True, "procesamiento": False, "antecedentes": False, "revision_solicitud": False,
            "crear": False, "editar": False, "eliminar": False, "aprobar": False
        }
    }

    # Asignar permisos mediante SQL
    for rol_nombre, config in permisos_por_rol.items():
        es_todos = config.get("todos", False)
        for mod in modulos:
            puede_ver = 1 if es_todos or config.get(mod, False) else 0
            for acc in acciones:
                if es_todos:
                    permitido = 1
                elif acc == "ver":
                    permitido = puede_ver
                else:
                    permitido = 1 if (puede_ver and config.get(acc, False)) else 0

                op.execute(f"""
                    INSERT INTO rol_permisos (id_rol, modulo, accion, permitido)
                    SELECT id, '{mod}', '{acc}', {permitido}
                    FROM roles
                    WHERE nombre_rol = '{rol_nombre}'
                    ON DUPLICATE KEY UPDATE permitido = VALUES(permitido);
                """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('rol_permisos')
    op.drop_table('sistema_config')
