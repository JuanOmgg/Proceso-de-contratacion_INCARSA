from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query, Depends, Response, Request
from src.schemas.inducciones_schema import InduccionUpdate
from src.utils.security import get_current_user
from src.services.certificado_induccion_service import (
    OBTENER_DATOS_CERTIFICADO_DB,
    GENERAR_PDF_CERTIFICADO_INDUCCION
)
from src.services.inducciones import (
    OBTENER_INDUCCION_PERSONA,
    ACTUALIZAR_INDUCCION,
    LISTAR_TODAS_INDUCCIONES
)

router = APIRouter(prefix="/inducciones", tags=["Inducciones"])


def _validar_rol_induccion(current_user: dict):
    rol = str(current_user.get("rol") or current_user.get("nombre_rol") or "").strip().upper()
    id_rol = int(current_user.get("id_rol") or 0)
    roles_permitidos = ["GESCO", "SCR", "ADMINISTRADOR", "ADMIN", "SUPERADMIN", "SST", "SOLICITANTE"]
    if id_rol in [1, 2, 4, 5, 6, 7, 8] or any(r in rol for r in roles_permitidos):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para consultar o modificar vigencias de inducción."
    )


@router.get("/getAll", status_code=status.HTTP_200_OK)
@router.get("/getall", status_code=status.HTTP_200_OK)
@router.get("", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK, include_in_schema=False)
def GET_ALL_inducciones_endpoint(current_user: dict = Depends(get_current_user)):
    """
    Lista el estado de inducción de todas las personas registradas en el sistema.
    """
    _validar_rol_induccion(current_user)
    resultado = LISTAR_TODAS_INDUCCIONES()
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al listar inducciones.")
        )
    return resultado.get("datos", [])


@router.get("/persona/{persona_id}", status_code=status.HTTP_200_OK)
def GET_induccion_persona_endpoint(
    persona_id: int,
    auto_renovar: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene la vigencia y datos de inducción de una persona.
    Permitido para GESCO, SCR, Administrador y Superadmin.
    """
    _validar_rol_induccion(current_user)
    resultado = OBTENER_INDUCCION_PERSONA(persona_id, auto_renovar=auto_renovar)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado.get("mensaje", "No se encontró el registro de inducción.")
        )
    return resultado["datos"]


from database import GET_conexion


def _obtener_nombre_auditor_gesco(current_user: dict) -> str:
    """
    Obtiene el nombre real del usuario de GESCO/sistema que realiza la renovación.
    Consulta en la tabla usuarios por su ID si no está completo en el token.
    """
    user_id = current_user.get("sub") or current_user.get("id")
    if user_id:
        try:
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

    # Fallback si no se encontró en DB
    nombre_token = f"{current_user.get('nombre') or current_user.get('nombres') or ''} {current_user.get('apellido') or current_user.get('apellidos') or ''}".strip()
    return nombre_token or current_user.get("correo") or "Auditor GESCO"


@router.patch("/persona/{persona_id}", status_code=status.HTTP_200_OK)
def PATCH_induccion_persona_endpoint(
    persona_id: int,
    payload: InduccionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza la inducción o renueva su vigencia a 1 año.
    Siempre asigna como auditor responsable al usuario de GESCO en sesión que renueva.
    """
    _validar_rol_induccion(current_user)
    auditor_responsable = _obtener_nombre_auditor_gesco(current_user)
    payload.responsable = auditor_responsable
    resultado = ACTUALIZAR_INDUCCION(persona_id, payload, responsable_defecto=auditor_responsable)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al actualizar la inducción.")
        )
    return {"exito": True, "mensaje": resultado["mensaje"], "auditor": auditor_responsable}


@router.post("/persona/{persona_id}/renovar", status_code=status.HTTP_200_OK)
def POST_renovar_induccion_endpoint(
    persona_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Renueva inmediatamente la inducción a 1 año desde hoy.
    Siempre asigna como auditor responsable al usuario de GESCO en sesión que renueva.
    """
    _validar_rol_induccion(current_user)
    auditor_responsable = _obtener_nombre_auditor_gesco(current_user)
    resultado = ACTUALIZAR_INDUCCION(persona_id, InduccionUpdate(responsable=auditor_responsable), responsable_defecto=auditor_responsable)
    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al renovar la inducción.")
        )
    return {"exito": True, "mensaje": "Inducción renovada exitosamente (+1 año de vigencia).", "auditor": auditor_responsable}


import io
import zipfile

EMPRESAS_GRUPO = ["INCARSA", "CARBOINSA", "UNIMINAS", "MILPA"]


@router.get("/persona/{persona_id}/certificado/zip", status_code=status.HTTP_200_OK)
@router.get("/persona/{persona_id}/certificado", status_code=status.HTTP_200_OK)
def GET_certificado_persona_endpoint(
    persona_id: int,
    id_form: Optional[int] = None,
    empresa: Optional[str] = None,
    formato: Optional[str] = None,
    descargar: bool = False,
    request: Request = None
):
    """
    Genera y descarga el Certificado Oficial de Inducción para una persona:
    - Permite seleccionar la empresa (INCARSA, CARBOINSA, UNIMINAS, MILPA).
    - Permite generar un archivo ZIP con los certificados de las 4 empresas del grupo.
    - Si no se especifica 'id_form', toma el formulario de su última inducción o evaluación aprobada.
    """
    # Sanitización robusta de parámetros
    target_form_id = id_form if isinstance(id_form, int) else (int(id_form) if (isinstance(id_form, str) and str(id_form).isdigit()) else None)
    empresa_clean = str(empresa).strip() if isinstance(empresa, str) else None
    formato_clean = str(formato).strip().lower() if isinstance(formato, str) else None
    descargar_bool = bool(descargar) if isinstance(descargar, bool) else (str(descargar).lower() in ("true", "1"))

    if not target_form_id:
        try:
            with GET_conexion() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id_formulario
                        FROM inducciones
                        WHERE id_persona = %s AND id_formulario IS NOT NULL
                        ORDER BY fecha_vigencia DESC
                        LIMIT 1
                        """,
                        (persona_id,)
                    )
                    row = cursor.fetchone()
                    if row and row.get("id_formulario"):
                        target_form_id = row["id_formulario"]
                    else:
                        cursor.execute(
                            """
                            SELECT id_formulario
                            FROM resultados_formulario
                            WHERE id_persona = %s AND estado = 1
                            ORDER BY fecha_realizacion DESC
                            LIMIT 1
                            """,
                            (persona_id,)
                        )
                        r_row = cursor.fetchone()
                        if r_row:
                            target_form_id = r_row["id_formulario"]
        except Exception as e:
            print(f"⚠️ Error buscando formulario de inducción: {e}")

    if not target_form_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La persona no tiene un formulario de inducción aprobado o registrado."
        )

    # Detectar si se solicitó ZIP con las 4 empresas
    es_zip = False
    if request and hasattr(request, "url") and request.url.path.endswith("/zip"):
        es_zip = True
    elif empresa_clean and empresa_clean.upper() in ["TODAS", "ZIP", "ALL", "TODOS"]:
        es_zip = True
    elif formato_clean == "zip":
        es_zip = True

    base_url = str(request.base_url) if request and hasattr(request, "base_url") else ""

    if es_zip:
        # Generar ZIP con certificados para las 4 empresas del grupo
        zip_buffer = io.BytesIO()
        nombre_persona_safe = "Persona"
        doc_num_safe = ""

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for emp_nombre in EMPRESAS_GRUPO:
                res_datos = OBTENER_DATOS_CERTIFICADO_DB(
                    id_formulario=target_form_id,
                    id_persona=persona_id,
                    empresa=emp_nombre
                )
                if not res_datos.get("exito"):
                    continue

                nombre_persona_safe = "".join(c for c in res_datos.get("nombre_persona", "Persona") if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
                doc_num_safe = str(res_datos.get("numero_documento") or "").strip()

                try:
                    pdf_bytes = GENERAR_PDF_CERTIFICADO_INDUCCION(res_datos, base_url=base_url)
                    pdf_filename = f"Certificado_Induccion_{nombre_persona_safe}_{doc_num_safe}_{emp_nombre}.pdf" if doc_num_safe else f"Certificado_Induccion_{nombre_persona_safe}_{emp_nombre}.pdf"
                    zip_file.writestr(pdf_filename, pdf_bytes)
                except Exception as e:
                    print(f"⚠️ Error generando PDF {emp_nombre} en ZIP: {e}")

        zip_data = zip_buffer.getvalue()
        if not zip_data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudieron generar los certificados para el archivo ZIP.")

        zip_filename = f"Certificados_Induccion_{nombre_persona_safe}_{doc_num_safe}_GRUPO_EMPRESARIAL.zip" if doc_num_safe else f"Certificados_Induccion_{nombre_persona_safe}_GRUPO_EMPRESARIAL.zip"
        return Response(
            content=zip_data,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )

    # Caso PDF individual
    res_datos = OBTENER_DATOS_CERTIFICADO_DB(
        id_formulario=target_form_id,
        id_persona=persona_id,
        empresa=empresa_clean
    )

    if not res_datos.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res_datos.get("mensaje"))

    try:
        pdf_bytes = GENERAR_PDF_CERTIFICADO_INDUCCION(res_datos, base_url=base_url)
    except Exception as e:
        print(f"❌ Error generando PDF de inducción: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    safe_name = "".join(c for c in res_datos.get("nombre_persona", "Persona") if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    doc_num = str(res_datos.get("numero_documento") or "").strip()
    emp_upper = empresa_clean.upper() if empresa_clean else ""
    emp_tag = f"_{emp_upper}" if emp_upper in EMPRESAS_GRUPO else ""
    filename = f"Certificado_Induccion_{safe_name}_{doc_num}{emp_tag}.pdf" if doc_num else f"Certificado_Induccion_{safe_name}{emp_tag}.pdf"
    disposition = "attachment" if descargar_bool else "inline"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )

