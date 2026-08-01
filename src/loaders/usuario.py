from config import settings
from src.loaders.usuario_loader import CREATE_user_db, GET_user_db, DELETE_user_db
from src.transformers import TRANSFORM_USER, TRANSFORM_USER_FOR_FRONT
from src.schemas.usuario_schema import UsuarioInput

import bcrypt


def CREATE_user(payload: UsuarioInput) -> dict:
    # 1. Convertimos el modelo de Pydantic a diccionario
    data_raw = payload.model_dump()

    # 2. Pasamos por tu transformador
    data_clean = TRANSFORM_USER(data_raw)

    # 3. Encriptamos la contraseña limpia
    password_plana = data_clean.get("contrasena", "")
    password_bytes = password_plana.encode("utf-8")
    salt = bcrypt.gensalt()
    data_clean["contrasena"] = bcrypt.hashpw(password_bytes, salt).decode(
        "utf-8"
    )

    # 4. Persistimos en MySQL
    return CREATE_user_db(data_clean)


def READ_user(id_user: int) -> dict:

    if id_user <= 0:
        return {
            "exito": False,
            "mensaje": f"El ID {id_user} del usuario debe ser un entero positivo",
        }

    resultado = GET_user_db(id_user)

    if not resultado["exito"]:
        return {"exito": False, "mensaje": resultado["mensaje"]}

    usuario_raw = resultado["data"]
    user_clean = TRANSFORM_USER_FOR_FRONT(usuario_raw)

    return {"exito": True, "data": user_clean}

def DELETE_user(id_user: int) -> dict:
    if id_user <= 0:
        return {
            "exito": False,
            "mensaje": f"El ID {id_user} del usuario debe ser un entero positivo",
        }

    resultado = DELETE_user_db(id_user)

    if not resultado["exito"]:
        return {"exito": False, "mensaje": resultado["mensaje"]}

    return {"exito": True, "mensaje": resultado["mensaje"]}