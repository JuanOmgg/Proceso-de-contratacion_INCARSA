import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union


# ========================================================
# PARSEADORES Y FORMATEADORES DE FECHA Y PLACA
# ========================================================


def parsear_fecha(
    val_fecha: Optional[Union[str, date, datetime]],
) -> Optional[str]:
    if not val_fecha:
        return None

    # 1. Si Pydantic o la BD nos entrega un objeto 'date' o 'datetime'
    if isinstance(val_fecha, (date, datetime)):
        return val_fecha.strftime("%Y-%m-%d")

    # 2. Si viene como cadena de texto (str)
    if isinstance(val_fecha, str):
        val_limpia = val_fecha.strip().split("T")[0].split(" ")[0]
        fecha_normalizada = val_limpia.replace("/", "-")

        formatos = [
            "%Y-%m-%d",  # ISO / Estándar internacional
            "%d-%m-%Y",  # Estándar Latino / Español
        ]

        for fmt in formatos:
            try:
                return datetime.strptime(fecha_normalizada, fmt).strftime(
                    "%Y-%m-%d"
                )
            except ValueError:
                continue

    return None


def FORMAT_FOR_FRONT(fecha_db: Any) -> str:

    if not fecha_db:
        return ""

    if isinstance(fecha_db, (datetime, date)):
        return fecha_db.strftime("%d-%m-%Y")

    try:
        val_str = str(fecha_db).strip().split("T")[0].split(" ")[0]
        return datetime.strptime(val_str, "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError:
        return str(fecha_db)


def FORMATEAR_PLACA(placa_raw: Optional[str]) -> str:
    if not placa_raw:
        return ""

    texto = str(placa_raw).strip().upper()
    match = re.search(r"([A-Z]{3}).*?(\d{3})", texto)

    if match:
        letras, numeros = match.groups()
        return f"{letras}-{numeros}"

    return re.sub(r"\s+", "", texto)


# ========================================================
# LIMPIADORES DE SUBTABLAS (Reutilizables)
# ========================================================


def limpiar_vehiculos(raw_vehiculos: Any) -> List[Dict[str, str]]:
    if not raw_vehiculos:
        return []

    if isinstance(raw_vehiculos, dict):
        raw_vehiculos = [raw_vehiculos]

    vehiculos_limpios = []
    for v in raw_vehiculos:
        if isinstance(v, dict):
            vehiculos_limpios.append(
                {
                    "tipo": str(v.get("tipo") or "").strip().upper(),
                    "placa": FORMATEAR_PLACA(v.get("placa")),
                }
            )
    return vehiculos_limpios


def limpiar_personas(raw_personas: Any) -> List[Dict[str, str]]:
    if not raw_personas or not isinstance(raw_personas, list):
        return []

    personas_limpias = []
    for p in raw_personas:
        if isinstance(p, dict):
            personas_limpias.append(
                {
                    "ap_nombre": str(p.get("ap_nombre") or "").strip().title(),
                    "tipo_doc": str(p.get("tipo_doc") or "").strip().upper(),
                    "identificacion": str(p.get("identificacion") or "")
                    .replace(".", "")
                    .strip(),
                    "cargo": str(p.get("cargo") or "").strip().title(),
                }
            )
    return personas_limpias


def limpiar_equipos(raw_equipos: Any) -> List[Dict[str, str]]:
    if not raw_equipos or not isinstance(raw_equipos, list):
        return []

    equipos_limpios = []
    for eq in raw_equipos:
        if isinstance(eq, dict):
            equipos_limpios.append(
                {
                    "marca": str(eq.get("marca") or "").strip().upper(),
                    "modelo": str(eq.get("modelo") or "").strip().upper(),
                    "serie": str(eq.get("serie") or "").strip().upper(),
                }
            )
    return equipos_limpios


# TRANSFORMADORES PRINCIPALES


def transformar_solicitud(datos_raw: dict) -> dict:
    """Transformador completo para peticiones POST (Creación)."""
    solicitud_limpia = {
        "empresa_origen": str(datos_raw.get("empresa_origen") or "")
        .strip()
        .upper(),
        "diligenciado_por": int(datos_raw.get("diligenciado_por") or 0),
        "nivel_de_riesgo": str(datos_raw.get("nivel_de_riesgo") or "BAJO")
        .strip()
        .upper(),
        "tipo_de_persona": str(datos_raw.get("tipo_de_persona") or "").strip(),
        "empresa_contratista": str(
            datos_raw.get("empresa_contratista") or ""
        )
        .strip()
        .upper(),
        "planta_a_visitar": str(
            datos_raw.get("planta_a_visitar") or ""
        ).strip(),
        "actividad": str(datos_raw.get("actividad") or "").strip(),
        "estado": str(datos_raw.get("estado") or "PENDIENTE")
        .strip()
        .upper(),
    }

    # Conversión de fechas
    for campo_fecha in ["fecha_inicio", "fecha_fin"]:
        val_fecha = datos_raw.get(campo_fecha)
        solicitud_limpia[campo_fecha] = parsear_fecha(val_fecha)

    # Subtablas
    raw_v = datos_raw.get("vehiculo") or datos_raw.get("vehiculos")
    solicitud_limpia["vehiculo"] = limpiar_vehiculos(raw_v)
    solicitud_limpia["personas"] = limpiar_personas(datos_raw.get("personas"))
    solicitud_limpia["eq_computo"] = limpiar_equipos(
        datos_raw.get("eq_computo")
    )

    return solicitud_limpia


def transformar_solicitud_patch(datos_raw: dict) -> dict:
    """Transformador parcial para peticiones PATCH (Actualización)."""
    solicitud_limpia = {}

    mapeo_strings_upper = [
        "empresa_origen",
        "nivel_de_riesgo",
        "empresa_contratista",
        "estado",
    ]
    mapeo_strings_normales = ["tipo_de_persona", "planta_a_visitar", "actividad"]

    for k in mapeo_strings_upper:
        if k in datos_raw and datos_raw[k] is not None:
            solicitud_limpia[k] = str(datos_raw[k]).strip().upper()

    for k in mapeo_strings_normales:
        if k in datos_raw and datos_raw[k] is not None:
            solicitud_limpia[k] = str(datos_raw[k]).strip()

    if "diligenciado_por" in datos_raw and datos_raw["diligenciado_por"] is not None:
        solicitud_limpia["diligenciado_por"] = int(
            datos_raw["diligenciado_por"] or 0
        )

    for campo_fecha in ["fecha_inicio", "fecha_fin"]:
        if campo_fecha in datos_raw:
            solicitud_limpia[campo_fecha] = parsear_fecha(
                datos_raw[campo_fecha]
            )

    # Procesamiento seguro de subtablas solo si vienen en el PATCH
    if "vehiculo" in datos_raw or "vehiculos" in datos_raw:
        raw_v = datos_raw.get("vehiculo") or datos_raw.get("vehiculos")
        solicitud_limpia["vehiculo"] = limpiar_vehiculos(raw_v)

    if "personas" in datos_raw:
        solicitud_limpia["personas"] = limpiar_personas(datos_raw["personas"])

    if "eq_computo" in datos_raw:
        solicitud_limpia["eq_computo"] = limpiar_equipos(datos_raw["eq_computo"])

    return solicitud_limpia