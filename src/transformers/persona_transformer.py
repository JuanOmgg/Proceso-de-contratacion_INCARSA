def TRANSFOR_PERSON(data_json: dict) -> dict:

    return{

        "nombre": data_json.get("nombre", "").strip().capitalize(),
        "apellido": data_json.get("apellido", "").strip().capitalize(),
        "tipo_doc": data_json.get("tipo_doc", ""),
        "identificacion": data_json.get("identificacion", "").strip(),
        "cargo": data_json.get("cargo", ""),
        "observacion": data_json.get("observacion", "").strip(),
        "documentos_ids": data_json.get("documentos_ids", []),
    }