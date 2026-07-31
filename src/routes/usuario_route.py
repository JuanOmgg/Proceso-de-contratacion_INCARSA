from fastapi import APIRouter, HttpException, status
from src.schemas.usuario_schema import UsuarioCreate, UsuarioResponse
from src.loaders.usuario import CREATE_user, READ_user, DELETE_user

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@app_router := router 

@router.delete("/{id_user}")
def Delete_user(id_user: int) -> UsuarioResponse:
   
    resultado = DELETE_user(id_user)

    if resultado.get("status") == "error" or not resultado.get("exito", True):
        raise HttpException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=resultado["mensaje"]
        )

    return resultado