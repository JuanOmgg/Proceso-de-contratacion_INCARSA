from typing import Any
from src.loaders.correspondencia_loader import (
    CREATE_correspondencia_db,
    GET_correspondencia_db,
    DELETE_correspondencia_db,
    GET_ALL_correspondencia_db,
    UPDATE_correspondencia_db
)
from src.transformers.correspondencia_transformer import TRANSFORM_CORRESPONDENCIA, TRANSFORM_CORRESPONDENCIA_PATCH
from src.schemas.correspondencia_schema import CorrespondenciaInput, UPDATE_correspondenciaInput

def CREATE_correspondencia(payload: CorrespondenciaInput) -> dict:

    data_raw = payload.model_dump()
    data_clean = TRANSFORM_CORRESPONDENCIA(data_raw)

    return CREATE_correspondencia_db(data_clean)

def GET_correspondencia(id_corr: Any) -> dict:

    if isinstance(id_corr, int) and id_corr <= 0:
        return {
            "exito": False,
            "mensaje": f"El ID {id_corr} de la correspondencia debe ser un entero positivo"
        }
    
    resultado = GET_correspondencia_db(id_corr)

    if not resultado["exito"]:
        return {"exito": False, "mensaje": resultado["mensaje"]}

    correspondencia_raw = resultado["data"]
    correspondencia_clean = TRANSFORM_CORRESPONDENCIA(correspondencia_raw)
    correspondencia_clean["id"] = correspondencia_raw.get("id")

    return {"exito": True, "data": correspondencia_clean}

def GET_ALL_correspondencia() -> dict:

    resultado = GET_ALL_correspondencia_db()
    if not resultado.get("exito"):
        return {"exito": False, "mensaje": resultado.get("mensaje", "Error al obtener la correspondencia"), "data": []}

    datos = resultado.get("data", [])
    lista_limpia = []
    for item in datos:
        clean = TRANSFORM_CORRESPONDENCIA(item)
        clean["id"] = item.get("id")
        lista_limpia.append(clean)

    return {"exito": True, "data": lista_limpia, "total": len(lista_limpia)}
    
def DELETE_correspondencia(corr: int) -> dict:

    if corr <= 0:
        return {
            "exito": False,    
            "mensaje": f"El ID {corr} de la correspondencia debe ser un entero positivo"
        }

    resultado = DELETE_correspondencia_db(corr)
    if not resultado["exito"]:
        return {"exito": False, "mensaje": resultado["mensaje"]}
    
    return {
        "exito": True, 
        "mensaje": resultado["mensaje"]
    }

def UPDATE_correspondencia(corr: int, payload: UPDATE_correspondenciaInput) -> dict:
    if corr <= 0:
        return {
            "exito": False,
            "mensaje": f"El ID {corr} de la correspondencia debe ser un entero positivo"
        }

    data_raw = payload.model_dump(exclude_unset=True)
    data_clean = TRANSFORM_CORRESPONDENCIA_PATCH(data_raw)

    return UPDATE_correspondencia_db(corr, data_clean)


    