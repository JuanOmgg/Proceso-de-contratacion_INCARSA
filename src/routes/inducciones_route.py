from fastapi import APIRouter, HTTPException, status, Query, Depends
from src.schemas.inducciones_schema import InduccionUpdate
from src.utils.security import get_current_user
from src.services.inducciones import (
    OBTENER_INDUCCION_PERSONA,
    ACTUALIZAR_INDUCCION,
    LISTAR_TODAS_INDUCCIONES
)

router = APIRouter(prefix="/inducciones", tags=["Inducciones"])


def _validar_rol_induccion(current_user: dict):
    rol = str(current_user.get("rol") or current_user.get("nombre_rol") or "").strip().upper()
    id_rol = int(current_user.get("id_rol") or 0)
    roles_permitidos = ["GESCO", "SCR", "ADMINISTRADOR", "ADMIN", "SUPERADMIN", "SST", "GESTION DOCUMENTAL"]
    if id_rol in [1, 2, 4, 5, 6, 7, 8] or any(r in rol for r in roles_permitidos):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para consultar o modificar vigencias de inducción."
    )


@router.get("/getAll", status_code=status.HTTP_200_OK)
@router.get("/getall", status_code=status.HTTP_200_OK)
@router.get("", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK, include_in_schema=False)
def GET_ALL_inducciones_endpoint(current_user: dict = Depends(get_current_user)):
    """
    Lista el estado de inducción de todas las personas registradas en el sistema.
    """
    _validar_rol_induccion(current_user)
    resultado = LISTAR_TODAS_INDUCCIONES()
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al listar inducciones.")
        )
    return resultado.get("datos", [])


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


from database import GET_conexion


def _obtener_nombre_auditor_gesco(current_user: dict) -> str:
    """
    Obtiene el nombre real del usuario de GESCO/sistema que realiza la renovación.
    Consulta en la tabla usuarios por su ID si no está completo en el token.
    """
    user_id = current_user.get("sub") or current_user.get("id")
    if user_id:
        try:
            with GET_conexion() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        "SELECT nombres, apellidos, correo FROM usuarios WHERE id = %s",
                        (user_id,)
                    )
                    u = cursor.fetchone()
                    if u:
                        nombre_completo = f"{u.get('nombres') or ''} {u.get('apellidos') or ''}".strip()
                        if nombre_completo:
                            return nombre_completo
                        if u.get("correo"):
                            return u["correo"]
        except Exception:
            pass

    # Fallback si no se encontró en DB
    nombre_token = f"{current_user.get('nombre') or current_user.get('nombres') or ''} {current_user.get('apellido') or current_user.get('apellidos') or ''}".strip()
    return nombre_token or current_user.get("correo") or "Auditor GESCO"


@router.patch("/persona/{persona_id}", status_code=status.HTTP_200_OK)
def PATCH_induccion_persona_endpoint(
    persona_id: int,
    payload: InduccionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza la inducción o renueva su vigencia a 1 año.
    Siempre asigna como auditor responsable al usuario de GESCO en sesión que renueva.
    """
    _validar_rol_induccion(current_user)
    auditor_responsable = _obtener_nombre_auditor_gesco(current_user)
    payload.responsable = auditor_responsable
    resultado = ACTUALIZAR_INDUCCION(persona_id, payload, responsable_defecto=auditor_responsable)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al actualizar la inducción.")
        )
    return {"exito": True, "mensaje": resultado["mensaje"], "auditor": auditor_responsable}


@router.post("/persona/{persona_id}/renovar", status_code=status.HTTP_200_OK)
def POST_renovar_induccion_endpoint(
    persona_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Renueva inmediatamente la inducción a 1 año desde hoy.
    Siempre asigna como auditor responsable al usuario de GESCO en sesión que renueva.
    """
    _validar_rol_induccion(current_user)
    auditor_responsable = _obtener_nombre_auditor_gesco(current_user)
    resultado = ACTUALIZAR_INDUCCION(persona_id, InduccionUpdate(responsable=auditor_responsable), responsable_defecto=auditor_responsable)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al renovar la inducción.")
        )
    return {"exito": True, "mensaje": "Inducción renovada exitosamente (+1 año de vigencia).", "auditor": auditor_responsable}

