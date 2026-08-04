from fastapi import APIRouter, HTTPException, status
from src.schemas.planta_schema import PlantaInput, UpdatePlantaInput
from src.services.planta import CREATE_planta
from src.loaders.planta_loader import (
    GET_planta_db, 
    UPDATE_planta_db, 
    DELETE_planta_db
    )
from src.transformers.planta_transformer import TRANSFORM_PLANTA

router = APIRouter(prefix="/planta", tags=["Planta"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def CREATE_planta_rt(payload: PlantaInput):

    resultado = CREATE_planta(payload)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje")
        )

    return resultado

@router.get("/{id_planta}", status_code=status.HTTP_200_OK)
def GET_planta_rt(id_planta: int):

    print(f"🔍 [GET] Buscando planta/zona con ID #{id_planta} en la base de datos")
    resultado = GET_planta_db(id_planta)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje")
        )

    print(f"📦 [GET] Datos de la planta/zona #{id_planta} recuperados con éxito.")
    return resultado

@router.patch("/{id_planta}", status_code=status.HTTP_200_OK)
def UPDATE_planta_rt(id_planta: int, payload: UpdatePlantaInput):

    print(f"🔄 [PATCH] Actualizando planta con ID #{id_planta} en la base de datos...")
    data_raw = payload.model_dump(exclude_unset=True)

    data_update = TRANSFORM_PLANTA(data_raw)

    if not data_update:

        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "❌❌ No se proporcionaron datos para actualizar la planta/zona ❌❌"
        )

    print(f"⚙️ [LOADER] Aplicando cambios en MySQL para la planta/zona #{id_planta}...")
    resultado = UPDATE_planta_db(id_planta, data_update)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = resultado.get("mensaje")
        )
    
    print(f"✅ [PUT] Planta/zona con ID #{id_planta} actualizada con éxito.")
    return resultado

@router.delete("/{id_planta}")
def DELETE_planta_rt(id_planta: int):

    print(f"🗑️ [DELETE] Eliminando planta #{id_planta} de la base de datos...")
    resultado = DELETE_planta_db(id_planta)

    if resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= resultado["mensaje"]
        )

    print(f"✅ Planta/zona #{id_planta} eliminado correctamente de la base de datos.")
    return resultado

