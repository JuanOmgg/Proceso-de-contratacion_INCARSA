import os
import re
import secrets
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
import bcrypt

import time
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

security_scheme = HTTPBearer()

# Carga de clave JWT: sin claves de respaldo quemadas en el código fuente
_raw_secret = os.getenv("JWT_SECRET_KEY", "").strip()
if not _raw_secret:
    if os.getenv("ENVIRONMENT", "").lower() == "production":
        raise RuntimeError("FATAL: La variable de entorno 'JWT_SECRET_KEY' no está configurada en producción. Por seguridad, configúrela en el archivo .env.")
    # Genera una clave efímera criptográficamente segura para la sesión actual si no se definió en .env
    _raw_secret = secrets.token_urlsafe(64)
    print("⚠️ [SEGURIDAD] 'JWT_SECRET_KEY' no está definida en .env. Se generó una clave efímera segura en memoria para esta sesión.")

SECRET_KEY = _raw_secret

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

def generar_codigo_otp() -> str:
    """Genera un código OTP de 6 dígitos criptográficamente seguro usando secrets (CSPRNG)."""
    return f"{secrets.randbelow(900000) + 100000}"

def obtener_ip_cliente(request: Request) -> str:
    """Extrae la IP del cliente considerando encabezados de proxy inverso."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

_ip_verificacion_intentos: dict[str, list[float]] = {}

def verificar_rate_limit_ip(ip: str, max_intentos: int = 15, ventana_segundos: int = 60) -> None:
    """Limita la tasa de intentos de verificación por dirección IP (previene ataques de fuerza bruta)."""
    ahora = time.time()
    historial = _ip_verificacion_intentos.get(ip, [])
    historial = [t for t in historial if ahora - t < ventana_segundos]
    
    if len(historial) >= max_intentos:
        _ip_verificacion_intentos[ip] = historial
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de verificación desde esta dirección IP. Por favor espera un momento antes de reintentar."
        )
    
    historial.append(ahora)
    _ip_verificacion_intentos[ip] = historial

def hash_codigo_seguro(codigo: str) -> str:
    """Calcula un hash HMAC-SHA256 con la clave secreta del servidor para códigos de 6 dígitos.
    Evita ataques de reversión por diccionario/fuerza bruta sobre el millón de combinaciones
    en caso de filtración de la base de datos.
    """
    key = SECRET_KEY.encode('utf-8')
    data = str(codigo).strip().encode('utf-8')
    return hmac.new(key, data, hashlib.sha256).hexdigest()

def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        print(f"Error verificando contraseña: {e}")
        return False

_user_sessions_revoked_at: dict[int, int] = {}

def invalidate_user_sessions(user_id: int, timestamp: int | None = None) -> None:
    """Invalida todas las sesiones JWT de un usuario emitidas antes del timestamp actual."""
    ts = timestamp or int(datetime.now(timezone.utc).timestamp())
    _user_sessions_revoked_at[int(user_id)] = ts
    try:
        from database import GET_conexion
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE usuarios SET password_changed_at = FROM_UNIXTIME(%s) WHERE id = %s",
                    (ts, int(user_id))
                )
                conn.commit()
    except Exception as e:
        print(f"⚠️ [SEGURIDAD] Error actualizando password_changed_at en BD: {e}")

def get_user_sessions_revoked_at(user_id: int) -> int:
    """Obtiene el timestamp de última revocación en memoria o consulta la BD si no está en caché."""
    uid = int(user_id)
    if uid in _user_sessions_revoked_at:
        return _user_sessions_revoked_at[uid]
    
    try:
        from database import GET_conexion
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT UNIX_TIMESTAMP(password_changed_at) AS ts FROM usuarios WHERE id = %s",
                    (uid,)
                )
                row = cur.fetchone()
                if row and row.get("ts") is not None:
                    ts = int(row["ts"])
                    _user_sessions_revoked_at[uid] = ts
                    return ts
                else:
                    _user_sessions_revoked_at[uid] = 0
                    return 0
    except Exception as e:
        print(f"⚠️ [SEGURIDAD] Error consultando password_changed_at: {e}")
        return 0

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Genera un token JWT firmado con fecha de emisión (iat) y expiración (exp)."""
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)

    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": int(now_utc.timestamp())
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("El token ha expirado.")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Token inválido: {e}")
        return None
    except Exception as e:
        print(f"Error decodificando el token: {e}")
        return None
    
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """Extrae el token del header Authorization, lo valida y comprueba que la sesión no haya sido invalidada por cambio de clave."""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado. Por favor, inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("tipo") == "2fa_pending":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación incompleta. Debes completar la verificación en 2 pasos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Asegurar conveniencia de acceso al id del usuario
    if "sub" in payload and "id" not in payload:
        try:
            payload["id"] = int(payload["sub"])
        except ValueError:
            payload["id"] = payload["sub"]

    # Validar si el token fue emitido antes de un cambio de contraseña
    user_id_val = payload.get("id") or payload.get("sub")
    if user_id_val is not None:
        try:
            uid = int(user_id_val)
            token_iat = payload.get("iat")
            revoked_at = get_user_sessions_revoked_at(uid)
            if revoked_at and revoked_at > 0:
                if token_iat is None or int(token_iat) < revoked_at:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="La sesión ha expirado porque la contraseña fue modificada. Por favor, inicia sesión nuevamente.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        except HTTPException:
            raise
        except Exception as e:
            pass

    return payload

def require_role(roles_permitidos: list[str | int]):
    """Dependencia para restringir rutas a roles específicos (por nombre o id)."""
    def rol_checker(current_user: dict = Depends(get_current_user)):
        user_rol = str(current_user.get("rol", "")).strip().lower()
        user_id_rol = str(current_user.get("id_rol", "")).strip()

        permitidos_norm = [str(r).strip().lower() for r in roles_permitidos]

        # SuperAdmin hereda todos los permisos y tiene acceso total
        if user_rol in ("superadmin", "super admin", "super_admin"):
            return current_user

        if user_rol not in permitidos_norm and user_id_rol not in permitidos_norm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta acción."
            )
        return current_user
    return rol_checker

def require_permission(modulo: str | list[str], accion: str):
    """Dependencia para validar permisos granulares por módulo y acción según DB."""
    def permission_checker(current_user: dict = Depends(get_current_user)):
        user_rol = str(current_user.get("rol", "")).strip().lower()
        if user_rol in ("superadmin", "super admin", "super_admin"):
            return current_user

        id_rol = current_user.get("id_rol")
        if not id_rol:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: El usuario no tiene un rol asignado."
            )

        from src.loaders.superadmin_loader import GET_permisos_rol_db
        perm_data = GET_permisos_rol_db(int(id_rol))
        permisos = perm_data.get("permisos", {})

        modulos = [modulo] if isinstance(modulo, str) else modulo
        tiene_permiso = any(permisos.get(m, {}).get(accion, False) for m in modulos)
        if not tiene_permiso:
            mod_str = "/".join(modulos)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permisos suficientes para '{accion}' en el módulo '{mod_str}'."
            )
        return current_user
    return permission_checker


def PARSEAR_dispositivo_user_agent(ua_string: str | None, client_hint_model: str | None = None) -> str:
    """
    Convierte la cadena User-Agent HTTP y/o Client Hints en una descripción forense
    y legible del dispositivo (marca, modelo y plataforma) y navegador para
    constancias legales y auditorías de firma digital (Ley 527/1999 & Ley 1581/2012).
    """
    if not ua_string or not str(ua_string).strip():
        if client_hint_model and str(client_hint_model).strip():
            return f"Móvil ({client_hint_model.strip()}) · Navegador Web"
        return "Dispositivo Web Seguro"

    ua = str(ua_string)
    ua_lower = ua.lower()

    # 1. Plataforma y Fabricante
    if "iphone" in ua_lower:
        plataforma = "Móvil Apple (iPhone)"
    elif "ipad" in ua_lower:
        plataforma = "Tablet Apple (iPad)"
    elif "macintosh" in ua_lower or "mac os x" in ua_lower or "mac os" in ua_lower:
        plataforma = "PC Apple (macOS)"
    elif "windows" in ua_lower:
        win_ver = "11/10" if "nt 10.0" in ua_lower else "Windows"
        plataforma = f"PC (Windows {win_ver})"
    elif "android" in ua_lower:
        # Detectar modelo de dispositivo (primero client hint, luego User-Agent)
        modelo = str(client_hint_model or "").strip()
        if not modelo:
            m = re.search(r'android\s+[\d\.]+;\s*([^;\)]+)', ua, re.IGNORECASE)
            if m:
                raw_m = m.group(1).split('Build')[0].strip('; )(')
                if raw_m and raw_m.lower() not in ('k', 'mobile', 'wv', 'none'):
                    modelo = raw_m

        m_lower = (modelo or ua_lower).lower()

        # Si el modelo vino como huella de hardware GPU (contexto HTTP sin Client Hints)
        if modelo.startswith("GPU:"):
            gpu_name = modelo.replace("GPU:", "").strip()
            gpu_lower = gpu_name.lower()
            if "xclipse" in gpu_lower:
                plataforma = f"Móvil Samsung Galaxy (Exynos · {gpu_name})"
            elif "mali-g78" in gpu_lower:
                plataforma = f"Móvil Samsung / ARM ({gpu_name})"
            elif "adreno" in gpu_lower:
                plataforma = f"Móvil Android (Qualcomm · {gpu_name})"
            elif "mali" in gpu_lower:
                plataforma = f"Móvil Android (ARM · {gpu_name})"
            elif "powervr" in gpu_lower:
                plataforma = f"Móvil Android (PowerVR · {gpu_name})"
            else:
                plataforma = f"Móvil Android ({gpu_name})"
        elif any(x in m_lower for x in ["sm-", "samsung", "galaxy", "gt-", "sch-", "sgh-"]):
            plataforma = f"Móvil Samsung ({modelo})" if modelo else "Móvil Samsung"
        elif any(x in m_lower for x in ["redmi", "xiaomi", "poco", "mi ", "210", "220", "230", "240", "m20", "m21"]):
            plataforma = f"Móvil Xiaomi ({modelo})" if modelo else "Móvil Xiaomi (Redmi / POCO)"
        elif any(x in m_lower for x in ["moto", "motorola", "xt"]):
            plataforma = f"Móvil Motorola ({modelo})" if modelo else "Móvil Motorola"
        elif "pixel" in m_lower:
            plataforma = f"Móvil Google ({modelo})" if modelo else "Móvil Google Pixel"
        elif any(x in m_lower for x in ["huawei", "honor", "vog-", "clt-", "mar-", "ane-", "pot-"]):
            plataforma = f"Móvil Huawei ({modelo})" if modelo else "Móvil Huawei"
        elif any(x in m_lower for x in ["oppo", "cph"]):
            plataforma = f"Móvil OPPO ({modelo})" if modelo else "Móvil OPPO"
        elif any(x in m_lower for x in ["vivo", "v2"]):
            plataforma = f"Móvil Vivo ({modelo})" if modelo else "Móvil Vivo"
        elif any(x in m_lower for x in ["realme", "rmx"]):
            plataforma = f"Móvil Realme ({modelo})" if modelo else "Móvil Realme"
        elif any(x in m_lower for x in ["infinix", "tecno"]):
            plataforma = f"Móvil Transsion ({modelo})" if modelo else "Móvil Infinix / Tecno"
        elif "oneplus" in m_lower:
            plataforma = f"Móvil OnePlus ({modelo})" if modelo else "Móvil OnePlus"
        else:
            plataforma = f"Móvil Android ({modelo})" if modelo else "Móvil (Android)"
    elif "linux" in ua_lower:
        plataforma = "PC (Linux)"
    elif "cros" in ua_lower:
        plataforma = "PC (ChromeOS)"
    else:
        plataforma = f"Dispositivo ({client_hint_model})" if client_hint_model else "Dispositivo Web"

    # 2. Navegador Web
    if "samsungbrowser" in ua_lower:
        navegador = "Samsung Internet"
    elif "edg/" in ua_lower or "edge/" in ua_lower:
        navegador = "Microsoft Edge"
    elif "opr/" in ua_lower or "opera" in ua_lower:
        navegador = "Opera"
    elif "chrome/" in ua_lower and "chromium" not in ua_lower:
        navegador = "Google Chrome"
    elif "safari/" in ua_lower and "chrome" not in ua_lower and "chromium" not in ua_lower:
        navegador = "Safari"
    elif "firefox/" in ua_lower:
        navegador = "Firefox"
    else:
        navegador = "Navegador Web"

    return f"{plataforma} · {navegador}"

