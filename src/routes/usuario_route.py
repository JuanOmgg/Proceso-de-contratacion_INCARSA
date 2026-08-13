from src.loaders.usuario_loader import GET_BY_ROL_with_count_db
from fastapi import APIRouter, HTTPException, status
from src.schemas.usuario_schema import UsuarioInput, UsuarioResponse, UpdateUsuarioInput, UsuarioData
from src.services.usuario import CREATE_user, READ_user, DELETE_user
from src.loaders.usuario_loader import DELETE_user_db, UPDATE_user_db, GET_ALL_users_db, GET_BY_ROL_with_count_db
from src.transformers.usuario_transformer import TRANSFORM_USER
from typing import List, Dict, Any

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def CREATE_user_rt(payload: UsuarioInput):

    resultado = CREATE_user(payload)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje"),
        )

    return resultado

@router.get("/usuarios/conteo-por-rol", response_model=List[Dict[str, Any]])
def get_conteo_roles():
    try:
        
        conteos = GET_BY_ROL_with_count_db() 
        
        return conteos 

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener métricas de roles: {str(e)}"
        )

@router.get("/{id_user}", status_code=status.HTTP_200_OK, response_model=UsuarioData)   
def GET_user_rt(id_user:int):

    print(f"🔍 [GET] Buscando usuario con ID #{id_user} en la base de datos... ")
    resultado = READ_user(id_user)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje"),
        )
    
    print(f"📦 [GET] Datos del usuario #{id_user} recuperados con éxito.")
    return resultado

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[UsuarioData])
def GET_ALL_users_rt():
    
    print(f"🔍 [GET_ALL] Buscando todos los usuarios en la base de datos... ")
    resultado = GET_ALL_users_db()

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje"),
        )
    
    print(f"📦 [GET_ALL] Datos de los usuarios recuperados con éxito.")
    return resultado["datos_user"]


@router.patch("/{id_user}", status_code=status.HTTP_200_OK)
def UPDATE_user_rt(id_user: int, payload: UpdateUsuarioInput):

    print(f"🔄 [PATCH] Actualizando usuario con ID #{id_user} en la base de datos... ")

    new_updates = payload.model_dump(exclude_unset=True)

    if not new_updates:
        print("⚠️ No se enviaron campos válidos en el body para actualizar.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar."
        )

    print(f"⚙️ [LOADER] Aplicando cambios en MySQL para el usuario #{id_user}...")
    resultado = UPDATE_user_db(id_user, new_updates)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje"),
        )
    print(f"✨ Usuario #{id_user} actualizado correctamente en la base de datos.")
    return resultado

@router.delete("/{id_user}")
def Delete_user(id_user: int):
   
    print(f"🗑️ [DELETE] Eliminando usuario #{id_user} de la base de datos...")
    resultado = DELETE_user_db(id_user)

    if resultado.get("exito") == False or not resultado.get("exito", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=resultado["mensaje"]
        )

    print(f"✅ Usuario #{id_user} eliminado correctamente de la base de datos.")
    return resultado