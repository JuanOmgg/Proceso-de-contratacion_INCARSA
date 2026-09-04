from fastapi import APIRouter, HTTPException, status
from src.loaders.roles_loader import GET_rol_by_id, GETALL_roles

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/getAll", status_code=status.HTTP_200_OK)
@router.get("/getall", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK)
@router.get("", status_code=status.HTTP_200_OK, include_in_schema=False)
def GET_ALL_roles_rt():

    print("[ROLES] Buscando todos los roles en la base de datos...")
    roles = GETALL_roles()

    if roles is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar los roles en la base de datos.",
        )

    print(f"[ROLES] {len(roles)} rol(es) recuperado(s) con exito.")
    return {"exito": True, "data": roles}


@router.get("/{id_rol}", status_code=status.HTTP_200_OK)
def GET_rol_rt(id_rol: int):

    print(f"[ROLES] Buscando rol con ID #{id_rol} en la base de datos...")
    resultado = GET_rol_by_id(id_rol)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje"),
        )

    print(f"[ROLES] Rol #{id_rol} recuperado con exito.")
    return resultado
