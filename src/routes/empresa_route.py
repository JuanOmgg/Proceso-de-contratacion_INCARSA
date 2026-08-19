from fastapi import APIRouter, HTTPException, status
from src.loaders.empresa_loader import GET_empresas_con_plantas_bd

router = APIRouter(prefix="/api/v1/empresas", tags=["Empresas"])

@router.get("/", status_code=status.HTTP_200_OK)
def GET_empresas():
    """
    Retorna todas las empresas con sus plantas anidadas.
    Respuesta: [{ id, nombre, plantas: [{ id, nombre }, ...] }, ...]
    """
    print("🔍 [GET] Consultando empresas y plantas...")
    
    resultado = GET_empresas_con_plantas_bd()
    
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al obtener las empresas.")
        )
    
    return resultado.get("datos", [])
