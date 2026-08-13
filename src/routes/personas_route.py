from fastapi import APIRouter, HTTPException, status
from src.schemas.personas_schema import PersonInput
from src.services.personas import CREATE_person

router = APIRouter(prefix="/personas", tags=["Personas"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def CREATE_person_rt(payload: PersonInput):
    resultado = CREATE_person(payload)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje"),
        )

    return resultado

