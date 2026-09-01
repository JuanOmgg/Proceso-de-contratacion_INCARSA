import os
import random
import hashlib
import bcrypt
import resend 
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status

from dotenv import load_dotenv

load_dotenv()

from src.schemas.auth_schema import RecuperacionInput, VerificarCodigoInput, RestablecerPasswordInput

from src.loaders.auth_loader import (
    SEARCH_userbyCorreo_db,
    POST_recoveryToken_db,
    GET_validateTokens_db,
    PATCH_password_db
)

resend.api_key = os.getenv("RESEND_API_KEY", "")

router = APIRouter(prefix="/auth", tags=["Autenticación"])

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_correo_smtp(destinatario: str, asunto: str, cuerpo_html: str) -> bool:
    load_dotenv()
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").replace(" ", "").strip()
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "INCARSA Soporte")

    if not smtp_user or not smtp_pass:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = f"{smtp_from_name} <{smtp_user}>"
    msg["To"] = destinatario
    msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=12) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [destinatario], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [destinatario], msg.as_string())
        print(f"[AUTH-SMTP] Correo de recuperacion enviado exitosamente a {destinatario}")
        return True
    except Exception as e:
        print(f"[AUTH-SMTP] Error enviando correo a {destinatario}: {e}")
        return False

@router.post("/solicitar_recuperacion", status_code=status.HTTP_200_OK)
def solicitar_recuperacion(payload: RecuperacionInput):
    correo = payload.correo.strip().lower()

    usuario = SEARCH_userbyCorreo_db(correo)

    mensaje_exito = {
        "exito": True,
        "mensaje": "Si el correo está registrado en el sistema, se ha enviado un código de recuperación."
    }

    if not usuario:
        print(f"[AUTH] Solicitud de recuperacion para correo no registrado: {correo}")
        return mensaje_exito

    codigo_plano = f"{random.randint(100000, 999999)}"
    codigo_hash = hashlib.sha256(codigo_plano.encode()).hexdigest()
    expiracion = datetime.utcnow() + timedelta(minutes=15)

    POST_recoveryToken_db(usuario["id_usuario"], codigo_hash, expiracion)

    html_correo = f"""
        <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 28px; border: 1px solid #e5e7eb; border-radius: 12px; background: #ffffff;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h2 style="color: #ea580c; margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 1px;">INCARSA</h2>
                <p style="color: #6b7280; font-size: 13px; margin-top: 4px;">Control y Gestión de Contratos</p>
            </div>
            <h3 style="color: #111827; font-size: 18px; margin-bottom: 12px;">Código de recuperación de contraseña</h3>
            <p style="color: #4b5563; font-size: 14px; line-height: 1.5; margin-bottom: 20px;">
                Has solicitado restablecer tu contraseña de acceso al sistema INCARSA. Utiliza el siguiente código de verificación:
            </p>
            <div style="background: #f9fafb; border: 2px dashed #ea580c; border-radius: 10px; padding: 18px; text-align: center; margin-bottom: 20px;">
                <span style="font-family: monospace, Courier; font-size: 34px; font-weight: bold; letter-spacing: 8px; color: #ea580c;">{codigo_plano}</span>
            </div>
            <p style="color: #6b7280; font-size: 13px; line-height: 1.5; margin-bottom: 24px;">
                Este código expira en <strong>15 minutos</strong>. Si no solicitaste este cambio, puedes ignorar este mensaje de forma segura.
            </p>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin-bottom: 16px;" />
            <p style="color: #9ca3af; font-size: 11px; text-align: center; margin: 0;">
                Este es un mensaje automático generado por la plataforma INCARSA. Por favor no responder a este correo.
            </p>
        </div>
    """

    email_enviado = False

    # 1. Intentar enviar con SMTP directo (llega a CUALQUIER correo corporativo/externo)
    email_enviado = enviar_correo_smtp(
        destinatario=correo,
        asunto="Código de recuperación de contraseña - INCARSA",
        cuerpo_html=html_correo
    )

    # 2. Si SMTP no está configurado, intentar con Resend como alternativa
    if not email_enviado:
        load_dotenv()
        api_key_actual = os.getenv("RESEND_API_KEY", resend.api_key)
        resend.api_key = api_key_actual

        if resend.api_key and not resend.api_key.startswith("re_XXXX"):
            try:
                resend.Emails.send({
                    "from": "PSI Soporte <onboarding@resend.dev>",
                    "to": [correo],
                    "subject": "Código de recuperación de contraseña - INCARSA",
                    "html": html_correo
                })
                email_enviado = True
                print(f"[AUTH-RESEND] Correo de recuperacion enviado exitosamente a: {correo}")
            except Exception as e:
                err_msg = str(e)
                print(f"[AUTH-RESEND] Intento de envio a {correo} devolvio: {err_msg}")
                if "testing emails to your own email address" in err_msg:
                    try:
                        resend.Emails.send({
                            "from": "PSI Soporte <onboarding@resend.dev>",
                            "to": ["juandeveloper2427@gmail.com"],
                            "subject": f"Código de recuperación de contraseña ({correo}) - INCARSA",
                            "html": html_correo
                        })
                        email_enviado = True
                        print(f"[AUTH-RESEND] Correo de recuperacion enviado a juandeveloper2427@gmail.com (cuenta Resend)")
                    except Exception as e2:
                        print(f"[AUTH-RESEND] Error enviando email a cuenta Resend: {e2}")

    print(f"[RECUPERACION] Codigo generado para '{correo}': {codigo_plano} (Email enviado: {email_enviado})")

    # Si el correo no pudo ser despachado, mostramos el código demo en el front para no bloquear la prueba
    if not email_enviado:
        mensaje_exito["codigo_demo"] = codigo_plano

    return mensaje_exito

@router.post("/verificar-codigo", status_code=status.HTTP_200_OK)
def verificar_codigo(payload: VerificarCodigoInput):
    correo = payload.correo.strip().lower()
    codigo_hash = hashlib.sha256(payload.codigo.strip().encode()).hexdigest()

    usuario = SEARCH_userbyCorreo_db(correo)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo no se encuentra registrado.")

    token_info = GET_validateTokens_db(usuario["id_usuario"], codigo_hash)
    if not token_info:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código ingresado es incorrecto.")

    if token_info.get("used"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este código ya ha sido utilizado.")

    expira_en = token_info.get("expiration_time")
    if expira_en and datetime.utcnow() > expira_en:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código ha expirado.")

    return {"exito": True, "mensaje": "Código verificado correctamente."}

@router.post("/restablecer-contrasena", status_code=status.HTTP_200_OK)
def restablecer_contrasena(payload: RestablecerPasswordInput):
    correo = payload.correo.strip().lower()
    codigo_hash = hashlib.sha256(payload.codigo.strip().encode()).hexdigest()

    usuario = SEARCH_userbyCorreo_db(correo)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Datos o código inválidos.")

    token_info = GET_validateTokens_db(usuario["id_usuario"], codigo_hash)
    
    if not token_info:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código ingresado es incorrecto.")

    if token_info.get("used"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este código ya ha sido utilizado.")

    expira_en = token_info.get("expiration_time")
    if expira_en and datetime.utcnow() > expira_en:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código ha expirado.")

    # Hashear contraseña con bcrypt para compatibilidad total con el sistema
    password_bytes = payload.nueva_contrasena.encode('utf-8')
    salt = bcrypt.gensalt()
    nueva_pass_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    actualizado = PATCH_password_db(usuario["id_usuario"], nueva_pass_hash, token_info["id"])
    if not actualizado:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo actualizar la contraseña.")

    return {"exito": True, "mensaje": "Contraseña actualizada correctamente."}
