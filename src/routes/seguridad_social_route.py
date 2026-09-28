from fastapi import APIRouter, HTTPException, status, Query, Depends
from src.schemas.seguridad_social_schema import SeguridadSocialUpdate, HistorialSolicitudSSCreate
from src.utils.security import get_current_user
from src.services.seguridad_social import (
    OBTENER_SEGURIDAD_SOCIAL_PERSONA,
    ACTUALIZAR_SEGURIDAD_SOCIAL,
    REGISTRAR_HISTORIAL_SOLICITUD_SS,
    LISTAR_TODOS_SEGURIDAD_SOCIAL
)

router = APIRouter(prefix="/seguridad-social", tags=["Seguridad Social"])


def check_ss_permission(accion: str = "ver"):
    def dependency(current_user: dict = Depends(get_current_user)):
        user_rol = str(current_user.get("rol", "")).strip().lower()
        if user_rol in ("superadmin", "super admin", "super_admin"):
            return current_user
        # SST, Administrador y SCR tienen permiso por defecto
        if user_rol in ("sst", "administrador", "admin", "scr"):
            return current_user
        
        id_rol = current_user.get("id_rol")
        if id_rol:
            try:
                from src.loaders.superadmin_loader import GET_permisos_rol_db
                perm_data = GET_permisos_rol_db(int(id_rol))
                permisos = perm_data.get("permisos", {})
                if permisos.get("seguridad_social", {}).get(accion, False):
                    return current_user
            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes permisos suficientes para '{accion}' en el módulo de Seguridad Social."
        )
    return dependency


@router.get("/persona/{persona_id}", status_code=status.HTTP_200_OK)
def GET_seguridad_social_persona_endpoint(
    persona_id: int, 
    current_user: dict = Depends(check_ss_permission("ver"))
):
    """
    Obtiene los registros de seguridad social y el historial consolidado de una persona.
    """
    resultado = OBTENER_SEGURIDAD_SOCIAL_PERSONA(persona_id)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", "No se encontró el registro de seguridad social.")
        )
    return resultado["datos"]


@router.patch("/persona/{persona_id}", status_code=status.HTTP_200_OK)
def PATCH_seguridad_social_persona_endpoint(
    persona_id: int, 
    payload: SeguridadSocialUpdate,
    current_user: dict = Depends(check_ss_permission("editar"))
):
    """
    Actualiza la fecha de vigencia dictaminada por SST, anotaciones y responsable.
    """
    # El responsable SIEMPRE debe ser el usuario de SST en sesión que realiza el dictamen
    nombres = current_user.get("nombres") or current_user.get("nombre") or ""
    apellidos = current_user.get("apellidos") or current_user.get("apellido") or ""
    full = f"{nombres} {apellidos}".strip()
    payload.responsable = full or current_user.get("usuario") or payload.responsable or "SST"

    resultado = ACTUALIZAR_SEGURIDAD_SOCIAL(persona_id, payload)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al actualizar seguridad social.")
        )
    return {"exito": True, "mensaje": resultado["mensaje"]}


@router.post("/persona/{persona_id}/historial", status_code=status.HTTP_201_CREATED)
def POST_historial_solicitud_ss_endpoint(
    persona_id: int, 
    payload: HistorialSolicitudSSCreate,
    current_user: dict = Depends(check_ss_permission("crear"))
):
    """
    Registra una solicitud en el historial de seguridad social de la persona.
    """
    resultado = REGISTRAR_HISTORIAL_SOLICITUD_SS(persona_id, payload)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al registrar el historial en seguridad social.")
        )
    return {"exito": True, "mensaje": resultado["mensaje"]}


@router.get("/getAll", status_code=status.HTTP_200_OK)
@router.get("/getall", status_code=status.HTTP_200_OK)
@router.get("", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK, include_in_schema=False)
def GET_ALL_seguridad_social_endpoint(current_user: dict = Depends(check_ss_permission("ver"))):
    """
    Lista todos los registros de seguridad social de las personas con su estado de vigencia y total de solicitudes.
    """
    resultado = LISTAR_TODOS_SEGURIDAD_SOCIAL()
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al listar registros de seguridad social.")
        )
    return resultado.get("datos", [])
