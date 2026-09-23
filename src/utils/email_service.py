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
  <title>Autorización de Tratamiento de Datos Personales — Ley 1581 de 2012</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f1f5f9; padding: 30px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" max-width="600" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
          
          <!-- Encabezado Institucional -->
          <tr>
            <td style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 32px 28px; text-align: center;">
              <h1 style="color: #38bdf8; font-size: 26px; font-weight: 900; margin: 0; letter-spacing: 1.5px;">PSI</h1>
              <p style="color: #94a3b8; font-size: 13px; font-weight: 700; margin: 4px 0 0 0; text-transform: uppercase; letter-spacing: 1px;">
                Control de Acceso y Gestión de Contratistas
              </p>
            </td>
          </tr>

          <!-- Contenido Principal -->
          <tr>
            <td style="padding: 32px 28px;">
              <div style="background-color: #ecfeff; border: 1px solid #a5f3fc; border-radius: 10px; padding: 12px 16px; margin-bottom: 24px; text-align: center;">
                <span style="color: #0e7490; font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">
                  📋 Solicitud de Ingreso Radicado: <strong>{rad_display}</strong>
                </span>
              </div>

              <h2 style="color: #0f172a; font-size: 20px; font-weight: 800; margin: 0 0 12px 0;">
                Hola, {nombre_display}
              </h2>

              <p style="font-size: 14px; line-height: 1.6; color: #475569; margin: 0 0 16px 0;">
                Has sido registrado(a) por <strong>{emp_display}</strong> en la solicitud de ingreso a instalaciones industriales identificada con radicado <strong>{rad_display}</strong>.
              </p>

              <!-- Marco Legal Ley 1581 de 2012 -->
              <div style="background-color: #f8fafc; border-left: 4px solid #0284c7; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                <h3 style="color: #0369a1; font-size: 13px; font-weight: 800; text-transform: uppercase; margin: 0 0 8px 0; letter-spacing: 0.5px;">
                  ⚖️ Autorización de Datos Personales (Ley 1581 de 2012)
                </h3>
                <p style="font-size: 13px; line-height: 1.6; color: #334155; margin: 0;">
                  De conformidad con la <strong>Ley Estatutaria 1581 de 2012</strong> y el <strong>Decreto 1377 de 2013</strong> de la República de Colombia, requerimos tu consentimiento previo, expreso e informado para el tratamiento de tus datos personales exclusivamente con fines de:
                </p>
                <ul style="font-size: 12px; line-height: 1.5; color: #475569; margin: 8px 0 0 0; padding-left: 20px;">
                  <li>Control de acceso, identificación y seguridad física en porterías y plantas industriales.</li>
                  <li>Verificación de cumplimiento de requisitos de seguridad y salud en el trabajo (SST).</li>
                  <li>Atención y coordinación de planes de emergencia y contingencias.</li>
                </ul>
              </div>

              <div style="background-color: #fff1f2; border: 1px solid #fecdd3; border-radius: 10px; padding: 12px 16px; margin-bottom: 24px;">
                <p style="color: #be123c; font-size: 12px; font-weight: 700; margin: 0; line-height: 1.5;">
                  ⚠️ <strong>Requisito Indispensable para tu Ingreso:</strong> Si no autorizas el tratamiento de tus datos personales, el sistema de portería bloqueará automáticamente tu acceso a las instalaciones, aún cuando la solicitud se encuentre aprobada administrativamente.
                </p>
              </div>

              <!-- Botón de Acción Principal -->
              <div style="text-align: center; margin: 30px 0;">
                <a href="{url_autorizacion}" target="_blank" style="display: inline-block; background-color: #0284c7; color: #ffffff; text-decoration: none; font-size: 15px; font-weight: 800; padding: 14px 32px; border-radius: 10px; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35); text-transform: uppercase; letter-spacing: 0.5px;">
                  Ver y Autorizar Tratamiento de Datos
                </a>
              </div>

              <p style="font-size: 12px; color: #64748b; text-align: center; margin: 0 0 8px 0;">
                Si el botón no funciona, puedes copiar y pegar el siguiente enlace en tu navegador:
              </p>
              <p style="font-size: 11px; color: #0284c7; text-align: center; word-break: break-all; margin: 0;">
                <a href="{url_autorizacion}" style="color: #0284c7;">{url_autorizacion}</a>
              </p>
            </td>
          </tr>

          <!-- Pie de Página Legal -->
          <tr>
            <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 28px; text-align: center;">
              <p style="font-size: 11px; color: #94a3b8; line-height: 1.5; margin: 0;">
                Como titular de los datos, tienes derecho a conocer, actualizar, rectificar y revocar tu autorización en cualquier momento conforme a la legislación colombiana vigente.
              </p>
              <p style="font-size: 11px; color: #cbd5e1; margin: 8px 0 0 0;">
                Este es un mensaje automático generado por la plataforma PSI. Por favor no responder a este correo.
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

