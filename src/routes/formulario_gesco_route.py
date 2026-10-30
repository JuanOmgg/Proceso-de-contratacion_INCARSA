import io
import os
import shutil
import uuid
import zipfile
import base64
import re
import time
from fastapi import APIRouter, HTTPException, status, Query, Depends, Response, Request, UploadFile, File
from typing import Optional, List
from datetime import datetime
from src.services.certificado_induccion_service import (
    OBTENER_DATOS_CERTIFICADO_DB,
    GENERAR_PDF_CERTIFICADO_INDUCCION
)
from src.schemas.formulario_gesco_schema import (
    FormularioGescoInput,
    FormularioGescoUpdate,
    FormularioGescoResponse
)
from src.utils.security import get_current_user
from src.loaders.formulario_gesco_loader import (
    GET_formularios_gesco_db,
    GET_formulario_gesco_por_id_db,
    CREATE_formulario_gesco_db,
    UPDATE_formulario_gesco_db,
    DELETE_formulario_gesco_db,
    slugify_formulario
)
from src.schemas.pregunta_schema import PreguntaInput, PreguntasSyncPayload
from src.loaders.pregunta_loader import (
    GET_preguntas_por_formulario_db,
    CREATE_pregunta_db,
    SYNC_preguntas_formulario_db
)

router = APIRouter(prefix="/formularios-gesco", tags=["Formularios GESCO"])


import unicodedata


def _sanitizar_nombre_archivo(texto: str) -> str:
    if not texto:
        return "Persona"
    nfkd = unicodedata.normalize('NFKD', str(texto))
    ascii_text = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    safe = "".join(c for c in ascii_text if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    return safe or "Persona"


def _validar_acceso_gesco(current_user: dict):
    rol = str(current_user.get("rol") or current_user.get("nombre_rol") or "").strip().upper()
    id_rol = int(current_user.get("id_rol") or 0)
    roles_permitidos = ["GESCO", "ADMINISTRADOR", "ADMIN", "SUPERADMIN", "SCR"]
    if id_rol in [1, 2, 4, 7, 8] or any(r in rol for r in roles_permitidos):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para administrar formularios de GESCO."
    )


def _obtener_nombre_creador(current_user: dict) -> str:
    """
    Obtiene el nombre completo del usuario que crea el formulario.
    """
    user_id = current_user.get("sub") or current_user.get("id")
    if user_id:
        try:
            from database import GET_conexion
            with GET_conexion() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        "SELECT nombres, apellidos, correo FROM usuarios WHERE id = %s",
                        (user_id,)
                    )
                    u = cursor.fetchone()
                    if u:
                        nombre_completo = f"{u.get('nombres') or ''} {u.get('apellidos') or ''}".strip()
                        if nombre_completo:
                            return nombre_completo
                        if u.get("correo"):
                            return u["correo"]
        except Exception:
            pass

    nombre_token = f"{current_user.get('nombre') or current_user.get('nombres') or ''} {current_user.get('apellido') or current_user.get('apellidos') or ''}".strip()
    return nombre_token or current_user.get("correo") or "Auditor GESCO"


@router.get("/getAll", status_code=status.HTTP_200_OK)
@router.get("/getall", status_code=status.HTTP_200_OK)
@router.get("", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK, include_in_schema=False)
def LISTAR_formularios_gesco(
    tipo_personal: Optional[str] = Query(None, description="Filtrar por tipo de personal"),
    solo_activos: bool = Query(False, description="Filtrar solo formularios activos"),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista todos los formularios GESCO registrados.
    """
    res = GET_formularios_gesco_db(tipo_personal=tipo_personal, solo_activos=solo_activos)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res.get("datos", [])


@router.get("/{id_form}", status_code=status.HTTP_200_OK)
def OBTENER_formulario_gesco(id_form: str):
    """
    Obtiene los metadatos generales de un formulario GESCO por su ID numérico, nombre o slug amigable.
    Acceso público para permitir que el portal de inducción/evaluación cargue el título,
    descripción y vigencia sin exigir login administrativo.
    """
    res = GET_formulario_gesco_por_id_db(id_form)
    if not res.get("exito") or not res.get("datos"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res.get("mensaje", "Formulario no encontrado."))
    return res["datos"]


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def CREAR_formulario_gesco(
    payload: FormularioGescoInput,
    current_user: dict = Depends(get_current_user)
):
    """
    Crea un nuevo formulario GESCO de inducción asignando al creador responsable.
    """
    _validar_acceso_gesco(current_user)
    payload_dict = payload.model_dump()
    user_id = current_user.get("sub") or current_user.get("id")
    if user_id:
        try:
            payload_dict["id_creador"] = int(user_id)
        except (ValueError, TypeError):
            payload_dict["id_creador"] = None
    payload_dict["creador_nombre"] = _obtener_nombre_creador(current_user)
    res = CREATE_formulario_gesco_db(payload_dict)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.patch("/{id_form}/toggle-activo", status_code=status.HTTP_200_OK)
def TOGGLE_ACTIVO_formulario_gesco(
    id_form: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Alterna el estado activo/inactivo de un formulario GESCO.
    """
    _validar_acceso_gesco(current_user)
    form_res = GET_formulario_gesco_por_id_db(id_form)
    if not form_res.get("exito") or not form_res.get("datos"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulario no encontrado.")
    nuevo_estado = not bool(form_res["datos"].get("is_active"))
    res = UPDATE_formulario_gesco_db(id_form, {"is_active": nuevo_estado})
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return {
        "exito": True,
        "mensaje": f"Formulario {'activado' if nuevo_estado else 'desactivado'} exitosamente.",
        "is_active": nuevo_estado
    }


@router.put("/{id_form}", status_code=status.HTTP_200_OK)
@router.patch("/{id_form}", status_code=status.HTTP_200_OK)
def ACTUALIZAR_formulario_gesco(
    id_form: int,
    payload: FormularioGescoUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza datos de un formulario GESCO existente.
    """
    _validar_acceso_gesco(current_user)
    res = UPDATE_formulario_gesco_db(id_form, payload.model_dump(exclude_unset=True))
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.delete("/{id_form}", status_code=status.HTTP_200_OK)
def ELIMINAR_formulario_gesco(
    id_form: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina o desactiva un formulario GESCO.
    """
    _validar_acceso_gesco(current_user)
    res = DELETE_formulario_gesco_db(id_form)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


# ============================================================================
# ENDPOINTS ANIDADOS DE PREGUNTAS POR FORMULARIO
# ============================================================================

@router.get("/{id_form}/preguntas", status_code=status.HTTP_200_OK)
def LISTAR_preguntas_del_formulario(
    id_form: int,
    solo_activas: bool = Query(False, description="Filtrar solo preguntas activas"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene todas las preguntas y opciones de este formulario GESCO.
    """
    res = GET_preguntas_por_formulario_db(id_form, solo_activas=solo_activas)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res.get("mensaje"))
    return res.get("datos", [])


@router.post("/{id_form}/preguntas", status_code=status.HTTP_201_CREATED)
def CREAR_pregunta_en_formulario(
    id_form: int,
    payload: PreguntaInput,
    current_user: dict = Depends(get_current_user)
):
    """
    Crea una nueva pregunta asignada directamente a este formulario GESCO.
    """
    _validar_acceso_gesco(current_user)
    data = payload.model_dump()
    data["id_formulario"] = id_form
    res = CREATE_pregunta_db(data)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.post("/{id_form}/preguntas/sync", status_code=status.HTTP_200_OK)
def SINCRONIZAR_preguntas_del_formulario(
    id_form: int,
    payload: PreguntasSyncPayload,
    current_user: dict = Depends(get_current_user)
):
    """
    Sincroniza en un solo lote todas las preguntas y opciones de este formulario GESCO.
    """
    _validar_acceso_gesco(current_user)
    raw_list = [q.model_dump() for q in payload.preguntas]
    res = SYNC_preguntas_formulario_db(id_form, raw_list)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.post("/upload-imagen", status_code=status.HTTP_201_CREATED)
async def SUBIR_imagen_pregunta(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Sube una imagen de apoyo para una pregunta de formulario GESCO a la carpeta uploads/gesco.
    Admite formatos: PNG, JPG, JPEG, WEBP, SVG, GIF.
    Máximo 15 MB.
    """
    _validar_acceso_gesco(current_user)

    EXTENSIONES_IMAGEN = {"png", "jpg", "jpeg", "webp", "svg", "gif"}
    MAX_BYTES = 15 * 1024 * 1024  # 15 MB

    nombre_original = file.filename or "imagen.png"
    extension = nombre_original.rsplit(".", 1)[-1].lower().strip() if "." in nombre_original else ""

    if extension not in EXTENSIONES_IMAGEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato '.{extension}' no permitido para imágenes. Formatos válidos: PNG, JPG, JPEG, WEBP, SVG, GIF."
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
            detail=f"La imagen supera el tamaño máximo permitido de 15 MB ({round(tamano_bytes / (1024 * 1024), 2)} MB recibidos)."
        )

    if tamano_bytes == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo enviado está vacío.")

    # Directorio destino: uploads/gesco
    raiz_proyecto = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    directorio_destino = os.path.join(raiz_proyecto, "uploads", "gesco")
    os.makedirs(directorio_destino, exist_ok=True)

    nombre_unico = f"gesco_{uuid.uuid4().hex[:12]}.{extension}"
    ruta_fisica = os.path.join(directorio_destino, nombre_unico)

    try:
        with open(ruta_fisica, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error guardando la imagen: {str(e)}")

    url_archivo = f"/uploads/gesco/{nombre_unico}"

    return {
        "exito": True,
        "url_imagen": url_archivo,
        "imagen_url": url_archivo,
        "nombre_archivo": nombre_original,
        "tamano_bytes": tamano_bytes
    }


# ============================================================================
# ENDPOINTS PÚBLICOS DE EVALUACIÓN / INDUCCIÓN CANDIDATOS
# ============================================================================

from pydantic import BaseModel, Field
from database import GET_conexion
from src.loaders.pregunta_loader import (
    CALCULAR_Y_REGISTRAR_EVALUACION_DB,
    SIMULAR_EVALUACION_DB,
    GET_estadisticas_formulario_db
)


@router.get("/{id_form}/estadisticas", status_code=status.HTTP_200_OK)
def OBTENER_estadisticas_formulario(
    id_form: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene las estadísticas y analíticas de presentación de un formulario GESCO:
    - Cantidad total de evaluaciones, personas únicas evaluadas, aprobados y reprobados.
    - Por cada pregunta: porcentaje de aciertos, veces respondida.
    - Por cada opción: cuántas veces ha sido seleccionada y porcentaje de selección.
    - Muestra de respuestas abiertas para preguntas de texto.
    """
    _validar_acceso_gesco(current_user)
    res_f = GET_formulario_gesco_por_id_db(id_form)
    if not res_f.get("exito") or not res_f.get("datos"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Formulario '{id_form}' no encontrado.")
    id_form_real = int(res_f["datos"]["id"])
    res = GET_estadisticas_formulario_db(id_form_real)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res.get("mensaje"))
    return res


class RespuestaEvaluacionItem(BaseModel):
    id_pregunta: int
    id_opcion: Optional[int] = None
    texto_respuesta: Optional[str] = None


class EvaluacionSubmission(BaseModel):
    id_persona: Optional[int] = None
    numero_documento: Optional[str] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    correo: Optional[str] = None
    cargo: Optional[str] = None
    area_sede: Optional[str] = None
    tipo_doc: Optional[str] = "CC"
    foto_en_vivo: Optional[str] = None  # Base64 data URL capturado en vivo por la cámara
    respuestas: List[RespuestaEvaluacionItem]


@router.get("/{id_form}/evaluacion", status_code=status.HTTP_200_OK)
def OBTENER_evaluacion_formulario(
    id_form: str,
    cedula: Optional[str] = Query(None, description="Número de documento de la persona para verificar vigencia previa"),
    id_persona: Optional[int] = Query(None, description="ID de la persona si ya se conoce"),
    simulacion: bool = Query(False, description="Activa el modo de prueba/simulador administrativo")
):
    """
    Endpoint para que el candidato cargue su cuestionario de inducción o para simulación administrativa:
    - En modo normal:
      - Si la persona ya tiene vigencia activa, le notifica inmediatamente sin exigirle examen.
      - Si requiere examen, selecciona aleatoriamente la cantidad configurada en el banco de preguntas.
    - En modo simulación (simulacion=True):
      - Omite verificación de vigencia en BD y entrega una muestra aleatoria para pruebas.
    - Oculta 'is_correct' en las opciones para prevenir trampas.
    """
    res_f = GET_formulario_gesco_por_id_db(id_form)
    if not res_f.get("exito") or not res_f.get("datos"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Formulario '{id_form}' no encontrado.")
    form_meta = res_f["datos"]
    id_form_real = int(form_meta["id"])

    persona_info = None

    # MODO SIMULACIÓN: Inicia directamente con un perfil de prueba administrativo
    if simulacion:
        persona_info = {
            "id": None,
            "nombre": "Administrador",
            "apellido": "(Modo Simulación)",
            "nombres": "Administrador",
            "apellidos": "(Modo Simulación)",
            "identificacion": "SIMULADOR",
            "numero_documento": "SIMULADOR",
            "tipo_doc": "CC",
            "cargo": "Auditor",
            "correo": "admin@incarsa.com"
        }
    else:
        # 1. Comprobar vigencia activa de la persona si se envió cédula o id_persona
        if cedula or id_persona:
            try:
                with GET_conexion() as conexion:
                    with conexion.cursor() as cursor:
                        if id_persona:
                            cursor.execute("SELECT id, nombre, apellido, identificacion, tipo_doc, cargo, correo FROM personas WHERE id = %s", (id_persona,))
                        else:
                            cursor.execute("SELECT id, nombre, apellido, identificacion, tipo_doc, cargo, correo FROM personas WHERE identificacion = %s", (str(cedula).strip(),))
                        persona_info = cursor.fetchone()

                        if persona_info:
                            persona_info["nombres"] = persona_info.get("nombre")
                            persona_info["apellidos"] = persona_info.get("apellido")
                            persona_info["numero_documento"] = persona_info.get("identificacion")
                            persona_info["tipo_doc"] = persona_info.get("tipo_doc") or "CC"
                            persona_info["cargo"] = persona_info.get("cargo") or ""
                            persona_info["correo"] = persona_info.get("correo") or ""
                            pid = persona_info["id"]
                            cursor.execute("""
                                SELECT fecha_vigencia, DATEDIFF(fecha_vigencia, CURDATE()) AS dias_restantes
                                FROM inducciones
                                WHERE id_persona = %s
                                  AND (id_formulario = %s OR id_formulario IS NULL)
                                  AND fecha_vigencia >= CURDATE()
                                ORDER BY fecha_vigencia DESC
                                LIMIT 1
                            """, (pid, id_form_real))
                            vig = cursor.fetchone()
                            if vig:
                                fecha_str = vig["fecha_vigencia"].isoformat() if hasattr(vig["fecha_vigencia"], "isoformat") else str(vig["fecha_vigencia"])
                                return {
                                    "exito": True,
                                    "simulacion": False,
                                    "induccion_activa": True,
                                    "persona": persona_info,
                                    "fecha_vigencia": fecha_str,
                                    "dias_restantes": int(vig.get("dias_restantes") or 0),
                                    "mensaje": f"Hola {persona_info.get('nombre') or ''}, ya cuentas con inducción vigente activa hasta el {fecha_str} ({vig.get('dias_restantes')} días restantes). No es necesario realizar la evaluación."
                                }
            except Exception as e:
                print(f"⚠️ Aviso comprobando vigencia de persona en evaluación: {e}")

    # 2. Generar preguntas aleatorias del banco de preguntas
    res_preguntas = GET_preguntas_por_formulario_db(
        id_formulario=id_form_real,
        solo_activas=False if simulacion else True,
        aleatorio=True,
        ocultar_respuestas_correctas=True
    )
    if not res_preguntas.get("exito"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res_preguntas.get("mensaje"))

    form_meta = res_preguntas.get("formulario") or {}

    # Validar si el formulario tiene una fecha límite y ya venció
    if not simulacion and form_meta.get("fecha_limite"):
        try:
            fl_raw = form_meta["fecha_limite"]
            limite_dt = datetime.fromisoformat(str(fl_raw))
            if limite_dt.hour == 0 and limite_dt.minute == 0 and limite_dt.second == 0:
                limite_dt = limite_dt.replace(hour=23, minute=59, second=59)
            if datetime.now() > limite_dt:
                fecha_formateada = limite_dt.strftime("%d/%m/%Y")
                return {
                    "exito": True,
                    "formulario_expirado": True,
                    "simulacion": False,
                    "induccion_activa": False,
                    "persona": persona_info,
                    "formulario": form_meta,
                    "fecha_limite": fl_raw,
                    "mensaje": f"El plazo de presentación para este formulario finalizó el {fecha_formateada}. No se admiten nuevas respuestas."
                }
        except Exception as e:
            print(f"Aviso comprobando fecha_limite en evaluación: {e}")

    return {
        "exito": True,
        "simulacion": simulacion,
        "induccion_activa": False,
        "formulario_expirado": False,
        "persona": persona_info,
        "formulario": form_meta,
        "total_banco": res_preguntas.get("total_banco", 0),
        "evaluadas": res_preguntas.get("evaluadas", 0),
        "preguntas": res_preguntas.get("datos", [])
    }


@router.post("/{id_form}/evaluar", status_code=status.HTTP_200_OK)
def SUBMIT_evaluacion_formulario(
    id_form: str,
    payload: EvaluacionSubmission
):
    """
    Califica la evaluación presentada por el candidato o trabajador:
    - Valida o registra automáticamente a la persona si es personal interno o no tiene usuario.
    - Valida respuestas contra el banco de preguntas.
    - Si aprueba (>= 80%), actualiza vigencia de inducción a +1 año y activa aprobación automática en GESCO.
    - Registra el resultado histórico en resultados_formulario.
    """
    res_f = GET_formulario_gesco_por_id_db(id_form)
    if not res_f.get("exito") or not res_f.get("datos"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Formulario '{id_form}' no encontrado.")
    id_form_real = int(res_f["datos"]["id"])
    nombre_form_raw = res_f["datos"].get("nombre") or f"formulario_{id_form_real}"
    clean_form_name = re.sub(r"[^\w\-]", "_", slugify_formulario(nombre_form_raw)).strip("_") or f"form_{id_form_real}"

    target_persona_id = payload.id_persona
    doc_clean = str(payload.numero_documento or "").strip()

    es_interno_form = False
    datos_participante_interno = None

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # Comprobar límite de fecha del formulario y si es interno
                cursor.execute("SELECT fecha_limite, nombre, es_interno, tipo_personal FROM formularioGesco WHERE id = %s", (id_form_real,))
                form_row = cursor.fetchone()
                if form_row:
                    es_interno_form = bool(form_row.get("es_interno")) or "interno" in str(form_row.get("tipo_personal") or "").lower()
                    if form_row.get("nombre"):
                        clean_form_name = re.sub(r"[^\w\-]", "_", slugify_formulario(form_row["nombre"])).strip("_") or clean_form_name
                    if form_row.get("fecha_limite"):
                        fl_dt = form_row["fecha_limite"]
                        if isinstance(fl_dt, str):
                            fl_dt = datetime.fromisoformat(fl_dt)
                        if fl_dt.hour == 0 and fl_dt.minute == 0 and fl_dt.second == 0:
                            fl_dt = fl_dt.replace(hour=23, minute=59, second=59)
                        if datetime.now() > fl_dt:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"El plazo para responder este formulario finalizó el {fl_dt.strftime('%d/%m/%Y')}."
                            )

                row = None
                if target_persona_id:
                    cursor.execute("SELECT id, nombre, apellido, correo, cargo, identificacion FROM personas WHERE id = %s", (target_persona_id,))
                    row = cursor.fetchone()
                    if row and not doc_clean and row.get("identificacion"):
                        doc_clean = str(row["identificacion"]).strip()
                elif doc_clean:
                    cursor.execute("SELECT id, nombre, apellido, correo, cargo, identificacion FROM personas WHERE identificacion = %s", (doc_clean,))
                    row = cursor.fetchone()

                if row:
                    target_persona_id = row["id"]
                    # Actualizar datos si venían vacíos
                    updates = []
                    u_vals = []
                    if payload.nombre and not row.get("nombre"):
                        updates.append("nombre = %s")
                        u_vals.append(str(payload.nombre).strip())
                    if payload.apellido and not row.get("apellido"):
                        updates.append("apellido = %s")
                        u_vals.append(str(payload.apellido).strip())
                    if payload.correo and not row.get("correo"):
                        updates.append("correo = %s")
                        u_vals.append(str(payload.correo).strip())
                    if payload.cargo and not row.get("cargo"):
                        updates.append("cargo = %s")
                        u_vals.append(str(payload.cargo).strip())
                    if updates:
                        u_vals.append(target_persona_id)
                        cursor.execute(f"UPDATE personas SET {', '.join(updates)} WHERE id = %s", tuple(u_vals))
                        conexion.commit()

                # Para formularios internos: estructurar datos específicos en tabla aparte
                if es_interno_form:
                    datos_participante_interno = {
                        "numero_documento": doc_clean or str(target_persona_id or "0"),
                        "tipo_doc": payload.tipo_doc or "CC",
                        "nombre": (payload.nombre or (row.get("nombre") if row else "Trabajador")).strip(),
                        "apellido": (payload.apellido or (row.get("apellido") if row else "")).strip(),
                        "correo": (payload.correo or (row.get("correo") if row else "")).strip(),
                        "cargo": (payload.cargo or (row.get("cargo") if row else "Personal Interno")).strip(),
                        "area_sede": (payload.area_sede or "").strip()
                    }
                elif not row:
                    # Formulario de contratistas/externos: Registrar automáticamente en personas si no existe
                    if not doc_clean and not payload.nombre:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Se requiere el número de documento y nombre de la persona para registrar la evaluación."
                        )
                    nom = str(payload.nombre or "Trabajador").strip()[:50]
                    ape = str(payload.apellido or "").strip()[:50]
                    tdoc = str(payload.tipo_doc or "CC").strip().upper()[:70]
                    cgo = str(payload.cargo or "Personal Interno").strip()[:30]
                    cor = (str(payload.correo or "").strip()[:255]) or None
                    
                    solo_digitos = re.sub(r"\D", "", doc_clean)
                    if solo_digitos:
                        try:
                            ident_val = int(solo_digitos)
                            if ident_val > 2147483647:
                                ident_val = int(str(ident_val)[-9:])
                        except (ValueError, OverflowError):
                            ident_val = int(str(int(time.time()))[-9:])
                    else:
                        ident_val = int(str(int(time.time()))[-9:])

                    cursor.execute(
                        """
                        INSERT INTO personas (nombre, apellido, tipo_doc, identificacion, cargo, correo, fecha_creacion)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        """,
                        (nom, ape, tdoc, ident_val, cgo, cor)
                    )
                    conexion.commit()
                    target_persona_id = cursor.lastrowid
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error al resolver o registrar persona en evaluacion: {e}")

    if not target_persona_id and not datos_participante_interno:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere un número de documento para registrar la evaluación."
        )

    # Procesar y guardar foto de evidencia con formato: {numero_documento}_{nombre_formulario}_{timestamp}.jpg
    foto_url = None
    if payload.foto_en_vivo and "base64," in payload.foto_en_vivo:
        try:
            header, encoded = payload.foto_en_vivo.split("base64,", 1)
            data_bytes = base64.b64decode(encoded)
            if len(data_bytes) < 8 * 1024 * 1024:
                folder_path = os.path.join("uploads", "gesco", "evidencias")
                os.makedirs(folder_path, exist_ok=True)
                doc_for_file = re.sub(r"[^\w\-]", "", doc_clean or str(target_persona_id or "participante")).strip("_")
                filename = f"{doc_for_file}_{clean_form_name}_{int(time.time())}.jpg"
                file_path = os.path.join(folder_path, filename)
                with open(file_path, "wb") as f_out:
                    f_out.write(data_bytes)
                foto_url = f"/uploads/gesco/evidencias/{filename}"
        except Exception as e_foto:
            print(f"⚠️ Error al guardar foto de evidencia en vivo: {e_foto}")

    respuestas_dict = [r.model_dump() for r in payload.respuestas]
    res = CALCULAR_Y_REGISTRAR_EVALUACION_DB(
        id_formulario=id_form_real,
        id_persona=target_persona_id,
        respuestas=respuestas_dict,
        foto_evidencia_url=foto_url,
        datos_participante_interno=datos_participante_interno
    )

    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))

    return res


@router.post("/{id_form}/simular", status_code=status.HTTP_200_OK)
def SIMULAR_evaluacion_formulario(
    id_form: str,
    payload: EvaluacionSubmission
):
    """
    Simula la calificación de una evaluación GESCO en memoria (Modo Prueba).
    - No requiere cédula real ni id_persona en la base de datos.
    - Valida respuestas contra el banco de preguntas.
    - No altera tablas de inducciones, solicitudes ni resultados_formulario.
    - Entrega desglose detallado con opciones correctas para verificar el funcionamiento.
    """
    res_f = GET_formulario_gesco_por_id_db(id_form)
    if not res_f.get("exito") or not res_f.get("datos"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Formulario '{id_form}' no encontrado.")
    id_form_real = int(res_f["datos"]["id"])

    respuestas_dict = [r.model_dump() for r in payload.respuestas]
    res = SIMULAR_EVALUACION_DB(id_form_real, respuestas_dict)

    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))

    return res


# ============================================================================
# ENDPOINT DE GENERACIÓN / DESCARGA DE CERTIFICADOS DE INDUCCIÓN
# ============================================================================

@router.get("/{id_form}/certificado", status_code=status.HTTP_200_OK)
@router.get("/{id_form}/certificado/{id_persona}", status_code=status.HTTP_200_OK)
def OBTENER_CERTIFICADO_INDUCCION_ENDPOINT(
    id_form: int,
    id_persona: Optional[int] = None,
    cedula: Optional[str] = Query(None, description="Número de documento de la persona"),
    empresa: Optional[str] = Query(None, description="Empresa para la plantilla: INCARSA, CARBOINSA, UNIMINAS, MILPA"),
    simulacion: bool = Query(False, description="Genera certificado en modo prueba/simulación"),
    descargar: bool = Query(False, description="Fuerza descarga como archivo adjunto"),
    request: Request = None
):
    """
    Genera y entrega el Certificado Oficial de Inducción en formato PDF
    estilizado sobre la plantilla institucional de la empresa correspondiente:
    - Incluye Nombre del formulario, Nombre de la persona, Documento, Fecha de aprobación y Fecha de vigencia.
    - Aplica la plantilla PDF corporativa (INCARSA, CARBOINSA, UNIMINAS, MILPA).
    """
    res_datos = OBTENER_DATOS_CERTIFICADO_DB(
        id_formulario=id_form,
        id_persona=id_persona,
        numero_documento=cedula,
        empresa=empresa,
        es_simulacion=simulacion
    )

    if not res_datos.get("exito"):
        msg = res_datos.get("mensaje", "No se pudo generar el certificado.")
        status_code = status.HTTP_404_NOT_FOUND if "no encontrad" in msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=msg)

    base_url = str(request.base_url) if request else ""
    try:
        pdf_bytes = GENERAR_PDF_CERTIFICADO_INDUCCION(res_datos, base_url=base_url)
    except Exception as e:
        print(f"❌ Error al generar PDF de certificado de inducción: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el certificado en PDF: {str(e)}"
        )

    safe_name = _sanitizar_nombre_archivo(res_datos.get("nombre_persona", "Persona"))
    doc_num = str(res_datos.get("numero_documento") or "").strip()
    emp_tag = "".join(c for c in str(res_datos.get("empresa") or "INCARSA") if c.isalnum()).upper()
    filename = f"Certificado_Induccion_{emp_tag}_{safe_name}_{doc_num}.pdf" if doc_num else f"Certificado_Induccion_{emp_tag}_{safe_name}.pdf"
    disposition = "attachment" if descargar else "inline"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )


@router.get("/{id_form}/certificados-zip", status_code=status.HTTP_200_OK)
def DESCARGAR_TODOS_CERTIFICADOS_ZIP_ENDPOINT(
    id_form: int,
    id_persona: Optional[int] = None,
    cedula: Optional[str] = Query(None, description="Número de documento de la persona"),
    simulacion: bool = Query(False, description="Genera certificados en modo prueba/simulación"),
    request: Request = None
):
    """
    Genera y entrega un archivo comprimido .ZIP con las constancias oficiales
    de inducción personalizadas para las 4 empresas: INCARSA, CARBOINSA, UNIMINAS y MILPA.
    """
    empresas = ["INCARSA", "CARBOINSA", "UNIMINAS", "MILPA"]
    zip_buffer = io.BytesIO()
    base_url = str(request.base_url) if request else ""
    persona_nombre = "Persona"
    doc_num = ""

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for emp in empresas:
            res_datos = OBTENER_DATOS_CERTIFICADO_DB(
                id_formulario=id_form,
                id_persona=id_persona,
                numero_documento=cedula,
                empresa=emp,
                es_simulacion=simulacion
            )
            if not res_datos.get("exito"):
                continue
            persona_nombre = res_datos.get("nombre_persona", persona_nombre)
            doc_num = str(res_datos.get("numero_documento") or "").strip()
            pdf_bytes = GENERAR_PDF_CERTIFICADO_INDUCCION(res_datos, base_url=base_url)
            safe_name = _sanitizar_nombre_archivo(persona_nombre)
            fname = f"Certificado_Induccion_{emp}_{safe_name}_{doc_num}.pdf" if doc_num else f"Certificado_Induccion_{emp}_{safe_name}.pdf"
            zip_file.writestr(fname, pdf_bytes)

    zip_buffer.seek(0)
    safe_name = _sanitizar_nombre_archivo(persona_nombre)
    zip_filename = f"Certificados_Induccionx4_{safe_name}_{doc_num}.zip" if doc_num else f"Certificados_Induccionx4_{safe_name}.zip"

    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )

