import os
import shutil
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from src.loaders.solicitudes_loaders import (
    DELETE_solicitud_bd,
    GET_solicitud_bd,
    CREATE_solicitud_bd,
    UPDATE_solicitud_bd,
)
from src.schemas.solicitud_schema import SolicitudInput, UPDATE_Schema_Optionals
from src.transformers import transformar_solicitud, transformar_solicitud_patch

router = APIRouter(prefix="/api/v1/solicitudes", tags=["Solicitudes"])


MAPEO_SUBDIRECTORIOS = {
    "cedula": "cedulas",
    "doc_identidad": "cedulas",
    "identificacion": "cedulas",
    "arl": "arl",
    "examen": "examenes_medicos",
    "examenes": "examenes_medicos",
    "examenes_medicos": "examenes_medicos",
    "medico": "examenes_medicos",
    "otros": "otros",
    "otro": "otros",
    "actividad": "otros",
}


@router.post("/subir-documento/", status_code=status.HTTP_201_CREATED)
async def SUBIR_documento_persona(
    file: UploadFile = File(...),
    tipo_documento: str = Form("general")
):
    """
    Recibe un archivo físico (PDF, PNG, JPG, JPEG) y la categoría (cedula, arl, eps, gesco),
    lo guarda en la subcarpeta correspondiente ('uploads/documentos/{subcarpeta}/')
    y retorna la URL estática organizada.
    """
    nombre_original = file.filename or "documento.pdf"
    extension = nombre_original.split(".")[-1].lower() if "." in nombre_original else "pdf"

    formatos_permitidos = ["pdf", "png", "jpg", "jpeg"]
    if extension not in formatos_permitidos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato '.{extension}' no permitido. Solo se aceptan archivos PDF, PNG, JPG o JPEG."
        )

    # Determinar subcarpeta según tipo_documento
    tipo_norm = str(tipo_documento).strip().lower()
    subcarpeta = MAPEO_SUBDIRECTORIOS.get(tipo_norm, "general")

    # Generar un nombre único para evitar sobrescribir archivos con el mismo nombre
    nombre_unico = f"{uuid.uuid4().hex}.{extension}"
    carpeta_destino = os.path.join("uploads", "documentos", subcarpeta)
    os.makedirs(carpeta_destino, exist_ok=True)
    ruta_fisica = os.path.join(carpeta_destino, nombre_unico)

    try:
        with open(ruta_fisica, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        url_acceso = f"/uploads/documentos/{subcarpeta}/{nombre_unico}"
        print(f"📁 [FILE UPLOAD] Archivo '{nombre_original}' ({subcarpeta}) guardado en '{url_acceso}'")

        return {
            "exito": True,
            "mensaje": f"Archivo guardado exitosamente en la categoría '{subcarpeta}'.",
            "nombre_archivo": nombre_unico,
            "url_documento": url_acceso,
            "nombre_original": nombre_original,
            "categoria": subcarpeta,
        }

    except Exception as e:
        print(f"❌ Error al guardar el archivo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al guardar el archivo: {e}"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
def CREATE_solicitud(payload: SolicitudInput):
    datos_raw = payload.model_dump()

    print("🧹 [TRANSFORMER] Limpiando y normalizando datos entrantes por API...")
    datos_limpios = transformar_solicitud(datos_raw)

    print("🚀 [LOADER] Insertando solicitud en MySQL...")
    resultado = CREATE_solicitud_bd(datos_limpios)

    if not resultado.get("exito", False):
        print(f"❌ Error al crear solicitud: {resultado.get('mensaje')}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al intentar guardar la solicitud."),
        )

    ids = resultado.get("ids_generados", [resultado.get("id_generado")])
    print(f"✅ Solicitud(es) {ids} creada(s) exitosamente.")
    return {
        "estado": "success",
        "mensaje": resultado.get("mensaje", "Solicitud procesada correctamente."),
        "datos_guardados": resultado,
    }


@router.get("/{solicitud_id}", status_code=status.HTTP_200_OK)
def GET_solicitud(solicitud_id: int):
    print(f"🔍 [GET] Buscando solicitud #{solicitud_id} en la base de datos...")
    resultado = GET_solicitud_bd(solicitud_id)

    if not resultado.get("exito"):
        print(f"⚠️ Solicitud #{solicitud_id} no encontrada.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje"),
        )

    print(f"📦 [GET] Datos de la solicitud #{solicitud_id} recuperados con éxito.")
    return resultado["datos"]


@router.patch("/{solicitud_id}", status_code=status.HTTP_200_OK)
def UPDATE_solicitud(solicitud_id: int, datos_in: UPDATE_Schema_Optionals):
    print(f"📝 [PATCH] Tomando los campos enviados para actualizar la solicitud #{solicitud_id}...")
    new_updates = datos_in.model_dump(exclude_unset=True)

    if not new_updates:
        print("⚠️ No se enviaron campos válidos en el body para actualizar.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar."
        )

    print(f"⚙️ [TRANSFORMER] Aplicando transformaciones de PATCH para la solicitud #{solicitud_id}...")
    datos_transformados = transformar_solicitud_patch(new_updates)

    print(f"💾 [LOADER] Aplicando cambios en MySQL para la solicitud #{solicitud_id}...")
    resultado = UPDATE_solicitud_bd(solicitud_id, datos_transformados)

    if not resultado.get("exito"):
        print(f"❌ Error al actualizar solicitud #{solicitud_id}: {resultado.get('mensaje')}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje"),
        )

    print(f"✨ Solicitud #{solicitud_id} actualizada correctamente en la base de datos.")
    return {"estado": "success", "mensaje": resultado["mensaje"]}


@router.delete("/{solicitud_id}", status_code=status.HTTP_200_OK)
def DELETE_solicitud(solicitud_id: int):
    print(f"🗑️ [DELETE] Eliminando solicitud #{solicitud_id} de la base de datos...")
    resultado = DELETE_solicitud_bd(solicitud_id)

    if not resultado.get("exito"):
        print(f"⚠️ No se pudo eliminar la solicitud #{solicitud_id}: {resultado.get('mensaje')}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado["mensaje"],
        )

    print(f"💥 Solicitud #{solicitud_id} borrada con éxito.")
    return {
        "estado": "success", 
        "mensaje": resultado["mensaje"]
    }