# src/transformers/usuario_transformer.py
def TRANSFORM_USER(data_json: dict) -> dict:

    return {
        "nombres": data_json.get("nombres", "").strip(),
        "apellidos": data_json.get("apellidos", "").strip(),
        "tipo_documento": data_json.get("tipo_documento", "").strip(),
        "num_documento": int(data_json.get("num_documento", 0)),
        "num_telefono": int(data_json.get("num_telefono", 0)),
        "correo": data_json.get("correo", "").strip().lower(),
        "contrasena": data_json.get("contrasena", ""),
        "id_rol": int(data_json.get("id_rol", 0)),  # 0 - garantiza que se conviertan a entero (int)
    }


def TRANSFORM_USER_FOR_FRONT(usuario_db: dict) -> dict:

    # No se permite campo de contrasena para evitar manipulaciones maliciosas desde ell frontend

    if not usuario_db:
        return {}

    return {
        "id": usuario_db.get("id"),
        "nombres": usuario_db.get("nombres"),
        "apellidos": usuario_db.get("apellidos"),
        "tipo_documento": usuario_db.get("tipo_documento"),
        "num_documento": usuario_db.get("num_documento"),
        "num_telefono": usuario_db.get("num_telefono"),
        "correo": usuario_db.get("correo"),
        "id_rol": usuario_db.get("id_rol"),
        "nombre_rol": usuario_db.get("nombre_rol", None),  # Si se hace JOIN con roles
    }
