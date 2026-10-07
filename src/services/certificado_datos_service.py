import io
import os
from datetime import datetime
import qrcode
from PIL import Image

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image as RLImage,
        KeepTogether,
        HRFlowable
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def GENERAR_pdf_certificado_datos(datos: dict, base_url: str = "", es_interno: bool = False) -> bytes:
    """
    Genera el Certificado / Constancia Oficial en PDF de Autorización de Tratamiento
    de Datos Personales (Ley 1581 de 2012 - Formato Institucional FR_SLV_016).
    
    :param datos: Diccionario con la información del titular y metadatos de firma.
    :param base_url: URL base para generar el QR de verificación pública.
    :param es_interno: Si es True, incluye datos forenses completos (IP y Dispositivo)
                       para auditoría SG-SST / usuarios del sistema. Si es False, oculta
                       los datos técnicos directos y los protege bajo custodia digital.
    :return: Bytes del documento PDF.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("La librería 'reportlab' no está instalada en el entorno Python activo.")

    buffer = io.BytesIO()

    # Configuración de márgenes compactos y elegantes
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=32,
        rightMargin=32,
        topMargin=28,
        bottomMargin=28
    )

    styles = getSampleStyleSheet()

    # Paleta de colores sobria, corporativa e institucional
    c_primary = colors.HexColor("#0f2744")      # Azul marino oscuro corporativo
    c_secondary = colors.HexColor("#0284c7")    # Azul institucional
    c_dark = colors.HexColor("#1e293b")         # Texto principal
    c_muted = colors.HexColor("#475569")        # Texto secundario
    c_border = colors.HexColor("#cbd5e1")       # Borde sutil
    c_bg_box = colors.HexColor("#f8fafc")       # Fondo sutil caja
    c_emerald_dark = colors.HexColor("#065f46") # Verde éxito
    c_emerald_bg = colors.HexColor("#ecfdf5")   # Fondo verde suave

    # Estilos tipográficos
    style_header_title = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13,
        textColor=c_primary,
        alignment=0
    )
    style_header_sub = ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=c_muted,
        alignment=0
    )
    style_code_box = ParagraphStyle(
        'CodeBox',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=c_primary,
        alignment=2
    )

    style_banner_resp = ParagraphStyle(
        'BannerResp',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1
    )

    style_cell_label = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=c_muted
    )
    style_cell_value = ParagraphStyle(
        'CellValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=c_dark
    )
    style_cell_mono = ParagraphStyle(
        'CellMono',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=11,
        textColor=c_secondary
    )

    style_legal_title = ParagraphStyle(
        'LegalTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=c_primary
    )
    style_legal_p = ParagraphStyle(
        'LegalP',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=9.2,
        textColor=c_dark,
        alignment=4 # Justificado
    )

    style_security_title = ParagraphStyle(
        'SecTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=c_emerald_dark
    )
    style_security_desc = ParagraphStyle(
        'SecDesc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=c_dark
    )
    style_security_mono = ParagraphStyle(
        'SecMono',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=c_primary
    )

    style_footer = ParagraphStyle(
        'FooterLegal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.5,
        leading=8.5,
        textColor=colors.HexColor("#64748b"),
        alignment=1
    )

    story = []

    # Extraer variables
    empresa_origen = datos.get("empresa_origen") or "INCARSA S.A.S."
    correo_institucional = datos.get("correo_institucional") or "incarsasas@incarsa.com.co"
    radicado = datos.get("codigo_radicado") or "S/R"
    nombre_completo = datos.get("nombre_completo") or "TITULAR NO ESPECIFICADO"
    tipo_doc = datos.get("tipo_doc") or "C.C."
    identificacion = str(datos.get("identificacion") or datos.get("cedula") or "S/D")
    cargo = datos.get("cargo") or "Personal Contratista"
    contratista = datos.get("empresa_contratista") or "Personal Directo / General"
    correo = datos.get("correo") or "No registrado"
    plantas = datos.get("plantas_texto") or "Instalaciones Industriales"
    token = datos.get("token") or ""
    fecha_resp = str(datos.get("fecha_respuesta_datos") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    ip_datos = datos.get("ip_datos") or "Captura Digital Segura"
    dispositivo_datos = datos.get("dispositivo_datos") or "Dispositivo Web Seguro"
    estado = str(datos.get("estado_datos") or "AUTORIZADO").upper()

    # 1. ENCABEZADO OFICIAL FORMATO FR_SLV_016
    header_data = [
        [
            Paragraph("<b>AUTORIZACIÓN TRATAMIENTO DE DATOS PERSONALES</b><br/>"
                      "<font color='#475569'>Procesos de Selección, Vinculación, Contratación y Acceso a Instalaciones</font>", style_header_title),
            Paragraph("<b>FORMATO INSTITUCIONAL</b><br/>"
                      "<b>Código:</b> FR_SLV_016<br/>"
                      "<b>Versión:</b> 00 · <b>Vigencia:</b> 16/01/2025", style_code_box)
        ]
    ]
    t_header = Table(header_data, colWidths=[380, 168])
    t_header.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, c_primary),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 4))

    # 2. BANNER EMPRESA RESPONSABLE
    banner_data = [[
        Paragraph(f"ORGANIZACIÓN RESPONSABLE: <b>{empresa_origen.upper()}</b> &nbsp;·&nbsp; "
                  f"LEY ESTATUTARIA 1581 DE 2012 & DECRETO 1377 DE 2013", style_banner_resp)
    ]]
    t_banner = Table(banner_data, colWidths=[548])
    t_banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_primary),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_banner)
    story.append(Spacer(1, 5))

    # 3. TABLA FICHA DEL TITULAR DE LA INFORMACIÓN
    info_titular_data = [
        [
            Paragraph("<b>NOMBRES Y APELLIDOS:</b>", style_cell_label),
            Paragraph(f"<b>{nombre_completo.upper()}</b>", style_cell_value),
            Paragraph("<b>DOCUMENTO:</b>", style_cell_label),
            Paragraph(f"<b>{tipo_doc} {identificacion}</b>", style_cell_mono)
        ],
        [
            Paragraph("<b>CARGO / LABOR:</b>", style_cell_label),
            Paragraph(cargo, style_cell_value),
            Paragraph("<b>CORREO CONTACTO:</b>", style_cell_label),
            Paragraph(correo, style_cell_value)
        ],
        [
            Paragraph("<b>EMPRESA CONTRATISTA:</b>", style_cell_label),
            Paragraph(contratista, style_cell_value),
            Paragraph("<b>RADICADO / SOLICITUD:</b>", style_cell_label),
            Paragraph(radicado, style_cell_mono)
        ],
        [
            Paragraph("<b>PLANTA(S) DESTINO:</b>", style_cell_label),
            Paragraph(plantas, style_cell_value),
            Paragraph("<b>ESTADO CONSENTIMIENTO:</b>", style_cell_label),
            Paragraph(f"<font color='#059669'><b>● {estado}</b></font>", style_cell_value)
        ]
    ]
    t_info = Table(info_titular_data, colWidths=[110, 174, 114, 150])
    t_info.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.8, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor("#f8fafc")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 6))

    # 4. CUERPO LEGAL SINTÉTICO (ALCANCE FORMAL FR_SLV_016)
    p_intro = Paragraph(
        f"En mi calidad de Titular de los datos personales, manifiesto de manera libre, previa, expresa, informada "
        f"e inequívoca que autorizo a la sociedad <b>{empresa_origen}</b> (la “Organización”), para que en calidad "
        f"de Responsable recolecte, almacene, circule, use, transmita y dé tratamiento a mi información personal y documentación aportada, "
        f"de conformidad con su <i>Manual de Políticas de Tratamiento de Datos Personales</i> y las siguientes condiciones:",
        style_legal_p
    )
    story.append(p_intro)
    story.append(Spacer(1, 3))

    clauses_data = [
        [
            Paragraph("<b>1. Finalidades Principales:</b> Validar requisitos de acceso físico y permanencia a plantas y minas; comprobación de idoneidad técnica y referencias; cumplimiento del Sistema de Seguridad y Salud en el Trabajo (SG-SST); verificación ininterrumpida de afiliación y pago de Seguridad Social Integral (ARL, EPS, AFP); atención ante emergencias; monitoreo mediante CCTV y trazabilidad de portería.", style_legal_p)
        ],
        [
            Paragraph("<b>2. Datos Sensibles y Biométricos:</b> Se me informó el carácter facultativo de suministrar datos sensibles (imágenes CCTV, registros fotográficos, biometría, aptitud médica laboral), reconociendo que son obligatorios para los estándares de seguridad industrial y prevención de riesgos en instalaciones de la Organización.", style_legal_p)
        ],
        [
            Paragraph("<b>3. Veracidad y Comprobación:</b> Declaro que la información aportada es veraz, íntegra y exacta, facultando a la Organización a corroborarla sin restricciones ante entidades públicas, privadas o de seguridad social.", style_legal_p)
        ],
        [
            Paragraph("<b>4. Delimitación Laboral:</b> La presente manifestación de datos y la participación en solicitudes de ingreso no configura ni compromete existencia de vínculo ni contrato laboral directo entre las partes.", style_legal_p)
        ],
        [
            Paragraph(f"<b>5. Canales Institucionales de Habeas Data:</b> Para el ejercicio de los derechos de conocer, actualizar, rectificar y suprimir datos, la Organización dispone del canal oficial: <b>{correo_institucional}</b> y sus oficinas administrativas.", style_legal_p)
        ]
    ]
    t_clauses = Table(clauses_data, colWidths=[548])
    t_clauses.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fafafa")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_clauses)
    story.append(Spacer(1, 6))

    # 5. GENERAR CÓDIGO QR DE VERIFICACIÓN
    url_validacion = f"{base_url.rstrip('/')}/autorizacion-datos/{token}" if token else base_url
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=3,
        border=1
    )
    qr.add_data(url_validacion or "https://psi.incarsa.com.co")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0f2744", back_color="white")
    
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    rl_qr = RLImage(qr_buffer, width=64, height=64)

    # 6. RECUADRO DE CONSTANCIA Y EVIDENCIA DIGITAL (AUDITORÍA SST & SIC)
    if es_interno:
        titulo_evidencia = "CONSTANCIA DE FIRMA Y AUDITORÍA DIGITAL (LEY 527/1999 & LEY 1581/2012) · CONTROL INTERNO"
        linea_trazabilidad = (
            f"<b>Dirección IP:</b> {ip_datos} &nbsp;|&nbsp; <b>Dispositivo / Entorno:</b> {dispositivo_datos}<br/>"
            "<font color='#475569'><i>Firma electrónica consignada mediante consentimiento informado de 3 factores (Lectura, Validación y Autorización). Registro de auditoría forense para SG-SST y SIC.</i></font>"
        )
    else:
        titulo_evidencia = "CONSTANCIA DE FIRMA Y ACEPTACIÓN DIGITAL (LEY 527/1999 & LEY 1581/2012)"
        linea_trazabilidad = (
            "<b>Trazabilidad Digital:</b> Registro de consentimiento informado custodiado bajo bitácora segura y cadena de custodia institucional.<br/>"
            "<font color='#475569'><i>Firma electrónica consignada mediante consentimiento informado de 3 factores (Lectura, Validación y Autorización).</i></font>"
        )

    cert_box_data = [
        [
            Paragraph(
                f"<b>{titulo_evidencia}</b><br/>"
                f"<font color='#065f46'><b>✔ ESTADO: {estado}</b></font> &nbsp;|&nbsp; "
                f"<b>Fecha y Hora:</b> {fecha_resp}<br/>"
                f"{linea_trazabilidad}",
                style_security_desc
            ),
            rl_qr
        ]
    ]
    t_cert_box = Table(cert_box_data, colWidths=[464, 84])
    t_cert_box.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1.2, c_emerald_dark),
        ('BACKGROUND', (0,0), (-1,-1), c_emerald_bg),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_cert_box)
    story.append(Spacer(1, 6))

    # 7. PIE DE PÁGINA FORMAL
    if es_interno:
        texto_pie = (
            "Copia Oficial de Control y Auditoría Interna · Sistema de Gestión de Acceso y Solicitudes (PSI) INCARSA S.A.S.<br/>"
            "Documento con plena validez probatoria para auditorías del SG-SST, Ministerio del Trabajo y SIC. Trazabilidad técnica reservada."
        )
    else:
        texto_pie = (
            "Certificado Oficial de Autorización del Titular · Sistema de Gestión de Acceso y Solicitudes (PSI) INCARSA S.A.S.<br/>"
            "Documento con plena validez jurídica probatoria bajo la Ley 1581 de 2012 y Ley 527 de 1999. Consulte y verifique escaneando el código QR."
        )
    p_footer = Paragraph(texto_pie, style_footer)
    story.append(p_footer)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
