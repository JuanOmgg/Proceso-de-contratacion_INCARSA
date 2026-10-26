import io
import os
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader, PdfWriter

from database import GET_conexion

# Meses en español
MESES_ES = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
    5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
    9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
}

PALETAS_EMPRESA = {
    "INCARSA": {
        "primary": colors.HexColor("#0f2744"),
        "accent": colors.HexColor("#d9381e"),      # Naranja rojizo corporativo INCARSA
        "secondary": colors.HexColor("#334155"),
        "muted": colors.HexColor("#64748b"),
        "box_border": colors.HexColor("#86efac"),
        "box_bg": colors.HexColor("#f0fdf4"),
        "box_text": colors.HexColor("#166534"),
    },
    "CARBOINSA": {
        "primary": colors.HexColor("#0f2744"),
        "accent": colors.HexColor("#1d4ed8"),      # Azul institucional CARBOINSA
        "secondary": colors.HexColor("#334155"),
        "muted": colors.HexColor("#64748b"),
        "box_border": colors.HexColor("#93c5fd"),
        "box_bg": colors.HexColor("#eff6ff"),
        "box_text": colors.HexColor("#1e40af"),
    },
    "UNIMINAS": {
        "primary": colors.HexColor("#0f2744"),
        "accent": colors.HexColor("#15803d"),      # Verde esmeralda UNIMINAS
        "secondary": colors.HexColor("#334155"),
        "muted": colors.HexColor("#64748b"),
        "box_border": colors.HexColor("#86efac"),
        "box_bg": colors.HexColor("#f0fdf4"),
        "box_text": colors.HexColor("#166534"),
    },
    "MILPA": {
        "primary": colors.HexColor("#0f2744"),
        "accent": colors.HexColor("#dc2626"),      # Rojo carmesí MILPA
        "secondary": colors.HexColor("#334155"),
        "muted": colors.HexColor("#64748b"),
        "box_border": colors.HexColor("#fca5a5"),
        "box_bg": colors.HexColor("#fef2f2"),
        "box_text": colors.HexColor("#991b1b"),
    }
}


def RESOLVER_PLANTILLA_CERTIFICADO(empresa: str, nombre_formulario: str = "") -> str:
    """
    Resuelve la ruta absoluta de la plantilla PDF en 'certificados/'
    según la empresa solicitada y el nombre del formulario.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "certificados"))
    empresa_norm = (empresa or "").strip().upper()
    form_norm = (nombre_formulario or "").strip().upper()

    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"El directorio de plantillas no existe: {base_dir}")

    files = os.listdir(base_dir)

    # 1. CARBOINSA
    if "CARBOINSA" in empresa_norm:
        for f in files:
            if "CARBOINSA" in f.upper() and f.endswith(".pdf"):
                return os.path.join(base_dir, f)

    # 2. UNIMINAS
    if "UNIMINAS" in empresa_norm:
        for f in files:
            if "UNIMINAS" in f.upper() and f.endswith(".pdf"):
                return os.path.join(base_dir, f)

    # 3. MILPA
    if "MILPA" in empresa_norm:
        if "CURSO" in form_norm:
            for f in files:
                if "CURSO" in f.upper() and "MILPA" in f.upper() and f.endswith(".pdf"):
                    return os.path.join(base_dir, f)
        for f in files:
            if "FUNDAC" in f.upper() and "MILPA" in f.upper() and f.endswith(".pdf"):
                return os.path.join(base_dir, f)
        for f in files:
            if "MILPA" in f.upper() and f.endswith(".pdf"):
                return os.path.join(base_dir, f)

    # 4. INCARSA (Por defecto)
    for f in files:
        if "INCARSA" in f.upper() and f.endswith(".pdf"):
            return os.path.join(base_dir, f)

    # 5. Fallback al primer archivo PDF
    for f in files:
        if f.endswith(".pdf"):
            return os.path.join(base_dir, f)

    raise FileNotFoundError("No se encontró ninguna plantilla PDF en la carpeta de certificados.")


def _formatear_fecha_es(fecha_val) -> str:
    """
    Convierte un objeto date, datetime o string a formato legible en mayúsculas:
    Ej: 16 / OCTUBRE / 2026
    """
    if not fecha_val:
        return "N/D"

    if isinstance(fecha_val, str):
        # Intentar parsear ISO o fecha común
        try:
            if "T" in fecha_val:
                fecha_val = datetime.fromisoformat(fecha_val.replace("Z", "+00:00"))
            elif len(fecha_val) >= 10:
                fecha_val = datetime.strptime(fecha_val[:10], "%Y-%m-%d").date()
        except Exception:
            return fecha_val

    if isinstance(fecha_val, (datetime, date)):
        dia = fecha_val.day
        mes = MESES_ES.get(fecha_val.month, str(fecha_val.month))
        anio = fecha_val.year
        return f"{dia:02d} / {mes} / {anio}"

    return str(fecha_val)


def _formatear_documento(tipo_doc: str, num_doc: Any) -> str:
    """
    Formatea el documento de identidad con separador de miles.
    Ej: C.C. No. 1.053.847.291
    """
    tipo = (tipo_doc or "C.C.").strip().upper()
    if not tipo.endswith("."):
        if tipo in ["CC", "TI", "CE", "PA"]:
            tipo = f"{tipo[0]}.{tipo[1]}."

    doc_str = str(num_doc or "").strip()
    if doc_str.isdigit():
        try:
            num_int = int(doc_str)
            doc_str = f"{num_int:,}".replace(",", ".")
        except Exception:
            pass

    return f"{tipo} No. {doc_str}"


def GENERAR_PDF_CERTIFICADO_INDUCCION(datos: Dict[str, Any], base_url: str = "") -> bytes:
    """
    Genera el Certificado / Constancia Oficial de Inducción en PDF:
    - Sobreescribe directamente sobre las plantillas PDF oficiales (960x540 landscape).
    - Incluye Nombre de la persona, Documento, Nombre del Formulario, Fecha de Aprobación y Vigencia.
    - Estampa código QR de validación institucional.
    - Adapta paleta tipográfica según la empresa (INCARSA, CARBOINSA, UNIMINAS, MILPA).
    """
    empresa_nombre = str(datos.get("empresa") or "INCARSA").strip().upper()
    nombre_formulario = str(datos.get("nombre_formulario") or "Inducción General").strip()
    nombre_persona = str(datos.get("nombre_persona") or "Personal Contratista").strip().upper()
    tipo_doc = str(datos.get("tipo_documento") or "C.C.")
    numero_doc = datos.get("numero_documento") or "S/D"
    fecha_aprob = datos.get("fecha_aprobacion")
    fecha_vig = datos.get("fecha_vigencia")
    es_simulacion = bool(datos.get("es_simulacion"))

    # Seleccionar paleta
    empresa_key = "INCARSA"
    for k in ["CARBOINSA", "UNIMINAS", "MILPA"]:
        if k in empresa_nombre:
            empresa_key = k
            break
    paleta = PALETAS_EMPRESA.get(empresa_key, PALETAS_EMPRESA["INCARSA"])

    # Resolver plantilla base
    template_path = RESOLVER_PLANTILLA_CERTIFICADO(empresa_key, nombre_formulario)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Plantilla PDF no encontrada en: {template_path}")

    # Canvas dimensions: 960 x 540 puntos
    width, height = 960, 540
    center_x = 490

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))

    # 1. Header / Título Principal
    can.setFont("Helvetica-Bold", 23)
    can.setFillColor(paleta["primary"])
    can.drawCentredString(center_x, 425, "CONSTANCIA DE APROBACIÓN")

    # 2. Subtítulo
    can.setFont("Helvetica-Bold", 10.5)
    can.setFillColor(paleta["muted"])
    can.drawCentredString(center_x, 400, "EL PROCESO DE GESTIÓN DEL CONOCIMIENTO HACE CONSTAR QUE:")

    # 3. Nombre de la Persona (con ajuste dinámico si es muy largo)
    font_name_size = 26
    str_width_name = can.stringWidth(nombre_persona, "Helvetica-Bold", font_name_size)
    if str_width_name > 520:
        font_name_size = max(18, int(font_name_size * (520 / str_width_name)))

    can.setFont("Helvetica-Bold", font_name_size)
    can.setFillColor(paleta["accent"])
    can.drawCentredString(center_x, 348, nombre_persona)

    # 4. Documento de Identidad
    doc_formateado = _formatear_documento(tipo_doc, numero_doc)
    can.setFont("Helvetica-Bold", 12.5)
    can.setFillColor(paleta["secondary"])
    can.drawCentredString(center_x, 320, doc_formateado)

    # 5. Declaración de Cumplimiento
    can.setFont("Helvetica", 11.5)
    can.setFillColor(paleta["muted"])
    can.drawCentredString(center_x, 280, "Ha completado y aprobado satisfactoriamente los contenidos y la evaluación de:")

    # 6. Nombre del Formulario (con ajuste si es muy largo)
    form_size = 17
    form_str = nombre_formulario.upper()
    form_width = can.stringWidth(form_str, "Helvetica-Bold", form_size)
    if form_width > 540:
        form_size = max(13, int(form_size * (540 / form_width)))

    can.setFont("Helvetica-Bold", form_size)
    can.setFillColor(paleta["primary"])
    can.drawCentredString(center_x, 252, form_str)

    # 7. Línea divisoria elegante
    can.setStrokeColor(colors.HexColor("#e2e8f0"))
    can.setLineWidth(1)
    can.line(center_x - 220, 226, center_x + 220, 226)

    # 8. Cajas Métricas de Fechas (Aprobación y Vigencia)
    box_y = 158
    box_h = 52
    box_w = 180

    fecha_aprob_str = _formatear_fecha_es(fecha_aprob)
    fecha_vig_str = _formatear_fecha_es(fecha_vig)

    # Caja A: Fecha de Aprobación
    can.setFillColor(colors.HexColor("#f8fafc"))
    can.setStrokeColor(colors.HexColor("#cbd5e1"))
    can.roundRect(center_x - 200, box_y, box_w, box_h, 6, fill=1, stroke=1)

    can.setFont("Helvetica-Bold", 8.5)
    can.setFillColor(paleta["muted"])
    can.drawCentredString(center_x - 200 + (box_w / 2), box_y + 34, "FECHA DE APROBACIÓN")

    can.setFont("Helvetica-Bold", 12.5)
    can.setFillColor(paleta["primary"])
    can.drawCentredString(center_x - 200 + (box_w / 2), box_y + 14, fecha_aprob_str)

    # Caja B: Vigencia Hasta
    can.setFillColor(paleta["box_bg"])
    can.setStrokeColor(paleta["box_border"])
    can.roundRect(center_x + 20, box_y, box_w, box_h, 6, fill=1, stroke=1)

    can.setFont("Helvetica-Bold", 8.5)
    can.setFillColor(paleta["box_text"])
    can.drawCentredString(center_x + 20 + (box_w / 2), box_y + 34, "VIGENCIA HASTA")

    can.setFont("Helvetica-Bold", 12.5)
    can.setFillColor(paleta["box_text"])
    can.drawCentredString(center_x + 20 + (box_w / 2), box_y + 14, fecha_vig_str)

    # 9. Leyenda Pie de Página (Sin código QR por solicitud)
    can.setFont("Helvetica", 8)
    can.setFillColor(paleta["muted"])
    leyenda = f"Constancia Digital Certificada · Sistema GESCO · {empresa_key}"
    if es_simulacion:
        leyenda += " (MODO SIMULACIÓN - VISTA PREVIA)"
    can.drawCentredString(center_x, 75, leyenda)

    # Watermark sutil si es simulación
    if es_simulacion:
        can.saveState()
        can.setFont("Helvetica-Bold", 40)
        can.setFillColor(colors.Color(0.8, 0.2, 0.2, alpha=0.10))
        can.drawCentredString(center_x, 270, "SIMULACIÓN / PRUEBA")
        can.restoreState()

    can.save()
    packet.seek(0)

    # Combinar con la plantilla PDF
    template_pdf = PdfReader(template_path)
    overlay_pdf = PdfReader(packet)

    writer = PdfWriter()
    page = template_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer.add_page(page)

    out_buffer = io.BytesIO()
    writer.write(out_buffer)
    out_buffer.seek(0)
    return out_buffer.getvalue()


def OBTENER_DATOS_CERTIFICADO_DB(
    id_formulario: int,
    id_persona: Optional[int] = None,
    numero_documento: Optional[str] = None,
    empresa: Optional[str] = None,
    es_simulacion: bool = False
) -> Dict[str, Any]:
    """
    Consulta la base de datos para extraer los datos verificados de la inducción
    aprobada por la persona y empaqueta el diccionario para el generador PDF.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Obtener Formulario
                cursor.execute(
                    "SELECT id, nombre, vigencia, tipo_personal FROM formulariogesco WHERE id = %s",
                    (id_formulario,)
                )
                form = cursor.fetchone()
                if not form:
                    return {"exito": False, "mensaje": f"Formulario #{id_formulario} no encontrado en el sistema."}

                vigencia_dias = int(form.get("vigencia") or 365)
                nombre_form = form.get("nombre") or "Inducción General"

                # CASO SIMULACIÓN: No exige registros reales en personas ni resultados
                if es_simulacion:
                    today = date.today()
                    return {
                        "exito": True,
                        "es_simulacion": True,
                        "id_formulario": id_formulario,
                        "nombre_formulario": nombre_form,
                        "nombre_persona": "Usuario Administrador (Simulación)",
                        "tipo_documento": "C.C.",
                        "numero_documento": numero_documento or "1.000.000.000",
                        "fecha_aprobacion": today,
                        "fecha_vigencia": today + timedelta(days=vigencia_dias),
                        "empresa": empresa or "INCARSA"
                    }

                # CASO PRODUCCIÓN: Debe existir persona y aprobación registrada
                persona = None
                if id_persona:
                    cursor.execute(
                        "SELECT id, nombre, apellido, tipo_doc, identificacion FROM personas WHERE id = %s",
                        (id_persona,)
                    )
                    persona = cursor.fetchone()
                elif numero_documento:
                    cursor.execute(
                        "SELECT id, nombre, apellido, tipo_doc, identificacion FROM personas WHERE identificacion = %s",
                        (str(numero_documento).strip(),)
                    )
                    persona = cursor.fetchone()

                if not persona:
                    return {
                        "exito": False,
                        "mensaje": "No se encontró a la persona en el sistema con los datos suministrados."
                    }

                pid = persona["id"]
                nombre_completo = f"{persona.get('nombre') or ''} {persona.get('apellido') or ''}".strip()
                tipo_doc = persona.get("tipo_doc") or "C.C."
                num_doc = persona.get("identificacion")

                # 2. Consultar resultado de aprobación en resultados_formulario
                cursor.execute(
                    """
                    SELECT fecha_realizacion, resultado, estado
                    FROM resultados_formulario
                    WHERE id_persona = %s AND id_formulario = %s AND estado = 1
                    ORDER BY fecha_realizacion DESC
                    LIMIT 1
                    """,
                    (pid, id_formulario)
                )
                resultado = cursor.fetchone()

                # 3. Consultar registro de inducción (vigencia activa)
                cursor.execute(
                    """
                    SELECT fecha_induccion, fecha_vigencia, id_empresa
                    FROM inducciones
                    WHERE id_persona = %s AND (id_formulario = %s OR id_formulario IS NULL)
                    ORDER BY fecha_vigencia DESC
                    LIMIT 1
                    """,
                    (pid, id_formulario)
                )
                induccion = cursor.fetchone()

                # Si no hay ni resultado aprobado ni inducción registrada
                if not resultado and not induccion:
                    return {
                        "exito": False,
                        "mensaje": f"La persona {nombre_completo} ({num_doc}) no registra aprobación para el formulario '{nombre_form}'."
                    }

                # Fechas
                fecha_aprobacion = None
                if resultado and resultado.get("fecha_realizacion"):
                    fecha_aprobacion = resultado["fecha_realizacion"]
                elif induccion and induccion.get("fecha_induccion"):
                    fecha_aprobacion = induccion["fecha_induccion"]
                else:
                    fecha_aprobacion = date.today()

                fecha_vigencia = None
                if induccion and induccion.get("fecha_vigencia"):
                    fecha_vigencia = induccion["fecha_vigencia"]
                else:
                    # Calcular sumando vigencia_dias
                    base_date = fecha_aprobacion.date() if isinstance(fecha_aprobacion, datetime) else fecha_aprobacion
                    fecha_vigencia = base_date + timedelta(days=vigencia_dias)

                # Empresa
                empresa_final = empresa
                if not empresa_final and induccion and induccion.get("id_empresa"):
                    cursor.execute("SELECT nombre_empresa FROM empresa WHERE id = %s", (induccion["id_empresa"],))
                    row_emp = cursor.fetchone()
                    if row_emp:
                        empresa_final = row_emp.get("nombre_empresa")

                if not empresa_final:
                    # Intentar buscar en solicitudes activas de la persona
                    cursor.execute(
                        """
                        SELECT s.empresa_origen
                        FROM solicitudes s
                        INNER JOIN ingresantes ing ON ing.id_solicitud = s.id
                        WHERE ing.id_persona = %s
                        ORDER BY s.id DESC
                        LIMIT 1
                        """,
                        (pid,)
                    )
                    row_sol = cursor.fetchone()
                    if row_sol and row_sol.get("empresa_origen"):
                        empresa_final = row_sol["empresa_origen"]

                if not empresa_final:
                    empresa_final = "INCARSA"

                return {
                    "exito": True,
                    "es_simulacion": False,
                    "id_persona": pid,
                    "id_formulario": id_formulario,
                    "nombre_persona": nombre_completo,
                    "tipo_documento": tipo_doc,
                    "numero_documento": num_doc,
                    "nombre_formulario": nombre_form,
                    "fecha_aprobacion": fecha_aprobacion,
                    "fecha_vigencia": fecha_vigencia,
                    "empresa": empresa_final
                }

    except Exception as e:
        print(f"❌ Error al consultar datos para certificado de inducción: {e}")
        return {"exito": False, "mensaje": f"Error en base de datos: {str(e)}"}
