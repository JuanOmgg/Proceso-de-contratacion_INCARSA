import re
from typing import Any, Dict, List, Optional


def FORMATEAR_PLACA(placa_raw: Optional[str]) -> str:
    """
    Estandariza el formato de placas vehiculares:
    Elimina espacios, guiones y caracteres no alfanuméricos, retornando
    la placa en mayúsculas sin guiones (ej. 'ABC123', 'ABC12D', 'R12345').
    """
    if not placa_raw:
        return ""

    # Limpiar espacios, guiones, puntos y caracteres no alfanuméricos, pasando a mayúsculas
    texto_limpio = re.sub(r"[^A-Z0-9]", "", str(placa_raw).strip().upper())
    return texto_limpio


def limpiar_documentos_vehiculo(raw_docs: Any) -> List[Dict[str, str]]:
    """
    Normaliza y limpia la lista de documentos de un vehículo.
    """
    if not raw_docs:
        return []

    if isinstance(raw_docs, dict):
        raw_docs = [raw_docs]

    docs_limpios = []
    if isinstance(raw_docs, list):
        for d in raw_docs:
            if isinstance(d, dict):
                nom = d.get("nom_documento") or d.get("nombre_archivo") or ""
                t_doc = d.get("tipo_doc") or "general"
                if nom:
                    docs_limpios.append(
                        {
                            "tipo_doc": str(t_doc).strip().lower(),
                            "nom_documento": str(nom).strip(),
                            "nombre_archivo": str(nom).strip(),
                        }
                    )
    return docs_limpios


def TRANSFORMER_vehiculo(datos_raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Limpia, valida y estandariza los datos de un vehículo para inserción (POST).
    """
    docs_raw = (
        datos_raw.get("documentos")
        or datos_raw.get("documentos_ids")
        or []
    )
    docs_limpios = limpiar_documentos_vehiculo(docs_raw)

    licencia_doc = str(datos_raw.get("licencia_doc") or "").strip()
    if licencia_doc and not any(d.get("tipo_doc", "").lower().startswith("licencia") for d in docs_limpios):
        docs_limpios.append({
            "tipo_doc": "licencia",
            "nom_documento": licencia_doc,
            "nombre_archivo": licencia_doc
        })

    return {
        "tipo": str(datos_raw.get("tipo") or "").strip().upper(),
        "placa": FORMATEAR_PLACA(datos_raw.get("placa")),
        "conductor": str(datos_raw.get("conductor") or "").strip(),
        "licencia_doc": licencia_doc,
        "documentos": docs_limpios,
    }


def TRANSFORMER_vehiculo_patch(datos_raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforma de manera segura los datos de un vehículo en peticiones de actualización parcial (PATCH).
    """
    vehiculo_limpio: Dict[str, Any] = {}

    if "tipo" in datos_raw and datos_raw["tipo"] is not None:
        vehiculo_limpio["tipo"] = str(datos_raw["tipo"]).strip().upper()

    if "placa" in datos_raw and datos_raw["placa"] is not None:
        vehiculo_limpio["placa"] = FORMATEAR_PLACA(datos_raw["placa"])

    if "conductor" in datos_raw and datos_raw["conductor"] is not None:
        vehiculo_limpio["conductor"] = str(datos_raw["conductor"]).strip()

    if "licencia_doc" in datos_raw and datos_raw["licencia_doc"] is not None:
        vehiculo_limpio["licencia_doc"] = str(datos_raw["licencia_doc"]).strip()

    if "documentos" in datos_raw or "documentos_ids" in datos_raw:
        docs_raw = (
            datos_raw.get("documentos")
            if "documentos" in datos_raw
            else datos_raw.get("documentos_ids")
        )
        docs_limpios = limpiar_documentos_vehiculo(docs_raw)
        if vehiculo_limpio.get("licencia_doc") and not any(d.get("tipo_doc", "").lower().startswith("licencia") for d in docs_limpios):
            docs_limpios.append({
                "tipo_doc": "licencia",
                "nom_documento": vehiculo_limpio["licencia_doc"],
                "nombre_archivo": vehiculo_limpio["licencia_doc"]
            })
        vehiculo_limpio["documentos"] = docs_limpios
    elif vehiculo_limpio.get("licencia_doc"):
        # Si se pasó licencia_doc pero no la lista de documentos, asegurar que se actualice la licencia
        vehiculo_limpio["documentos"] = [{
            "tipo_doc": "licencia",
            "nom_documento": vehiculo_limpio["licencia_doc"],
            "nombre_archivo": vehiculo_limpio["licencia_doc"]
        }]

    return vehiculo_limpio


def limpiar_lista_vehiculos(raw_vehiculos: Any) -> List[Dict[str, Any]]:
    """
    Procesa y limpia múltiples vehículos (lista o dict individual).
    """
    if not raw_vehiculos:
        return []

    if isinstance(raw_vehiculos, dict):
        raw_vehiculos = [raw_vehiculos]

    vehiculos_limpios = []
    if isinstance(raw_vehiculos, list):
        for v in raw_vehiculos:
            if isinstance(v, dict):
                vehiculos_limpios.append(TRANSFORMER_vehiculo(v))

    return vehiculos_limpios