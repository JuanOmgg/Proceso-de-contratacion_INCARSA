# src/transformers/usuario_transformer.py
def TRANSFORM_USER(data_json: dict) -> dict:

    res = {
        "nombres": data_json.get("nombres", "").strip().capitalize(),
        "apellidos": data_json.get("apellidos", "").strip().capitalize(),
        "tipo_documento": data_json.get("tipo_documento", "").strip(),
        "num_documento": int(data_json.get("num_documento", "")),
        "num_telefono": int(data_json.get("num_telefono", "")),
        "correo": data_json.get("correo", "").strip().lower(),
        "contrasena": data_json.get("contrasena", ""),
        "id_rol": int(data_json.get("id_rol", 0)),
        "is_active": bool(data_json.get("is_active", True)),
    }
    if "plantas_ids" in data_json and data_json["plantas_ids"] is not None:
        res["plantas_ids"] = [int(p) for p in data_json["plantas_ids"] if str(p).isdigit()]
    return res


def TRANSFORM_USER_FOR_FRONT(usuario_db: dict) -> dict:

    if not usuario_db:
        return {}

    return {
        "id": usuario_db.get("id"),
        "nombres": usuario_db.get("nombres"),
        "apellidos": usuario_db.get("apellidos"),
        "nombre_completo": f"{usuario_db.get('nombres', '')} {usuario_db.get('apellidos', '')}".strip(),
        "tipo_documento": usuario_db.get("tipo_documento"),
        "num_documento": usuario_db.get("num_documento"),
        "num_telefono": usuario_db.get("num_telefono"),
        "correo": usuario_db.get("correo"),
        "id_rol": usuario_db.get("id_rol"),
        "rol": usuario_db.get("nombre_rol", usuario_db.get("rol")),
        "is_active": bool(usuario_db.get("is_active", True)),
        "fecha_creacion": usuario_db.get("fecha_creacion"),
        "plantas_ids": usuario_db.get("plantas_ids", []),
        "plantas": usuario_db.get("plantas", []),
    }
