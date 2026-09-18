from fastapi import APIRouter, HTTPException, status, Query, Depends
from src.schemas.inducciones_schema import InduccionUpdate
from src.utils.security import get_current_user
from src.services.inducciones import (
    OBTENER_INDUCCION_PERSONA,
    ACTUALIZAR_INDUCCION
)

router = APIRouter(prefix="/inducciones", tags=["Inducciones"])


def _validar_rol_induccion(current_user: dict):
    rol = str(current_user.get("rol") or current_user.get("nombre_rol") or "").strip().toUpperCase() if hasattr(str, 'toUpperCase') else str(current_user.get("rol") or current_user.get("nombre_rol") or "").strip().upper()
    id_rol = int(current_user.get("id_rol") or 0)
    roles_permitidos = ["GESCO", "SCR", "ADMINISTRADOR", "ADMIN", "SUPERADMIN"]
    if id_rol in [1, 2, 4, 8] or any(r in rol for r in roles_permitidos):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para consultar o modificar vigencias de inducción."
    )


@router.get("/persona/{persona_id}", status_code=status.HTTP_200_OK)
def GET_induccion_persona_endpoint(
    persona_id: int,
    auto_renovar: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene la vigencia y datos de inducción de una persona.
    Permitido para GESCO, SCR, Administrador y Superadmin.
    """
    _validar_rol_induccion(current_user)
    resultado = OBTENER_INDUCCION_PERSONA(persona_id, auto_renovar=auto_renovar)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", "No se encontró el registro de inducción.")
        )
    return resultado["datos"]


@router.patch("/persona/{persona_id}", status_code=status.HTTP_200_OK)
def PATCH_induccion_persona_endpoint(
    persona_id: int,
    payload: InduccionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza manualmente la inducción o renueva su vigencia a 1 año.
    Permitido para GESCO, SCR, Administrador y Superadmin.
    """
    _validar_rol_induccion(current_user)
    nombre_usuario = (
        f"{current_user.get('nombre') or current_user.get('nombres') or ''} {current_user.get('apellido') or current_user.get('apellidos') or ''}".strip()
        or current_user.get("usuario")
        or "Auditor GESCO"
    )
    resultado = ACTUALIZAR_INDUCCION(persona_id, payload, responsable_defecto=nombre_usuario)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al actualizar la inducción.")
        )
    return {"exito": True, "mensaje": resultado["mensaje"]}


@router.post("/persona/{persona_id}/renovar", status_code=status.HTTP_200_OK)
def POST_renovar_induccion_endpoint(
    persona_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Renueva inmediatamente la inducción a 1 año desde hoy.
    """
    _validar_rol_induccion(current_user)
    nombre_usuario = (
        f"{current_user.get('nombre') or current_user.get('nombres') or ''} {current_user.get('apellido') or current_user.get('apellidos') or ''}".strip()
        or current_user.get("usuario")
        or "Auditor GESCO"
    )
    resultado = ACTUALIZAR_INDUCCION(persona_id, InduccionUpdate(), responsable_defecto=nombre_usuario)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al renovar la inducción.")
        )
    return {"exito": True, "mensaje": "Inducción renovada exitosamente (+1 año de vigencia)."}
