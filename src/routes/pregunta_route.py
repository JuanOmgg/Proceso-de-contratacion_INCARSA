from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional, List
from src.schemas.pregunta_schema import (
    PreguntaInput,
    PreguntaUpdate,
    PreguntasSyncPayload
)
from src.utils.security import get_current_user
from src.loaders.pregunta_loader import (
    GET_preguntas_por_formulario_db,
    GET_pregunta_por_id_db,
    CREATE_pregunta_db,
    UPDATE_pregunta_db,
    TOGGLE_estado_pregunta_db,
    DELETE_pregunta_db,
    SYNC_preguntas_formulario_db
)

router = APIRouter(prefix="/preguntas", tags=["Preguntas GESCO"])


def _validar_permisos_gesco(current_user: dict):
    rol = str(current_user.get("rol") or current_user.get("nombre_rol") or "").strip().upper()
    id_rol = int(current_user.get("id_rol") or 0)
    roles_permitidos = ["GESCO", "ADMINISTRADOR", "ADMIN", "SUPERADMIN", "SCR", "SST"]
    if id_rol in [1, 2, 4, 7, 8] or any(r in rol for r in roles_permitidos):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para administrar preguntas de inducción GESCO."
    )


@router.get("/formulario/{id_form}", status_code=status.HTTP_200_OK)
def LISTAR_preguntas_por_formulario(
    id_form: int,
    solo_activas: bool = Query(False, description="Filtrar solo preguntas con estado activo"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene todas las preguntas con sus opciones para un formulario GESCO.
    """
    res = GET_preguntas_por_formulario_db(id_form, solo_activas=solo_activas)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res.get("mensaje"))
    return res.get("datos", [])


@router.post("/formulario/{id_form}/sync", status_code=status.HTTP_200_OK)
def SINCRONIZAR_preguntas_formulario(
    id_form: int,
    payload: PreguntasSyncPayload,
    current_user: dict = Depends(get_current_user)
):
    """
    Sincroniza en un solo lote todas las preguntas y opciones de un formulario GESCO.
    Ideal para el diseñador/constructor visual de preguntas.
    """
    _validar_permisos_gesco(current_user)
    raw_list = [q.model_dump() for q in payload.preguntas]
    res = SYNC_preguntas_formulario_db(id_form, raw_list)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.get("/{id_pregunta}", status_code=status.HTTP_200_OK)
def OBTENER_pregunta(
    id_pregunta: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene los detalles de una pregunta y sus opciones asociadas.
    """
    res = GET_pregunta_por_id_db(id_pregunta)
    if not res.get("exito") or not res.get("datos"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res.get("mensaje", f"Pregunta #{id_pregunta} no encontrada.")
        )
    return res["datos"]


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def CREAR_pregunta(
    payload: PreguntaInput,
    current_user: dict = Depends(get_current_user)
):
    """
    Crea una nueva pregunta con sus opciones de respuesta.
    """
    _validar_permisos_gesco(current_user)
    res = CREATE_pregunta_db(payload.model_dump())
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.put("/{id_pregunta}", status_code=status.HTTP_200_OK)
def ACTUALIZAR_pregunta(
    id_pregunta: int,
    payload: PreguntaUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza el enunciado, tipo o estado de una pregunta y sincroniza sus opciones.
    """
    _validar_permisos_gesco(current_user)
    res = UPDATE_pregunta_db(id_pregunta, payload.model_dump(exclude_unset=True))
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.patch("/{id_pregunta}/toggle-estado", status_code=status.HTTP_200_OK)
def TOGGLE_ESTADO_pregunta(
    id_pregunta: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Alterna el estado activo/inactivo de una pregunta.
    """
    _validar_permisos_gesco(current_user)
    res = TOGGLE_estado_pregunta_db(id_pregunta)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.delete("/{id_pregunta}", status_code=status.HTTP_200_OK)
def ELIMINAR_pregunta(
    id_pregunta: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina una pregunta y todas sus opciones asociadas.
    """
    _validar_permisos_gesco(current_user)
    res = DELETE_pregunta_db(id_pregunta)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res
