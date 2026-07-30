from src.database import GET_conexion


def SAVE_user_db(usuario: dict) -> dict:

    try:
        with GET_conexion() as conexion:

            if not conexion:
                return {
                        "exito": False,
                        "mensaje": "No se pudo establecer conexión con la base de datos",
                }
            
            with conexion:
                with conexion.cursor() as cursor:            

                    sql_user = """
                        INSERT INTO usuarios (
                            nombres, apellidos, tipo_documento, num_documento, num_telefono,
                            correo, contrasena, id_rol
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)        
                    """
                    valores_user = (
                        usuario.get("nombres", ""),
                        usuario.get("apellidos", ""),
                        usuario.get("tipo_documento", ""),
                        usuario.get("num_documento", 0),
                        usuario.get("num_telefono", 0),
                        usuario.get("correo", ""),
                        usuario.get("contrasena", ""),
                        usuario.get("id_rol", 0),
                    )

                    cursor.execute(sql_user, valores_user)
                    user_id = cursor.lastrowid

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
            if not conexion:
                    return {"exito": False, "mensaje": "❌❌ Sin conexión a la base de datos ❌❌"}

            
            with conexion.cursor(dictionary=True) as cursor:

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
                        u.fecha_creacion,
                        r.nombre_rol,
                        r.descripcion AS descripcion_rol
                    FROM usuarios u
                    INNER JOIN roles r ON u.id_rol = r.id_rol
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

def UPDATE_user_db(id_user: int, new_data: dict) -> dict: 

    try:

        with GET_conexion() as conexion:

            if not conexion:
                return {"exito": False, "mensaje": "Sin conexión con la base de datos."}

            with conexion:

                with conexion.cursor(dictionary=True) as cursor:

                    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id_user,)) # obetenr datos actuales en la misma conexion
                    data_current = cursor.fetchone()

                    if not data_current:
                        return{
                            "exito": False,
                            "mensaje" : f"Usuario {id_user} no encontrado."                              
                        }

                    nombres = new_data.get("nombres") or data_current.get("nombres", "")
                    apellidos = new_data.get("apellidos") or data_current.get("apellidos", "")
                    tipo_documento = new_data.get("tipo_documento") or data_current.get("tipo_documento", "")
                    num_documento = new_data.get("num_documento") or data_current.get("num_documento", 0)
                    num_telefono = new_data.get("num_telefono") or data_current.get("num_telefono", 0)
                    correo = new_data.get("correo") or data_current.get("correo", "")
                    contrasena = new_data.get("contrasena") or data_current.get("contrasena", "")
                    id_rol = new_data.get("id_rol") or data_current.get("id_rol", 0)

                    sql_user = """

                        UPDATE usuarios SET
                            nombres = %s,
                            apellidos = %s,
                            tipo_documento  = %s,
                            num_documento = %s,
                            num_telefono = %s,
                            correo = %s,
                            contrasena = %s,
                            id_rol = %s
                        WHERE id = %s

                    """

                    valores_user = (
                        nombres,
                        apellidos,
                        tipo_documento,
                        num_documento,
                        num_telefono,
                        correo,
                        contrasena,
                        id_rol,
                        id_user,
                    )

                    cursor.execute(sql_user, valores_user)

        print(f"Usuario con id {id_user} fue actualizado con éxito.")
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

    try:
        with GET_conexion() as conexion:

            if not conexion:
                return {"exito": False, "mensaje": "Sin conexión con la base de datos."}

            with conexion:
                with conexion.cursor() as cursor:
                    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id_user,))
                    if cursor.rowcount == 0:
                        return {
                            "exito": False,
                            "mensaje": f"Usuario con ID {id_user} no encontrado.",
                        }

        print(f"Usuario con ID {id_user} eliminado con éxito.")
        return {
            "exito": True,
            "mensaje": f"Usuario con ID {id_user} eliminado correctamente.",
        }

    except Exception as e:
        print(f"Error al eliminar el usuario {id_user}: {e}.")
        return {
            "exito": False,
            "mensaje": f"Error al eliminar en la base de datos. {e}",
        }