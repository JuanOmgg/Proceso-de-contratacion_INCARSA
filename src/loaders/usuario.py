from config import settings
from src.loaders.usuario_loader import SAVE_user_db, GET_user_db, DELETE_user_db
from src.transformers import transform_user_db_to_response

import bcrypt


def CREATE_user(
    nombre: str,
    apellido: str,
    tipo_doc: str,
    documento: int,
    telefono: int,
    correo: str,
    password: str,
    id_rol: int,
) -> dict:

    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    nuevo_usuario = {
        "nombres": nombre,
        "apellidos": apellido,
        "tipo_documento": tipo_doc,
        "num_documento": documento,
        "num_telefono": telefono,
        "correo": correo,
        "contrasena": password_hash,
        "id_rol": id_rol,
    }

    result = SAVE_user_db(nuevo_usuario)

    if result["exito"]:
        return {
            "status": "success",
            "mensaje": result["mensaje"],
            "id_generado": result["id_generado"],
        }
    else:
        return {"status": "error", "mensaje": result["mensaje"]}


def READ_user(id_user: int) -> dict:

    if id_user <= 0:
        return {
            "status": "error",
            "mensaje": f"El ID {id_user} del usuario debe ser un entero positivo",
        }

    resultado = GET_user_db(id_user)

    if not resultado["exito"]:
        return {"status": "error", "mensaje": resultado["mensaje"]}

    usuario_raw = resultado["data"]
    user_clean = transform_user_db_to_response(usuario_raw)

    return {"status": "success", "data": user_clean}

def DELETE_user(id_user: int) -> dict:
    if id_user <= 0:
        return {
            "status": "error",
            "mensaje": f"El ID {id_user} del usuario debe ser un entero positivo",
        }

    resultado = DELETE_user_db(id_user)

    if not resultado["exito"]:
        return {"status": "error", "mensaje": resultado["mensaje"]}

    return {"status": "success", "mensaje": resultado["mensaje"]}