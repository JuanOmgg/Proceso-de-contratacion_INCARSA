import hashlib
from datetime import datetime
from database import GET_conexion

def SEARCH_userbyCorreo_db(correo: str):
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = "SELECT id, id AS id_usuario, correo, is_active FROM usuarios WHERE LOWER(correo) = %s"
                cursor.execute(sql, (correo.lower(),))
                return cursor.fetchone()
    except Exception as e:
        print(f"❌ Error buscando usuario por correo: {e}")
        return None

def GET_user_for_login_db(correo: str):
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = """
                SELECT 
                    u.id,
                    u.nombres,
                    u.apellidos,
                    u.correo,
                    u.contrasena,
                    u.id_rol,
                    u.is_active,
                    r.nombre_rol AS rol
                FROM usuarios u
                LEFT JOIN roles r ON u.id_rol = r.id
                WHERE LOWER(u.correo) = %s
                LIMIT 1
                """
                cursor.execute(sql, (correo.strip().lower(),))
                usuario = cursor.fetchone()
                if not usuario:
                    return None
                
                # Obtener plantas asignadas
                cursor.execute("""
                    SELECT p.id, p.nombre 
                    FROM usuario_plantas up
                    INNER JOIN planta p ON up.id_planta = p.id
                    WHERE up.id_usuario = %s
                """, (usuario["id"],))
                plantas = cursor.fetchall() or []
                usuario["plantas"] = plantas
                usuario["plantas_ids"] = [p["id"] for p in plantas]
                return usuario
    except Exception as e:
        print(f"❌ Error buscando usuario para login: {e}")
        return None

def POST_recoveryToken_db(id_usuario: int, code_hash: str, expiration_time: datetime):
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("UPDATE tokens_reset SET used = TRUE WHERE id_usuario = %s", (id_usuario,))
                sql = """
                INSERT INTO tokens_reset (id_usuario, code_hash, expiration_time)
                VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (id_usuario, code_hash, expiration_time))
                conexion.commit()
                return True
    except Exception as e:
        print(f"❌ Error guardando token de recuperación: {e}")
        return False

def GET_validateTokens_db(id_usuario: int, code_hash: str):
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = """
                SELECT id, expiration_time, used 
                FROM tokens_reset 
                WHERE id_usuario = %s AND code_hash = %s 
                ORDER BY creado_en DESC LIMIT 1
                """
                cursor.execute(sql, (id_usuario, code_hash))
                return cursor.fetchone()
    except Exception as e:
        print(f"❌ Error validando token: {e}")
        return None

def PATCH_password_db(id_usuario: int, newPass_hash: str, id_token: int):
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "UPDATE usuarios SET contrasena = %s, password_changed_at = NOW() WHERE id = %s",
                    (newPass_hash, id_usuario)
                )
                cursor.execute("UPDATE tokens_reset SET used = TRUE WHERE id = %s", (id_token,))
                conexion.commit()
                try:
                    from src.utils.security import invalidate_user_sessions
                    invalidate_user_sessions(id_usuario)
                except Exception as ex:
                    print(f"⚠️ Error invalidando sesiones previas: {ex}")
                return True
    except Exception as e:
        print(f"❌ Error actualizando contraseña del usuario: {e}")
        return False

def POST_2faToken_db(id_usuario: int, code_hash: str, expiration_time: datetime):
    """Guarda un nuevo código de verificación 2FA invalidando los anteriores pendientes."""
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("UPDATE tokens_2fa SET used = TRUE WHERE id_usuario = %s AND used = FALSE", (id_usuario,))
                sql = """
                INSERT INTO tokens_2fa (id_usuario, code_hash, expiration_time)
                VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (id_usuario, code_hash, expiration_time))
                conexion.commit()
                return True
    except Exception as e:
        print(f"❌ Error guardando token 2FA: {e}")
        return False

def GET_validate2faToken_db(id_usuario: int, code_hash: str):
    """Busca y retorna el token 2FA para el usuario y hash dados."""
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = """
                SELECT id, expiration_time, used 
                FROM tokens_2fa 
                WHERE id_usuario = %s AND code_hash = %s 
                ORDER BY creado_en DESC LIMIT 1
                """
                cursor.execute(sql, (id_usuario, code_hash))
                return cursor.fetchone()
    except Exception as e:
        print(f"❌ Error validando token 2FA: {e}")
        return None

def MARK_2faToken_used_db(id_token: int):
    """Marca un token 2FA como utilizado."""
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("UPDATE tokens_2fa SET used = TRUE WHERE id = %s", (id_token,))
                conexion.commit()
                return True
    except Exception as e:
        print(f"❌ Error marcando token 2FA como usado: {e}")
        return False

def GET_latest_active_2fa_db(id_usuario: int):
    """Obtiene el último token 2FA generado para el usuario."""
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = """
                SELECT id, code_hash, expiration_time, used, intentos
                FROM tokens_2fa 
                WHERE id_usuario = %s 
                ORDER BY creado_en DESC LIMIT 1
                """
                cursor.execute(sql, (id_usuario,))
                return cursor.fetchone()
    except Exception as e:
        print(f"❌ Error buscando último token 2FA: {e}")
        return None

def INCREMENT_intentos_2fa_db(id_token: int) -> int:
    """Incrementa los intentos fallidos de un token 2FA. Si llega a 5, lo invalida (used=TRUE). Retorna los nuevos intentos."""
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("UPDATE tokens_2fa SET intentos = intentos + 1 WHERE id = %s", (id_token,))
                cursor.execute("SELECT intentos FROM tokens_2fa WHERE id = %s", (id_token,))
                row = cursor.fetchone()
                intentos = row["intentos"] if row else 5
                if intentos >= 5:
                    cursor.execute("UPDATE tokens_2fa SET used = TRUE WHERE id = %s", (id_token,))
                conexion.commit()
                return intentos
    except Exception as e:
        print(f"❌ Error incrementando intentos 2FA: {e}")
        return 5

def GET_latest_active_reset_db(id_usuario: int):
    """Obtiene el último token de restablecimiento generado para el usuario."""
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = """
                SELECT id, code_hash, expiration_time, used, intentos
                FROM tokens_reset 
                WHERE id_usuario = %s 
                ORDER BY creado_en DESC LIMIT 1
                """
                cursor.execute(sql, (id_usuario,))
                return cursor.fetchone()
    except Exception as e:
        print(f"❌ Error buscando último token reset: {e}")
        return None

def INCREMENT_intentos_reset_db(id_token: int) -> int:
    """Incrementa los intentos fallidos de un token reset. Si llega a 5, lo invalida (used=TRUE). Retorna los nuevos intentos."""
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("UPDATE tokens_reset SET intentos = intentos + 1 WHERE id = %s", (id_token,))
                cursor.execute("SELECT intentos FROM tokens_reset WHERE id = %s", (id_token,))
                row = cursor.fetchone()
                intentos = row["intentos"] if row else 5
                if intentos >= 5:
                    cursor.execute("UPDATE tokens_reset SET used = TRUE WHERE id = %s", (id_token,))
                conexion.commit()
                return intentos
    except Exception as e:
        print(f"❌ Error incrementando intentos reset: {e}")
        return 5