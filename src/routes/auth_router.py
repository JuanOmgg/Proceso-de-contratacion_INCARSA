import os
import random
import hashlib
import bcrypt
import resend 
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Response

from dotenv import load_dotenv

load_dotenv()

from src.schemas.auth_schema import (
    LoginInput,
    RecuperacionInput,
    VerificarCodigoInput,
    RestablecerPasswordInput,
    PerfilUpdateInput,
    Verificar2FAInput,
    Reenviar2FAInput
)

from src.loaders.auth_loader import (
    SEARCH_userbyCorreo_db,
    GET_user_for_login_db,
    POST_recoveryToken_db,
    GET_validateTokens_db,
    PATCH_password_db,
    POST_2faToken_db,
    GET_validate2faToken_db,
    MARK_2faToken_used_db
)

from src.utils.security import verify_password, create_access_token, decode_access_token, get_current_user
from src.loaders.superadmin_loader import GET_permisos_rol_db, GET_dos_pasos_status


resend.api_key = os.getenv("RESEND_API_KEY", "")

router = APIRouter(prefix="/auth", tags=["Autenticación"])

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_correo_smtp(destinatario: str, asunto: str, cuerpo_html: str) -> bool:
    load_dotenv(override=True)
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

def ofuscar_correo(email: str) -> str:
    """Ofusca un correo electrónico para visualización segura: ej. j***o@incarsa.com.co"""
    try:
        partes = email.strip().split("@")
        if len(partes) != 2:
            return email
        nombre, dominio = partes
        if len(nombre) <= 2:
            nombre_ofuscado = nombre[0] + "***"
        else:
            nombre_ofuscado = nombre[0] + "***" + nombre[-1]
        return f"{nombre_ofuscado}@{dominio}"
    except Exception:
        return email

def generar_html_correo_2fa(nombre_usuario: str, codigo_plano: str) -> str:
    """Genera la plantilla HTML con estética Dark Premium para el correo de verificación en dos pasos."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="dark">
  <title>Verificación en 2 Pasos — PSI INCARSA</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b1120; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e2e8f0;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #0b1120; padding: 36px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 540px; background-color: #0f172a; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 45px -10px rgba(0, 0, 0, 0.7); border: 1px solid #1e293b;">
          
          <!-- Franja superior en degradado Sky / Indigo Neón -->
          <tr>
            <td style="height: 5px; background: linear-gradient(90deg, #38bdf8 0%, #6366f1 50%, #2563eb 100%); line-height: 5px; font-size: 1px;">&nbsp;</td>
          </tr>

          <!-- Encabezado Institucional -->
          <tr>
            <td style="padding: 32px 32px 20px 32px; text-align: center; border-bottom: 1px solid #1e293b;">
              <h1 style="color: #ffffff; font-size: 24px; font-weight: 800; margin: 0; letter-spacing: 0.5px; font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
                INCARSA <span style="color: #38bdf8; font-weight: 300;">·</span> <span style="color: #cbd5e1; font-size: 18px; font-weight: 500;">Gestión de Acceso a Planta</span>
              </h1>
              <p style="color: #94a3b8; font-size: 12px; font-weight: 500; margin: 6px 0 0 0;">
                Sistema de Control y Gestión de Seguridad · Plataforma PSI
              </p>
              <div style="display: inline-block; background-color: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 20px; padding: 4px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 14px;">
                🔐 Verificación en 2 Pasos (2FA)
              </div>
            </td>
          </tr>

          <!-- Contenido Principal -->
          <tr>
            <td style="padding: 28px 32px 32px 32px;">
              <h2 style="color: #ffffff; font-size: 19px; font-weight: 800; margin: 0 0 12px 0; text-align: center;">
                Tu código de acceso seguro
              </h2>
              <p style="font-size: 14px; line-height: 1.6; color: #cbd5e1; margin: 0 0 24px 0; text-align: center;">
                Hola <strong style="color: #ffffff;">{nombre_usuario}</strong>, se ha detectado un inicio de sesión en tu cuenta de la plataforma <strong style="color: #ffffff;">PSI</strong>. Ingresa el siguiente código temporal de 6 dígitos para verificar tu identidad:
              </p>

              <!-- Tarjeta OTP en Modo Oscuro -->
              <div style="background-color: #020617; border: 1px solid #1e293b; border-radius: 12px; padding: 22px 16px; text-align: center; margin-bottom: 22px; box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5);">
                <div style="font-family: 'Courier New', Courier, monospace; font-size: 40px; font-weight: 900; letter-spacing: 12px; color: #38bdf8; line-height: 1; padding-left: 12px;">
                  {codigo_plano}
                </div>
                <div style="margin-top: 12px; font-size: 12px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px;">
                  ⏱️ Válido por 10 minutos
                </div>
              </div>

              <!-- Aviso de seguridad -->
              <div style="background-color: rgba(56, 189, 248, 0.05); border-left: 4px solid #38bdf8; border-radius: 8px; padding: 14px 16px; margin-bottom: 8px;">
                <p style="font-size: 12px; line-height: 1.5; color: #cbd5e1; margin: 0;">
                  🛡️ <strong style="color: #ffffff;">¿No fuiste tú?</strong> Si no estás intentando iniciar sesión en este momento, alguien podría tener tu contraseña. Te recomendamos comunicarte inmediatamente con el administrador del sistema.
                </p>
              </div>
            </td>
          </tr>

          <!-- Pie de Página -->
          <tr>
            <td style="background-color: #080d19; border-top: 1px solid #1e293b; padding: 20px 32px; text-align: center;">
              <p style="font-size: 11px; color: #94a3b8; line-height: 1.5; margin: 0;">
                <strong style="color: #ffffff;">INCARSA</strong> · Industria de Alimentos y Concentrados de Santander · Plataforma PSI
              </p>
              <p style="font-size: 10px; color: #64748b; margin: 6px 0 0 0;">
                Este es un mensaje generado automáticamente por el sistema de seguridad. Por favor, no respondas a este correo.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

def enviar_correo_2fa(destinatario: str, nombre_usuario: str, codigo_plano: str) -> bool:
    html = generar_html_correo_2fa(nombre_usuario, codigo_plano)
    enviado = enviar_correo_smtp(
        destinatario=destinatario,
        asunto="Código de verificación en 2 pasos - INCARSA",
        cuerpo_html=html
    )
    if not enviado:
        load_dotenv()
        api_key_actual = os.getenv("RESEND_API_KEY", resend.api_key)
        resend.api_key = api_key_actual
        if resend.api_key and not resend.api_key.startswith("re_XXXX"):
            try:
                resend.Emails.send({
                    "from": "PSI Soporte <onboarding@resend.dev>",
                    "to": [destinatario],
                    "subject": "Código de verificación en 2 pasos - INCARSA",
                    "html": html
                })
                enviado = True
                print(f"[AUTH-RESEND] Correo 2FA enviado exitosamente a: {destinatario}")
            except Exception as e:
                err_msg = str(e)
                print(f"[AUTH-RESEND] Intento de envio 2FA a {destinatario} devolvio: {err_msg}")
                if "testing emails to your own email address" in err_msg:
                    try:
                        resend.Emails.send({
                            "from": "PSI Soporte <onboarding@resend.dev>",
                            "to": ["juandeveloper2427@gmail.com"],
                            "subject": f"Código de verificación en 2 pasos ({destinatario}) - INCARSA",
                            "html": html
                        })
                        enviado = True
                    except Exception as e2:
                        print(f"[AUTH-RESEND] Error enviando email 2FA a cuenta Resend: {e2}")
    return enviado

@router.post("/login", status_code=status.HTTP_200_OK)
def login(payload: LoginInput, response: Response):
    correo = payload.correo.strip().lower()
    usuario = GET_user_for_login_db(correo)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas."
        )

    is_active_val = usuario.get("is_active")
    if not is_active_val or str(is_active_val).strip() in ("0", "false", "False"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta se encuentra inactiva. Comunícate con el administrador."
        )

    # Validar contraseña con bcrypt mediante security.py
    contrasena_almacenada = usuario.get("contrasena") or ""
    if not verify_password(payload.contrasena, contrasena_almacenada):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas."
        )

    # =========================================================================
    # VERIFICACIÓN EN 2 PASOS (2FA) ACTIVADA POR EL SUPERADMINISTRADOR
    # =========================================================================
    dos_pasos_activo = GET_dos_pasos_status()
    if dos_pasos_activo:
        codigo_plano = f"{random.randint(100000, 999999)}"
        codigo_hash = hashlib.sha256(codigo_plano.encode()).hexdigest()
        expiracion = datetime.utcnow() + timedelta(minutes=10)

        POST_2faToken_db(usuario["id"], codigo_hash, expiracion)

        nombre_usuario = usuario.get("nombres", "Usuario")
        email_enviado = enviar_correo_2fa(usuario["correo"], nombre_usuario, codigo_plano)

        # Generar token temporal de 2FA firmado con expiración de 10 minutos
        temp_token = create_access_token(
            data={
                "sub": str(usuario["id"]),
                "correo": usuario["correo"],
                "tipo": "2fa_pending"
            },
            expires_delta=timedelta(minutes=10)
        )

        res_payload = {
            "exito": True,
            "requiere_2fa": True,
            "mensaje": "Se ha enviado un código de verificación de 6 dígitos a tu correo corporativo.",
            "temp_token": temp_token,
            "correo_ofuscado": ofuscar_correo(usuario["correo"])
        }

        # Si el correo no pudo ser despachado por SMTP/Resend en entorno local, incluir código demo
        if not email_enviado:
            res_payload["codigo_demo"] = codigo_plano

        return res_payload

    # =========================================================================
    # LOGIN DIRECTO (Si 2FA está desactivado por el Superadministrador)
    # =========================================================================
    token_data = {
        "sub": str(usuario["id"]),
        "correo": usuario["correo"],
        "rol": usuario.get("rol", "USUARIO"),
        "id_rol": usuario.get("id_rol")
    }

    token = create_access_token(data=token_data)
    nombre_completo = f"{usuario.get('nombres', '')} {usuario.get('apellidos', '')}".strip()

    permisos_info = GET_permisos_rol_db(int(usuario["id_rol"])) if usuario.get("id_rol") else {}

    # Establecer cookies de autenticación para navegaciones directas del navegador
    response.set_cookie(
        key="token",
        value=token,
        httponly=False,
        max_age=86400 * 7,
        path="/",
        samesite="lax"
    )
    response.set_cookie(
        key="incarsa_token",
        value=token,
        httponly=False,
        max_age=86400 * 7,
        path="/",
        samesite="lax"
    )

    return {
        "exito": True,
        "mensaje": "Inicio de sesión exitoso.",
        "access_token": token,
        "token_type": "bearer",
        "permisos": permisos_info.get("permisos", {}),
        "usuario": {
            "id": usuario["id"],
            "nombre": nombre_completo,
            "correo": usuario["correo"],
            "rol": usuario.get("rol", "USUARIO"),
            "id_rol": usuario.get("id_rol"),
            "plantas_ids": usuario.get("plantas_ids", []),
            "plantas": usuario.get("plantas", [])
        }
    }

@router.post("/verificar-2fa", status_code=status.HTTP_200_OK)
def verificar_2fa(payload: Verificar2FAInput, response: Response):
    """Valida el código OTP de 6 dígitos ingresado por el usuario y emite la sesión final."""
    token_data = decode_access_token(payload.temp_token)
    if not token_data or token_data.get("tipo") != "2fa_pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La sesión de verificación ha expirado o no es válida. Por favor, inicia sesión nuevamente."
        )

    try:
        user_id = int(token_data.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador de usuario inválido en la sesión."
        )

    codigo_hash = hashlib.sha256(payload.codigo.strip().encode()).hexdigest()

    token_info = GET_validate2faToken_db(user_id, codigo_hash)
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de verificación ingresado es incorrecto."
        )

    if token_info.get("used"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este código de verificación ya ha sido utilizado."
        )

    expira_en = token_info.get("expiration_time")
    if expira_en and datetime.utcnow() > expira_en:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de verificación ha expirado. Solicita un nuevo código."
        )

    # Marcar token como utilizado
    MARK_2faToken_used_db(token_info["id"])

    # Obtener datos frescos del usuario para emitir la sesión final
    correo = token_data.get("correo", "").strip().lower()
    usuario = GET_user_for_login_db(correo)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en el sistema."
        )

    is_active_val = usuario.get("is_active")
    if not is_active_val or str(is_active_val).strip() in ("0", "false", "False"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta se encuentra inactiva. Comunícate con el administrador."
        )

    # Construir token JWT final
    final_token_data = {
        "sub": str(usuario["id"]),
        "correo": usuario["correo"],
        "rol": usuario.get("rol", "USUARIO"),
        "id_rol": usuario.get("id_rol")
    }

    final_token = create_access_token(data=final_token_data)
    nombre_completo = f"{usuario.get('nombres', '')} {usuario.get('apellidos', '')}".strip()
    permisos_info = GET_permisos_rol_db(int(usuario["id_rol"])) if usuario.get("id_rol") else {}

    # Establecer cookies de autenticación
    response.set_cookie(
        key="token",
        value=final_token,
        httponly=False,
        max_age=86400 * 7,
        path="/",
        samesite="lax"
    )
    response.set_cookie(
        key="incarsa_token",
        value=final_token,
        httponly=False,
        max_age=86400 * 7,
        path="/",
        samesite="lax"
    )

    return {
        "exito": True,
        "mensaje": "Verificación en 2 pasos completada exitosamente.",
        "access_token": final_token,
        "token_type": "bearer",
        "permisos": permisos_info.get("permisos", {}),
        "usuario": {
            "id": usuario["id"],
            "nombre": nombre_completo,
            "correo": usuario["correo"],
            "rol": usuario.get("rol", "USUARIO"),
            "id_rol": usuario.get("id_rol"),
            "plantas_ids": usuario.get("plantas_ids", []),
            "plantas": usuario.get("plantas", [])
        }
    }

@router.post("/reenviar-2fa", status_code=status.HTTP_200_OK)
def reenviar_2fa(payload: Reenviar2FAInput):
    """Reenvía un nuevo código OTP de 6 dígitos al correo del usuario en proceso de verificación."""
    token_data = decode_access_token(payload.temp_token)
    if not token_data or token_data.get("tipo") != "2fa_pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La sesión de verificación ha expirado. Por favor, inicia sesión nuevamente."
        )

    try:
        user_id = int(token_data.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador de usuario inválido en la sesión."
        )

    correo = token_data.get("correo", "").strip().lower()
    usuario = SEARCH_userbyCorreo_db(correo)
    if not usuario or not usuario.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no se encuentra activo."
        )

    codigo_plano = f"{random.randint(100000, 999999)}"
    codigo_hash = hashlib.sha256(codigo_plano.encode()).hexdigest()
    expiracion = datetime.utcnow() + timedelta(minutes=10)

    POST_2faToken_db(user_id, codigo_hash, expiracion)

    nombre_usuario = usuario.get("nombres") if "nombres" in usuario else "Usuario"
    email_enviado = enviar_correo_2fa(correo, nombre_usuario, codigo_plano)

    res = {
        "exito": True,
        "mensaje": "Se ha enviado un nuevo código de verificación a tu correo corporativo."
    }
    if not email_enviado:
        res["codigo_demo"] = codigo_plano

    return res


@router.get("/me", summary="Obtener perfil del usuario autenticado", status_code=status.HTTP_200_OK)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id")
    from src.services.usuario import READ_user
    if user_id:
        res = READ_user(user_id)
        if res.get("exito") and res.get("data"):
            return {
                "exito": True,
                "usuario": res["data"]
            }
    return {
        "exito": True,
        "usuario": current_user
    }

@router.patch("/me", summary="Actualizar perfil del usuario autenticado (teléfono y contraseña)", status_code=status.HTTP_200_OK)
def update_current_user_profile(payload: PerfilUpdateInput, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado."
        )

    updates = {}
    if payload.num_telefono is not None:
        t_clean = str(payload.num_telefono).strip()
        if t_clean:
            if not t_clean.isdigit():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El número de teléfono debe contener únicamente dígitos."
                )
            if len(t_clean) < 7 or len(t_clean) > 15:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El número de teléfono debe tener entre 7 y 15 dígitos."
                )
            updates["num_telefono"] = t_clean

    if payload.contrasena is not None and str(payload.contrasena).strip():
        pwd = str(payload.contrasena).strip()
        if len(pwd) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe tener al menos 6 caracteres."
            )
        if payload.confirmar_contrasena is not None:
            if pwd != str(payload.confirmar_contrasena).strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Las contraseñas ingresadas no coinciden."
                )
        updates["contrasena"] = pwd

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron datos para actualizar."
        )

    from src.loaders.usuario_loader import UPDATE_user_db
    res = UPDATE_user_db(int(user_id), updates)
    if not res.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("mensaje", "Error al actualizar el perfil.")
        )

    from src.services.usuario import READ_user
    user_fresco = READ_user(int(user_id))
    return {
        "exito": True,
        "mensaje": "Perfil actualizado exitosamente.",
        "usuario": user_fresco.get("data", {})
    }

@router.post("/solicitar_recuperacion", status_code=status.HTTP_200_OK)
def solicitar_recuperacion(payload: RecuperacionInput):
    correo = payload.correo.strip().lower()

    usuario = SEARCH_userbyCorreo_db(correo)

    if not usuario:
        print(f"[AUTH] Solicitud de recuperacion para correo no registrado: {correo}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El correo ingresado no se encuentra registrado en el sistema."
        )

    if not usuario.get("is_active"):
        print(f"[AUTH] Solicitud de recuperacion para usuario inactivo: {correo}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario asociado a este correo se encuentra inactivo. Comunícate con el administrador."
        )

    mensaje_exito = {
        "exito": True,
        "mensaje": "Se ha enviado un código de recuperación a tu correo electrónico."
    }

    codigo_plano = f"{random.randint(100000, 999999)}"
    codigo_hash = hashlib.sha256(codigo_plano.encode()).hexdigest()
    expiracion = datetime.utcnow() + timedelta(minutes=15)

    POST_recoveryToken_db(usuario["id_usuario"], codigo_hash, expiracion)

    html_correo = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="dark">
  <title>Recuperación de Contraseña — PSI INCARSA</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b1120; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e2e8f0;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #0b1120; padding: 36px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 540px; background-color: #0f172a; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 45px -10px rgba(0, 0, 0, 0.7); border: 1px solid #1e293b;">
          
          <!-- Franja superior en degradado Sky / Blue Neón -->
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
                Sistema de Control y Gestión de Seguridad · Plataforma PSI
              </p>
              <div style="display: inline-block; background-color: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 20px; padding: 4px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 14px;">
                Seguridad de la Cuenta
              </div>
            </td>
          </tr>

          <!-- Contenido Principal -->
          <tr>
            <td style="padding: 28px 32px 32px 32px;">
              <h2 style="color: #ffffff; font-size: 19px; font-weight: 800; margin: 0 0 12px 0; text-align: center;">
                Código de verificación
              </h2>
              <p style="font-size: 14px; line-height: 1.6; color: #cbd5e1; margin: 0 0 24px 0; text-align: center;">
                Has solicitado restablecer tu contraseña de acceso al sistema <strong style="color: #ffffff;">PSI</strong>. Utiliza el siguiente código para completar la verificación:
              </p>

              <!-- Tarjeta OTP en Modo Oscuro (High Contrast Sky Blue) -->
              <div style="background-color: #020617; border: 1px solid #1e293b; border-radius: 12px; padding: 22px 16px; text-align: center; margin-bottom: 22px; box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5);">
                <div style="font-family: 'Courier New', Courier, monospace; font-size: 38px; font-weight: 900; letter-spacing: 10px; color: #38bdf8; line-height: 1; padding-left: 10px;">
                  {codigo_plano}
                </div>
                <div style="margin-top: 10px; font-size: 12px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px;">
                  ⏱️ Válido por 15 minutos
                </div>
              </div>

              <!-- Aviso de seguridad en modo oscuro -->
              <div style="background-color: rgba(56, 189, 248, 0.05); border-left: 4px solid #38bdf8; border-radius: 8px; padding: 14px 16px; margin-bottom: 8px;">
                <p style="font-size: 12px; line-height: 1.5; color: #cbd5e1; margin: 0;">
                  🛡️ <strong style="color: #ffffff;">¿No solicitaste este código?</strong> Si no realizaste esta solicitud, puedes ignorar este mensaje con total seguridad. Tu contraseña actual no se modificará.
                </p>
              </div>
            </td>
          </tr>

          <!-- Pie de Página: Modo Oscuro -->
          <tr>
            <td style="background-color: #080d19; border-top: 1px solid #1e293b; padding: 20px 32px; text-align: center;">
              <p style="font-size: 11px; color: #94a3b8; line-height: 1.5; margin: 0;">
                <strong style="color: #ffffff;">INCARSA</strong> · Industria de Alimentos y Concentrados de Santander · Plataforma PSI
              </p>
              <p style="font-size: 10px; color: #64748b; margin: 6px 0 0 0;">
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El correo no se encuentra registrado.")

    if not usuario.get("is_active"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El usuario se encuentra inactivo.")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El correo no se encuentra registrado.")

    if not usuario.get("is_active"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El usuario se encuentra inactivo.")

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
