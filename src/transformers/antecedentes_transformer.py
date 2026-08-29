from datetime import datetime, date, timezone, timedelta
from typing import Dict, Any, Optional

TZ_COLOMBIA = timezone(timedelta(hours=-5))


def FORMATEAR_FECHA_STR(fecha_val: Any) -> Optional[str]:
    if not fecha_val:
        return None
    if isinstance(fecha_val, datetime):
        if fecha_val.tzinfo is not None:
            fecha_val = fecha_val.astimezone(TZ_COLOMBIA).replace(tzinfo=None)
        return fecha_val.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(fecha_val, date):
        return fecha_val.strftime("%Y-%m-%d")
    return str(fecha_val)


def NORMALIZAR_DATETIME_LOCAL(dt_val: Any) -> Optional[datetime]:
    if not dt_val:
        return None
    if isinstance(dt_val, str):
        try:
            if dt_val.endswith("Z") or "+" in dt_val or (len(dt_val) > 10 and "-" in dt_val[10:]):
                dt_obj = datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
                return dt_obj.astimezone(TZ_COLOMBIA).replace(tzinfo=None)
            else:
                return datetime.fromisoformat(dt_val)
        except Exception:
            return None
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is not None:
            return dt_val.astimezone(TZ_COLOMBIA).replace(tzinfo=None)
        return dt_val
    return None


def NORMALIZAR_DATE(d_val: Any) -> Optional[date]:
    if not d_val:
        return None
    if isinstance(d_val, datetime):
        if d_val.tzinfo is not None:
            return d_val.astimezone(TZ_COLOMBIA).date()
        return d_val.date()
    if isinstance(d_val, date):
        return d_val
    if isinstance(d_val, str):
        date_part = d_val.split("T")[0].split(" ")[0].strip()
        try:
            return date.fromisoformat(date_part)
        except Exception:
            return None
    return None


def TRANSFORM_ANTECEDENTE_DATA(data: Dict[str, Any]) -> Dict[str, Any]:
    """Limpia y normaliza datos antes de insertar o responder."""
    resultado = {}
    if "responsable" in data:
        resultado["responsable"] = str(data["responsable"]).strip() if data["responsable"] else None
    if "anotaciones" in data:
        resultado["anotaciones"] = str(data["anotaciones"]).strip() if data["anotaciones"] else None
    if "id_empresa" in data:
        resultado["id_empresa"] = int(data["id_empresa"]) if data["id_empresa"] else None
    if "fecha_consulta" in data:
        resultado["fecha_consulta"] = NORMALIZAR_DATE(data["fecha_consulta"])
    if "ultima_revision" in data:
        resultado["ultima_revision"] = NORMALIZAR_DATETIME_LOCAL(data["ultima_revision"])
    return resultado
