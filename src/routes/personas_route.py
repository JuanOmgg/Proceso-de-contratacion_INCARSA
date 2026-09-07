from fastapi import APIRouter, HTTPException, status, Depends
from src.schemas.personas_schema import PersonInput, PersonInputUpdate
from src.loaders.personas_loader import (
    GET_ALL_person_db,
    GET_person_by_id_db,
    UPDATE_person_db,
    DELETE_person_db,
    DELETE_documento_persona_db,
)
from src.services.personas import CREATE_person
from src.utils.security import get_current_user, require_permission

router = APIRouter(prefix="/personas", tags=["Personas"])

@router.post("/create", status_code=status.HTTP_201_CREATED)
def CREATE_person_rt(payload: PersonInput, current_user: dict = Depends(require_permission("personas", "crear"))):

    resultado = CREATE_person(payload)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje"),
        )

    return resultado

@router.get("/getAll", status_code=status.HTTP_200_OK)
@router.get("/getall", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK)
@router.get("", status_code=status.HTTP_200_OK, include_in_schema=False)
def GET_ALL_person_rt(current_user: dict = Depends(get_current_user)):

    print("🔍 [GETALL] Consultando todas las personas en la base de datos...")

    resultado = GET_ALL_person_db()

    if not resultado.get("exito", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al obtener personas.")
        )

    return resultado

@router.get("/{persona_id}", status_code=status.HTTP_200_OK)
def GET_person_by_id_rt(persona_id: int, current_user: dict = Depends(get_current_user)):
    resultado = GET_person_by_id_db(persona_id)
    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", f"Persona con ID {persona_id} no encontrada.")
        )
    return resultado

@router.put("/{persona_id}", status_code=status.HTTP_200_OK)
@router.patch("/{persona_id}", status_code=status.HTTP_200_OK)
def UPDATE_person_rt(
    persona_id: int,
    payload: PersonInputUpdate,
    current_user: dict = Depends(require_permission("personas", "editar"))
):
    datos = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    resultado = UPDATE_person_db(persona_id, datos)
    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al actualizar persona.")
        )
    return resultado

@router.delete("/{persona_id}", status_code=status.HTTP_200_OK)
@router.delete("/delete/{persona_id}", status_code=status.HTTP_200_OK)
def DELETE_person_rt(
    persona_id: int,
    current_user: dict = Depends(require_permission("personas", "eliminar"))
):
    resultado = DELETE_person_db(persona_id)
    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al eliminar persona.")
        )
    return resultado

@router.delete("/{persona_id}/documentos/{documento_id}", status_code=status.HTTP_200_OK)
@router.delete("/documentos/{documento_id}", status_code=status.HTTP_200_OK)
def DELETE_documento_persona_rt(
    documento_id: int,
    persona_id: int = None,
    current_user: dict = Depends(require_permission("personas", "editar"))
):
    resultado = DELETE_documento_persona_db(documento_id, persona_id)
    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", "Error al eliminar el documento de la persona.")
        )
    return resultado
