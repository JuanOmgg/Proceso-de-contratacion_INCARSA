def transform_json_to_create_user_params(data_json: dict) -> dict:
    
    return {
        "nombre": data_json.get("nombres", "").strip(),
        "apellido": data_json.get("apellidos", "").strip(),
        "tipo_doc": data_json.get("tipo_de_documento", "").strip(),
        "documento": int(data_json.get("num_documento", 0)),
        "telefono": int(data_json.get("numero_de_telefono", 0)),
        "correo": data_json.get("correo", "").strip().lower(),
        "password": data_json.get("password", ""),
        "id_rol": int(data_json.get("id_rol", 0)) # 0 - garantiza que se conviertan a entero (int)
    }


def transform_user_db_to_response(usuario_db: dict) -> dict:

    # No se permite campo de contrasena para enitar manipulaciones maliciosas desde ell frontend
     
    if not usuario_db:
        return {}

    return {
        "id_user": usuario_db.get("id_user"),
        "nombres": usuario_db.get("nombres"),
        "apellidos": usuario_db.get("apellidos"),
        "tipo_de_documento": usuario_db.get("tipo_de_documento"),
        "num_documento": usuario_db.get("num_documento"),
        "numero_de_telefono": usuario_db.get("numero_de_telefono"),
        "correo": usuario_db.get("correo"),
        "id_rol": usuario_db.get("id_rol"),
        "nombre_rol": usuario_db.get("nombre_rol", None),  # Si se hace JOIN con roles
        "fecha_creacion": str(usuario_db.get("fecha_creacion", ""))
    }