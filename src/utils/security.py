import os
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
import bcrypt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

security_scheme = HTTPBearer()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "02psi0926_incarsa_jwt_secure_super_secret_key_2026_prod")

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
