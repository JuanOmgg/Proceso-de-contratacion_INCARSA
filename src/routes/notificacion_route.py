from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import Optional
from pydantic import BaseModel

from src.loaders.notificacion_loader import (
    crear_notificacion_db,
    obtener_notificaciones_db,
    contar_no_leidas_db,
    marcar_leida_db,
    marcar_todas_leidas_db,
)
from src.utils.security import get_current_user

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


class NotificacionCreate(BaseModel):
    titulo: str
    mensaje: str
    tipo: Optional[str] = "info"
    enlace: Optional[str] = None
    id_usuario: Optional[int] = None
    rol_destino: Optional[int] = None


class MarcarTodasRequest(BaseModel):
    id_usuario: Optional[int] = None
    id_rol: Optional[int] = None


@router.get("", status_code=status.HTTP_200_OK)
def listar_notificaciones(
    id_usuario: Optional[int] = Query(None, description="ID del usuario logueado"),
    id_rol: Optional[int] = Query(None, description="ID del rol del usuario logueado"),
    limit: int = Query(50, ge=1, le=200, description="Cantidad máxima de notificaciones a retornar"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene las notificaciones para un usuario o rol, junto con el conteo de no leídas.
    """
    user_id = id_usuario or current_user.get("id")
    rol_id = id_rol or current_user.get("id_rol")
    notificaciones = obtener_notificaciones_db(id_usuario=user_id, id_rol=rol_id, limit=limit)
    no_leidas = contar_no_leidas_db(id_usuario=user_id, id_rol=rol_id)
    return {
        "estado": "OK",
        "no_leidas": no_leidas,
        "notificaciones": notificaciones,
    }


@router.patch("/{id_notificacion}/leer", status_code=status.HTTP_200_OK)
def marcar_como_leida(id_notificacion: int, current_user: dict = Depends(get_current_user)):
    """
    Marca una notificación específica como leída.
    """
    exito = marcar_leida_db(id_notificacion)
    if not exito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La notificación no fue encontrada o ya estaba leída.",
        )
    return {
        "estado": "OK",
        "mensaje": "Notificación marcada como leída.",
    }


@router.patch("/marcar-todas-leidas", status_code=status.HTTP_200_OK)
def marcar_todas_como_leidas(payload: MarcarTodasRequest, current_user: dict = Depends(get_current_user)):
    """
    Marca todas las notificaciones pendientes del usuario o su rol como leídas.
    """
    user_id = payload.id_usuario or current_user.get("id")
    rol_id = payload.id_rol or current_user.get("id_rol")
    marcar_todas_leidas_db(id_usuario=user_id, id_rol=rol_id)
    return {
        "estado": "OK",
        "mensaje": "Todas las notificaciones fueron marcadas como leídas.",
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def crear_notificacion(payload: NotificacionCreate, current_user: dict = Depends(get_current_user)):
    """
    Crea una nueva notificación manualmente.
    """
    notif_id = crear_notificacion_db(
        titulo=payload.titulo,
        mensaje=payload.mensaje,
        tipo=payload.tipo or "info",
        enlace=payload.enlace,
        id_usuario=payload.id_usuario or current_user.get("id"),
        rol_destino=payload.rol_destino,
    )
    if not notif_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo registrar la notificación.",
        )
    return {
        "estado": "OK",
        "id": notif_id,
        "mensaje": "Notificación creada con éxito.",
    }
