from fastapi import APIRouter, Depends, HTTPException, status
from src.utils.security import get_current_user, require_permission
from src.loaders.dispositivo_loader import GET_ALL_dispositivos_db

router = APIRouter(prefix="/api/v1/dispositivos", tags=["Dispositivos"])


@router.get("/", status_code=status.HTTP_200_OK)
@router.get("/getAll", status_code=status.HTTP_200_OK)
@router.get("/getall", status_code=status.HTTP_200_OK)
def GET_ALL_dispositivos_endpoint(current_user: dict = Depends(require_permission("dispositivos", "ver"))):
    """
    Retorna la lista consolidada de dispositivos y equipos registrados en solicitudes.
    Acceso controlado mediante el módulo 'dispositivos' y permiso 'ver'.
    """
    try:
        datos = GET_ALL_dispositivos_db()
        return datos
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar dispositivos: {str(e)}"
        )
