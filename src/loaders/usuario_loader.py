from database import GET_conexion
import bcrypt

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

def GET_user_db(id_user: int) -> dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

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

                cursor.execute(sql, (id_user,))

                usuario = cursor.fetchone()

                if not usuario:
                    return {
                        "exito": False,
                        "mensaje": f"❌❌ El usuario con ID '{id_user}' no fue encontrado. ❌❌",
                    }
                return {"exito": True, "data": usuario}

    except Exception as e:
        print(f"❌❌ Error al consultar usuario en la BD: {e} ❌❌")
        return {
            "exito": False,
            "mensaje": f"❌❌ No fue posible encontrar al usuario {e} ❌❌",
        }

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
                        r.nombre_rol AS rol,
                        u.fecha_creacion
                    FROM usuarios u
                    INNER JOIN roles r ON u.id_rol = r.id
                    ORDER BY u.id DESC
                """)
                datos_user = cursor.fetchall()

                print(f"📦 [LOADER] Se recuperaron {len(datos_user)} usuarios de la base de datos.")

                return{
                    "exito": True,
                    "mensaje": "Usuarios encontrados con éxito",
                    "datos_user": datos_user
                }

    except Exception as e:
        print(f"❌❌ Error al consultar usuarios en la BD: {e} ❌❌")
        return {
            "exito": False,
            "mensaje": f"❌❌ No fue posible encontrar los usuarios {e} ❌❌",
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

                # 3. SQL dinámico: Solo actualiza las columnas enviadas
                campos_sql = [f"{campo} = %s" for campo in new_updates.keys()]
                valores = list(new_updates.values())
                valores.append(id_user)

                sql_user = (
                    f"UPDATE usuarios SET {', '.join(campos_sql)} WHERE id = %s"
                )

                cursor.execute(sql_user, valores)

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

                cursor.execute("DELETE FROM usuarios WHERE id = %s", (id_user,)) #verifica si existe

                if cursor.rowcount == 0:
                    return {
                        "exito": False,
                        "mensaje": f"❌❌ El usuario con ID #{id_user} no existe. ❌❌",
                    }
                conexion.commit()

        return {
            "exito": True,
            "mensaje": f"✅✅ Usuario con ID {id_user} eliminado correctamente. ✅✅",
        }            

    except Exception as e:
        print(f"❌❌ Error al eliminar el usuario {id_user}: {e} ❌❌")
        return {
            "exito": False,
            "mensaje": f"❌❌ Error al eliminar en la base de datos. {e} ❌❌",
        }