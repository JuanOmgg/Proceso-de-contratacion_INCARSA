import os
import shutil
import uuid
import io
import qrcode
from PIL import Image, ImageDraw, ImageFont
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status, Query, Depends, Request, Response, Body
from src.utils.file_manager import guardar_documento_seguro
from src.loaders.solicitudes_loaders import (
    DELETE_solicitud_bd,
    GET_solicitud_bd,
    CREATE_solicitud_bd,
    UPDATE_solicitud_bd,
    GET_ALL_solicitudes_bd,
    GET_date_count_db,
    REGISTRAR_dictamen_db,
    ACTUALIZAR_autorizacion_personas_db,
    VALIDAR_token_edicion_db,
    CONSUMIR_token_edicion_db,
    GET_resumen_verificacion_porteria_db,
    GET_detalle_autorizacion_datos_db,
    REGISTRAR_respuesta_autorizacion_datos_db,
    REENVIAR_correo_autorizacion_datos_db,
    CREAR_token_formulario_db,
    OBTENER_token_formulario_db,
    LISTAR_tokens_formulario_db,
    REVOCAR_token_formulario_db,
    MARCAR_token_usado_db,
    APROBAR_envio_solicitud_db
)
from src.schemas.solicitud_schema import (
    SolicitudInput,
    UPDATE_Schema_Optionals,
    DictamenInput,
    RespuestaAutorizacionInput,
    CrearTokenFormularioInput,
)
from src.transformers import transformar_solicitud, transformar_solicitud_patch
from src.utils.security import get_current_user, require_role, require_permission
from src.loaders.notificacion_loader import marcar_leida_por_solicitud_db
from typing import List, Dict, Any, Optional

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
    tipo_documento: str = Form("general"),
    current_user: dict = Depends(get_current_user)
):
    # Determinar subcarpeta según el tipo de documento recibido
    tipo_norm = str(tipo_documento).strip().lower()
    subcarpeta = MAPEO_SUBDIRECTORIOS.get(tipo_norm, "general")

    # Guardar archivo con validaciones de seguridad (extensión, Magic Bytes, tamaño máx)
    archivo_guardado = await guardar_documento_seguro(file, subcarpeta=subcarpeta)

    print(f"📁 [FILE UPLOAD SEGURO] '{archivo_guardado['nombre_original']}' ({subcarpeta}) -> '{archivo_guardado['url_documento']}'")

    return {
        "exito": True,
        "mensaje": f"Archivo guardado exitosamente en la categoría '{subcarpeta}'.",
        "nombre_archivo": archivo_guardado["nombre_archivo"],
        "url_documento": archivo_guardado["url_documento"],
        "nombre_original": archivo_guardado["nombre_original"],
        "categoria": subcarpeta,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
@router.post("", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def CREATE_solicitud(payload: SolicitudInput, current_user: dict = Depends(require_permission("solicitudes", "crear"))):
    datos_raw = payload.model_dump()
    if not datos_raw.get("id_usuario"):
        datos_raw["id_usuario"] = current_user.get("id")

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

@router.get("/fechasCount", response_model=List[Dict[str, Any]])
def GET_fechasCount_rt(current_user: dict = Depends(get_current_user)):

    try:

        Fcount = GET_date_count_db()

        return Fcount

    except Exception as e:
        print(f"❌ Error al obtener fechas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener fechas: {e}"
        )

@router.get("/getall", status_code=status.HTTP_200_OK)
@router.get("/getAll", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK)
@router.get("", status_code=status.HTTP_200_OK, include_in_schema=False)
def GET_ALL_solicitudes(
    active: Optional[bool] = Query(None, description="Filtrar solo solicitudes activas. Por defecto: None"),
    id_usuario: Optional[int] = Query(None, description="Filtrar por plantas del usuario si es SST o GESCO"),
    diligenciado_por: Optional[int] = Query(None, description="Filtrar por usuario que diligenció la solicitud"),
    current_user: dict = Depends(get_current_user)
):
    rol_user = str(current_user.get("rol", "")).strip().upper()
    id_rol_user = current_user.get("id_rol")
    try:
        id_rol_user = int(id_rol_user) if id_rol_user is not None else None
    except (ValueError, TypeError):
        pass

    # Administradores y Superadministradores tienen acceso al histórico absoluto de solicitudes.
    # Los demás roles no ven solicitudes inactivas que ya caducaron según la fecha actual.
    es_admin = (id_rol_user in (1, 2)) or ("ADMIN" in rol_user) or (rol_user in ("SUPERADMIN", "ADMINISTRADOR", "ADMIN", "SUPER ADMIN"))
    excluir_inactivas_vencidas = not es_admin

    # Si el usuario autenticado es SST (6) o GESCO (7), SIEMPRE filtrar estrictamente por sus plantas asignadas
    if id_rol_user in (6, 7) or rol_user in ("SST", "GESCO"):
        id_usuario = current_user.get("id")

    # Si el usuario autenticado es Gestión Documental (5), SIEMPRE filtrar estrictamente por las que él haya diligenciado
    if id_rol_user == 5 or "GESTION DOCUMENTAL" in rol_user or "GESTIÓN DOCUMENTAL" in rol_user:
        diligenciado_por = current_user.get("id")

    print(f"🔍 [GET] Consultando solicitudes (activas={active}, id_usuario={id_usuario}, diligenciado_por={diligenciado_por}, excluir_inactivas_vencidas={excluir_inactivas_vencidas})...")
    
    resultado = GET_ALL_solicitudes_bd(
        only_active=active, 
        id_usuario=id_usuario, 
        diligenciado_por=diligenciado_por,
        excluir_inactivas_vencidas=excluir_inactivas_vencidas
    )

    if not resultado.get("exito", True):
        error_msg = resultado.get("mensaje", "Error desconocido en la consulta de solicitudes.")
        print(f"❌ Error interno en GET_ALL_solicitudes_bd: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al obtener las solicitudes.")
        )

    return resultado.get("datos", resultado)


@router.get("/publico/verificar/{codigo}", status_code=status.HTTP_200_OK)
def VERIFICAR_solicitud_porteria_publico_rt(codigo: str):
    """
    Endpoint público optimizado para vigilantes y control de acceso en porterías.
    No requiere sesión activa para permitir escaneo rápido desde teléfonos móviles de portería.
    """
    print(f"🛡️ [PORTERÍA] Consultando resumen de acceso para solicitud '{codigo}'...")
    resultado = GET_resumen_verificacion_porteria_db(codigo)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", "Solicitud no encontrada.")
        )
    return resultado["datos"]


@router.get("/{codigo}/qr", status_code=status.HTTP_200_OK)
@router.get("/publico/qr/{codigo}", status_code=status.HTTP_200_OK)
def GENERAR_qr_solicitud_rt(codigo: str, request: Request):
    """
    Genera dinámicamente la imagen PNG del código QR que apunta a la página de verificación.
    """
    cod_clean = codigo.strip().upper()
    base_url = str(request.base_url).rstrip("/")

    # Si se accede desde localhost o 127.0.0.1, reemplazar por la IP LAN local
    # para que al escanear con la cámara del celular en la misma red Wi-Fi funcione de inmediato
    if "localhost" in base_url or "127.0.0.1" in base_url:
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            lan_ip = s.getsockname()[0]
            s.close()
            if lan_ip and lan_ip != "127.0.0.1":
                base_url = base_url.replace("localhost", lan_ip).replace("127.0.0.1", lan_ip)
        except Exception:
            pass

    url_verificacion = f"{base_url}/verificar/{cod_clean}"

    # Consultar información de la solicitud para rotular la tarjeta (empresa origen y código)
    empresa_origen = "INCARSA"
    empresa_contratista = ""
    codigo_mostrado = cod_clean
    try:
        resumen = GET_resumen_verificacion_porteria_db(cod_clean)
        if resumen.get("exito"):
            datos = resumen.get("datos", {})
            empresa_origen = str(datos.get("empresa_origen") or "INCARSA").strip()
            empresa_contratista = str(datos.get("empresa_contratista") or "").strip()
            codigo_mostrado = str(datos.get("codigo") or cod_clean).strip()
    except Exception as e_res:
        print(f"⚠️ Aviso al rotular tarjeta QR: {e_res}")

    # Generar el código QR base
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(url_verificacion)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0f172a", back_color="#ffffff").convert("RGB")
    qr_w, qr_h = qr_img.size

    # Cargar fuentes del sistema con fallback seguro multiplataforma
    def _cargar_fuente(nombre_archivo, tamano):
        rutas_candidatas = [
            os.path.join("C:/Windows/Fonts", nombre_archivo),
            f"/usr/share/fonts/truetype/dejavu/{nombre_archivo}",
            f"/usr/share/fonts/TTF/{nombre_archivo}",
            f"/Library/Fonts/{nombre_archivo}"
        ]
        for ruta in rutas_candidatas:
            if os.path.exists(ruta):
                try:
                    return ImageFont.truetype(ruta, tamano)
                except Exception:
                    pass
        return ImageFont.load_default()

    font_titulo = _cargar_fuente("arialbd.ttf", 23)
    font_sub = _cargar_fuente("segoeuib.ttf", 11)
    font_contratista = _cargar_fuente("arial.ttf", 11)
    font_codigo = _cargar_fuente("consolab.ttf", 25)
    font_ayuda = _cargar_fuente("arial.ttf", 10)

    # Calcular dimensiones de la tarjeta
    tiene_contratista = bool(empresa_contratista and empresa_contratista.lower() not in ("no especificada", "—", "-"))
    header_h = 100 if tiene_contratista else 82
    footer_h = 108
    card_w = max(qr_w + 90, 460)
    card_h = header_h + qr_h + footer_h

    canvas = Image.new("RGB", (card_w, card_h), "#FFFFFF")
    draw = ImageDraw.Draw(canvas)

    # 1. Cabecera: Empresa Origen (Título superior solicitado)
    tit_texto = empresa_origen.upper()
    if len(tit_texto) > 34:
        tit_texto = tit_texto[:32] + "..."
    draw.text((card_w // 2, 30), tit_texto, fill="#0f172a", font=font_titulo, anchor="mm")
    draw.text((card_w // 2, 56), "PASE PARA CONTROL DE ACCESO", fill="#0284c7", font=font_sub, anchor="mm")

    if tiene_contratista:
        c_texto = f"Contratista: {empresa_contratista}"
        if len(c_texto) > 46:
            c_texto = c_texto[:44] + "..."
        draw.text((card_w // 2, 77), c_texto, fill="#475569", font=font_contratista, anchor="mm")

    # Separador cabecera
    draw.line([(28, header_h - 6), (card_w - 28, header_h - 6)], fill="#e2e8f0", width=1)

    # 2. Código QR centrado
    qr_x = (card_w - qr_w) // 2
    qr_y = header_h + 8
    canvas.paste(qr_img, (qr_x, qr_y))

    # Separador inferior
    sep_inf_y = qr_y + qr_h + 8
    draw.line([(28, sep_inf_y), (card_w - 28, sep_inf_y)], fill="#e2e8f0", width=1)

    # 3. Pie de tarjeta: Caja con el Código de Radicado para digitación manual del vigilante
    box_w = min(card_w - 60, 320)
    box_x1 = (card_w - box_w) // 2
    box_y1 = sep_inf_y + 14
    box_x2 = box_x1 + box_w
    box_y2 = box_y1 + 44
    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=10, fill="#f8fafc", outline="#94a3b8", width=1)

    # Código radicado destacado
    draw.text((card_w // 2, (box_y1 + box_y2) // 2), codigo_mostrado, fill="#0f172a", font=font_codigo, anchor="mm")

    # Leyenda para el vigilante
    draw.text((card_w // 2, box_y2 + 18), "En caso de no leer el QR, digite este radicado en el sistema", fill="#64748b", font=font_ayuda, anchor="mm")

    # Borde redondeado exterior de la tarjeta
    draw.rounded_rectangle([2, 2, card_w - 3, card_h - 3], radius=16, outline="#cbd5e1", width=2)

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    buf.seek(0)

    return Response(
        content=buf.getvalue(),
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": f'inline; filename="PASE-{cod_clean}.png"'
        }
    )


@router.get("/{solicitud_id}", status_code=status.HTTP_200_OK)
def GET_solicitud(solicitud_id: str, current_user: dict = Depends(get_current_user)):
    print(f"🔍 [GET] Buscando solicitud #{solicitud_id} en la base de datos...")
    resultado = GET_solicitud_bd(solicitud_id)

    if not resultado.get("exito"):
        print(f"⚠️ Solicitud #{solicitud_id} no encontrada.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje"),
        )

    # Si alguien revisa la solicitud desde otra parte que no sea notificaciones (listado, dashboard, modal, URL directa),
    # marcar automáticamente como leídas las notificaciones pendientes asociadas a esta solicitud para su usuario o rol
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else None
        rol_id = current_user.get("id_rol") if isinstance(current_user, dict) else None
        marcar_leida_por_solicitud_db(solicitud_id, id_usuario=user_id, id_rol=rol_id)
    except Exception as e_notif:
        print(f"⚠️ Error al auto-marcar notificaciones para solicitud #{solicitud_id}: {e_notif}")

    print(f"📦 [GET] Datos de la solicitud #{solicitud_id} recuperados con éxito.")
    return resultado["datos"]


@router.post("/{solicitud_id}/dictamen", status_code=status.HTTP_200_OK)
def REGISTRAR_dictamen_rt(
    solicitud_id: str,
    payload: DictamenInput,
    current_user: dict = Depends(require_permission("solicitudes", "aprobar"))
):
    print(f"📝 [DICTAMEN] Registrando dictamen para solicitud #{solicitud_id} por {payload.rol} (planta={payload.id_planta})...")
    dict_payload = payload.model_dump()
    if not dict_payload.get("id_usuario"):
        dict_payload["id_usuario"] = current_user.get("id")
    nombre_autenticado = f"{current_user.get('nombres', '')} {current_user.get('apellidos', '')}".strip()
    if not dict_payload.get("nombre_revisor") or str(dict_payload.get("nombre_revisor", "")).startswith("Auditor ("):
        if nombre_autenticado:
            dict_payload["nombre_revisor"] = nombre_autenticado
    resultado = REGISTRAR_dictamen_db(solicitud_id, dict_payload)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al registrar dictamen.")
        )
    return resultado
 
@router.post("/{solicitud_id}/personas-autorizacion", status_code=status.HTTP_200_OK)
@router.put("/{solicitud_id}/personas-autorizacion", status_code=status.HTTP_200_OK)
def ACTUALIZAR_personas_autorizacion_rt(
    solicitud_id: str,
    payload: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    rol_user = str(current_user.get("rol", "")).strip().upper()
    id_rol_user = current_user.get("id_rol")
    try:
        id_rol_user = int(id_rol_user) if id_rol_user is not None else None
    except (ValueError, TypeError):
        pass

    roles_validos = ("SST", "GESCO", "SCR", "ADMINISTRADOR", "ADMIN", "SUPERADMIN", "EQUIPO SCR - RADICADOS")
    if id_rol_user not in (1, 2, 4, 6, 7, 8) and rol_user not in roles_validos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar autorizaciones de personal en esta solicitud."
        )

    if not payload.get("id_usuario"):
        payload["id_usuario"] = current_user.get("id")
    if not payload.get("rol"):
        payload["rol"] = current_user.get("rol") or current_user.get("nombre_rol") or rol_user
    if not payload.get("nombre_revisor"):
        payload["nombre_revisor"] = f"{current_user.get('nombres', '')} {current_user.get('apellidos', '')}".strip()

    resultado = ACTUALIZAR_autorizacion_personas_db(solicitud_id, payload)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al actualizar autorizaciones de personas.")
        )
    return resultado

@router.get("/{solicitud_id}/validar-token-edicion", status_code=status.HTTP_200_OK)
def VALIDAR_token_edicion_rt(
    solicitud_id: str,
    token: str = Query(..., description="Token de edición única"),
    current_user: dict = Depends(require_permission("solicitudes", "editar"))
):
    resultado = VALIDAR_token_edicion_db(solicitud_id, token)
    if not resultado.get("valido"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=resultado.get("mensaje", "El token de edición no es válido o ha expirado.")
        )
    return resultado


@router.patch("/{solicitud_id}", status_code=status.HTTP_200_OK)
@router.put("/{solicitud_id}", status_code=status.HTTP_200_OK)
def UPDATE_solicitud(solicitud_id: str, datos_in: UPDATE_Schema_Optionals, current_user: dict = Depends(require_permission("solicitudes", "editar"))):

    print(f"📝 [PATCH] Tomando los campos enviados para actualizar la solicitud #{solicitud_id}...")
    new_updates = datos_in.model_dump(exclude_unset=True)

    if not new_updates:
        print("⚠️ No se enviaron campos válidos en el body para actualizar.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar."
        )

    # Restricciones de edición según rol y estado:
    user_rol = str(current_user.get("rol", "")).strip().lower()
    es_super = user_rol in ("superadmin", "super admin", "super_admin")

    # Proteger el solicitante original: al editar una solicitud (o cambiar su estado) NUNCA se debe alterar la persona que la diligenció
    new_updates.pop("diligenciado_por", None)

    token_edicion = new_updates.pop("token_edicion", None)
    consumir_token = False

    # 1. Los usuarios sin rol SUPERADMIN no pueden cambiar el estado de la solicitud directamente
    if not es_super and "estado" in new_updates:
        del new_updates["estado"]

    # 2. Obtener estado actual de la solicitud
    actual = GET_solicitud_bd(solicitud_id)
    if not actual.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solicitud #{solicitud_id} no encontrada."
        )

    datos_actuales = actual.get("datos", {})
    estado_actual = str(datos_actuales.get("estado") or "").strip().upper()
    real_id = datos_actuales.get("id", solicitud_id)

    if estado_actual == "DEVUELTO PARA CORRECCIÓN":
        if not token_edicion and not es_super:
            print(f"🚫 [PATCH] Usuario '{user_rol}' intentó editar la solicitud #{solicitud_id} en estado '{estado_actual}' sin token de edición única.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Esta solicitud fue devuelta para corrección única. Solo puedes editarla accediendo mediante el enlace de la notificación con un token válido."
            )

        if token_edicion:
            val_token = VALIDAR_token_edicion_db(real_id, token_edicion)
            if not val_token.get("valido"):
                print(f"🚫 [PATCH] Token de edición inválido o consumido para #{solicitud_id}: {val_token.get('mensaje')}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=val_token.get("mensaje", "El enlace de edición única no es válido o ya fue utilizado.")
                )
            consumir_token = True
        elif es_super:
            new_updates["estado"] = "POR APROBAR"

    elif not es_super:
        # Solo pueden editar si la solicitud se encuentra en estado 'ENVIADO' o 'PRE-ENVIADO'
        if estado_actual not in ("ENVIADO", "PRE-ENVIADO"):
            print(f"🚫 [PATCH] Usuario con rol '{user_rol}' intentó editar la solicitud #{solicitud_id} en estado '{estado_actual}'. Solo SUPERADMIN puede editar fuera de 'ENVIADO' / 'PRE-ENVIADO'.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: La solicitud se encuentra en estado '{estado_actual}'. Solo puede ser editada mientras esté en estado 'ENVIADO' o 'PRE-ENVIADO', o por un usuario con rol SUPERADMIN."
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

    # Si se realizó mediante edición única con token, consumir token y registrar auditoría + notificación a SCR
    if consumir_token and token_edicion:
        res_consumo = CONSUMIR_token_edicion_db(
            solicitud_id=real_id,
            token=token_edicion,
            id_usuario=current_user.get("id"),
            nombre_usuario=current_user.get("nombre") or current_user.get("usuario")
        )
        if not res_consumo.get("exito"):
            print(f"⚠️ Aviso al consumir token de edición: {res_consumo.get('mensaje')}")

    print(f"✨ Solicitud #{solicitud_id} actualizada correctamente en la base de datos.")
    return {"estado": "success", "mensaje": resultado["mensaje"]}


@router.delete("/{solicitud_id}", status_code=status.HTTP_200_OK)
def DELETE_solicitud(solicitud_id: str, current_user: dict = Depends(require_permission("solicitudes", "eliminar"))):
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


# =========================================================================
# ENDPOINTS PÚBLICOS Y PRIVADOS: AUTORIZACIÓN DE DATOS (LEY 1581 DE 2012)
# =========================================================================

@router.get("/publico/autorizacion-datos/{token}", status_code=status.HTTP_200_OK)
def OBTENER_detalle_autorizacion(token: str):
    """
    Ruta pública: Consulta la información requerida para mostrarle al titular
    su solicitud de tratamiento de datos personales bajo la Ley 1581 de 2012.
    """
    resultado = GET_detalle_autorizacion_datos_db(token)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", "Enlace de autorización no encontrado o no válido.")
        )
    return resultado


@router.post("/publico/autorizacion-datos/{token}/responder", status_code=status.HTTP_200_OK)
def REGISTRAR_respuesta_autorizacion(token: str, datos: RespuestaAutorizacionInput, request: Request):
    """
    Ruta pública: Registra la aceptación o rechazo formal de tratamiento de datos personales.
    Captura de forma inmutable la IP de origen y marca de tiempo legal.
    """
    # Determinar IP del cliente
    ip_origen = request.headers.get("X-Forwarded-For")
    if ip_origen:
        ip_origen = ip_origen.split(",")[0].strip()
    elif request.client:
        ip_origen = request.client.host
    else:
        ip_origen = "Desconocida"

    resultado = REGISTRAR_respuesta_autorizacion_datos_db(
        token=token,
        acepto=datos.acepto,
        ip=ip_origen,
        motivo_rechazo=datos.motivo_rechazo
    )

    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "No se pudo registrar la respuesta de autorización.")
        )
    return resultado


@router.post("/{solicitud_id}/personas/{persona_id}/reenviar-autorizacion", status_code=status.HTTP_200_OK)
def REENVIAR_correo_autorizacion(
    solicitud_id: int,
    persona_id: int,
    current_user: dict = Depends(require_permission("solicitudes", "editar"))
):
    """
    Ruta autenticada: Permite a los analistas/administradores reenviar el correo
    de solicitud de autorización de datos personales a un ingresante específico.
    """
    resultado = REENVIAR_correo_autorizacion_datos_db(solicitud_id=solicitud_id, persona_id=persona_id)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al reenviar el correo de autorización.")
        )
    return resultado


# =========================================================================
# ENDPOINTS PARA FORMULARIOS TEMPORALES CON TOKEN (SOLICITANTE Y PÚBLICO)
# =========================================================================

@router.post("/tokens-formulario", status_code=status.HTTP_201_CREATED)
def CREAR_token_formulario_rt(
    payload: CrearTokenFormularioInput,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Ruta autenticada: Permite a un Solicitante (o Administrador) generar un enlace
    temporal con token para que una empresa o persona externa llene el formulario.
    """
    user_id = current_user.get("id")
    id_rol = current_user.get("id_rol")
    rol_nom = str(current_user.get("rol") or current_user.get("nombre_rol") or "").strip().upper()

    es_autorizado = (id_rol in (1, 2, 5)) or any(r in rol_nom for r in ("ADMIN", "SOLICITANTE", "GESTION DOCUMENTAL"))
    if not es_autorizado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los usuarios con rol Solicitante o Administrador pueden generar formularios temporales."
        )

    if not payload.id_empresa_contratista and not payload.destinatario_nombre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes seleccionar la Empresa Contratista para emitir el pase de diligenciamiento."
        )

    resultado = CREAR_token_formulario_db(
        id_usuario=user_id,
        duracion_horas=payload.duracion_horas or 24.0,
        destinatario_nombre=payload.destinatario_nombre,
        destinatario_email=payload.destinatario_email,
        fecha_expiracion_personalizada=payload.fecha_expiracion_personalizada,
        id_empresa_contratista=payload.id_empresa_contratista
    )
    if not resultado.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.get("mensaje"))

    base_url = str(request.base_url).rstrip("/")
    tok = resultado["datos"]["token"]
    resultado["datos"]["url_formulario"] = f"{base_url}/formulario-temporal/{tok}"
    return resultado


@router.get("/tokens-formulario", status_code=status.HTTP_200_OK)
def LISTAR_tokens_formulario_rt(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Ruta autenticada: Lista los enlaces temporales generados por el solicitante actual.
    """
    user_id = current_user.get("id")
    id_rol = current_user.get("id_rol")
    rol_nom = str(current_user.get("rol") or current_user.get("nombre_rol") or "").strip().upper()
    es_admin = (id_rol in (1, 2)) or ("ADMIN" in rol_nom)

    resultado = LISTAR_tokens_formulario_db(id_usuario=user_id, es_admin=es_admin)
    base_url = str(request.base_url).rstrip("/")
    for item in resultado.get("datos", []):
        item["url_formulario"] = f"{base_url}/formulario-temporal/{item['token']}"

    return resultado


@router.post("/tokens-formulario/{token_id}/revocar", status_code=status.HTTP_200_OK)
def REVOCAR_token_formulario_rt(
    token_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Ruta autenticada: Revoca o cancela un enlace temporal que no haya sido utilizado aún.
    """
    user_id = current_user.get("id")
    id_rol = current_user.get("id_rol")
    rol_nom = str(current_user.get("rol") or current_user.get("nombre_rol") or "").strip().upper()
    es_admin = (id_rol in (1, 2)) or ("ADMIN" in rol_nom)

    resultado = REVOCAR_token_formulario_db(token_id=token_id, id_usuario=user_id, es_admin=es_admin)
    if not resultado.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.get("mensaje"))
    return resultado


@router.get("/publico/formulario-temporal/{token}", status_code=status.HTTP_200_OK)
def OBTENER_formulario_temporal_publico_rt(token: str):
    """
    Ruta pública: Valida el token temporal y retorna los metadatos necesarios
    para el diligenciamiento externo junto con los catálogos requeridos.
    """
    resultado = OBTENER_token_formulario_db(token)
    if not resultado.get("valido"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=resultado.get("mensaje"))
    return resultado


@router.post("/publico/formulario-temporal/{token}/subir-documento", status_code=status.HTTP_201_CREATED)
async def SUBIR_documento_formulario_temporal_rt(
    token: str,
    file: UploadFile = File(...),
    tipo_documento: str = Form("general")
):
    """
    Ruta pública segura: Permite a un tercero adjuntar documentos requeridos
    (cédula, ARL, SOAT, exámenes) validando que el token temporal esté activo.
    """
    val = OBTENER_token_formulario_db(token)
    if not val.get("valido"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=val.get("mensaje"))

    tipo_norm = str(tipo_documento).strip().lower()
    subcarpeta = MAPEO_SUBDIRECTORIOS.get(tipo_norm, "general")
    archivo_guardado = await guardar_documento_seguro(file, subcarpeta=subcarpeta)

    return {
        "exito": True,
        "mensaje": f"Archivo guardado exitosamente en la categoría '{subcarpeta}'.",
        "nombre_archivo": archivo_guardado["nombre_archivo"],
        "url_documento": archivo_guardado["url_documento"],
        "nombre_original": archivo_guardado["nombre_original"],
        "categoria": subcarpeta,
    }


@router.post("/publico/formulario-temporal/{token}/personas", status_code=status.HTTP_200_OK)
def GUARDAR_persona_formulario_temporal_rt(token: str, payload: dict = Body(...)):
    """
    Ruta pública segura: Permite a un tercero registrar o actualizar una persona
    durante el diligenciamiento del formulario temporal.
    """
    val = OBTENER_token_formulario_db(token)
    if not val.get("valido"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=val.get("mensaje"))

    from src.loaders.personas_loader import CREATE_person_db, UPDATE_person_db, GET_person_by_id_db

    nombre = str(payload.get("nombre") or payload.get("nombres") or "").strip()
    apellido = str(payload.get("apellido") or payload.get("apellidos") or "").strip()
    tipo_doc = str(payload.get("tipo_doc") or payload.get("tipoDoc") or "CC").strip().upper()
    identificacion = str(payload.get("identificacion") or payload.get("numDoc") or "").strip()
    cargo = str(payload.get("cargo") or "Personal").strip()
    correo = str(payload.get("correo") or "").strip().lower()
    observacion = str(payload.get("observacion") or "").strip()
    docs_raw = payload.get("documentos_ids") or payload.get("documentos") or []

    docs_clean = []
    for d in docs_raw:
        if isinstance(d, dict) and d.get("nombre_archivo"):
            t_doc = str(d.get("tipo_doc") or "Documento").strip()
            if t_doc in ("Otro documento", "Otro") and d.get("tipo_doc_otro"):
                t_doc = str(d.get("tipo_doc_otro")).strip()
            docs_clean.append({
                "tipo_doc": t_doc,
                "nombre_archivo": str(d.get("nombre_archivo")).strip(),
                "vigencia": d.get("vigencia") or None
            })

    p_data = {
        "nombre": nombre,
        "apellido": apellido,
        "tipo_doc": tipo_doc,
        "identificacion": identificacion,
        "cargo": cargo,
        "correo": correo,
        "observacion": observacion,
        "documentos_ids": docs_clean
    }

    p_id = payload.get("id")
    target_id = None
    if p_id and str(p_id).isdigit() and int(p_id) > 0:
        res = UPDATE_person_db(int(p_id), p_data)
        target_id = int(p_id)
    else:
        from database import GET_conexion
        existing_id = None
        try:
            with GET_conexion() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM personas WHERE identificacion = %s LIMIT 1", (identificacion,))
                    row = cur.fetchone()
                    if row:
                        existing_id = row["id"]
        except Exception:
            pass

        if existing_id:
            res = UPDATE_person_db(existing_id, p_data)
            target_id = existing_id
        else:
            res = CREATE_person_db(p_data)
            target_id = res.get("persona")

    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje", "Error al guardar persona."))

    fresh = GET_person_by_id_db(target_id)
    return {
        "exito": True,
        "mensaje": res.get("mensaje", "Persona guardada correctamente."),
        "id": target_id,
        "persona": fresh.get("datos") or fresh.get("persona") or {"id": target_id, **p_data}
    }


@router.post("/publico/formulario-temporal/{token}/vehiculos", status_code=status.HTTP_200_OK)
def GUARDAR_vehiculo_formulario_temporal_rt(token: str, payload: dict = Body(...)):
    """
    Ruta pública segura: Permite a un tercero registrar o actualizar un vehículo
    durante el diligenciamiento del formulario temporal.
    """
    val = OBTENER_token_formulario_db(token)
    if not val.get("valido"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=val.get("mensaje"))

    import re
    from src.loaders.vehiculo_loader import CREATE_vehiculo_db, UPDATE_vehiculo_db, GET_vehiculo_by_id_db

    placa = re.sub(r"[^A-Z0-9]", "", str(payload.get("placa") or "").strip().upper())
    tipo = str(payload.get("tipo") or payload.get("tipo_vehiculo") or "Camioneta").strip()
    conductor = str(payload.get("conductor") or payload.get("conductor_nombre") or "").strip()
    licencia_doc = str(payload.get("licencia_doc") or "").strip()
    docs_raw = payload.get("documentos") or payload.get("documentos_ids") or []

    docs_clean = []
    for d in docs_raw:
        if isinstance(d, dict) and (d.get("nombre_archivo") or d.get("nom_documento")):
            t_doc = str(d.get("tipo_doc") or "SOAT").strip()
            if t_doc in ("Otro documento", "Otro") and d.get("tipo_doc_otro"):
                t_doc = str(d.get("tipo_doc_otro")).strip()
            docs_clean.append({
                "tipo_doc": t_doc,
                "nom_documento": str(d.get("nombre_archivo") or d.get("nom_documento")).strip()
            })

    v_data = {
        "placa": placa,
        "tipo": tipo,
        "conductor": conductor,
        "licencia_doc": licencia_doc,
        "documentos": docs_clean
    }

    v_id = payload.get("id")
    target_id = None
    if v_id and str(v_id).isdigit() and int(v_id) > 0:
        res = UPDATE_vehiculo_db(int(v_id), v_data)
        target_id = int(v_id)
    else:
        res = CREATE_vehiculo_db(v_data)
        if res.get("exito"):
            target_id = res.get("id")
        elif res.get("duplicado") and res.get("data", {}).get("id"):
            target_id = int(res["data"]["id"])
            res = UPDATE_vehiculo_db(target_id, v_data)

    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje", "Error al guardar vehículo."))

    fresh = GET_vehiculo_by_id_db(target_id)
    return {
        "exito": True,
        "mensaje": res.get("mensaje", "Vehículo guardado correctamente."),
        "id": target_id,
        "vehiculo": fresh.get("datos") or {"id": target_id, **v_data}
    }


@router.post("/publico/formulario-temporal/{token}/enviar", status_code=status.HTTP_201_CREATED)
def ENVIAR_formulario_temporal_publico_rt(token: str, payload: SolicitudInput):
    """
    Ruta pública: Radica la solicitud completada por el tercero.
    - Se almacena con estado 'PRE-ENVIADO'.
    - Se asigna como responsable al usuario Solicitante que creó el token.
    - Se marca el token temporal como consumido.
    - Notifica internamente al Solicitante para su aprobación.
    """
    val = OBTENER_token_formulario_db(token)
    if not val.get("valido"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=val.get("mensaje"))

    solicitante_id = val.get("solicitante_id")
    datos_raw = payload.model_dump()
    datos_raw["id_usuario"] = solicitante_id
    datos_raw["diligenciado_por"] = solicitante_id
    datos_raw["estado"] = "PRE-ENVIADO"

    # Priorizar la empresa contratista definida en el pase temporal
    if val.get("id_empresa_contratista"):
        datos_raw["empresa_contratista"] = val["id_empresa_contratista"]
    elif not datos_raw.get("empresa_contratista") and val.get("contratista_nombre"):
        from database import GET_conexion
        try:
            with GET_conexion() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id FROM emp_contratista WHERE LOWER(TRIM(nombre)) = %s LIMIT 1",
                        (str(val.get("contratista_nombre")).strip().lower(),)
                    )
                    row = cur.fetchone()
                    if row:
                        datos_raw["empresa_contratista"] = row["id"]
        except Exception:
            pass

    datos_limpios = transformar_solicitud(datos_raw)
    datos_limpios["estado"] = "PRE-ENVIADO"
    datos_limpios["diligenciado_por"] = solicitante_id
    if datos_raw.get("empresa_contratista"):
        datos_limpios["empresa_contratista"] = datos_raw["empresa_contratista"]

    resultado = CREATE_solicitud_bd(datos_limpios)
    if not resultado.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.get("mensaje", "Error al radicar solicitud."))

    id_gen = resultado.get("id_generado") or (resultado.get("ids_generados") or [None])[0]
    if id_gen:
        MARCAR_token_usado_db(token=token, id_solicitud=id_gen)

    return {
        "exito": True,
        "mensaje": "Formulario radicado con éxito en estado PRE-ENVIADO. El solicitante responsable revisará y autorizará el envío formal.",
        "codigo": resultado.get("codigo"),
        "codigos_generados": resultado.get("codigos_generados"),
        "id_generado": id_gen
    }


@router.post("/{solicitud_id}/aprobar-envio", status_code=status.HTTP_200_OK)
def APROBAR_envio_solicitud_rt(
    solicitud_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Ruta autenticada: Permite al Solicitante responsable aprobar la solicitud en estado
    PRE-ENVIADO, cambiándola oficialmente a ENVIADO e iniciando el flujo de revisión (SST, GESCO, SCR).
    """
    user_id = current_user.get("id")
    id_rol = current_user.get("id_rol")
    rol_nom = str(current_user.get("rol") or current_user.get("nombre_rol") or "").strip().upper()
    es_admin = (id_rol in (1, 2)) or ("ADMIN" in rol_nom)

    resultado = APROBAR_envio_solicitud_db(solicitud_id=solicitud_id, id_usuario=user_id, es_admin=es_admin)
    if not resultado.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.get("mensaje"))

    return resultado
