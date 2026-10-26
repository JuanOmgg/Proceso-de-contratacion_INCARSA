import os
import random
import hashlib
import bcrypt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Response, Request

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
    MARK_2faToken_used_db,
    GET_latest_active_2fa_db,
    INCREMENT_intentos_2fa_db,
    GET_latest_active_reset_db,
    INCREMENT_intentos_reset_db
)

from src.utils.security import (
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user,
    hash_codigo_seguro,
    generar_codigo_otp,
    obtener_ip_cliente,
    verificar_rate_limit_ip
)
from src.loaders.superadmin_loader import GET_permisos_rol_db, GET_dos_pasos_status


router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Cooldown en memoria para prevenir spam de reenvío en el servidor (60 segundos)
_cooldown_recuperacion: dict[str, datetime] = {}
_cooldown_2fa: dict[int, datetime] = {}

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_correo_smtp(destinatario: str, asunto: str, cuerpo_html: str) -> bool:
    try:
        from src.loaders.superadmin_loader import GET_configuracion_correos_induccion_db
        cfg_correos = GET_configuracion_correos_induccion_db()
        if not cfg_correos.get("correos_habilitados", True):
            print(f"[AUTH-EMAIL-TEST-MODE] Despacho SMTP pausado por SuperAdmin. Envio simulado con exito hacia '{destinatario}'.")
            return True
    except Exception:
        pass

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
    """Genera la plantilla HTML ejecutiva con fondo blanco y acento Signal Red para el código 2FA."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Verificación en 2 Pasos — PSI INCARSA</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f1f5f9; padding: 36px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 540px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.06), 0 8px 10px -6px rgba(0, 0, 0, 0.04); border: 1px solid #e2e8f0;">
          
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
                🔐 Verificación en 2 Pasos (2FA)
              </div>
            </td>
          </tr>

          <!-- Contenido Principal -->
          <tr>
            <td style="padding: 28px 32px 32px 32px; background-color: #ffffff;">
              <h2 style="color: #0f172a; font-size: 19px; font-weight: 800; margin: 0 0 10px 0; text-align: center;">
                Tu código de acceso seguro
              </h2>
              <p style="font-size: 14px; line-height: 1.6; color: #334155; margin: 0 0 24px 0; text-align: center;">
                Hola <strong style="color: #0f172a;">{nombre_usuario}</strong>, se ha detectado un inicio de sesión en tu cuenta de la plataforma <strong style="color: #0f172a;">PSI</strong>. Ingresa el siguiente código temporal de 6 dígitos para verificar tu identidad:
              </p>

              <!-- Tarjeta OTP en Blanco y Signal Red -->
              <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #fb3b4c; border-radius: 12px; padding: 22px 16px; text-align: center; margin-bottom: 22px;">
                <div style="font-family: 'Courier New', Courier, monospace; font-size: 40px; font-weight: 900; letter-spacing: 12px; color: #fb3b4c; line-height: 1; padding-left: 12px;">
                  {codigo_plano}
                </div>
                <div style="margin-top: 12px; font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.8px;">
                  ⏱️ Válido por 10 minutos
                </div>
              </div>

              <!-- Aviso de seguridad -->
              <div style="background-color: #fff1f2; border-left: 4px solid #fb3b4c; border-radius: 8px; padding: 14px 16px; margin-bottom: 8px;">
                <p style="font-size: 12px; line-height: 1.5; color: #9f1239; margin: 0;">
                  🛡️ <strong style="color: #881337;">¿No fuiste tú?</strong> Si no estás intentando iniciar sesión en este momento, alguien podría tener tu contraseña. Te recomendamos comunicarte inmediatamente con el administrador del sistema.
                </p>
              </div>
            </td>
          </tr>

          <!-- Pie de Página -->
          <tr>
            <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 32px; text-align: center;">
              <p style="font-size: 11px; color: #64748b; line-height: 1.5; margin: 0;">
                <strong style="color: #0f172a;">INCARSA S.A.S.</strong> · NIT 830.078.829-5 · Plataforma PSI
              </p>
              <p style="font-size: 10px; color: #94a3b8; margin: 6px 0 0 0;">
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
    return enviar_correo_smtp(
        destinatario=destinatario,
        asunto="Código de verificación en 2 pasos - INCARSA",
        cuerpo_html=html
    )

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
        # Iniciar cooldown de 2FA
        _cooldown_2fa[usuario["id"]] = datetime.utcnow()
        codigo_plano = generar_codigo_otp()
        codigo_hash = hash_codigo_seguro(codigo_plano)
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

    cookie_secure = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("COOKIE_SECURE", "false").lower() == "true"
    # Establecer cookies de autenticación HttpOnly para proteger contra robo vía XSS
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        max_age=86400 * 7,
        path="/",
        samesite="lax",
        secure=cookie_secure
    )
    response.set_cookie(
        key="incarsa_token",
        value=token,
        httponly=True,
        max_age=86400 * 7,
        path="/",
        samesite="lax",
        secure=cookie_secure
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
def verificar_2fa(payload: Verificar2FAInput, request: Request, response: Response):
    """Valida el código OTP de 6 dígitos ingresado por el usuario, limita intentos a 5 y emite la sesión final."""
    # 1. Limitación de tasa por dirección IP (anti fuerza bruta)
    client_ip = obtener_ip_cliente(request)
    verificar_rate_limit_ip(client_ip)

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

    # 2. Consultar el último token 2FA activo generado
    token_info = GET_latest_active_2fa_db(user_id)
    if not token_info or token_info.get("used"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de verificación ya ha sido utilizado o no existe. Solicita uno nuevo."
        )

    if token_info.get("intentos", 0) >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Has superado el límite de 5 intentos fallidos. El código ha sido invalidado por seguridad. Solicita uno nuevo."
        )

    expira_en = token_info.get("expiration_time")
    if expira_en and datetime.utcnow() > expira_en:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de verificación ha expirado. Solicita un nuevo código."
        )

    codigo_hash = hash_codigo_seguro(payload.codigo)
    legacy_hash = hashlib.sha256(payload.codigo.strip().encode()).hexdigest()

    # 3. Validar coincidencia de hash
    if token_info["code_hash"] != codigo_hash and token_info["code_hash"] != legacy_hash:
        nuevos_intentos = INCREMENT_intentos_2fa_db(token_info["id"])
        if nuevos_intentos >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código incorrecto. Has alcanzado el límite de 5 intentos y el código ha sido invalidado. Solicita uno nuevo."
            )
        restantes = 5 - nuevos_intentos
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Código incorrecto. Te quedan {restantes} {'intento' if restantes == 1 else 'intentos'} antes de que el código sea bloqueado."
        )

    # Código correcto: marcar como utilizado
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

    cookie_secure = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("COOKIE_SECURE", "false").lower() == "true"
    # Establecer cookies de autenticación HttpOnly para proteger contra robo vía XSS
    response.set_cookie(
        key="token",
        value=final_token,
        httponly=True,
        max_age=86400 * 7,
        path="/",
        samesite="lax",
        secure=cookie_secure
    )
    response.set_cookie(
        key="incarsa_token",
        value=final_token,
        httponly=True,
        max_age=86400 * 7,
        path="/",
        samesite="lax",
        secure=cookie_secure
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

    # Cooldown de 60 segundos en el servidor para prevenir abuso de reenvío
    ahora = datetime.utcnow()
    ultimo_2fa = _cooldown_2fa.get(user_id)
    if ultimo_2fa:
        delta = (ahora - ultimo_2fa).total_seconds()
        if delta < 60:
            restante = int(60 - delta)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Debes esperar {restante} segundos antes de solicitar otro código de verificación."
            )
    _cooldown_2fa[user_id] = ahora

    codigo_plano = generar_codigo_otp()
    codigo_hash = hash_codigo_seguro(codigo_plano)
    expiracion = datetime.utcnow() + timedelta(minutes=10)

    POST_2faToken_db(user_id, codigo_hash, expiracion)

    nombre_usuario = usuario.get("nombres") if "nombres" in usuario else "Usuario"
    email_enviado = enviar_correo_2fa(correo, nombre_usuario, codigo_plano)

    return {
        "exito": True,
        "mensaje": "Se ha enviado un nuevo código de verificación a tu correo corporativo."
    }


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
def update_current_user_profile(payload: PerfilUpdateInput, response: Response, current_user: dict = Depends(get_current_user)):
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
        if len(pwd) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe tener al menos 8 caracteres."
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
    res_data = {
        "exito": True,
        "mensaje": "Perfil actualizado exitosamente.",
        "usuario": user_fresco.get("data", {})
    }

    # Si se actualizó la contraseña, emitir nuevo token válido para el usuario actual y renovar cookies
    if "contrasena" in updates:
        token_data = {
            "sub": str(user_id),
            "correo": user_fresco.get("data", {}).get("correo", current_user.get("correo")),
            "rol": current_user.get("rol", "USUARIO"),
            "id_rol": current_user.get("id_rol")
        }
        nuevo_token = create_access_token(data=token_data)
        res_data["access_token"] = nuevo_token
        res_data["token_type"] = "bearer"
        cookie_secure = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("COOKIE_SECURE", "false").lower() == "true"
        response.set_cookie(key="token", value=nuevo_token, httponly=True, max_age=86400 * 7, path="/", samesite="lax", secure=cookie_secure)
        response.set_cookie(key="incarsa_token", value=nuevo_token, httponly=True, max_age=86400 * 7, path="/", samesite="lax", secure=cookie_secure)

    return res_data

@router.post("/solicitar_recuperacion", status_code=status.HTTP_200_OK)
def solicitar_recuperacion(payload: RecuperacionInput):
    correo = payload.correo.strip().lower()

    # Rate limiting / cooldown en el servidor (60 segundos por correo)
    ahora = datetime.utcnow()
    ultimo_intento = _cooldown_recuperacion.get(correo)
    if ultimo_intento:
        delta = (ahora - ultimo_intento).total_seconds()
        if delta < 60:
            restante = int(60 - delta)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Debes esperar {restante} segundos antes de solicitar otro código de recuperación."
            )
    _cooldown_recuperacion[correo] = ahora

    # Mensaje genérico para prevenir enumeración de usuarios (CWE-204)
    mensaje_generico = "Si la dirección de correo ingresada se encuentra registrada y activa, recibirás un código de verificación."

    usuario = SEARCH_userbyCorreo_db(correo)

    if not usuario or not usuario.get("is_active"):
        if not usuario:
            print(f"[AUTH] Solicitud de recuperacion para correo no registrado: {correo}")
        else:
            print(f"[AUTH] Solicitud de recuperacion para usuario inactivo: {correo}")
        return {
            "exito": True,
            "mensaje": mensaje_generico
        }

    codigo_plano = generar_codigo_otp()
    codigo_hash = hash_codigo_seguro(codigo_plano)
    expiracion = datetime.utcnow() + timedelta(minutes=15)

    POST_recoveryToken_db(usuario["id_usuario"], codigo_hash, expiracion)

    html_correo = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Recuperación de Contraseña — PSI INCARSA</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f1f5f9; padding: 36px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 540px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.06), 0 8px 10px -6px rgba(0, 0, 0, 0.04); border: 1px solid #e2e8f0;">
          
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
                🔑 Seguridad de la Cuenta
              </div>
            </td>
          </tr>

          <!-- Contenido Principal -->
          <tr>
            <td style="padding: 28px 32px 32px 32px; background-color: #ffffff;">
              <h2 style="color: #0f172a; font-size: 19px; font-weight: 800; margin: 0 0 10px 0; text-align: center;">
                Código de verificación
              </h2>
              <p style="font-size: 14px; line-height: 1.6; color: #334155; margin: 0 0 24px 0; text-align: center;">
                Has solicitado restablecer tu contraseña de acceso al sistema <strong style="color: #0f172a;">PSI</strong>. Utiliza el siguiente código para completar la verificación:
              </p>

              <!-- Tarjeta OTP en Blanco y Signal Red -->
              <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #fb3b4c; border-radius: 12px; padding: 22px 16px; text-align: center; margin-bottom: 22px;">
                <div style="font-family: 'Courier New', Courier, monospace; font-size: 38px; font-weight: 900; letter-spacing: 10px; color: #fb3b4c; line-height: 1; padding-left: 10px;">
                  {codigo_plano}
                </div>
                <div style="margin-top: 10px; font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.8px;">
                  ⏱️ Válido por 15 minutos
                </div>
              </div>

              <!-- Aviso de seguridad -->
              <div style="background-color: #fff1f2; border-left: 4px solid #fb3b4c; border-radius: 8px; padding: 14px 16px; margin-bottom: 8px;">
                <p style="font-size: 12px; line-height: 1.5; color: #9f1239; margin: 0;">
                  🛡️ <strong style="color: #881337;">¿No solicitaste este código?</strong> Si no realizaste esta solicitud, puedes ignorar este mensaje con total seguridad. Tu contraseña actual no se modificará.
                </p>
              </div>
            </td>
          </tr>

          <!-- Pie de Página -->
          <tr>
            <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 32px; text-align: center;">
              <p style="font-size: 11px; color: #64748b; line-height: 1.5; margin: 0;">
                <strong style="color: #0f172a;">INCARSA S.A.S.</strong> · NIT 830.078.829-5 · Plataforma PSI
              </p>
              <p style="font-size: 10px; color: #94a3b8; margin: 6px 0 0 0;">
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

    # Despachar código por SMTP directo
    email_enviado = enviar_correo_smtp(
        destinatario=correo,
        asunto="Código de recuperación de contraseña - INCARSA",
        cuerpo_html=html_correo
    )

    print(f"[RECUPERACION] Codigo generado para '{correo}': {codigo_plano} (Email enviado: {email_enviado})")

    return {
        "exito": True,
        "mensaje": mensaje_generico
    }

@router.post("/verificar-codigo", status_code=status.HTTP_200_OK)
def verificar_codigo(payload: VerificarCodigoInput, request: Request):
    # 1. Limitación de tasa por IP
    client_ip = obtener_ip_cliente(request)
    verificar_rate_limit_ip(client_ip)

    correo = payload.correo.strip().lower()
    usuario = SEARCH_userbyCorreo_db(correo)
    if not usuario or not usuario.get("is_active"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código ingresado es incorrecto o ha expirado.")

    token_info = GET_latest_active_reset_db(usuario["id_usuario"])
    if not token_info or token_info.get("used"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código ingresado es incorrecto o ha expirado.")

    if token_info.get("intentos", 0) >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Has superado el límite de 5 intentos permitidos. El código ha sido invalidado por seguridad. Solicita uno nuevo."
        )

    expira_en = token_info.get("expiration_time")
    if expira_en and datetime.utcnow() > expira_en:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código ha expirado.")

    codigo_hash = hash_codigo_seguro(payload.codigo)
    legacy_hash = hashlib.sha256(payload.codigo.strip().encode()).hexdigest()

    if token_info["code_hash"] != codigo_hash and token_info["code_hash"] != legacy_hash:
        nuevos_intentos = INCREMENT_intentos_reset_db(token_info["id"])
        if nuevos_intentos >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código incorrecto. Has alcanzado el límite de 5 intentos y el código ha sido invalidado. Solicita uno nuevo."
            )
        restantes = 5 - nuevos_intentos
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Código incorrecto. Te quedan {restantes} {'intento' if restantes == 1 else 'intentos'} antes de que el código sea bloqueado."
        )

    return {"exito": True, "mensaje": "Código verificado correctamente."}

@router.post("/restablecer-contrasena", status_code=status.HTTP_200_OK)
def restablecer_contrasena(payload: RestablecerPasswordInput, request: Request):
    # 1. Limitación de tasa por IP
    client_ip = obtener_ip_cliente(request)
    verificar_rate_limit_ip(client_ip)

    correo = payload.correo.strip().lower()
    usuario = SEARCH_userbyCorreo_db(correo)
    if not usuario or not usuario.get("is_active"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código ingresado es incorrecto o ha expirado.")

    token_info = GET_latest_active_reset_db(usuario["id_usuario"])
    if not token_info or token_info.get("used"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código ingresado es incorrecto o ha expirado.")

    if token_info.get("intentos", 0) >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Has superado el límite de 5 intentos permitidos. El código ha sido invalidado por seguridad. Solicita uno nuevo."
        )

    expira_en = token_info.get("expiration_time")
    if expira_en and datetime.utcnow() > expira_en:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código ha expirado.")

    codigo_hash = hash_codigo_seguro(payload.codigo)
    legacy_hash = hashlib.sha256(payload.codigo.strip().encode()).hexdigest()

    if token_info["code_hash"] != codigo_hash and token_info["code_hash"] != legacy_hash:
        nuevos_intentos = INCREMENT_intentos_reset_db(token_info["id"])
        if nuevos_intentos >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código incorrecto. Has alcanzado el límite de 5 intentos y el código ha sido invalidado. Solicita uno nuevo."
            )
        restantes = 5 - nuevos_intentos
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Código incorrecto. Te quedan {restantes} {'intento' if restantes == 1 else 'intentos'} antes de que el código sea bloqueado."
        )

    # Hashear contraseña con bcrypt para compatibilidad total con el sistema
    password_bytes = payload.nueva_contrasena.encode('utf-8')
    salt = bcrypt.gensalt()
    nueva_pass_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    actualizado = PATCH_password_db(usuario["id_usuario"], nueva_pass_hash, token_info["id"])
    if not actualizado:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo actualizar la contraseña.")

    return {"exito": True, "mensaje": "Contraseña actualizada correctamente."}

@router.post("/logout", summary="Cerrar sesión y limpiar cookies HttpOnly", status_code=status.HTTP_200_OK)
def logout_endpoint(response: Response):
    """Elimina las cookies de autenticación HttpOnly emitidas por el servidor."""
    response.delete_cookie(key="token", path="/")
    response.delete_cookie(key="incarsa_token", path="/")
    response.delete_cookie(key="access_token", path="/")
    return {"exito": True, "mensaje": "Sesión cerrada exitosamente."}
