from fastapi import APIRouter, HTTPException, status, Query
from src.schemas.antecedentes_schema import AntecedenteUpdate, HistorialSolicitudCreate
from src.services.antecedentes import (
    OBTENER_ANTECEDENTE_PERSONA,
    ACTUALIZAR_ANTECEDENTE,
    REGISTRAR_HISTORIAL_SOLICITUD,
    LISTAR_TODOS_ANTECEDENTES
)

router = APIRouter(prefix="/antecedentes", tags=["Antecedentes"])


@router.get("/persona/{persona_id}", status_code=status.HTTP_200_OK)
def GET_antecedente_persona_endpoint(persona_id: int, actualizar_revision: bool = Query(False)):
    """
    Obtiene los antecedentes y el historial consolidado de una persona.
    Si actualizar_revision=True, auto-actualiza ultima_revision y fecha_consulta (+1 año).
    """
    resultado = OBTENER_ANTECEDENTE_PERSONA(persona_id, actualizar_revision=actualizar_revision)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", "No se encontró el registro de antecedentes.")
        )
    return resultado["datos"]


@router.patch("/persona/{persona_id}", status_code=status.HTTP_200_OK)
def PATCH_antecedente_persona_endpoint(persona_id: int, payload: AntecedenteUpdate):
    """
    Actualiza manualmente campos como responsable o anotaciones.
    """
    resultado = ACTUALIZAR_ANTECEDENTE(persona_id, payload)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al actualizar antecedentes.")
        )
    return {"exito": True, "mensaje": resultado["mensaje"]}


@router.post("/persona/{persona_id}/historial", status_code=status.HTTP_201_CREATED)
def POST_historial_solicitud_endpoint(persona_id: int, payload: HistorialSolicitudCreate):
    """
    Registra una solicitud en el historial de antecedentes de la persona.
    """
    resultado = REGISTRAR_HISTORIAL_SOLICITUD(persona_id, payload)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al registrar el historial.")
        )
    return {"exito": True, "mensaje": resultado["mensaje"]}


@router.get("/getAll", status_code=status.HTTP_200_OK)
@router.get("/getall", status_code=status.HTTP_200_OK)
@router.get("", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK, include_in_schema=False)
def GET_ALL_antecedentes_endpoint():
    """
    Lista todos los registros de antecedentes de las personas con su total de solicitudes.
    """
    resultado = LISTAR_TODOS_ANTECEDENTES()
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al listar antecedentes.")
        )
    return resultado.get("datos", [])
