from datetime import datetime
from typing import Optional


def parsear_fecha(val_fecha: Optional[str]) -> Optional[str]:
    if not val_fecha or not isinstance(val_fecha, str):
        return val_fecha

    val_fecha = val_fecha.strip()

    # Reemplazamos barras por guiones para homogeneizar la lectura
    fecha_normalizada = val_fecha.replace("/", "-")

    # Lista de todos los formatos posibles de entrada
    formatos = [
        "%Y-%m-%d",  # Ej: 2026-08-24 o 2026/08/24
        "%d-%m-%Y",  # Ej: 24-08-2026 o 24/08/2026
        "%Y-%d-%m",  # Ej: 2026-24-08
    ]

    for fmt in formatos:
        try:
            # Parseamos la fecha y la devolvemos SIEMPRE en formato YYYY-MM-DD para MySQL
            return datetime.strptime(fecha_normalizada, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Si ningún formato coincidió, la devuelve tal cual
    return val_fecha

from datetime import date, datetime


def FORMAT_FOR_FRONT(fecha_db) -> str:

    # """Convierte una fecha de la BD a formato DD-MM-YYYY"""

    if not fecha_db:
        return ""
    if isinstance(fecha_db, (datetime, date)):
        return fecha_db.strftime("%d-%m-%Y")
    # Si viene como string 'YYYY-MM-DD'
    try:
        return datetime.strptime(str(fecha_db), "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError:
        return str(fecha_db)
    
def transformar_solicitud(datos_raw: dict) -> dict:

    # 1. Limpieza general de campos de texto
    solicitud_limpia = {
        "empresa_origen": datos_raw.get("empresa_origen", "").strip().upper(),
        "diligenciado_por": datos_raw.get("diligenciado_por", "").strip().title(),  # Transforma 'juan perez' -> 'Juan Perez'
        "nivel_de_riesgo": datos_raw.get("nivel_de_riesgo", "BAJO")
        .strip()
        .upper(),
        "tipo_de_persona": datos_raw.get("tipo_de_persona", "").strip(),
        "empresa_contratista": datos_raw.get("empresa_contratista", "")
        .strip()
        .upper(),
        "planta_a_visitar": datos_raw.get("planta_a_visitar", "").strip(),
        "actividad": datos_raw.get("actividad", "").strip(),
        "estado": datos_raw.get("estado", "PENDIENTE").strip().upper(),
    }

    # 2. Conversión segura de fechas a MySQL (YYYY-MM-DD)
    for campo_fecha in ["fecha_inicio", "fecha_fin"]:
        val_fecha = datos_raw.get(campo_fecha)
        solicitud_limpia[campo_fecha] = parsear_fecha(val_fecha)

    # 3. Limpieza de vehículo (previene error si 'vehiculo' viene como None)
    vehiculo_raw = datos_raw.get("vehiculo") or {}
    solicitud_limpia["vehiculo"] = {
        "tipo": vehiculo_raw.get("tipo", "").strip().upper(),
        "placa": vehiculo_raw.get("placa", "")
        .strip()
        .upper()
        .replace(" - ", "-")
        .replace(" ", ""),
    }

    # 4. Limpieza de la lista de personas
    personas_limpias = []
    for p in datos_raw.get("personas") or []:
        personas_limpias.append(
            {
                "ap_nombre": p.get("ap_nombre", "").strip().title(),
                "tipo_doc": p.get("tipo_doc", "").strip().upper(),
                "identificacion": str(p.get("identificacion", ""))
                .replace(".", "")
                .strip(),
                "cargo": p.get("cargo", "").strip().title(),
            }
        )
    solicitud_limpia["personas"] = personas_limpias

    # 5. Limpieza de equipos
    equipos_limpios = []
    for eq in datos_raw.get("eq_computo") or []:
        equipos_limpios.append(
            {
                "marca": eq.get("marca", "").strip().upper(),
                "modelo": eq.get("modelo", "").strip().upper(),
                "serie": eq.get("serie", "").strip().upper(),
            }
        )
    solicitud_limpia["eq_computo"] = equipos_limpios

    return solicitud_limpia