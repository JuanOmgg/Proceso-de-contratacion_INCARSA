import os
import secrets
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
import bcrypt

from fastapi import Depends, HTTPException, status
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

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Genera un token JWT firmado con fecha de expiración."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
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
    """Extrae el token del header Authorization, lo valida y devuelve los datos del usuario."""
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
