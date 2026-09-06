from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import Optional, List
from pydantic import BaseModel

from src.loaders.notificacion_loader import (
    crear_notificacion_db,
    obtener_notificaciones_db,
    contar_no_leidas_db,
    marcar_leida_db,
    marcar_todas_leidas_db,
    marcar_leida_por_solicitud_db,
    emitir_difusion_superadmin_db,
    obtener_historial_difusion_db,
)
from src.utils.security import get_current_user, require_role

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


class MarcarPorSolicitudRequest(BaseModel):
    id_o_codigo: str
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


@router.patch("/marcar-leida-solicitud", status_code=status.HTTP_200_OK)
def marcar_leida_por_solicitud(payload: MarcarPorSolicitudRequest, current_user: dict = Depends(get_current_user)):
    """
    Marca como leídas las notificaciones asociadas a una solicitud cuando el usuario entra a revisarla.
    """
    user_id = payload.id_usuario or current_user.get("id")
    rol_id = payload.id_rol or current_user.get("id_rol")
    afectadas = marcar_leida_por_solicitud_db(
        id_o_codigo=payload.id_o_codigo,
        id_usuario=user_id,
        id_rol=rol_id
    )
    return {
        "estado": "OK",
        "mensaje": f"{afectadas} notificación(es) marcada(s) como leída(s).",
        "afectadas": afectadas
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


class DifusionSuperadminRequest(BaseModel):
    titulo: str
    mensaje: str
    tipo: Optional[str] = "info"
    enlace: Optional[str] = None
    destinatario_tipo: str = "rol"  # "rol", "usuarios", "todos"
    roles_ids: Optional[List[int]] = None
    usuarios_ids: Optional[List[int]] = None


@router.post("/difusion", status_code=status.HTTP_201_CREATED)
def emitir_difusion(
    payload: DifusionSuperadminRequest,
    current_user: dict = Depends(require_role(["SUPERADMIN"]))
):
    """
    Emite comunicados masivos o personalizados hacia roles o usuarios específicos (Exclusivo SuperAdmin).
    """
    res = emitir_difusion_superadmin_db(
        titulo=payload.titulo,
        mensaje=payload.mensaje,
        tipo=payload.tipo or "info",
        enlace=payload.enlace,
        destinatario_tipo=payload.destinatario_tipo,
        roles_ids=payload.roles_ids,
        usuarios_ids=payload.usuarios_ids,
    )
    if not res.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("mensaje", "No fue posible emitir el comunicado.")
        )
    return res


@router.get("/historial-difusion", status_code=status.HTTP_200_OK)
def obtener_historial_difusion(
    limit: int = Query(25, ge=1, le=100),
    current_user: dict = Depends(require_role(["SUPERADMIN"]))
):
    """
    Retorna el registro histórico de notificaciones y comunicados emitidos en la plataforma (Exclusivo SuperAdmin).
    """
    historial = obtener_historial_difusion_db(limit=limit)
    return {
        "estado": "OK",
        "total": len(historial),
        "historial": historial,
    }

