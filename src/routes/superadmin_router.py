from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Optional, Any
from src.schemas.superadmin_schema import MantenimientoInput, PermisosRolInput

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

# -----------------------------------------------------------------------------
# VISTA HTML: Panel de Control SuperAdmin & Previsualización 503
# -----------------------------------------------------------------------------
@router.get("/superadmin", response_class=HTMLResponse, summary="Vista principal del Panel SuperAdmin")
def superadmin_panel_view(request: Request):
    return templates.TemplateResponse(name="superadmin-panel.html", request=request)

@router.get("/superadmin/previsualizar-503", response_class=HTMLResponse, summary="Previsualización de Pantalla 503")
def previsualizar_503(request: Request):
    from main import MODULO_NOMBRES
    mantenimiento = GET_mantenimiento_status()
    tipo = mantenimiento.get("tipo", "general")
    modulos = mantenimiento.get("modulos") or []
    
    nombre_mod = None
    if tipo == "modulos" and modulos:
        nombres = [MODULO_NOMBRES.get(m, m.replace("_", " ").title()) for m in modulos]
        nombre_mod = ", ".join(nombres[:3])
        if len(nombres) > 3:
            nombre_mod += f" (+{len(nombres) - 3} más)"

    return templates.TemplateResponse(
        name="errors/error-503.html",
        request=request,
        status_code=200,
        context={
            "mensaje": mantenimiento.get("mensaje"),
            "tiempo": mantenimiento.get("tiempo"),
            "tipo_mantenimiento": tipo,
            "modulo_afectado": modulos[0] if modulos else None,
            "nombre_modulo_afectado": nombre_mod,
            "temporizador_fin": mantenimiento.get("temporizador_fin"),
            "temporizador_minutos": mantenimiento.get("temporizador_minutos") or 30
        }
    )

@router.get("/superadmin/previsualizar-403", response_class=HTMLResponse, summary="Previsualización de Pantalla 403")
def previsualizar_403(request: Request):
    """Previsualiza la pantalla de error 403 (Acceso no autorizado / Forbidden)."""
    return templates.TemplateResponse(
        name="errors/error-403.html",
        request=request,
        status_code=200
    )

@router.get("/superadmin/previsualizar-404", response_class=HTMLResponse, summary="Previsualización de Pantalla 404")
def previsualizar_404(request: Request):
    """Previsualiza la pantalla de error 404 (Página no encontrada / Not Found)."""
    return templates.TemplateResponse(
        name="errors/error-404.html",
        request=request,
        status_code=200
    )

@router.get("/superadmin/previsualizar-500", response_class=HTMLResponse, summary="Previsualización de Pantalla 500")
def previsualizar_500(request: Request):
    """Previsualiza la pantalla de error 500 (Error interno del servidor)."""
    return templates.TemplateResponse(
        name="errors/error-500.html",
        request=request,
        status_code=200
    )

# -----------------------------------------------------------------------------
# API: Gestión de Modo Mantenimiento (HTTP 503)
# -----------------------------------------------------------------------------
@router.get("/api/v1/superadmin/mantenimiento", status_code=status.HTTP_200_OK)
@router.get("/api/v1/sistema/mantenimiento", status_code=status.HTTP_200_OK)
def get_mantenimiento():
    """Consulta el estado del modo mantenimiento (general, por módulos y cronómetro)."""
    return {
        "exito": True,
        **GET_mantenimiento_status()
    }

@router.post("/api/v1/superadmin/mantenimiento", status_code=status.HTTP_200_OK)
def set_mantenimiento(payload: MantenimientoInput, current_user: dict = Depends(require_role(["SUPERADMIN"]))):
    """Activa o desactiva el modo mantenimiento (Exclusivo SuperAdmin)."""
    nuevo_estado = SET_mantenimiento_status(
        activo=payload.activo,
        tipo=payload.tipo,
        modulos=payload.modulos,
        mensaje=payload.mensaje,
        tiempo=payload.tiempo,
        temporizador_minutos=payload.temporizador_minutos,
        temporizador_fin=payload.temporizador_fin
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
