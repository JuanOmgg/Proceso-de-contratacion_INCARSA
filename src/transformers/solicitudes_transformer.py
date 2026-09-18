import os
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from src.transformers.vehiculo_transformer import (
    FORMATEAR_PLACA,
    limpiar_lista_vehiculos as limpiar_vehiculos,
)



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






def limpiar_equipos(raw_equipos: Any) -> List[Dict[str, str]]:
    if not raw_equipos or not isinstance(raw_equipos, list):
        return []

    equipos_limpios = []
    for eq in raw_equipos:
        if isinstance(eq, dict):
            marca = str(eq.get("marca") or "").strip()
            modelo = str(eq.get("modelo") or "").strip()
            serie = str(eq.get("serie") or "").strip()
            if marca or modelo or serie:
                equipos_limpios.append(
                    {
                        "marca": marca.upper(),
                        "modelo": modelo.upper(),
                        "serie": serie.upper(),
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


def limpiar_vehiculos_solicitud(
    raw_v: Any, raw_ids: Any = None
) -> List[Dict[str, Any]]:
    """
    Normaliza los vehículos a ingresar en la solicitud para la tabla Veh_ingreso.
    Soporta IDs directos o datos de vehículo (tipo, placa).
    """
    vehiculos_limpios = []

    if raw_ids and isinstance(raw_ids, list):
        for vid in raw_ids:
            if str(vid).isdigit():
                vehiculos_limpios.append(
                    {"id_vehiculo": int(vid), "licencia_doc": 0}
                )

    if not raw_v:
        return vehiculos_limpios

    if isinstance(raw_v, (dict, int, str)):
        raw_v = [raw_v]

    if isinstance(raw_v, list):
        for v in raw_v:
            if isinstance(v, int) or (isinstance(v, str) and v.isdigit()):
                vehiculos_limpios.append(
                    {"id_vehiculo": int(v), "licencia_doc": ""}
                )
            elif isinstance(v, dict):
                lic_doc_val = v.get("licencia_doc")
                lic_doc = str(lic_doc_val).strip() if lic_doc_val is not None else ""
                cond_val = str(v.get("conductor") or "").strip()
                raw_pid = v.get("id_persona") or v.get("conductor_id")
                id_persona = int(raw_pid) if raw_pid and str(raw_pid).isdigit() and int(raw_pid) > 0 else None
                
                target_vid = v.get("id_vehiculo") or v.get("id")
                id_vehiculo = int(target_vid) if target_vid and str(target_vid).isdigit() and int(target_vid) > 0 else None

                v_dict = {
                    "licencia_doc": lic_doc,
                    "conductor": cond_val,
                    "id_persona": id_persona,
                    "conductor_id": id_persona,
                    "documentos": v.get("documentos") or [],
                }
                if id_vehiculo:
                    v_dict["id_vehiculo"] = id_vehiculo
                if v.get("placa"):
                    v_dict["tipo"] = str(v.get("tipo") or "CAMIONETA").strip().upper()
                    v_dict["placa"] = FORMATEAR_PLACA(v.get("placa"))

                vehiculos_limpios.append(v_dict)

    return vehiculos_limpios


def transformar_solicitud(datos_raw: dict) -> dict:
    """Valida, limpia y transforma una estructura JSON de solicitud."""
    solicitud_limpia = {
        "codigo": str(datos_raw.get("codigo") or datos_raw.get("codigo_radicado") or "").strip().upper() or None,
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
        "observaciones": str(datos_raw.get("observaciones") or datos_raw.get("observacion") or "").strip(),
        "estado": str(datos_raw.get("estado") or "ENVIADO")
        .strip()
        .upper(),
        "plantas_ids": datos_raw.get("plantas_ids") or [],
        "personas_ids": [
            int(p) for p in (datos_raw.get("personas_ids") or []) if str(p).isdigit()
        ],
        "personas": datos_raw.get("personas") or datos_raw.get("ingresantes"),
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

    # Subtablas (Veh_ingreso y equipos)
    raw_v = datos_raw.get("vehiculo") or datos_raw.get("vehiculos")
    raw_v_ids = datos_raw.get("vehiculos_ids")
    solicitud_limpia["vehiculos"] = limpiar_vehiculos_solicitud(raw_v, raw_v_ids)
    raw_eq = datos_raw.get("eq_computo")
    if raw_eq is None:
        raw_eq = datos_raw.get("equipos") or datos_raw.get("computos")
    solicitud_limpia["eq_computo"] = limpiar_equipos(raw_eq)

    return solicitud_limpia


def transformar_solicitud_patch(datos_raw: dict) -> dict:
    """Transformador parcial para peticiones PATCH (Actualización)."""
    solicitud_limpia = {}

    if "codigo" in datos_raw and datos_raw["codigo"] is not None:
        solicitud_limpia["codigo"] = str(datos_raw["codigo"]).strip().upper()
    elif "codigo_radicado" in datos_raw and datos_raw["codigo_radicado"] is not None:
        solicitud_limpia["codigo"] = str(datos_raw["codigo_radicado"]).strip().upper()

    if "observaciones" in datos_raw or "observacion" in datos_raw:
        solicitud_limpia["observaciones"] = str(datos_raw.get("observaciones") or datos_raw.get("observacion") or "").strip()

    if "personas" in datos_raw or "ingresantes" in datos_raw:
        solicitud_limpia["personas"] = datos_raw.get("personas") or datos_raw.get("ingresantes")

    mapeo_strings_upper = [
        "nivel_de_riesgo",
        "estado",
    ]
    mapeo_strings_normales = ["tipo_personal", "planta_a_visitar", "actividad"]

    for k in mapeo_strings_upper:
        if k in datos_raw and datos_raw[k] is not None:
            solicitud_limpia[k] = str(datos_raw[k]).strip().upper()

    for k in mapeo_strings_normales:
        if k in datos_raw and datos_raw[k] is not None:
            solicitud_limpia[k] = str(datos_raw[k]).strip()

    if "empresa_origen" in datos_raw and datos_raw["empresa_origen"] is not None:
        val_eo = str(datos_raw["empresa_origen"]).strip()
        solicitud_limpia["empresa_origen"] = int(val_eo) if val_eo.isdigit() else val_eo

    if "empresa_contratista" in datos_raw and datos_raw["empresa_contratista"] is not None:
        val_ec = str(datos_raw["empresa_contratista"]).strip()
        solicitud_limpia["empresa_contratista"] = int(val_ec) if val_ec.isdigit() else val_ec

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
    if (
        "vehiculo" in datos_raw
        or "vehiculos" in datos_raw
        or "vehiculos_ids" in datos_raw
    ):
        raw_v = datos_raw.get("vehiculo") or datos_raw.get("vehiculos")
        raw_v_ids = datos_raw.get("vehiculos_ids")
        solicitud_limpia["vehiculos"] = limpiar_vehiculos_solicitud(
            raw_v, raw_v_ids
        )

    if "eq_computo" in datos_raw or "equipos" in datos_raw or "computos" in datos_raw:
        raw_eq = datos_raw.get("eq_computo")
        if raw_eq is None:
            raw_eq = datos_raw.get("equipos") or datos_raw.get("computos")
        solicitud_limpia["eq_computo"] = limpiar_equipos(raw_eq)

    if "personas_ids" in datos_raw and datos_raw["personas_ids"] is not None:
        solicitud_limpia["personas_ids"] = [
            int(p) for p in datos_raw["personas_ids"] if str(p).isdigit()
        ]

    if "plantas_ids" in datos_raw and datos_raw["plantas_ids"] is not None:
        solicitud_limpia["plantas_ids"] = [
            int(p) for p in datos_raw["plantas_ids"] if str(p).isdigit()
        ]

    # Recalcular is_active si se envían ambas fechas y no se especificó is_active explícito
    if (
        "fecha_inicio" in solicitud_limpia
        and "fecha_fin" in solicitud_limpia
        and "is_active" not in solicitud_limpia
    ):
        solicitud_limpia["is_active"] = calcular_is_active(
            solicitud_limpia["fecha_inicio"], solicitud_limpia["fecha_fin"]
        )

    return solicitud_limpia