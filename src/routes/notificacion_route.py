import os
import uuid
import shutil
import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, status, Depends, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from typing import Optional, List
from pydantic import BaseModel

from src.loaders.notificacion_loader import (
    crear_notificacion_db,
    obtener_notificaciones_db,
    contar_no_leidas_db,
    marcar_leida_db,
    marcar_todas_leidas_db,
    marcar_leida_por_solicitud_db,
    emitir_difusion_superadmin_db,
    obtener_historial_difusion_db,
)
from src.utils.security import get_current_user, require_role, decode_access_token
from src.utils.broadcaster import notification_broadcaster

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


class NotificacionCreate(BaseModel):
    titulo: str
    mensaje: str
    tipo: Optional[str] = "info"
    enlace: Optional[str] = None
    archivo_url: Optional[str] = None
    archivo_nombre: Optional[str] = None
    id_usuario: Optional[int] = None
    rol_destino: Optional[int] = None


class MarcarTodasRequest(BaseModel):
    id_usuario: Optional[int] = None
    id_rol: Optional[int] = None


class MarcarPorSolicitudRequest(BaseModel):
    id_o_codigo: str
    id_usuario: Optional[int] = None
    id_rol: Optional[int] = None


@router.get("/stream")
async def stream_notificaciones(request: Request, token: Optional[str] = Query(None)):
    """
    Canal Server-Sent Events (SSE) para entrega de notificaciones en tiempo real ('en caliente').
    Permite a los usuarios recibir comunicados, cambios de estado y dictámenes sin recargar.
    """
    token_str = token
    if not token_str:
        auth_header = request.headers.get("Authorization") or ""
        if auth_header.startswith("Bearer "):
            token_str = auth_header.split(" ")[1]
        elif "token" in request.cookies:
            token_str = request.cookies.get("token")

    user_id = None
    id_rol = None
    rol_nombre = None

    if token_str:
        payload = decode_access_token(token_str)
        if payload:
            user_id = payload.get("sub") or payload.get("id")
            id_rol = payload.get("id_rol")
            rol_nombre = payload.get("rol")

    if not user_id and not id_rol:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida para conectar al canal de notificaciones en vivo."
        )

    queue = asyncio.Queue(maxsize=100)
    conn_id = str(uuid.uuid4())
    notification_broadcaster.register(
        connection_id=conn_id,
        queue=queue,
        user_id=user_id,
        id_rol=id_rol,
        rol=rol_nombre
    )

    async def event_generator():
        # Mensaje de bienvenida y sincronización de conexión
        init_data = json.dumps({
            "status": "connected",
            "userId": user_id,
            "roleId": id_rol,
            "rol": rol_nombre
        })
        yield f"event: connected\ndata: {init_data}\n\n"

        try:
            while True:
                if await request.is_disconnected():
                    break

                try:
                    mensaje = await asyncio.wait_for(queue.get(), timeout=20.0)
                    yield mensaje
                except asyncio.TimeoutError:
                    # Keep-alive ping para evitar desconexiones de proxy o navegador
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            notification_broadcaster.unregister(conn_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream"
        }
    )


@router.get("", status_code=status.HTTP_200_OK)
def listar_notificaciones(
    id_usuario: Optional[int] = Query(None, description="ID del usuario logueado"),
    id_rol: Optional[int] = Query(None, description="ID del rol del usuario logueado"),
    limit: int = Query(50, ge=1, le=200, description="Cantidad máxima de notificaciones a retornar"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene las notificaciones para un usuario o rol, junto con el conteo de no leídas.
    """
    user_id = id_usuario or current_user.get("id")
    rol_id = id_rol or current_user.get("id_rol")
    notificaciones = obtener_notificaciones_db(id_usuario=user_id, id_rol=rol_id, limit=limit)
    no_leidas = contar_no_leidas_db(id_usuario=user_id, id_rol=rol_id)
    return {
        "estado": "OK",
        "no_leidas": no_leidas,
        "notificaciones": notificaciones,
    }


@router.patch("/{id_notificacion}/leer", status_code=status.HTTP_200_OK)
def marcar_como_leida(id_notificacion: int, current_user: dict = Depends(get_current_user)):
    """
    Marca una notificación específica como leída.
    """
    exito = marcar_leida_db(id_notificacion)
    if not exito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La notificación no fue encontrada o ya estaba leída.",
        )
    # Notificar en vivo para sincronizar pestañas y clientes
    notification_broadcaster.notificar_leidas(
        id_usuario=current_user.get("id"),
        id_rol=current_user.get("id_rol"),
        id_notificacion=id_notificacion
    )
    return {
        "estado": "OK",
        "mensaje": "Notificación marcada como leída.",
    }


@router.patch("/marcar-todas-leidas", status_code=status.HTTP_200_OK)
def marcar_todas_como_leidas(payload: MarcarTodasRequest, current_user: dict = Depends(get_current_user)):
    """
    Marca todas las notificaciones pendientes del usuario o su rol como leídas.
    """
    user_id = payload.id_usuario or current_user.get("id")
    rol_id = payload.id_rol or current_user.get("id_rol")
    marcar_todas_leidas_db(id_usuario=user_id, id_rol=rol_id)
    # Notificar en vivo
    notification_broadcaster.notificar_leidas(
        id_usuario=user_id,
        id_rol=rol_id,
        todas=True
    )
    return {
        "estado": "OK",
        "mensaje": "Todas las notificaciones fueron marcadas como leídas.",
    }


@router.patch("/marcar-leida-solicitud", status_code=status.HTTP_200_OK)
def marcar_leida_por_solicitud(payload: MarcarPorSolicitudRequest, current_user: dict = Depends(get_current_user)):
    """
    Marca como leídas las notificaciones asociadas a una solicitud cuando el usuario entra a revisarla.
    """
    user_id = payload.id_usuario or current_user.get("id")
    rol_id = payload.id_rol or current_user.get("id_rol")
    afectadas = marcar_leida_por_solicitud_db(
        id_o_codigo=payload.id_o_codigo,
        id_usuario=user_id,
        id_rol=rol_id
    )
    if afectadas > 0:
        notification_broadcaster.notificar_leidas(
            id_usuario=user_id,
            id_rol=rol_id,
            todas=False
        )
    return {
        "estado": "OK",
        "mensaje": f"{afectadas} notificación(es) marcada(s) como leída(s).",
        "afectadas": afectadas
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def crear_notificacion(payload: NotificacionCreate, current_user: dict = Depends(get_current_user)):
    """
    Crea una nueva notificación manualmente.
    """
    target_user = payload.id_usuario or current_user.get("id")
    notif_id = crear_notificacion_db(
        titulo=payload.titulo,
        mensaje=payload.mensaje,
        tipo=payload.tipo or "info",
        enlace=payload.enlace,
        archivo_url=payload.archivo_url,
        archivo_nombre=payload.archivo_nombre,
        id_usuario=target_user,
        rol_destino=payload.rol_destino,
    )
    if not notif_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo registrar la notificación.",
        )

    # Difundir en caliente al destinatario
    notification_broadcaster.notificar_nueva(
        {
            "id": notif_id,
            "titulo": payload.titulo,
            "mensaje": payload.mensaje,
            "tipo": payload.tipo or "info",
            "enlace": payload.enlace,
            "archivo_url": payload.archivo_url,
            "archivo_nombre": payload.archivo_nombre,
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "leido": False,
            "id_usuario": target_user,
            "rol_destino": payload.rol_destino
        },
        target_user_id=target_user if not payload.rol_destino else None,
        target_role_id=payload.rol_destino
    )

    return {
        "estado": "OK",
        "id": notif_id,
        "mensaje": "Notificación creada con éxito.",
    }


@router.post("/subir-adjunto", status_code=status.HTTP_201_CREATED)
async def subir_adjunto_notificacion(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role(["SUPERADMIN"]))
):
    """
    Permite al SuperAdmin adjuntar un documento o archivo a un comunicado para descarga de los usuarios.
    Formatos soportados: PDF, Word, Excel, PowerPoint, ZIP, RAR, TXT, CSV, Imágenes.
    Tamaño máximo: 25 MB.
    """
    EXTENSIONES_PERMITIDAS = {
        "pdf", "png", "jpg", "jpeg", "webp",
        "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        "csv", "txt", "zip", "rar"
    }
    MAX_BYTES = 25 * 1024 * 1024  # 25 MB

    nombre_original = file.filename or "adjunto.pdf"
    extension = nombre_original.rsplit(".", 1)[-1].lower().strip() if "." in nombre_original else ""

    if extension not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato '.{extension}' no permitido. Se admiten documentos (PDF, DOCX, XLSX, etc.), comprimidos (ZIP, RAR) e imágenes."
        )

    # Validar tamaño
    try:
        file.file.seek(0, os.SEEK_END)
        tamano_bytes = file.file.tell()
        file.file.seek(0)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error leyendo el archivo: {str(e)}")

    if tamano_bytes > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el tamaño máximo permitido de 25 MB ({round(tamano_bytes / (1024 * 1024), 2)} MB recibidos)."
        )

    if tamano_bytes == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo enviado está vacío.")

    # Carpeta física destino
    directorio_destino = os.path.join("uploads", "documentos", "notificaciones")
    os.makedirs(directorio_destino, exist_ok=True)

    nombre_unico = f"{uuid.uuid4().hex}.{extension}"
    ruta_fisica = os.path.join(directorio_destino, nombre_unico)

    try:
        with open(ruta_fisica, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al guardar el archivo: {str(e)}")

    url_archivo = f"/uploads/documentos/notificaciones/{nombre_unico}"

    return {
        "exito": True,
        "url_archivo": url_archivo,
        "nombre_archivo": nombre_original,
        "tamano_bytes": tamano_bytes,
        "mensaje": "Documento subido correctamente."
    }


class DifusionSuperadminRequest(BaseModel):
    titulo: str
    mensaje: str
    tipo: Optional[str] = "info"
    enlace: Optional[str] = None
    archivo_url: Optional[str] = None
    archivo_nombre: Optional[str] = None
    destinatario_tipo: str = "rol"  # "rol", "usuarios", "todos"
    roles_ids: Optional[List[int]] = None
    usuarios_ids: Optional[List[int]] = None


@router.post("/difusion", status_code=status.HTTP_201_CREATED)
def emitir_difusion(
    payload: DifusionSuperadminRequest,
    current_user: dict = Depends(require_role(["SUPERADMIN"]))
):
    """
    Emite comunicados masivos o personalizados hacia roles o usuarios específicos (Exclusivo SuperAdmin).
    """
    res = emitir_difusion_superadmin_db(
        titulo=payload.titulo,
        mensaje=payload.mensaje,
        tipo=payload.tipo or "info",
        enlace=payload.enlace,
        archivo_url=payload.archivo_url,
        archivo_nombre=payload.archivo_nombre,
        destinatario_tipo=payload.destinatario_tipo,
        roles_ids=payload.roles_ids,
        usuarios_ids=payload.usuarios_ids,
    )
    if not res.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("mensaje", "No fue posible emitir el comunicado.")
        )

    # Difusión en caliente a los receptores conectados en tiempo real
    notif_data = {
        "titulo": payload.titulo,
        "mensaje": payload.mensaje,
        "tipo": payload.tipo or "info",
        "enlace": payload.enlace,
        "archivo_url": payload.archivo_url,
        "archivo_nombre": payload.archivo_nombre,
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "leido": False,
        "origen": "SUPERADMIN"
    }

    if payload.destinatario_tipo == "todos":
        notification_broadcaster.notificar_nueva(notif_data, broadcast_all=True)
    elif payload.destinatario_tipo == "rol":
        notification_broadcaster.notificar_nueva(notif_data, target_roles_ids=payload.roles_ids)
    elif payload.destinatario_tipo == "usuarios":
        notification_broadcaster.notificar_nueva(notif_data, target_users_ids=payload.usuarios_ids)

    return res


@router.get("/historial-difusion", status_code=status.HTTP_200_OK)
def obtener_historial_difusion(
    limit: int = Query(25, ge=1, le=100),
    current_user: dict = Depends(require_role(["SUPERADMIN"]))
):
    """
    Retorna el registro histórico de notificaciones y comunicados emitidos en la plataforma (Exclusivo SuperAdmin).
    """
    historial = obtener_historial_difusion_db(limit=limit)
    return {
        "estado": "OK",
        "total": len(historial),
        "historial": historial,
    }

