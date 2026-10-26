import os
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv



def get_baseURL() -> str:
    """
    Retorna la URL base del sistema para generar enlaces públicos.
    Prioriza APP_BASE_URL de entorno; de lo contrario detecta la IP LAN local.
    """
    load_dotenv(override=True)
    base = os.getenv("APP_BASE_URL", "").strip().rstrip("/")
    if base:
        return base

    port = os.getenv("PORT", "8000")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
        if lan_ip and lan_ip != "127.0.0.1":
            return f"http://{lan_ip}:{port}"
    except Exception:
        pass

    return f"http://localhost:{port}"


def enviar_correo(destinatario: str, asunto: str, cuerpo_html: str) -> bool:
    """
    Envía un correo electrónico vía SMTP directo configurado en .env.
    """
    dest = (destinatario or "").strip().lower()
    if not dest or "@" not in dest:
        print(f"⚠️ [EMAIL] Destinatario inválido: '{destinatario}'")
        return False

    # Verificar si el despacho SMTP está habilitado o pausado por SuperAdmin (Modo Pruebas)
    correos_activos = True
    try:
        from src.loaders.superadmin_loader import GET_configuracion_correos_induccion_db
        cfg_correos = GET_configuracion_correos_induccion_db()
        correos_activos = bool(cfg_correos.get("correos_habilitados", True))
    except Exception as e_cfg:
        correos_activos = True

    if not correos_activos:
        try:
            print(f"[EMAIL-TEST-MODE] Despacho SMTP en pausa por SuperAdmin. Envio simulado con exito hacia '{dest}' (Asunto: '{asunto}').")
        except Exception:
            pass
        return True

    load_dotenv(override=True)

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").replace(" ", "").strip()
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "PSI — Control de Acceso")

    # Intentar con SMTP
    if smtp_user and smtp_pass:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = f"{smtp_from_name} <{smtp_user}>"
        msg["To"] = dest
        msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))

        try:
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=12) as server:
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_user, [dest], msg.as_string())
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_user, [dest], msg.as_string())

            print(f"[OK] [EMAIL-SMTP] Correo enviado exitosamente a {dest}")
            return True
        except Exception as e:
            print(f"[WARN] [EMAIL-SMTP] Error al enviar correo a {dest}: {e}")

    return False


URLS_INDUCCION_EMPRESAS = {
    "INCARSA": "https://fundacionmilpa.wixsite.com/incarsacontratistas",
    "MILPA": "https://fundacionmilpa.wixsite.com/milpacontratistas",
    "CARBOINSA": "https://fundacionmilpa.wixsite.com/carboinsacontratista",
    "UNIMINAS": "https://fundacionmilpa.wixsite.com/uniminascontratistas",
}


def get_url_induccion_empresa(empresa_nombre_o_id: Any) -> str:
    """
    Retorna la URL oficial de la página de inducción según la empresa origen.
    Mapeo oficial:
      - INCARSA: https://fundacionmilpa.wixsite.com/incarsacontratistas
      - MILPA: https://fundacionmilpa.wixsite.com/milpacontratistas
      - CARBOINSA: https://fundacionmilpa.wixsite.com/carboinsacontratista
      - UNIMINAS: https://fundacionmilpa.wixsite.com/uniminascontratistas
    """
    txt = str(empresa_nombre_o_id or "").upper().strip()
    if "MILPA" in txt or txt == "2":
        return URLS_INDUCCION_EMPRESAS["MILPA"]
    if "CARBOINSA" in txt or txt == "3":
        return URLS_INDUCCION_EMPRESAS["CARBOINSA"]
    if "UNIMINAS" in txt or txt == "4":
        return URLS_INDUCCION_EMPRESAS["UNIMINAS"]
    return URLS_INDUCCION_EMPRESAS["INCARSA"]


def create_autorizacionDatos(
    nombre_persona: str,
    radicado: str,
    empresa_contratista: str,
    url_autorizacion: str,
    induccion_vigente: bool = False,
    fecha_vigencia_induccion: Optional[str] = None,
    dias_restantes_induccion: Optional[int] = None,
    url_induccion: Optional[str] = None,
    empresa_origen_nombre: Optional[str] = None
) -> str:
    """
    Genera la plantilla HTML para la solicitud formal de autorización
    de tratamiento de datos personales conforme a la Ley 1581 de 2012
    e incluye el estado/enlace de la Inducción Corporativa GESCO.
    Diseño corporativo: Fondo blanco limpio con acentos Signal Red e Índigo GESCO.
    """
    nombre_display = (nombre_persona or "Estimado(a) colaborador(a)").strip().title()
    rad_display = (radicado or "En trámite").strip().upper()
    emp_display = (empresa_contratista or "Empresa Contratista").strip()
    emp_origen_display = (empresa_origen_nombre or "INCARSA S.A.S.").strip()

    # Construir bloque de inducción según si ya cuenta con vigencia activa o no
    if induccion_vigente:
        vig_txt = fecha_vigencia_induccion or "Al día"
        dias_txt = f"({dias_restantes_induccion} días restantes)" if dias_restantes_induccion is not None else ""
        bloque_induccion = f"""
              <!-- ============================================================
                   SECCIÓN 2: INDUCCIÓN CORPORATIVA GESCO (VIGENTE)
              ============================================================= -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-top: 24px; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #10b981; border-radius: 12px; padding: 18px 20px;">
                <tr>
                  <td>
                    <div style="color: #059669; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
                      ✓ ESTADO DE INDUCCIÓN GESCO · VIGENTE
                    </div>
                    <div style="color: #0f172a; font-size: 15px; font-weight: 800; line-height: 1.2; margin-bottom: 4px;">
                      Inducción Corporativa al Día
                    </div>
                    <p style="font-size: 12px; line-height: 1.6; color: #166534; margin: 0;">
                      Verificamos en el sistema que el titular ya cuenta con <strong>inducción corporativa vigente activa</strong> válida hasta el <strong>{vig_txt}</strong> {dias_txt}. <strong>No requiere presentar la inducción para este ingreso.</strong>
                    </p>
                  </td>
                </tr>
              </table>"""
    else:
        url_ind_target = url_induccion or get_url_induccion_empresa(emp_origen_display)
        bloque_induccion = f"""
              <!-- ============================================================
                   SECCIÓN 2: INDUCCIÓN CORPORATIVA GESCO (REQUISITO PENDIENTE)
              ============================================================= -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-top: 24px; background-color: #faf5ff; border: 1px solid #e9d5ff; border-left: 4px solid #7c3aed; border-radius: 12px; padding: 18px 20px;">
                <tr>
                  <td>
                    <div style="color: #7c3aed; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
                      🎓 REQUISITO DE INGRESO · INDUCCIÓN GESCO
                    </div>
                    <div style="color: #0f172a; font-size: 15px; font-weight: 800; line-height: 1.2; margin-bottom: 6px;">
                      Curso de Inducción Corporativa — {emp_origen_display}
                    </div>
                    <p style="font-size: 12px; line-height: 1.6; color: #4b5563; margin: 0 0 16px 0;">
                      Para poder ingresar a las instalaciones industriales de <strong>{emp_origen_display}</strong>, es requisito obligatorio completar y aprobar el curso de inducción correspondiente en nuestro portal oficial.
                    </p>
                    <div style="text-align: center; margin: 10px 0 14px 0;">
                      <a href="{url_ind_target}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #7c3aed 0%, #6366f1 100%); color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 800; padding: 12px 28px; border-radius: 8px; box-shadow: 0 4px 14px rgba(124, 58, 237, 0.35); text-transform: uppercase; letter-spacing: 0.5px;">
                        Realizar Inducción en {emp_origen_display}
                      </a>
                    </div>
                    <p style="font-size: 11px; color: #64748b; text-align: center; margin: 0;">
                      O accede directamente mediante el siguiente enlace:<br>
                      <a href="{url_ind_target}" style="color: #7c3aed; font-weight: 600; text-decoration: underline; word-break: break-all;">{url_ind_target}</a>
                    </p>
                  </td>
                </tr>
              </table>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Autorización de Tratamiento de Datos Personales — Ley 1581 de 2012</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f1f5f9; padding: 36px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.06), 0 8px 10px -6px rgba(0, 0, 0, 0.04); border: 1px solid #e2e8f0;">
          
          <!-- Franja superior en color Signal Red -->
          <tr>
            <td style="height: 5px; background: linear-gradient(90deg, #fb3b4c 0%, #dc2626 100%); line-height: 5px; font-size: 1px;">&nbsp;</td>
          </tr>

          <!-- Encabezado Institucional -->
          <tr>
            <td style="padding: 32px 32px 20px 32px; text-align: center; border-bottom: 1px solid #f1f5f9; background-color: #ffffff;">
              <h1 style="color: #0f172a; font-size: 22px; font-weight: 800; margin: 0; letter-spacing: -0.3px;">
                INCARSA <span style="color: #fb3b4c; font-weight: 900;">·</span> <span style="color: #475569; font-size: 17px; font-weight: 500;">Gestión de Acceso a Planta</span>
              </h1>
              <p style="color: #64748b; font-size: 12px; font-weight: 500; margin: 5px 0 0 0;">
                Autorización de Tratamiento de Datos Personales — Ley 1581 de 2012
              </p>
              <div style="display: inline-block; background-color: #fef2f2; color: #dc2626; border: 1px solid #fecdd3; border-radius: 20px; padding: 4px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 12px;">
                Marco Legal Ley 1581 de 2012
              </div>
            </td>
          </tr>

          <!-- Contenido Principal -->
          <tr>
            <td style="padding: 28px 32px 32px 32px; background-color: #ffffff;">
              
              <!-- Tarjeta Titular + Radicado estilo UI -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #fb3b4c; border-radius: 12px; padding: 18px 20px; margin-bottom: 22px;">
                <tr>
                  <td style="vertical-align: middle;">
                    <div style="color: #fb3b4c; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">
                      TITULAR DE LOS DATOS
                    </div>
                    <div style="color: #0f172a; font-size: 19px; font-weight: 800; line-height: 1.2; margin-bottom: 4px;">
                      {nombre_display}
                    </div>
                    <div style="color: #64748b; font-size: 12px; font-weight: 600;">
                      EMPRESA CONTRATISTA: <span style="color: #334155;">{emp_display}</span>
                    </div>
                  </td>
                  <td align="right" style="vertical-align: middle; padding-left: 12px;">
                    <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 14px; text-align: right; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                      <div style="color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                        Solicitud / Radicado
                      </div>
                      <div style="color: #fb3b4c; font-size: 15px; font-weight: 900; letter-spacing: 0.5px; margin-top: 2px;">
                        {rad_display}
                      </div>
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Mensaje de Notificación -->
              <p style="font-size: 14px; line-height: 1.6; color: #334155; margin: 0 0 20px 0;">
                Has sido registrado(a) por <strong style="color: #0f172a;">{emp_display}</strong> en la solicitud de ingreso a instalaciones industriales identificada con radicado <strong style="color: #fb3b4c;">{rad_display}</strong>.
              </p>

              <!-- Aviso: Requisito Indispensable (Caja Ámbar Clara) -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #fffbeb; border: 1px solid #fde68a; border-radius: 10px; margin-bottom: 22px;">
                <tr>
                  <td style="padding: 14px 16px; font-size: 13px; line-height: 1.5; color: #92400e;">
                    <strong style="color: #b45309;">⚠️ Requisito Indispensable:</strong> La autorización de tratamiento de datos es obligatoria para validar su acceso en la portería y registrar su permanencia en planta bajo normativas SG-SST.
                  </td>
                </tr>
              </table>

              <!-- Sección Términos y Condiciones -->
              <div style="margin-bottom: 24px;">
                <div style="margin-bottom: 8px;">
                  <span style="color: #64748b; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">
                    Términos y Condiciones de la Autorización (Formato FR_SLV_016)
                  </span>
                </div>
                <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px 18px;">
                  <div style="margin-bottom: 8px; font-size: 10px; font-family: monospace; color: #fb3b4c; font-weight: 700;">
                    CÓDIGO: FR_SLV_016 · VERSIÓN: 00 · VIGENCIA: 16/01/2025
                  </div>
                  <h3 style="color: #0f172a; font-size: 12px; font-weight: 800; text-transform: uppercase; margin: 0 0 8px 0; letter-spacing: 0.5px;">
                    AUTORIZACIÓN TRATAMIENTO DE DATOS PERSONALES · {emp_origen_display}
                  </h3>
                  <p style="font-size: 12px; line-height: 1.6; color: #334155; margin: 0 0 10px 0;">
                    En cumplimiento de la <strong>Ley 1581 de 2012</strong>, el <strong>Decreto 1377 de 2013</strong> y el <em>“Manual de Políticas de Tratamiento de la Información de Datos Personales”</em>, requerimos su consentimiento previo, expreso e informado para que <strong>{emp_origen_display}</strong> trate sus datos personales para:
                  </p>
                  <ul style="font-size: 12px; line-height: 1.6; color: #475569; margin: 0 0 10px 0; padding-left: 20px;">
                    <li>Procedimientos administrativos, gestión de contratistas y control de acceso físico en porterías y plantas industriales.</li>
                    <li>Verificación de idoneidad, referencias y aportes al Sistema de Seguridad Social Integral (ARL, EPS, AFP).</li>
                    <li>Seguridad física mediante videovigilancia (CCTV) y cumplimiento de estándares SG-SST.</li>
                  </ul>
                  <p style="font-size: 11px; line-height: 1.5; color: #64748b; margin: 0;">
                    Canal oficial para derechos ARCO (acceso, corrección, supresión, reclamo): <a href="mailto:incarsasas@incarsa.com.co" style="color: #fb3b4c; text-decoration: underline;">incarsasas@incarsa.com.co</a>.
                  </p>
                </div>
              </div>

              <!-- Botón de Acción Principal Signal Red -->
              <div style="text-align: center; margin: 28px 0 22px 0;">
                <a href="{url_autorizacion}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #fb3b4c 0%, #dc2626 100%); color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 800; padding: 13px 34px; border-radius: 8px; box-shadow: 0 4px 14px rgba(251, 59, 76, 0.35); text-transform: uppercase; letter-spacing: 0.5px;">
                  Ver y Autorizar Tratamiento de Datos
                </a>
              </div>

              <p style="font-size: 12px; color: #64748b; text-align: center; margin: 0 0 6px 0;">
                Si el botón no funciona, puedes copiar y pegar el siguiente enlace en tu navegador:
              </p>
              <p style="font-size: 11px; text-align: center; word-break: break-all; margin: 0;">
                <a href="{url_autorizacion}" style="color: #fb3b4c; font-weight: 600; text-decoration: underline;">{url_autorizacion}</a>
              </p>

              <!-- Bloque Condicional de Inducción GESCO -->
              {bloque_induccion}

            </td>
          </tr>

          <!-- Pie de Página Legal -->
          <tr>
            <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 22px 32px; text-align: center;">
              <p style="font-size: 11px; color: #64748b; line-height: 1.5; margin: 0;">
                Como titular de los datos personales, le asisten los derechos previstos en la Ley 1581 de 2012 y el Formato FR_SLV_016. Puede solicitar la política institucional en <a href="mailto:incarsasas@incarsa.com.co" style="color: #fb3b4c; text-decoration: underline;">incarsasas@incarsa.com.co</a>.
              </p>
              <p style="font-size: 10px; color: #94a3b8; margin: 8px 0 0 0;">
                <strong style="color: #0f172a;">{emp_origen_display}</strong> · Plataforma PSI.<br>
                Este es un mensaje generado automáticamente por el sistema. Por favor, no respondas a este correo.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_autorizacionDatos(
    destinatario: str,
    nombre_persona: str,
    radicado: str,
    empresa_contratista: str,
    token_autorizacion: str,
    induccion_vigente: bool = False,
    fecha_vigencia_induccion: Optional[str] = None,
    dias_restantes_induccion: Optional[int] = None,
    url_induccion: Optional[str] = None,
    empresa_origen_nombre: Optional[str] = None
) -> bool:
    """
    Construye la URL y despacha el correo de autorización de datos personales
    con el bloque condicional de Inducción Corporativa GESCO.
    """
    base_url = get_baseURL()
    url_autorizacion = f"{base_url}/autorizacion-datos/{token_autorizacion}"
    asunto = f"Autorización de Datos Personales y Guía de Inducción — Radicado {radicado}"
    cuerpo_html = create_autorizacionDatos(
        nombre_persona=nombre_persona,
        radicado=radicado,
        empresa_contratista=empresa_contratista,
        url_autorizacion=url_autorizacion,
        induccion_vigente=induccion_vigente,
        fecha_vigencia_induccion=fecha_vigencia_induccion,
        dias_restantes_induccion=dias_restantes_induccion,
        url_induccion=url_induccion,
        empresa_origen_nombre=empresa_origen_nombre
    )
    return enviar_correo(destinatario, asunto, cuerpo_html)


def create_notificationRevision(
    nombre_revisor: str,
    rol_revisor: str,
    radicado: str,
    empresa_contratista: str,
    plantas: str,
    tipo_contratista: str,
    total_personas: int,
    total_vehiculos: int,
    fecha_inicio: str,
    fecha_fin: str,
    url_revision: str
) -> str:
    """
    Genera la plantilla HTML ejecutiva para notificar a los revisores de GESCO y SST
    cuando entra una solicitud al flujo de revisión técnica.
    Diseño corporativo: Fondo blanco limpio con acentos Signal Red.
    """
    rev_display = (nombre_revisor or "Revisor Técnico").strip().title()
    rol_display = (rol_revisor or "SST").strip().upper()
    rad_display = (radicado or "En trámite").strip().upper()
    emp_display = (empresa_contratista or "Empresa Contratista").strip()
    plantas_display = (plantas or "Planta asignada").strip()
    tipo_display = (tipo_contratista or "Contratista").strip().capitalize()
    
    # Texto descriptivo específico según rol
    if rol_display == "GESCO":
        rol_desc = "validación de inducciones corporativas, certificaciones y verificación de personal"
        badge_texto = "📋 Nueva Solicitud en Revisión (GESCO)"
    else:
        rol_desc = "validación de seguridad y salud en el trabajo, ARL, EPS y certificados de riesgo"
        badge_texto = "🛡️ Nueva Solicitud en Revisión (SST)"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nueva Solicitud para Revisión {rol_display} — Radicado {rad_display}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f1f5f9; padding: 36px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.06), 0 8px 10px -6px rgba(0, 0, 0, 0.04); border: 1px solid #e2e8f0;">
          
          <!-- Franja superior en color Signal Red -->
          <tr>
            <td style="height: 5px; background: linear-gradient(90deg, #fb3b4c 0%, #dc2626 100%); line-height: 5px; font-size: 1px;">&nbsp;</td>
          </tr>

          <!-- Encabezado Institucional -->
          <tr>
            <td style="padding: 32px 32px 20px 32px; text-align: center; border-bottom: 1px solid #f1f5f9; background-color: #ffffff;">
              <h1 style="color: #0f172a; font-size: 22px; font-weight: 800; margin: 0; letter-spacing: -0.3px;">
                INCARSA <span style="color: #fb3b4c; font-weight: 900;">·</span> <span style="color: #475569; font-size: 17px; font-weight: 500;">Control de Acceso</span>
              </h1>
              <p style="color: #64748b; font-size: 12px; font-weight: 500; margin: 5px 0 0 0;">
                Sistema de Control y Gestión de Seguridad · Plataforma PSI
              </p>
              <div style="display: inline-block; background-color: #fef2f2; color: #dc2626; border: 1px solid #fecdd3; border-radius: 20px; padding: 4px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; margin-top: 12px;">
                {badge_texto}
              </div>
            </td>
          </tr>

          <!-- Contenido Principal -->
          <tr>
            <td style="padding: 28px 32px 32px 32px; background-color: #ffffff;">
              <h2 style="color: #0f172a; font-size: 18px; font-weight: 800; margin: 0 0 10px 0;">
                Hola {rev_display},
              </h2>
              <p style="font-size: 14px; line-height: 1.6; color: #334155; margin: 0 0 20px 0;">
                Se ha radicado una nueva solicitud de acceso a instalaciones industriales identificada con radicado <strong style="color: #fb3b4c; font-weight: 800;">{rad_display}</strong>. Como revisor de <strong style="color: #0f172a;">{rol_display}</strong> para la(s) planta(s) asignada(s), se requiere tu {rol_desc}.
              </p>

              <!-- Tarjeta Resumen de la Solicitud -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #fb3b4c; border-radius: 12px; margin-bottom: 22px;">
                <tr>
                  <td style="padding: 18px 20px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                      <tr>
                        <td style="padding: 5px 0; font-size: 12px; color: #64748b; font-weight: 600; width: 140px;">Radicado:</td>
                        <td style="padding: 5px 0; font-size: 14px; color: #fb3b4c; font-weight: 800;">{rad_display}</td>
                      </tr>
                      <tr>
                        <td style="padding: 5px 0; font-size: 12px; color: #64748b; font-weight: 600;">Empresa:</td>
                        <td style="padding: 5px 0; font-size: 13px; color: #0f172a; font-weight: 700;">{emp_display}</td>
                      </tr>
                      <tr>
                        <td style="padding: 5px 0; font-size: 12px; color: #64748b; font-weight: 600;">Planta(s) Destino:</td>
                        <td style="padding: 5px 0; font-size: 13px; color: #0f172a; font-weight: 600;">{plantas_display}</td>
                      </tr>
                      <tr>
                        <td style="padding: 5px 0; font-size: 12px; color: #64748b; font-weight: 600;">Tipo de Acceso:</td>
                        <td style="padding: 5px 0; font-size: 13px; color: #0f172a; font-weight: 600;">{tipo_display}</td>
                      </tr>
                      <tr>
                        <td style="padding: 5px 0; font-size: 12px; color: #64748b; font-weight: 600;">Personal / Vehículos:</td>
                        <td style="padding: 5px 0; font-size: 13px; color: #0f172a; font-weight: 600;">{total_personas} persona(s) · {total_vehiculos} vehículo(s)</td>
                      </tr>
                      <tr>
                        <td style="padding: 5px 0; font-size: 12px; color: #64748b; font-weight: 600;">Vigencia Solicitada:</td>
                        <td style="padding: 5px 0; font-size: 13px; color: #0f172a; font-weight: 600;">{fecha_inicio} al {fecha_fin}</td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Botón de Acción Principal Signal Red -->
              <div style="text-align: center; margin: 28px 0 22px 0;">
                <a href="{url_revision}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #fb3b4c 0%, #dc2626 100%); color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 800; padding: 13px 34px; border-radius: 8px; box-shadow: 0 4px 14px rgba(251, 59, 76, 0.35); text-transform: uppercase; letter-spacing: 0.5px;">
                  Revisar Solicitud en Plataforma
                </a>
              </div>

              <p style="font-size: 12px; color: #64748b; text-align: center; margin: 0 0 6px 0;">
                Si el botón no abre directamente, puedes ingresar copiando este enlace:
              </p>
              <p style="font-size: 11px; text-align: center; word-break: break-all; margin: 0;">
                <a href="{url_revision}" style="color: #fb3b4c; font-weight: 600; text-decoration: underline;">{url_revision}</a>
              </p>
            </td>
          </tr>

          <!-- Pie de Página Legal -->
          <tr>
            <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 22px 32px; text-align: center;">
              <p style="font-size: 11px; color: #64748b; line-height: 1.5; margin: 0;">
                <strong style="color: #0f172a;">INCARSA S.A.S.</strong> · NIT 830.078.829-5 · Plataforma PSI.<br>
                Notificación automática para el equipo de revisión técnica ({rol_display}). Por favor, no respondas a este correo.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_notificationRevision(
    destinatario: str,
    nombre_revisor: str,
    rol_revisor: str,
    radicado: str,
    empresa_contratista: str,
    plantas: str,
    tipo_contratista: str = "Contratista",
    total_personas: int = 0,
    total_vehiculos: int = 0,
    fecha_inicio: str = "N/A",
    fecha_fin: str = "N/A"
) -> bool:
    """
    Construye la URL y despacha el correo de notificación de revisión a un revisor SST o GESCO.
    """
    base_url = get_baseURL()
    url_revision = f"{base_url}/solicitudes/revision/{radicado}"
    rol_display = (rol_revisor or "SST").strip().upper()
    asunto = f"Nueva Solicitud para Revisión ({rol_display}) — Radicado {radicado}"
    cuerpo_html = create_notificationRevision(
        nombre_revisor=nombre_revisor,
        rol_revisor=rol_display,
        radicado=radicado,
        empresa_contratista=empresa_contratista,
        plantas=plantas,
        tipo_contratista=tipo_contratista,
        total_personas=total_personas,
        total_vehiculos=total_vehiculos,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        url_revision=url_revision
    )
    return enviar_correo(destinatario, asunto, cuerpo_html)


