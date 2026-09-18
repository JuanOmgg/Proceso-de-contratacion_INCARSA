from fastapi import APIRouter, HTTPException, status, Depends
from typing import Any
from src.schemas.correspondencia_schema import CorrespondenciaInput, UPDATE_correspondenciaInput
from src.services.correspondencia import (
    CREATE_correspondencia,
    GET_correspondencia,
    GET_ALL_correspondencia,
    DELETE_correspondencia,
    UPDATE_correspondencia
)
from src.utils.security import get_current_user

router = APIRouter(prefix="/correspondencia", tags=["Correspondencia"])

@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def CREATE_correspondencia_rt(payload: CorrespondenciaInput):
    resultado = CREATE_correspondencia(payload)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al registrar la correspondencia.")
        )

    return resultado

@router.get("/getAll", status_code=status.HTTP_200_OK)
@router.get("/getall", status_code=status.HTTP_200_OK, include_in_schema=False)
@router.get("/", status_code=status.HTTP_200_OK)
@router.get("", status_code=status.HTTP_200_OK, include_in_schema=False)
def GET_ALL_correspondencia_rt(current_user: dict = Depends(get_current_user)):
    resultado = GET_ALL_correspondencia()

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al obtener el listado de correspondencia.")
        )

    return resultado

@router.get("/{id_corr}", status_code=status.HTTP_200_OK)
def GET_correspondencia_rt(id_corr: str, current_user: dict = Depends(get_current_user)):
    resultado = GET_correspondencia(id_corr)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", "Correspondencia no encontrada.")
        )

    return resultado

@router.put("/{id_corr}", status_code=status.HTTP_200_OK)
@router.patch("/{id_corr}", status_code=status.HTTP_200_OK)
def UPDATE_correspondencia_rt(id_corr: int, payload: UPDATE_correspondenciaInput, current_user: dict = Depends(get_current_user)):
    resultado = UPDATE_correspondencia(id_corr, payload)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al actualizar la correspondencia.")
        )

    return resultado

@router.delete("/{id_corr}", status_code=status.HTTP_200_OK)
def DELETE_correspondencia_rt(id_corr: int, current_user: dict = Depends(get_current_user)):
    resultado = DELETE_correspondencia(id_corr)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al eliminar la correspondencia.")
        )

    return resultado
