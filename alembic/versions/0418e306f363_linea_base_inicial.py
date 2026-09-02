"""linea_base_inicial

Revision ID: 0418e306f363
Revises: 
Create Date: 2026-08-30 20:08:29.534975

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0418e306f363'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Roles
    op.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre_rol VARCHAR(50) NOT NULL UNIQUE,
            descripcion VARCHAR(255) NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    op.execute("""
        INSERT INTO roles (nombre_rol, descripcion) VALUES
        ('Administrador', ''),
        ('SuperAdmin', ''),
        ('Vigilante', ''),
        ('Gestion documental', ''),
        ('SST', 'Seguridad y Salud en el Trabajo'),
        ('GESCO', 'Gestión del conocimiento'),
        ('SCR', 'Segurdad corporativa y riesgo')
        ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion);
    """)

    # 2. Empresa
    op.execute("""
        CREATE TABLE IF NOT EXISTS empresa (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre_empresa VARCHAR(50) NOT NULL UNIQUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    op.execute("""
        INSERT INTO empresa (nombre_empresa) VALUES
        ('INCARSA S.A.S.'),
        ('MILPA S.A.S.'),
        ('CARBOINSA S.A.S.'),
        ('UNIMINAS S.A.S.')
        ON DUPLICATE KEY UPDATE nombre_empresa = VALUES(nombre_empresa);
    """)

    # 3. Empresa Contratista (sin datos semilla)
    op.execute("""
        CREATE TABLE IF NOT EXISTS emp_contratista (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL UNIQUE,
            observacion VARCHAR(250) NULL,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 4. Planta
    op.execute("""
        CREATE TABLE IF NOT EXISTS planta (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_empresa INT NOT NULL,
            nombre VARCHAR(100) NOT NULL UNIQUE,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_empresa) REFERENCES empresa(id) ON DELETE RESTRICT ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 5. Usuarios
    op.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombres VARCHAR(50) NOT NULL,
            apellidos VARCHAR(50) NOT NULL,
            tipo_documento VARCHAR(50) NOT NULL,
            num_documento VARCHAR(20) NOT NULL UNIQUE,
            num_telefono VARCHAR(15) NOT NULL,
            correo VARCHAR(100) NOT NULL UNIQUE,
            contrasena VARCHAR(250) NOT NULL,
            id_rol INT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_rol) REFERENCES roles(id) ON DELETE RESTRICT ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    op.execute("""
        INSERT INTO usuarios (id, nombres, apellidos, tipo_documento, num_documento, num_telefono, correo, contrasena, id_rol, is_active) VALUES
        (1, 'Juan', 'Prieto', 'CC', '1212121212', '3000000000', 'juandeveloper2427@gmail.com', '$2b$12$MsmbFnqQWPQj.l35Je3yM.9D6j2jLYzq6J3Nas/kcVv.6S0Sp2zgu', 2, 1)
        ON DUPLICATE KEY UPDATE nombres = VALUES(nombres);
    """)

    # 6. Personas
    op.execute("""
        CREATE TABLE IF NOT EXISTS personas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(50) NOT NULL,
            apellido VARCHAR(50) NOT NULL,
            tipo_doc VARCHAR(70) NOT NULL,
            identificacion INT NOT NULL,
            cargo VARCHAR(30) NOT NULL,
            observacion VARCHAR(250) NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 7. Vehículos
    op.execute("""
        CREATE TABLE IF NOT EXISTS vehiculos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tipo VARCHAR(25) NOT NULL,
            placa VARCHAR(10) NOT NULL UNIQUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 8. Solicitudes
    op.execute("""
        CREATE TABLE IF NOT EXISTS solicitudes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo VARCHAR(50) NULL UNIQUE,
            empresa_origen INT NOT NULL,
            diligenciado_por INT NOT NULL,
            nivel_de_riesgo VARCHAR(20) NOT NULL,
            tipo_personal VARCHAR(30) NOT NULL,
            empresa_contratista INT NOT NULL,
            plantas_ids VARCHAR(255) NULL,
            personas_ids VARCHAR(255) NULL,
            vehiculos_ids VARCHAR(255) NULL,
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL,
            actividad TEXT NOT NULL,
            observaciones TEXT NULL,
            estado VARCHAR(30) NOT NULL DEFAULT 'ENVIADO',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (empresa_origen) REFERENCES empresa(id) ON DELETE RESTRICT ON UPDATE CASCADE,
            FOREIGN KEY (empresa_contratista) REFERENCES emp_contratista(id) ON DELETE RESTRICT ON UPDATE CASCADE,
            FOREIGN KEY (diligenciado_por) REFERENCES usuarios(id) ON DELETE RESTRICT ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 9. Visita
    op.execute("""
        CREATE TABLE IF NOT EXISTS visita (
            id_solicitud INT NOT NULL,
            id_planta INT NOT NULL,
            PRIMARY KEY (id_solicitud, id_planta),
            FOREIGN KEY (id_solicitud) REFERENCES solicitudes(id) ON DELETE CASCADE,
            FOREIGN KEY (id_planta) REFERENCES planta(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 10. Ingresantes
    op.execute("""
        CREATE TABLE IF NOT EXISTS ingresantes (
            id_solicitud INT NOT NULL,
            id_persona INT NOT NULL,
            autorizado BOOLEAN NOT NULL DEFAULT TRUE,
            motivo VARCHAR(255) NULL,
            PRIMARY KEY (id_solicitud, id_persona),
            FOREIGN KEY (id_solicitud) REFERENCES solicitudes(id) ON DELETE CASCADE,
            FOREIGN KEY (id_persona) REFERENCES personas(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 11. Veh_ingreso
    op.execute("""
        CREATE TABLE IF NOT EXISTS Veh_ingreso (
            id_solicitud INT NOT NULL,
            id_vehiculo INT NOT NULL,
            licencia_doc VARCHAR(255) NULL,
            PRIMARY KEY (id_solicitud, id_vehiculo),
            FOREIGN KEY (id_solicitud) REFERENCES solicitudes(id) ON DELETE CASCADE,
            FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 12. Documentos de Personas
    op.execute("""
        CREATE TABLE IF NOT EXISTS documentos_persona (
            id INT AUTO_INCREMENT PRIMARY KEY,
            persona_id INT NOT NULL,
            tipo_doc VARCHAR(50) NOT NULL,
            nombre_archivo VARCHAR(255) NOT NULL,
            FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 13. Documentos de Vehículos
    op.execute("""
        CREATE TABLE IF NOT EXISTS documentos_vehiculo (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_vehiculo INT NOT NULL,
            tipo_doc VARCHAR(50) NOT NULL,
            nom_documento VARCHAR(250) NOT NULL,
            FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 14. Equipos de Solicitud
    op.execute("""
        CREATE TABLE IF NOT EXISTS equipos_solicitud (
            id INT AUTO_INCREMENT PRIMARY KEY,
            solicitud_id INT NOT NULL,
            marca VARCHAR(50) NOT NULL,
            modelo VARCHAR(50) NOT NULL,
            serie VARCHAR(100) NOT NULL,
            FOREIGN KEY (solicitud_id) REFERENCES solicitudes(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 15. Antecedentes
    op.execute("""
        CREATE TABLE IF NOT EXISTS antecedentes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_persona INT NOT NULL UNIQUE,
            responsable VARCHAR(100) NULL,
            anotaciones TEXT NULL,
            id_empresa INT NULL,
            ultima_revision DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            fecha_consulta DATE NULL,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_persona) REFERENCES personas(id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (id_empresa) REFERENCES empresa(id) ON DELETE SET NULL ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 16. Historial de Solicitudes / Antecedentes
    op.execute("""
        CREATE TABLE IF NOT EXISTS antecedentes_historial_solicitudes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_antecedente INT NOT NULL,
            id_solicitud INT NULL,
            id_empresa INT NOT NULL,
            fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
            observacion VARCHAR(255) NULL,
            FOREIGN KEY (id_antecedente) REFERENCES antecedentes(id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (id_solicitud) REFERENCES solicitudes(id) ON DELETE SET NULL ON UPDATE CASCADE,
            FOREIGN KEY (id_empresa) REFERENCES empresa(id) ON DELETE RESTRICT ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 17. Asignación de Plantas a Usuarios
    op.execute("""
        CREATE TABLE IF NOT EXISTS usuario_plantas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_usuario INT NOT NULL,
            id_planta INT NOT NULL,
            fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (id_planta) REFERENCES planta(id) ON DELETE CASCADE ON UPDATE CASCADE,
            UNIQUE KEY uq_usuario_planta (id_usuario, id_planta)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # 18. Historial de Revisiones
    op.execute("""
        CREATE TABLE IF NOT EXISTS solicitud_revisiones (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_solicitud INT NOT NULL,
            id_planta INT NULL,
            rol VARCHAR(50) NOT NULL,
            id_usuario INT NULL,
            nombre_revisor VARCHAR(150) NULL,
            decision VARCHAR(20) NOT NULL,
            motivo_rechazo TEXT NULL,
            observacion TEXT NULL,
            fecha_revision DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_solicitud) REFERENCES solicitudes(id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (id_planta) REFERENCES planta(id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE SET NULL ON UPDATE CASCADE,
            UNIQUE KEY uq_solicitud_planta_rol (id_solicitud, id_planta, rol)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS solicitud_revisiones;")
    op.execute("DROP TABLE IF EXISTS usuario_plantas;")
    op.execute("DROP TABLE IF EXISTS antecedentes_historial_solicitudes;")
    op.execute("DROP TABLE IF EXISTS antecedentes;")
    op.execute("DROP TABLE IF EXISTS equipos_solicitud;")
    op.execute("DROP TABLE IF EXISTS documentos_vehiculo;")
    op.execute("DROP TABLE IF EXISTS documentos_persona;")
    op.execute("DROP TABLE IF EXISTS Veh_ingreso;")
    op.execute("DROP TABLE IF EXISTS ingresantes;")
    op.execute("DROP TABLE IF EXISTS visita;")
    op.execute("DROP TABLE IF EXISTS solicitudes;")
    op.execute("DROP TABLE IF EXISTS vehiculos;")
    op.execute("DROP TABLE IF EXISTS personas;")
    op.execute("DROP TABLE IF EXISTS usuarios;")
    op.execute("DROP TABLE IF EXISTS planta;")
    op.execute("DROP TABLE IF EXISTS emp_contratista;")
    op.execute("DROP TABLE IF EXISTS empresa;")
    op.execute("DROP TABLE IF EXISTS roles;")
