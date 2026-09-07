import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status, Depends

from src.utils.file_manager import guardar_documento_seguro
from src.schemas.vehiculo_schema import VehiculoInput, VehiculoUpdate
from src.utils.security import get_current_user, require_permission
from src.services.vehiculo import (
    CREATE_vehiculo as service_create_vehiculo,
    GET_ALL_vehiculos as service_get_all_vehiculos,
    GET_vehiculo_by_id as service_get_vehiculo_by_id,
    UPDATE_vehiculo as service_update_vehiculo,
    DELETE_vehiculo as service_delete_vehiculo,
    AGREGAR_documento_vehiculo as service_agregar_documento,
    ELIMINAR_documento_vehiculo as service_eliminar_documento,
)

router = APIRouter(prefix="/api/v1/vehiculos", tags=["Vehículos"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def CREATE_vehiculo_endpoint(payload: VehiculoInput, current_user: dict = Depends(require_permission("vehiculos", "crear"))):
    print("🚗 [POST] Creando nuevo vehículo...")
    resultado = service_create_vehiculo(payload)

    if not resultado.get("exito", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al crear el vehículo."),
        )

    return resultado


@router.get("/getAll", status_code=status.HTTP_200_OK)
@router.get("/getall", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK)
@router.get("", status_code=status.HTTP_200_OK, include_in_schema=False)
def GET_ALL_vehiculos_endpoint(current_user: dict = Depends(get_current_user)):
    print("🔍 [GET] Consultando lista de vehículos...")
    resultado = service_get_all_vehiculos()

    if not resultado.get("exito", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al consultar los vehículos."),
        )

    return resultado.get("datos", [])


@router.get("/{vehiculo_id}", status_code=status.HTTP_200_OK)
def GET_vehiculo_endpoint(vehiculo_id: int, current_user: dict = Depends(get_current_user)):
    print(f"🔍 [GET] Consultando vehículo #{vehiculo_id}...")
    resultado = service_get_vehiculo_by_id(vehiculo_id)

    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", f"Vehículo #{vehiculo_id} no encontrado."),
        )

    return resultado.get("datos")


@router.patch("/{vehiculo_id}", status_code=status.HTTP_200_OK)
@router.put("/{vehiculo_id}", status_code=status.HTTP_200_OK)
def UPDATE_vehiculo_endpoint(vehiculo_id: int, payload: VehiculoUpdate, current_user: dict = Depends(require_permission("vehiculos", "editar"))):
    print(f"📝 [PATCH/PUT] Actualizando vehículo #{vehiculo_id}...")
    resultado = service_update_vehiculo(vehiculo_id, payload)

    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al actualizar el vehículo."),
        )

    return {
        "exito": True,
        "estado": "success",
        "mensaje": resultado.get("mensaje"),
        "datos": resultado.get("data"),
        "data": resultado.get("data"),
    }


@router.delete("/{vehiculo_id}", status_code=status.HTTP_200_OK)
def DELETE_vehiculo_endpoint(vehiculo_id: int, current_user: dict = Depends(require_permission("vehiculos", "eliminar"))):
    print(f"🗑️ [DELETE] Eliminando vehículo #{vehiculo_id}...")
    resultado = service_delete_vehiculo(vehiculo_id)

    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", "Error al eliminar el vehículo."),
        )

    return {
        "estado": "success",
        "mensaje": resultado.get("mensaje"),
    }


@router.post("/{vehiculo_id}/documentos", status_code=status.HTTP_201_CREATED)
async def SUBIR_documento_vehiculo_endpoint(
    vehiculo_id: int,
    file: UploadFile = File(...),
    tipo_documento: str = Form("soat"),
    current_user: dict = Depends(get_current_user),
):
    # 1. Verificar si el vehículo existe
    vehiculo = service_get_vehiculo_by_id(vehiculo_id)
    if not vehiculo.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehículo #{vehiculo_id} no existe.",
        )

    # 2. Guardar archivo físico de forma segura (valida extensión, tamaño máx y Magic Bytes)
    archivo_guardado = await guardar_documento_seguro(file, subcarpeta="vehiculos")

    try:
        # 3. Registrar en BD en tabla documentos_vehiculo
        resultado_db = service_agregar_documento(
            vehiculo_id=vehiculo_id,
            tipo_doc=str(tipo_documento).strip().lower(),
            nom_documento=archivo_guardado["nombre_archivo"],
        )

        if not resultado_db.get("exito"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=resultado_db.get("mensaje"),
            )

        print(f"🚗 [DOC VEHÍCULO] '{archivo_guardado['nombre_original']}' guardado para vehículo #{vehiculo_id}")

        return {
            "exito": True,
            "mensaje": f"Documento '{tipo_documento}' guardado exitosamente para el vehículo #{vehiculo_id}.",
            "id_documento": resultado_db.get("id"),
            "nombre_archivo": archivo_guardado["nombre_archivo"],
            "nombre_original": archivo_guardado["nombre_original"],
            "url_documento": archivo_guardado["url_documento"],
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al registrar documento de vehículo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al asociar el documento al vehículo: {e}"
        )


@router.delete("/{vehiculo_id}/documentos/{documento_id}", status_code=status.HTTP_200_OK)
@router.delete("/documentos/{documento_id}", status_code=status.HTTP_200_OK)
def DELETE_documento_vehiculo_endpoint(
    documento_id: int,
    vehiculo_id: Optional[int] = None,
    current_user: dict = Depends(require_permission("vehiculos", "editar")),
):
    print(f"🗑️ [DELETE DOC VEHÍCULO] Eliminando documento #{documento_id}...")
    resultado = service_eliminar_documento(documento_id, vehiculo_id)

    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", "Error al eliminar documento del vehículo."),
        )

    return {
        "exito": True,
        "mensaje": resultado.get("mensaje"),
    }

