import os
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

try:
    import resend
except ImportError:
    resend = None


def obtener_base_url() -> str:
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
    Envía un correo electrónico intentando primero vía SMTP directo.
    Si falla o no está configurado, intenta como alternativa vía Resend.
    """
    dest = (destinatario or "").strip().lower()
    if not dest or "@" not in dest:
        print(f"⚠️ [EMAIL] Destinatario inválido: '{destinatario}'")
        return False

    load_dotenv(override=True)
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").replace(" ", "").strip()
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "PSI — Control de Acceso")

    # 1. Intentar con SMTP
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

            print(f"📧 [EMAIL-SMTP] Correo enviado exitosamente a {dest}")
            return True
        except Exception as e:
            print(f"⚠️ [EMAIL-SMTP] Error al enviar correo a {dest}: {e}")

    # 2. Fallback a Resend si está disponible
    if resend:
        api_key_actual = os.getenv("RESEND_API_KEY", getattr(resend, "api_key", ""))
        if api_key_actual and not api_key_actual.startswith("re_XXXX"):
            resend.api_key = api_key_actual
            try:
                resend.Emails.send({
                    "from": "PSI Control de Acceso <onboarding@resend.dev>",
                    "to": [dest],
                    "subject": asunto,
                    "html": cuerpo_html
                })
                print(f"📧 [EMAIL-RESEND] Correo enviado exitosamente a {dest}")
                return True
            except Exception as err:
                print(f"⚠️ [EMAIL-RESEND] Error enviando a {dest}: {err}")

    return False


def generar_html_autorizacion_datos(
    nombre_persona: str,
    radicado: str,
    empresa_contratista: str,
    url_autorizacion: str
) -> str:
    """
    Genera la plantilla HTML para la solicitud formal de autorización
    de tratamiento de datos personales conforme a la Ley 1581 de 2012.
    """
    nombre_display = (nombre_persona or "Estimado(a) colaborador(a)").strip().title()
    rad_display = (radicado or "En trámite").strip().upper()
    emp_display = (empresa_contratista or "Empresa Contratista").strip()

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="dark">
  <title>Autorización de Tratamiento de Datos Personales — Ley 1581 de 2012</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b1120; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e2e8f0;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #0b1120; padding: 36px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; background-color: #0f172a; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 45px -10px rgba(0, 0, 0, 0.7); border: 1px solid #1e293b;">
          
          <!-- Franja superior en degradado Neón Sky / Blue -->
          <tr>
            <td style="height: 5px; background: linear-gradient(90deg, #38bdf8 0%, #2563eb 100%); line-height: 5px; font-size: 1px;">&nbsp;</td>
          </tr>

          <!-- Encabezado Institucional Modo Oscuro -->
          <tr>
            <td style="padding: 32px 32px 20px 32px; text-align: center; border-bottom: 1px solid #1e293b;">
              <h1 style="color: #ffffff; font-size: 24px; font-weight: 800; margin: 0; letter-spacing: 0.5px; font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
                INCARSA <span style="color: #38bdf8; font-weight: 300;">·</span> <span style="color: #cbd5e1; font-size: 18px; font-weight: 500;">Gestión de Acceso a Planta</span>
              </h1>
              <p style="color: #94a3b8; font-size: 12px; font-weight: 500; margin: 6px 0 0 0;">
                Autorización de Tratamiento de Datos Personales — Ley 1581 de 2012
              </p>
              <div style="display: inline-block; background-color: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 20px; padding: 4px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 14px;">
                Marco Legal Ley 1581 de 2012
              </div>
            </td>
          </tr>

          <!-- Contenido Principal -->
          <tr>
            <td style="padding: 28px 32px 32px 32px;">
              
              <!-- Tarjeta Titular + Radicado estilo UI -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #0b1329; border: 1px solid #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 20px;">
                <tr>
                  <td style="vertical-align: middle;">
                    <div style="color: #38bdf8; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">
                      TITULAR DE LOS DATOS
                    </div>
                    <div style="color: #ffffff; font-size: 20px; font-weight: 800; line-height: 1.2; margin-bottom: 4px;">
                      {nombre_display}
                    </div>
                    <div style="color: #94a3b8; font-size: 12px; font-weight: 500;">
                      🏢 {emp_display}
                    </div>
                  </td>
                  <td align="right" style="vertical-align: middle; padding-left: 12px;">
                    <div style="background-color: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 10px 14px; text-align: right; display: inline-block;">
                      <div style="color: #94a3b8; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                        Solicitud / Radicado
                      </div>
                      <div style="color: #38bdf8; font-size: 15px; font-weight: 900; letter-spacing: 0.5px; margin-top: 2px;">
                        {rad_display}
                      </div>
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Mensaje de Notificación -->
              <p style="font-size: 14px; line-height: 1.6; color: #cbd5e1; margin: 0 0 20px 0;">
                Has sido registrado(a) por <strong style="color: #ffffff;">{emp_display}</strong> en la solicitud de ingreso a instalaciones industriales identificada con radicado <strong style="color: #38bdf8;">{rad_display}</strong>.
              </p>

              <!-- Aviso: Requisito Indispensable (Caja Ámbar Oscura idéntica a la UI) -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 10px; margin-bottom: 22px;">
                <tr>
                  <td style="padding: 14px 16px; font-size: 13px; line-height: 1.5; color: #fef08a;">
                    <strong style="color: #fde047;">⚠️ Requisito Indispensable:</strong> La autorización de tratamiento de datos es obligatoria para validar su acceso en la portería y registrar su permanencia en planta bajo normativas SG-SST.
                  </td>
                </tr>
              </table>

              <!-- Sección Términos y Condiciones -->
              <div style="margin-bottom: 24px;">
                <div style="margin-bottom: 8px;">
                  <span style="color: #94a3b8; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">
                    Términos y Condiciones de la Autorización (Formato FR_SLV_016)
                  </span>
                </div>
                <div style="background-color: #020617; border: 1px solid #1e293b; border-radius: 10px; padding: 16px 18px;">
                  <div style="margin-bottom: 8px; font-size: 10px; font-family: monospace; color: #38bdf8;">
                    CÓDIGO: FR_SLV_016 · VERSIÓN: 00 · VIGENCIA: 16/01/2025
                  </div>
                  <h3 style="color: #ffffff; font-size: 12px; font-weight: 800; text-transform: uppercase; margin: 0 0 8px 0; letter-spacing: 0.5px;">
                    AUTORIZACIÓN TRATAMIENTO DE DATOS PERSONALES · INCARSA S.A.S.
                  </h3>
                  <p style="font-size: 12px; line-height: 1.6; color: #cbd5e1; margin: 0 0 10px 0;">
                    En cumplimiento de la <strong>Ley 1581 de 2012</strong>, el <strong>Decreto 1377 de 2013</strong> y el <em>“Manual de Políticas de Tratamiento de la Información de Datos Personales”</em>, requerimos su consentimiento previo, expreso e informado para que <strong>INCARSA S.A.S. (NIT 830.078.829-5)</strong> trate sus datos personales para:
                  </p>
                  <ul style="font-size: 12px; line-height: 1.6; color: #94a3b8; margin: 0 0 10px 0; padding-left: 20px;">
                    <li>Procedimientos administrativos, gestión de contratistas y control de acceso físico en porterías y plantas industriales.</li>
                    <li>Verificación de idoneidad, referencias y aportes al Sistema de Seguridad Social Integral (ARL, EPS, AFP).</li>
                    <li>Seguridad física mediante videovigilancia (CCTV) y cumplimiento de estándares SG-SST.</li>
                  </ul>
                  <p style="font-size: 11px; line-height: 1.5; color: #64748b; margin: 0;">
                    Canal oficial para derechos ARCO (acceso, corrección, supresión, reclamo): <a href="mailto:incarsasas@incarsa.com.co" style="color: #38bdf8; text-decoration: none;">incarsasas@incarsa.com.co</a>.
                  </p>
                </div>
              </div>

              <!-- Botón de Acción Principal Azul Neón Gradiente -->
              <div style="text-align: center; margin: 30px 0 24px 0;">
                <a href="{url_autorizacion}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%); color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 800; padding: 14px 34px; border-radius: 10px; box-shadow: 0 4px 18px rgba(14, 165, 233, 0.35); text-transform: uppercase; letter-spacing: 0.6px;">
                  Ver y Autorizar Tratamiento de Datos
                </a>
              </div>

              <p style="font-size: 12px; color: #64748b; text-align: center; margin: 0 0 8px 0;">
                Si el botón no funciona, puedes copiar y pegar el siguiente enlace en tu navegador:
              </p>
              <p style="font-size: 11px; text-align: center; word-break: break-all; margin: 0;">
                <a href="{url_autorizacion}" style="color: #38bdf8; font-weight: 600; text-decoration: none;">{url_autorizacion}</a>
              </p>
            </td>
          </tr>

          <!-- Pie de Página Legal Modo Oscuro -->
          <tr>
            <td style="background-color: #080d19; border-top: 1px solid #1e293b; padding: 22px 32px; text-align: center;">
              <p style="font-size: 11px; color: #94a3b8; line-height: 1.5; margin: 0;">
                Como titular de los datos personales, le asisten los derechos previstos en la Ley 1581 de 2012 y el Formato FR_SLV_016. Puede consultar la política institucional en <a href="https://www.incarsa.com.co" style="color: #38bdf8; text-decoration: none;">www.incarsa.com.co</a> o solicitar atención en <a href="mailto:incarsasas@incarsa.com.co" style="color: #38bdf8; text-decoration: none;">incarsasas@incarsa.com.co</a>.
              </p>
              <p style="font-size: 10px; color: #64748b; margin: 8px 0 0 0;">
                <strong style="color: #ffffff;">INCARSA S.A.S.</strong> · NIT 830.078.829-5 · Plataforma PSI.<br>
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


def enviar_correo_autorizacion_datos(
    destinatario: str,
    nombre_persona: str,
    radicado: str,
    empresa_contratista: str,
    token_autorizacion: str
) -> bool:
    """
    Construye la URL y despacha el correo de autorización de datos personales.
    """
    base_url = obtener_base_url()
    url_autorizacion = f"{base_url}/autorizacion-datos/{token_autorizacion}"
    asunto = f"Autorización de Datos Personales (Ley 1581/2012) — Radicado {radicado}"
    cuerpo_html = generar_html_autorizacion_datos(
        nombre_persona=nombre_persona,
        radicado=radicado,
        empresa_contratista=empresa_contratista,
        url_autorizacion=url_autorizacion
    )
    return enviar_correo(destinatario, asunto, cuerpo_html)

