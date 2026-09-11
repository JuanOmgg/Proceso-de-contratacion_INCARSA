from datetime import datetime, date
from typing import Optional, Union

def formatear_solo_fecha(val_fecha: Optional[Union[str, date, datetime]] = None) -> str:
    """Extrae y formatea únicamente el día, mes y año (YYYY-MM-DD)."""
    if not val_fecha:
        return datetime.now().strftime("%Y-%m-%d")

    if isinstance(val_fecha, (date, datetime)):
        return val_fecha.strftime("%Y-%m-%d")

    if isinstance(val_fecha, str):
        val_limpia = val_fecha.strip().split("T")[0].split(" ")[0]
        fecha_normalizada = val_limpia.replace("/", "-")
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(fecha_normalizada, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return val_limpia

    return datetime.now().strftime("%Y-%m-%d")


def TRANSFORM_CORRESPONDENCIA(data_json: dict) -> dict:

    res = {
        "tipo_correspondencia": data_json.get("tipo_correspondencia", "").strip(),
        "asunto": data_json.get("asunto", "").strip().capitalize(),
        "procedencia": data_json.get("procedencia", "").strip().capitalize(),
        "destino": data_json.get("destino", "").strip().capitalize(),
        "fecha_envio": formatear_solo_fecha(data_json.get("fecha_envio")),
    }

    if data_json.get("radicado"):
        res["radicado"] = str(data_json.get("radicado")).strip().upper()

    return res


def TRANSFORM_CORRESPONDENCIA_PATCH(data_json: dict) -> dict:
    res = {}
    if "tipo_correspondencia" in data_json and data_json["tipo_correspondencia"] is not None:
        res["tipo_correspondencia"] = str(data_json["tipo_correspondencia"]).strip()
    if "asunto" in data_json and data_json["asunto"] is not None:
        res["asunto"] = str(data_json["asunto"]).strip().capitalize()
    if "procedencia" in data_json and data_json["procedencia"] is not None:
        res["procedencia"] = str(data_json["procedencia"]).strip().capitalize()
    if "destino" in data_json and data_json["destino"] is not None:
        res["destino"] = str(data_json["destino"]).strip().capitalize()
    if "fecha_envio" in data_json and data_json["fecha_envio"] is not None:
        res["fecha_envio"] = formatear_solo_fecha(data_json["fecha_envio"])
    if "radicado" in data_json and data_json["radicado"] is not None:
        res["radicado"] = str(data_json["radicado"]).strip().upper()
    return res