import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status

from src.schemas.vehiculo_schema import VehiculoInput, VehiculoUpdate
from src.services.vehiculo import (
    CREATE_vehiculo as service_create_vehiculo,
    GET_ALL_vehiculos as service_get_all_vehiculos,
    GET_vehiculo_by_id as service_get_vehiculo_by_id,
    UPDATE_vehiculo as service_update_vehiculo,
    DELETE_vehiculo as service_delete_vehiculo,
    AGREGAR_documento_vehiculo as service_agregar_documento,
)

router = APIRouter(prefix="/api/v1/vehiculos", tags=["Vehículos"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def CREATE_vehiculo_endpoint(payload: VehiculoInput):
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
def GET_ALL_vehiculos_endpoint():
    print("🔍 [GET] Consultando lista de vehículos...")
    resultado = service_get_all_vehiculos()

    if not resultado.get("exito", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al consultar los vehículos."),
        )

    return resultado.get("datos", [])


@router.get("/{vehiculo_id}", status_code=status.HTTP_200_OK)
def GET_vehiculo_endpoint(vehiculo_id: int):
    print(f"🔍 [GET] Consultando vehículo #{vehiculo_id}...")
    resultado = service_get_vehiculo_by_id(vehiculo_id)

    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", f"Vehículo #{vehiculo_id} no encontrado."),
        )

    return resultado.get("datos")


@router.patch("/{vehiculo_id}", status_code=status.HTTP_200_OK)
def UPDATE_vehiculo_endpoint(vehiculo_id: int, payload: VehiculoUpdate):
    print(f"📝 [PATCH] Actualizando vehículo #{vehiculo_id}...")
    resultado = service_update_vehiculo(vehiculo_id, payload)

    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al actualizar el vehículo."),
        )

    return {
        "estado": "success",
        "mensaje": resultado.get("mensaje"),
    }


@router.delete("/{vehiculo_id}", status_code=status.HTTP_200_OK)
def DELETE_vehiculo_endpoint(vehiculo_id: int):
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
):
    # 1. Verificar si el vehículo existe
    vehiculo = service_get_vehiculo_by_id(vehiculo_id)
    if not vehiculo.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehículo #{vehiculo_id} no existe.",
        )

    nombre_original = file.filename or "documento.pdf"
    extension = (
        nombre_original.split(".")[-1].lower()
        if "." in nombre_original
        else "pdf"
    )

    formatos_permitidos = ["pdf", "png", "jpg", "jpeg"]
    if extension not in formatos_permitidos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato '.{extension}' no permitido. Solo se aceptan PDF, PNG, JPG o JPEG.",
        )

    # 2. Guardar archivo físico en uploads/documentos/vehiculos
    nombre_unico = f"{uuid.uuid4().hex}.{extension}"
    carpeta_destino = os.path.join("uploads", "documentos", "vehiculos")
    os.makedirs(carpeta_destino, exist_ok=True)
    ruta_fisica = os.path.join(carpeta_destino, nombre_unico)

    try:
        with open(ruta_fisica, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Registrar en BD en tabla documentos_vehiculo
        resultado_db = service_agregar_documento(
            vehiculo_id=vehiculo_id,
            tipo_doc=str(tipo_documento).strip().lower(),
            nom_documento=nombre_unico,
        )

        if not resultado_db.get("exito"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=resultado_db.get("mensaje"),
            )

        url_acceso = f"/uploads/documentos/vehiculos/{nombre_unico}"
        return {
            "exito": True,
            "mensaje": f"Documento '{tipo_documento}' guardado exitosamente para el vehículo #{vehiculo_id}.",
            "id_documento": resultado_db.get("id"),
            "nombre_archivo": nombre_unico,
            "nombre_original": nombre_original,
            "url_documento": url_acceso,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al subir documento de vehículo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al guardar archivo: {e}",
        )
