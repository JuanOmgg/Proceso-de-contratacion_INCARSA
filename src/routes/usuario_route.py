from src.loaders.usuario_loader import GET_BY_ROL_with_count_db
from fastapi import APIRouter, HTTPException, status, Depends
from src.schemas.usuario_schema import UsuarioInput, UsuarioResponse, UpdateUsuarioInput, UsuarioData
from src.services.usuario import CREATE_user, READ_user, DELETE_user
from src.loaders.usuario_loader import DELETE_user_db, UPDATE_user_db, GET_ALL_users_db, GET_BY_ROL_with_count_db
from src.transformers.usuario_transformer import TRANSFORM_USER
from src.utils.security import get_current_user, require_role
from typing import List, Dict, Any

from src.loaders.roles_loader import GET_rol_by_id

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("/post", status_code=status.HTTP_201_CREATED)
def CREATE_user_rt(payload: UsuarioInput, current_user: dict = Depends(require_role(["Administrador"]))):

    # Regla: Solo SUPERADMIN puede crear usuarios con rol ADMINISTRADOR o SUPERADMIN
    rol_target = GET_rol_by_id(payload.id_rol)
    nombre_rol_target = rol_target.get("data", {}).get("nombre_rol", "").strip().upper() if rol_target.get("exito") else ""
    mi_rol = current_user.get("rol", "").strip().upper()

    if nombre_rol_target in ("ADMINISTRADOR", "SUPERADMIN") and mi_rol != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un usuario con rol SUPERADMIN puede crear usuarios con el rol ADMINISTRADOR.",
        )

    resultado = CREATE_user(payload)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje"),
        )

    return resultado

@router.get("/usuarios/conteo-por-rol", response_model=List[Dict[str, Any]])
def get_conteo_roles(current_user: dict = Depends(get_current_user)):
    try:
        conteos = GET_BY_ROL_with_count_db() 
        return conteos 
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener métricas de roles: {str(e)}"
        )

@router.get("/getAll", status_code=status.HTTP_200_OK, response_model=List[UsuarioData])
@router.get("/getall", status_code=status.HTTP_200_OK, response_model=List[UsuarioData])
@router.get("/", status_code=status.HTTP_200_OK, response_model=List[UsuarioData])
@router.get("", status_code=status.HTTP_200_OK, response_model=List[UsuarioData], include_in_schema=False)
def GET_ALL_users_rt(current_user: dict = Depends(get_current_user)):
    
    print("[USUARIOS] Buscando todos los usuarios en la base de datos...")
    resultado = GET_ALL_users_db()

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al obtener los usuarios."),
        )
    
    print("[USUARIOS] Datos de los usuarios recuperados con exito.")
    return resultado.get("datos", resultado.get("datos_user", []))

@router.get("/{id_user}", status_code=status.HTTP_200_OK, response_model=UsuarioData)   
def GET_user_rt(id_user: str, current_user: dict = Depends(get_current_user)):

    print(f"[USUARIOS] Buscando usuario '{id_user}' en la base de datos...")
    resultado = READ_user(id_user)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", "Usuario no encontrado"),
        )
    
    print(f"[USUARIOS] Datos del usuario '{id_user}' recuperados con exito.")
    return resultado["data"]


@router.patch("/{id_user}", status_code=status.HTTP_200_OK)
def UPDATE_user_rt(id_user: int, payload: UpdateUsuarioInput, current_user: dict = Depends(require_role(["Administrador"]))):

    print(f"[USUARIOS] Actualizando usuario con ID #{id_user} en la base de datos...")

    new_updates = payload.model_dump(exclude_unset=True)

    if not new_updates:
        print("[USUARIOS] No se enviaron campos validos en el body para actualizar.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar."
        )

    # Regla: Los administradores no pueden editar a otros administradores (exclusivo SUPERADMIN)
    usuario_existente = READ_user(id_user)
    if not usuario_existente.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=usuario_existente.get("mensaje", "Usuario no encontrado"),
        )

    usuario_data = usuario_existente.get("data", {})
    nombre_rol_actual = str(usuario_data.get("nombre_rol") or usuario_data.get("rol") or "").strip().upper()
    id_rol_actual = usuario_data.get("id_rol")
    mi_rol = current_user.get("rol", "").strip().upper()

    if (nombre_rol_actual in ("ADMINISTRADOR", "SUPERADMIN") or id_rol_actual in (1, 2)) and mi_rol != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un usuario con rol SUPERADMIN puede editar usuarios administradores.",
        )

    # Regla: Solo SUPERADMIN puede asignar el rol ADMINISTRADOR o SUPERADMIN
    if "id_rol" in new_updates:
        rol_target = GET_rol_by_id(new_updates["id_rol"])
        nombre_rol_target = rol_target.get("data", {}).get("nombre_rol", "").strip().upper() if rol_target.get("exito") else ""
        if nombre_rol_target in ("ADMINISTRADOR", "SUPERADMIN") and mi_rol != "SUPERADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo un usuario con rol SUPERADMIN puede asignar el rol ADMINISTRADOR.",
            )

    print(f"[USUARIOS] Aplicando cambios en MySQL para el usuario #{id_user}...")
    resultado = UPDATE_user_db(id_user, new_updates)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje"),
        )
    print(f"[USUARIOS] Usuario #{id_user} actualizado correctamente en la base de datos.")
    return resultado

@router.delete("/{id_user}")
def Delete_user(id_user: int, current_user: dict = Depends(require_role(["Administrador"]))):
   
    # Regla: Los administradores no pueden eliminar a otros administradores (exclusivo SUPERADMIN)
    usuario_existente = READ_user(id_user)
    if not usuario_existente.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=usuario_existente.get("mensaje", "Usuario no encontrado"),
        )

    usuario_data = usuario_existente.get("data", {})
    nombre_rol_actual = str(usuario_data.get("nombre_rol") or usuario_data.get("rol") or "").strip().upper()
    id_rol_actual = usuario_data.get("id_rol")
    mi_rol = current_user.get("rol", "").strip().upper()

    if (nombre_rol_actual in ("ADMINISTRADOR", "SUPERADMIN") or id_rol_actual in (1, 2)) and mi_rol != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un usuario con rol SUPERADMIN puede eliminar usuarios administradores.",
        )

    print(f"[DELETE] Eliminando usuario #{id_user} de la base de datos...")
    resultado = DELETE_user_db(id_user)

    if resultado.get("exito") == False or not resultado.get("exito", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=resultado["mensaje"]
        )

    print(f"[DELETE] Usuario #{id_user} eliminado correctamente de la base de datos.")
    return resultado