
CREATE DATABASE IF NOT EXISTS incarsa_ingresos;
USE incarsa_ingresos;

CREATE TABLE IF NOT EXISTS solicitudes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_origen VARCHAR(100) NOT NULL,
    diligenciado_por VARCHAR(150) NOT NULL,
    nivel_de_riesgo VARCHAR(20) NOT NULL,
    tipo_de_persona VARCHAR(30) NOT NULL,
    empresa_contratista VARCHAR(150) NOT NULL,
    planta_a_visitar VARCHAR(100) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    actividad TEXT NOT NULL,
    tipo_vehiculo VARCHAR(50),
    placa VARCHAR(20),
    estado VARCHAR(30) NOT NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS personas_solicitud (
    id INT AUTO_INCREMENT PRIMARY KEY,
    solicitud_id INT NOT NULL,
    item VARCHAR(10),
    ap_nombre VARCHAR(150) NOT NULL,
    tipo_doc VARCHAR(20) NOT NULL,
    identificacion BIGINT NOT NULL,
    cargo VARCHAR(100),
    FOREIGN KEY (solicitud_id) REFERENCES solicitudes(id) ON DELETE CASCADE
);

-- 4. Tabla Hija: Equipos de Cómputo asociados
CREATE TABLE IF NOT EXISTS equipos_solicitud (
    id INT AUTO_INCREMENT PRIMARY KEY,
    solicitud_id INT NOT NULL,
    marca VARCHAR(50) NOT NULL,
    modelo VARCHAR(50) NOT NULL,
    serie VARCHAR(100) NOT NULL,
    FOREIGN KEY (solicitud_id) REFERENCES solicitudes(id) ON DELETE CASCADE
);