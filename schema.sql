CREATE DATABASE IF NOT EXISTS incarsa_ingresos;
USE incarsa_ingresos;

-- 1. Roles (Sin dependencias)
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar roles base
INSERT INTO roles (nombre_rol, descripcion) VALUES
('Administrador', 'Control total del sistema, gestión de usuarios y configuraciones'),
('Gestion documental', 'Encargado de radicar y gestionar solicitudes de ingreso'),
('SST', 'Seguridad y Salud en el Trabajo - Revisión en paralelo'),
('GESCO', 'Gestión Comunal / Social - Revisión en paralelo'),
('Seguridad corporativa & riesgo', 'Visto bueno final y autorización estratégica de ingreso')
ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion);

-- 2. Empresa (Sin dependencias)
CREATE TABLE IF NOT EXISTS empresa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_empresa VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar empresas base
INSERT INTO empresa (nombre_empresa) VALUES
('INCARSA S.A.S.'),
('MILPA S.A.S.'),
('CARBOINSA S.A.S.'),
('UNIMINAS S.A.S.')
ON DUPLICATE KEY UPDATE nombre_empresa = VALUES(nombre_empresa);

-- 3. Empresa Contratista (Sin dependencias)
CREATE TABLE IF NOT EXISTS emp_contratista (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    observacion VARCHAR(250) NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar empresa contratista base
INSERT INTO emp_contratista (id, nombre, observacion) VALUES
(1, 'Contratista General S.A.S.', 'Empresa contratista base para pruebas')
ON DUPLICATE KEY UPDATE nombre = VALUES(nombre);

-- 4. Planta (Depende de empresa)
CREATE TABLE IF NOT EXISTS planta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_empresa INT NOT NULL,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_empresa) REFERENCES empresa(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Usuarios (Depende de roles)
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

-- Insertar usuario base
INSERT INTO usuarios (id, nombres, apellidos, tipo_documento, num_documento, num_telefono, correo, contrasena, id_rol, is_active) VALUES
(1, 'Administrador', 'Sistema', 'CC', '1000000000', '3000000000', 'admin@incarsa.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 1, TRUE)
ON DUPLICATE KEY UPDATE nombres = VALUES(nombres);

-- 6. Solicitudes (Depende de empresa, emp_contratista y usuarios)
CREATE TABLE IF NOT EXISTS solicitudes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_origen INT NOT NULL,
    diligenciado_por INT NOT NULL,
    nivel_de_riesgo VARCHAR(20) NOT NULL,
    tipo_personal VARCHAR(30) NOT NULL,
    empresa_contratista INT NOT NULL,
    plantas_ids VARCHAR(255) NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    actividad TEXT NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'ENVIADO',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_origen) REFERENCES empresa(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (empresa_contratista) REFERENCES emp_contratista(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (diligenciado_por) REFERENCES usuarios(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Visita (Tabla intermedia: Depende de solicitudes y planta)
CREATE TABLE IF NOT EXISTS visita (
    id_solicitud INT NOT NULL,
    id_planta INT NOT NULL,
    PRIMARY KEY (id_solicitud, id_planta),
    FOREIGN KEY (id_solicitud) REFERENCES solicitudes(id) ON DELETE CASCADE,
    FOREIGN KEY (id_planta) REFERENCES planta(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Subtablas asociadas a Solicitudes (Vehículos, Personas, Equipos)
CREATE TABLE IF NOT EXISTS vehiculos_solicitud (
    id INT AUTO_INCREMENT PRIMARY KEY,
    solicitud_id INT NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    placa VARCHAR(20) NOT NULL,
    FOREIGN KEY (solicitud_id) REFERENCES solicitudes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS personas_solicitud (
    id INT AUTO_INCREMENT PRIMARY KEY,
    solicitud_id INT NOT NULL,
    item INT NULL,
    ap_nombre VARCHAR(150) NOT NULL,
    tipo_doc VARCHAR(20) NOT NULL,
    identificacion VARCHAR(20) NOT NULL,
    cargo VARCHAR(100),
    FOREIGN KEY (solicitud_id) REFERENCES solicitudes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS documentos_persona (
    id INT AUTO_INCREMENT PRIMARY KEY,
    persona_id INT NOT NULL,
    tipo_doc VARCHAR(50) NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    FOREIGN KEY (persona_id) REFERENCES personas_solicitud(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS equipos_solicitud (
    id INT AUTO_INCREMENT PRIMARY KEY,
    solicitud_id INT NOT NULL,
    marca VARCHAR(50) NOT NULL,
    modelo VARCHAR(50) NOT NULL,
    serie VARCHAR(100) NOT NULL,
    FOREIGN KEY (solicitud_id) REFERENCES solicitudes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;