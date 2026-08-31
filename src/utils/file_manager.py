"""
Utilidad para el almacenamiento seguro de archivos en el servidor.

Este módulo centraliza la validación, seguridad y almacenamiento físico de
archivos subidos por los usuarios (cédulas, ARL, exámenes médicos, documentos de vehículos, etc.).
"""

import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException, status

# ==============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# ==============================================================================

# Límite de tamaño máximo permitido por archivo (10 MB).
# Esto previene ataques de Denegación de Servicio (DoS) donde alguien intente
# subir archivos gigantescos para saturar el ancho de banda, la memoria o el disco duro.
TAMANO_MAXIMO_MB = 10
TAMANO_MAXIMO_BYTES = TAMANO_MAXIMO_MB * 1024 * 1024

# Firmas de cabecera reales (Magic Bytes).
# Todo archivo en formato digital comienza con unos bytes específicos que identifican
# su verdadero formato, independientemente de la extensión que tenga en su nombre.
FIRMAS_MAGIC_BYTES = {
    "pdf": b"%PDF-",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "jpeg": b"\xff\xd8\xff",
}


async def guardar_documento_seguro(
    file: UploadFile,
    subcarpeta: str = "general",
    carpeta_base: str = os.path.join("uploads", "documentos"),
) -> dict:
    """
    Valida y guarda un archivo en disco de forma segura.

    Pasos de seguridad que realiza:
    1. Sanitiza el nombre y extrae la extensión normalizada en minúsculas.
    2. Comprueba que la extensión esté dentro de la lista permitida.
    3. Inspecciona los 'Magic Bytes' (los primeros bytes reales del archivo)
       para verificar que el contenido coincida verdaderamente con la extensión
       (evita que renombren ejecutables maliciosos a .pdf o .jpg).
    4. Verifica que el tamaño no exceda el límite permitido (10 MB).
    5. Asigna un nombre único generado con UUID v4 para evitar sobreescritura de archivos
       existentes o ataques de Directory Traversal en el nombre.
    6. Guarda el archivo en disco y retorna las rutas y metadatos limpios.

    :param file: Objeto UploadFile recibido en la petición de FastAPI.
    :param subcarpeta: Categoría o subdirectorio (ej. 'cedulas', 'arl', 'vehiculos').
    :param carpeta_base: Ruta base donde se organizan las subcarpetas.
    :return: Diccionario con los datos del archivo guardado.
    """

    # --------------------------------------------------------------------------
    # 1. Obtener y normalizar la extensión del archivo
    # --------------------------------------------------------------------------
    nombre_original = file.filename or "archivo_sin_nombre.pdf"
    
    if "." in nombre_original:
        extension = nombre_original.rsplit(".", 1)[-1].lower().strip()
    else:
        extension = ""

    # Validar si la extensión está en nuestra lista de formatos permitidos
    if extension not in FIRMAS_MAGIC_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Formato '.{extension}' no permitido. "
                f"Solo se admiten documentos PDF e imágenes (PNG, JPG, JPEG)."
            ),
        )

    # --------------------------------------------------------------------------
    # 2. Validar tamaño máximo del archivo (Prevenir saturación de disco / DoS)
    # --------------------------------------------------------------------------
    try:
        # Movemos el cursor interno al final del archivo para medir su longitud en bytes
        file.file.seek(0, os.SEEK_END)
        tamano_en_bytes = file.file.tell()
        # Volvemos a posicionar el cursor al principio (0) para poder leerlo luego
        file.file.seek(0)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar el tamaño del archivo: {str(e)}"
        )

    if tamano_en_bytes > TAMANO_MAXIMO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"El archivo '{nombre_original}' supera el tamaño máximo permitido "
                f"de {TAMANO_MAXIMO_MB} MB (Tamaño recibido: {round(tamano_en_bytes / (1024 * 1024), 2)} MB)."
            ),
        )

    if tamano_en_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo enviado está vacío (0 bytes)."
        )

    # --------------------------------------------------------------------------
    # 3. Validar Magic Bytes (Firma real del archivo)
    # --------------------------------------------------------------------------
    # Leemos los primeros 16 bytes para compararlos con la firma real del formato
    primeros_bytes = await file.read(16)
    # IMPORTANTE: Rebobinamos el cursor para que al copiar a disco no falten estos primeros bytes
    await file.seek(0)

    firma_esperada = FIRMAS_MAGIC_BYTES[extension]
    if not primeros_bytes.startswith(firma_esperada):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El contenido del archivo no coincide con su extensión declarada (.{extension}). "
                f"Por seguridad, el archivo ha sido rechazado."
            ),
        )

    # --------------------------------------------------------------------------
    # 4. Generar nombre único con UUID (Prevenir colisiones y Directory Traversal)
    # --------------------------------------------------------------------------
    nombre_unico = f"{uuid.uuid4().hex}.{extension}"

    # Crear el directorio destino físico si aún no existe
    directorio_destino = os.path.join(carpeta_base, subcarpeta)
    os.makedirs(directorio_destino, exist_ok=True)

    ruta_fisica = os.path.join(directorio_destino, nombre_unico)

    # --------------------------------------------------------------------------
    # 5. Guardar el archivo en disco de forma segura
    # --------------------------------------------------------------------------
    try:
        with open(ruta_fisica, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al escribir el archivo en disco: {str(e)}"
        )

    # Construir la URL relativa estática para consumo del frontend
    # Nota: Usamos barras normales ('/') para que sea una URL web válida independientemente de Windows o Linux
    url_acceso = f"/{carpeta_base.replace(os.sep, '/')}/{subcarpeta}/{nombre_unico}"

    return {
        "nombre_archivo": nombre_unico,
        "nombre_original": nombre_original,
        "url_documento": url_acceso,
        "categoria": subcarpeta,
        "tamano_bytes": tamano_en_bytes,
        "extension": extension,
    }
