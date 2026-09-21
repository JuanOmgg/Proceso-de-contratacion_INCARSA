def TRANSFOR_PERSON(data_json: dict) -> dict:
    correo_raw = data_json.get("correo")
    correo_clean = str(correo_raw).strip().lower() if correo_raw else None

    return {
        "nombre": str(data_json.get("nombre") or "").strip().capitalize(),
        "apellido": str(data_json.get("apellido") or "").strip().capitalize(),
        "tipo_doc": str(data_json.get("tipo_doc") or "CC").strip(),
        "identificacion": str(data_json.get("identificacion") or "").strip(),
        "cargo": str(data_json.get("cargo") or "Personal").strip(),
        "correo": correo_clean,
        "observacion": str(data_json.get("observacion") or "").strip(),
        "documentos_ids": data_json.get("documentos_ids") or [],
    }