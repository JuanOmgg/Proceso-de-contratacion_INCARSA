from fastapi import APIRouter, HTTPException, status
from src.schemas.emp_contratista_schema import EmpContratistaInput, UpdateEmpContratistainput
from src.services.emp_contratista import CREATE_emp_contratista
from src.transformers.empContr_transformer import TRANSFORM_EMPCONTRATISTA
from src.loaders.emp_contratista_loader import (
    GET_empCont_db, 
    UPDATE_empCont_db, 
    DELETE_empCont_db, 
    GET_ALL_empCont_db
    )

router = APIRouter(prefix = "/emp_contratista", tags = ["Empresas Contratistas"])

@router.post("", status_code=status.HTTP_201_CREATED)
def CREATE_empContratista_rt(payload: EmpContratistaInput):

    resultado = CREATE_emp_contratista(payload)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje"),
        )

    return resultado

@router.get("/{empcont_id}", status_code=status.HTTP_200_OK)
def GET_empContratista_rt(empcont_id: int):

    print(f"🔍 [GET] Buscando empresa contratista con ID #{empcont_id} en la base de datos")
    resultado = GET_empCont_db(empcont_id)

    if not resultado.get("exito", False):
        raise   HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje"),
        )
    
    print(f"📦 [GET] Datos de la empresa #{empcont_id} recuperados con éxito.")
    return resultado

@router.get("/", status_code=status.HTTP_200_OK)
def GET_ALL_empCont_rt():

    print("🔍 [GET] Consultando todas las empresas contratistas en la base de datos...")

    resultado = GET_ALL_empCont_db()

    if not resultado.get("exito", True):
        error_msg = resultado.get("mensaje", "Error desconocido en la consulta de empresas contratistas.")
        print(f"❌ Error interno en GET_ALL_empCont_db: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al obtener las emrpesas contratistas.")
        )

    return resultado.get("data", resultado)
@router.patch("/{empcont_id}", status_code=status.HTTP_200_OK)
def UPDATE_empContratista_rt(empcont_id: int, payload: UpdateEmpContratistainput):

    print(f"🔄 [PATCH] Actualizando empresa contratista con ID #{empcont_id} en la base de datos... ")
    data_raw = payload.model_dump(exclude_unset=True) 

    data_updates = TRANSFORM_EMPCONTRATISTA(data_raw)

    if not data_updates:
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="❌❌ No se proporcionaron datos para actualizar la empresa contratista ❌❌"
        )
    
    print(f"⚙️ [LOADER] Aplicando cambios en MySQL para la empresa #{empcont_id}...")
    resultado = UPDATE_empCont_db(empcont_id, data_updates)

    if not resultado.get("exito", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje"),
        )
    print(f"✅ [PUT] Empresa contratista con ID #{empcont_id} actualizada con éxito.")
    return resultado

@router.delete("/{empcont_id}", status_code=status.HTTP_200_OK)
def DELETE_empContratista_rt(empcont_id: int):

    print(f"🗑️ [DELETE] Eliminando empresa contratista con ID #{empcont_id} de la base de datos...")
    resultado = DELETE_empCont_db(empcont_id)

    if resultado.get("exito", False) is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje"),
        )

    return resultado