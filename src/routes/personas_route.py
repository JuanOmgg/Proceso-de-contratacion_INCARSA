from fastapi import APIRouter, HTTPException, status
from src.schemas.personas_schema import PersonInput
from src.loaders.personas_loader import GET_ALL_person_db
from src.services.personas import CREATE_person

router = APIRouter(prefix="/personas", tags=["Personas"])

@router.post("/create", status_code=status.HTTP_201_CREATED)
def CREATE_person_rt(payload: PersonInput):

    resultado = CREATE_person(payload)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje"),
        )

    return resultado

@router.get("/getAll", status_code=status.HTTP_200_OK)
@router.get("/getall", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK)
@router.get("", status_code=status.HTTP_200_OK, include_in_schema=False)
def GET_ALL_person_rt():

    print("🔍 [GETALL] Consultando todas las personas en la base de datos...")

    resultado = GET_ALL_person_db()

    if not resultado.get("exito", True):
        error_msg = resultado.get("mensaje")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= resultado.get("mensaje", "Error al obtener personas.")
        )

    return resultado
