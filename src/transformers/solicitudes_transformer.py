import os
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


def limpiar_personas(raw_personas: Any) -> List[Dict[str, Any]]:
    if not raw_personas or not isinstance(raw_personas, list):
        return []

    personas_limpias = []
    for p in raw_personas:
        if isinstance(p, dict):
            raw_docs = p.get("documentos", [])
            docs_limpios = []
            if isinstance(raw_docs, list):
                for d in raw_docs:
                    if isinstance(d, dict):
                        nombre_arc = d.get("nombre_archivo") or d.get("url_doc") or ""
                        nombre_limpio = os.path.basename(str(nombre_arc).strip())
                        if nombre_limpio:
                            docs_limpios.append(
                                {
                                    "tipo_doc": str(d.get("tipo_doc") or "general").strip().lower(),
                                    "nombre_archivo": nombre_limpio,
                                }
                            )

            personas_limpias.append(
                {
                    "ap_nombre": str(p.get("ap_nombre") or "").strip().title(),
                    "tipo_doc": str(p.get("tipo_doc") or "").strip().upper(),
                    "identificacion": str(p.get("identificacion") or "")
                    .replace(".", "")
                    .strip(),
                    "cargo": str(p.get("cargo") or "").strip().title(),
                    "documentos": docs_limpios,
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


def calcular_is_active(f_inicio: Any, f_fin: Any) -> bool:
    """Calcula si una solicitud está activa hoy según si hoy está entre fecha_inicio y fecha_fin (inclusive)."""
    today = date.today()

    def to_date(v):
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        if isinstance(v, str) and v.strip():
            try:
                val_limpia = v.strip().split("T")[0].split(" ")[0].replace("/", "-")
                for fmt in ["%Y-%m-%d", "%d-%m-%Y"]:
                    try:
                        return datetime.strptime(val_limpia, fmt).date()
                    except ValueError:
                        continue
            except Exception:
                return None
        return None

    d_start = to_date(f_inicio)
    d_end = to_date(f_fin)

    if d_start and d_end:
        return d_start <= today <= d_end
    return False


def transformar_solicitud(datos_raw: dict) -> dict:
    """Valida, limpia y transforma una estructura JSON de solicitud."""
    solicitud_limpia = {
        "empresa_origen": str(
            datos_raw.get("empresa_origen") or ""
        ).strip().upper(),
        "diligenciado_por": int(datos_raw.get("diligenciado_por") or 0),
        "nivel_de_riesgo": str(datos_raw.get("nivel_de_riesgo") or "BAJO")
        .strip()
        .upper(),
        "tipo_personal": str(datos_raw.get("tipo_personal") or "").strip(),
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
        "plantas_ids": datos_raw.get("plantas_ids") or [],
    }

    # Conversión de fechas
    for campo_fecha in ["fecha_inicio", "fecha_fin"]:
        val_fecha = datos_raw.get(campo_fecha)
        solicitud_limpia[campo_fecha] = parsear_fecha(val_fecha)

    # Calcular is_active dinámicamente según el rango [fecha_inicio, fecha_fin]
    solicitud_limpia["is_active"] = calcular_is_active(
        solicitud_limpia.get("fecha_inicio"),
        solicitud_limpia.get("fecha_fin"),
    )

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
    mapeo_strings_normales = ["tipo_personal", "planta_a_visitar", "actividad"]

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

    if "is_active" in datos_raw and datos_raw["is_active"] is not None:
        solicitud_limpia["is_active"] = bool(datos_raw["is_active"])

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