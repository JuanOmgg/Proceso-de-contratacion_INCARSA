from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from src.utils.security import get_current_user, require_role
from src.loaders.superadmin_loader import (
    GET_mantenimiento_status,
    SET_mantenimiento_status,
    GET_matriz_permisos_db,
    UPDATE_permisos_rol_db,
    GET_permisos_rol_db,
)

router = APIRouter(tags=["SuperAdmin"])
templates = Jinja2Templates(directory="templates")

# Schemas para requests
class MantenimientoInput(BaseModel):
    activo: bool
    mensaje: Optional[str] = None
    tiempo: Optional[str] = None

class PermisosRolInput(BaseModel):
    permisos: Optional[List[Dict[str, Any]]] = None
    modulos: Optional[Dict[str, bool]] = None
    acciones: Optional[Dict[str, bool]] = None

# -----------------------------------------------------------------------------
# VISTA HTML: Panel de Control SuperAdmin
# -----------------------------------------------------------------------------
@router.get("/superadmin", response_class=HTMLResponse, summary="Vista principal del Panel SuperAdmin")
def superadmin_panel_view(request: Request):
    return templates.TemplateResponse(name="superadmin-panel.html", request=request)

# -----------------------------------------------------------------------------
# API: Gestión de Modo Mantenimiento (HTTP 503)
# -----------------------------------------------------------------------------
@router.get("/api/v1/superadmin/mantenimiento", status_code=status.HTTP_200_OK)
def get_mantenimiento():
    """Consulta el estado del modo mantenimiento (público o interno)."""
    return {
        "exito": True,
        **GET_mantenimiento_status()
    }

@router.post("/api/v1/superadmin/mantenimiento", status_code=status.HTTP_200_OK)
def set_mantenimiento(payload: MantenimientoInput, current_user: dict = Depends(require_role(["SUPERADMIN"]))):
    """Activa o desactiva el modo mantenimiento (Exclusivo SuperAdmin)."""
    nuevo_estado = SET_mantenimiento_status(
        activo=payload.activo,
        mensaje=payload.mensaje,
        tiempo=payload.tiempo
    )
    return {
        "exito": True,
        "mensaje": "Estado de mantenimiento actualizado exitosamente.",
        **nuevo_estado
    }

# -----------------------------------------------------------------------------
# API: Gestión de Matriz de Permisos por Rol
# -----------------------------------------------------------------------------
@router.get("/api/v1/superadmin/permisos", status_code=status.HTTP_200_OK)
def get_permisos_matriz(current_user: dict = Depends(require_role(["SUPERADMIN"]))):
    """Retorna la matriz completa de roles y permisos (Exclusivo SuperAdmin)."""
    return GET_matriz_permisos_db()

@router.put("/api/v1/superadmin/permisos/{id_rol}", status_code=status.HTTP_200_OK)
def update_permisos_rol(id_rol: int, payload: PermisosRolInput, current_user: dict = Depends(require_role(["SUPERADMIN"]))):
    """Actualiza la configuración de módulos y acciones para un rol (Exclusivo SuperAdmin)."""
    try:
        exito = UPDATE_permisos_rol_db(
            id_rol=id_rol,
            permisos=payload.permisos,
            modulos=payload.modulos,
            acciones=payload.acciones
        )
        return {
            "exito": exito,
            "mensaje": "Permisos actualizados correctamente."
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

# -----------------------------------------------------------------------------
# API: Permisos del usuario autenticado (Para cualquier rol)
# -----------------------------------------------------------------------------
@router.get("/api/v1/roles/mis-permisos", status_code=status.HTTP_200_OK)
def get_mis_permisos(current_user: dict = Depends(get_current_user)):
    """Retorna los permisos asignados al rol del usuario en sesión."""
    id_rol = current_user.get("id_rol")
    if not id_rol:
        return {"superadmin": False, "modulos": {}, "acciones": {}}
    return GET_permisos_rol_db(int(id_rol))
