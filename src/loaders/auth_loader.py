import hashlib
from datetime import datetime
from database import GET_conexion

def SEARCH_userbyCorreo_db(correo: str):
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = "SELECT id, id AS id_usuario, correo FROM usuarios WHERE LOWER(correo) = %s AND is_active = TRUE"
                cursor.execute(sql, (correo.lower(),))
                return cursor.fetchone()
    except Exception as e:
        print(f"❌ Error buscando usuario por correo: {e}")
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
                cursor.execute("UPDATE usuarios SET contrasena = %s WHERE id = %s", (newPass_hash, id_usuario))
                cursor.execute("UPDATE tokens_reset SET used = TRUE WHERE id = %s", (id_token,))
                conexion.commit()
                return True
    except Exception as e:
        print(f"❌ Error actualizando contraseña del usuario: {e}")
        return False