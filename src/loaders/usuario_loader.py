from database import GET_conexion
import bcrypt
from typing import List, Dict, Any


def CREATE_user_db(usuario: dict) -> dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:            

                sql_user = """
                    INSERT INTO usuarios (
                        nombres, apellidos, tipo_documento, num_documento, num_telefono,
                        correo, contrasena, id_rol, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)        
                """
                valores_user = (
                    usuario.get("nombres", ""),
                    usuario.get("apellidos", ""),
                    usuario.get("tipo_documento", ""),
                    usuario.get("num_documento"),
                    usuario.get("num_telefono"),
                    usuario.get("correo", ""),
                    usuario.get("contrasena", ""),
                    usuario.get("id_rol"),
                    usuario.get("is_active", True),
                )

                cursor.execute(sql_user, valores_user)
                user_id = cursor.lastrowid

                # Guardar plantas asignadas si es rol SST (5) o GESCO (6)
                plantas_ids = usuario.get("plantas_ids") or []
                if int(usuario.get("id_rol", 0)) in (5, 6) and plantas_ids:
                    for p_id in plantas_ids:
                        if str(p_id).isdigit():
                            cursor.execute(
                                "INSERT IGNORE INTO usuario_plantas (id_usuario, id_planta) VALUES (%s, %s)",
                                (user_id, int(p_id))
                            )

                conexion.commit()  # Confirmar los cambios en la base de datos

        print(f"✅✅ El usuario {user_id} fue registrado con éxito. ✅✅")
        return {
            "exito": True,
            "mensaje": "✅✅ Usuario guardado exitosamente. ✅✅",
            "id_generado": user_id,
        }

    except Exception as us:
        print(f"❌❌ Error al intentar guardar usuario en la base de datos: {us}. ❌❌")
        return {
            "exito": False,
            "mensaje": f"❌❌ Error en la base de datos : {us} ❌❌",
        }

def GET_user_db(identificador: Any) -> dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                # Si es numérico
                if str(identificador).strip().isdigit():
                    sql = """
                        SELECT 
                            u.id,
                            u.nombres,
                            u.apellidos,
                            u.tipo_documento,
                            u.num_documento,
                            u.num_telefono,
                            u.correo,
                            u.contrasena,
                            u.id_rol,
                            u.is_active,
                            u.fecha_creacion,
                            r.nombre_rol,
                            r.descripcion AS descripcion_rol
                        FROM usuarios u
                        INNER JOIN roles r ON u.id_rol = r.id
                        WHERE u.id = %s
                    """
                    cursor.execute(sql, (int(identificador),))
                else:
                    term = str(identificador).strip().replace("-", " ")
                    sql = """
                        SELECT 
                            u.id,
                            u.nombres,
                            u.apellidos,
                            u.tipo_documento,
                            u.num_documento,
                            u.num_telefono,
                            u.correo,
                            u.contrasena,
                            u.id_rol,
                            u.is_active,
                            u.fecha_creacion,
                            r.nombre_rol,
                            r.descripcion AS descripcion_rol
                        FROM usuarios u
                        INNER JOIN roles r ON u.id_rol = r.id
                        WHERE LOWER(CONCAT(TRIM(u.nombres), ' ', TRIM(u.apellidos))) = LOWER(%s)
                           OR LOWER(u.nombres) = LOWER(%s)
                           OR LOWER(u.correo) = LOWER(%s)
                           OR LOWER(CONCAT(TRIM(u.nombres), ' ', TRIM(u.apellidos))) LIKE LOWER(%s)
                        LIMIT 1
                    """
                    cursor.execute(sql, (term, term, term, f"%{term}%"))

                usuario = cursor.fetchone()

                if not usuario:
                    return {
                        "exito": False,
                        "mensaje": f"❌❌ El usuario '{identificador}' no fue encontrado. ❌❌",
                    }

                # Obtener plantas asignadas
                user_id = usuario["id"]
                cursor.execute("""
                    SELECT p.id, p.nombre
                    FROM usuario_plantas up
                    INNER JOIN planta p ON up.id_planta = p.id
                    WHERE up.id_usuario = %s
                """, (user_id,))
                plantas_asignadas = cursor.fetchall() or []
                usuario["plantas"] = plantas_asignadas
                usuario["plantas_ids"] = [p["id"] for p in plantas_asignadas]

                return {"exito": True, "data": usuario}

    except Exception as e:
        print(f"❌❌ Error al consultar usuario en la BD: {e} ❌❌")
        return {
            "exito": False,
            "mensaje": f"❌❌ No fue posible encontrar al usuario {e} ❌❌",
        }

def GET_BY_ROL_with_count_db() -> List[Dict[str, Any]]:

    try:

        with GET_conexion() as conexion:

            with conexion.cursor() as cursor:

                sql_byRol = """
                    SELECT 
                        COALESCE(r.nombre_rol, 'Sin rol') AS rol,
                        COUNT(u.id) AS total
                    FROM usuarios u
                    LEFT JOIN roles r ON u.id_rol = r.id
                    WHERE u.is_active = 1
                      AND UPPER(COALESCE(r.nombre_rol, '')) != 'SUPERADMIN'
                    GROUP BY r.id, r.nombre_rol
                    ORDER BY total DESC
                """
                cursor.execute(sql_byRol)
                return cursor.fetchall()

    except Exception as e:
        
        print(f"❌ Error en GET_BY_ROL: {e}")
        raise e


def GET_ALL_users_db() -> dict:
    
    try:

        with GET_conexion() as conexion:

            with conexion.cursor() as cursor:

                cursor.execute("""
                    SELECT 
                        u.id,
                        CONCAT(u.nombres, ' ', u.apellidos) AS nombre_completo,
                        u.nombres,
                        u.apellidos,
                        u.tipo_documento,
                        u.num_documento,
                        u.num_telefono,
                        u.correo,
                        u.id_rol,
                        COALESCE(r.nombre_rol, 'Sin Rol') AS rol,
                        COALESCE(u.is_active, TRUE) AS is_active,
                        u.fecha_creacion
                    FROM usuarios u
                    LEFT JOIN roles r ON u.id_rol = r.id
                    WHERE UPPER(COALESCE(r.nombre_rol, '')) != 'SUPERADMIN'
                    ORDER BY u.id DESC
                """)
                datos_user = cursor.fetchall() or []

                # Obtener mapeo de plantas asignadas para todos los usuarios
                cursor.execute("""
                    SELECT up.id_usuario, p.id AS id_planta, p.nombre AS nombre_planta
                    FROM usuario_plantas up
                    INNER JOIN planta p ON up.id_planta = p.id
                """)
                plantas_rows = cursor.fetchall() or []
                user_plantas_map = {}
                for pr in plantas_rows:
                    u_id = pr["id_usuario"]
                    if u_id not in user_plantas_map:
                        user_plantas_map[u_id] = []
                    user_plantas_map[u_id].append({"id": pr["id_planta"], "nombre": pr["nombre_planta"]})

                for row in datos_user:
                    u_id = row["id"]
                    row_plantas = user_plantas_map.get(u_id, [])
                    row["plantas"] = row_plantas
                    row["plantas_ids"] = [p["id"] for p in row_plantas]
                    if row.get("fecha_creacion"):
                        row["fecha_creacion"] = str(row["fecha_creacion"])
                    if row.get("num_documento"):
                        row["num_documento"] = str(row["num_documento"])
                    if row.get("num_telefono"):
                        row["num_telefono"] = str(row["num_telefono"])

                print(f"[LOADER] Se recuperaron {len(datos_user)} usuarios de la base de datos.")

                return {
                    "exito": True,
                    "mensaje": "Usuarios encontrados con éxito",
                    "datos": datos_user,
                    "datos_user": datos_user
                }

    except Exception as e:
        print(f"[ERROR] Error al consultar usuarios en la BD: {e}")
        return {
            "exito": False,
            "mensaje": f"[ERROR] No fue posible encontrar los usuarios: {e}",
            "datos": [],
            "datos_user": []
        }




def UPDATE_user_db(id_user: int, new_updates: dict) -> dict:

    try:
        if not new_updates:
            return {
                "exito": False,
                "mensaje": "No hay campos para actualizar.",
            }

        # 1. Ciframos contraseña si viene en el PATCH
        if "contrasena" in new_updates and new_updates["contrasena"]:
            password_plana = str(new_updates["contrasena"])
            salt = bcrypt.gensalt()
            new_updates["contrasena"] = bcrypt.hashpw(
                password_plana.encode("utf-8"), salt
            ).decode("utf-8")

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 2. Verificar existencia
                cursor.execute(
                    "SELECT id FROM usuarios WHERE id = %s", (id_user,)
                )
                if not cursor.fetchone():
                    return {
                        "exito": False,
                        "mensaje": f"Usuario {id_user} no encontrado.",
                    }

                # 3. SQL dinámico: Solo actualiza las columnas válidas existentes
                cursor.execute("SHOW COLUMNS FROM usuarios")
                existing_cols = {row["Field"] for row in cursor.fetchall()}
                campos_validos = {k: v for k, v in new_updates.items() if k in existing_cols}

                if campos_validos:
                    campos_sql = [f"{campo} = %s" for campo in campos_validos.keys()]
                    valores = list(campos_validos.values())
                    valores.append(id_user)

                    sql_user = (
                        f"UPDATE usuarios SET {', '.join(campos_sql)} WHERE id = %s"
                    )

                    cursor.execute(sql_user, valores)

                # Sincronizar plantas si vienen en new_updates
                if "plantas_ids" in new_updates:
                    raw_plantas = new_updates["plantas_ids"]
                    cursor.execute("DELETE FROM usuario_plantas WHERE id_usuario = %s", (id_user,))
                    if isinstance(raw_plantas, list):
                        rol_actual = new_updates.get("id_rol")
                        if not rol_actual:
                            cursor.execute("SELECT id_rol FROM usuarios WHERE id = %s", (id_user,))
                            u_r = cursor.fetchone()
                            rol_actual = u_r["id_rol"] if u_r else 0

                        if int(rol_actual) in (5, 6):
                            for p_id in raw_plantas:
                                if str(p_id).isdigit():
                                    cursor.execute(
                                        "INSERT IGNORE INTO usuario_plantas (id_usuario, id_planta) VALUES (%s, %s)",
                                        (id_user, int(p_id))
                                    )

                conexion.commit()

        return {
            "exito": True,
            "mensaje": f"El usuario con ID {id_user} fue actualizado correctamente.",
        }

    except Exception as w:
        print(f"Error al actualizar el usuario {id_user}: {w}.")
        return {
            "exito": False,
            "mensaje": f"Error al actualizar en la base de datos. {w}",
        }


def DELETE_user_db(id_user: int) -> dict:

    if id_user <= 0:
        return {
            "exito": False,
            "mensaje": f"El ID {id_user} debe ser un entero positivo.",
        }
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                # Proteger contra la eliminación del usuario SUPERADMIN
                cursor.execute("""
                    SELECT r.nombre_rol 
                    FROM usuarios u 
                    LEFT JOIN roles r ON u.id_rol = r.id 
                    WHERE u.id = %s
                """, (id_user,))
                user_check = cursor.fetchone()
                if user_check and user_check.get("nombre_rol", "").strip().upper() == "SUPERADMIN":
                    return {
                        "exito": False,
                        "mensaje": "La cuenta con rol SUPERADMIN está protegida y no puede ser eliminada.",
                    }

                cursor.execute("DELETE FROM usuarios WHERE id = %s", (id_user,)) #verifica si existe

                if cursor.rowcount == 0:
                    return {
                        "exito": False,
                        "mensaje": f"[ERROR] El usuario con ID #{id_user} no existe.",
                    }
                conexion.commit()

        return {
            "exito": True,
            "mensaje": f"[OK] Usuario con ID {id_user} eliminado correctamente.",
        }            

    except Exception as e:
        print(f"[ERROR] Error al eliminar el usuario {id_user}: {e}")
        return {
            "exito": False,
            "mensaje": f"[ERROR] Error al eliminar en la base de datos: {e}",
        }