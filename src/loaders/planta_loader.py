from database import GET_conexion

def CREATE_planta_db(planta: dict) -> dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                sql = """
                    INSERT INTO planta (nombre, id_empresa)
                    VALUES (%s, %s)
                """

                valores = (
                    planta.get("nombre"),
                    planta.get("id_empresa")
                )

                cursor.execute(sql, valores)
                id_planta = cursor.lastrowid   

                conexion.commit()

        return {
            "exito": True,
            "mensaje": "✅✅ Planta creada exitosamente. ✅✅",
            "id": id_planta
        }

    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"❌❌ Error al crear la planta: {e} ❌❌"
        }

def GET_planta_db(id_planta: int) -> dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                sql = """
                    SELECT id, nombre, id_empresa
                    FROM planta
                    WHERE id = %s
                """

                cursor.execute(sql, (id_planta,))
                planta = cursor.fetchone()

                if not planta:
                    return {
                        "exito": False,
                        "mensaje": f"❌❌ No se encontró planta con ID {id_planta} ❌❌"
                    }

                return {
                    "exito": True,
                    "mensaje": f"✅✅ Planta con Id {id_planta} obtenida exitosamente. ✅✅",
                    "planta": planta
                }

    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"❌❌ Error al obtener la planta: {e} ❌❌"
        }

def GET_ALL_planta_db():

    try:

        with GET_conexion() as conexion:

            with conexion.cursor() as cursor:

                cursor.execute("""
                    SELECT 
                        p.id,
                        e.nombre_empresa AS N_empresa,
                        p.nombre

                    FROM planta p

                    INNER JOIN empresa e ON p.id_empresa = e.id
                """)

                plantas = cursor.fetchall()

                return {
                    "exito": True,
                    "datos": plantas,
                    "mensaje": "Plantas recuperadas con éxito."
                }
    except Exception as e:
        return{
            "exito": False,
            "mensaje": "No se pudo recuperar plantas de la base de datos",
        }


def UPDATE_planta_db(id_planta: int, new_updates: dict) -> dict:

    try:
        if not new_updates:
            return {
                "exito": False,
                "mensaje": "❌❌ No hay campos para actualizar ❌❌"
            }

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                cursor.execute(
                    "SELECT id FROM planta WHERE id = %s", (id_planta,)
                )

                if not cursor.fetchone():
                    return {
                        "exito": False,
                        "mensaje": f"No se encontró la planta/zona con Id {id_planta}"
                    }
                campos_sql = [f"{campo} = %s" for campo in new_updates.keys()]
                valores = list(new_updates.values())
                valores.append(id_planta)

                sql = (
                    f"UPDATE planta SET {', '.join(campos_sql)} WHERE id = %s"
                )

                cursor.execute(sql, valores)
                conexion.commit()

        return {
            "exito": True,
            "mensaje": f"✅✅ Planta/zona con ID {id_planta} actualizada con éxito ✅✅"
        }
    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"❌❌ Error al actualizar planta/zona: {e} ❌❌"
        }

def DELETE_planta_db(id_planta: int) -> dict:

    if id_planta <= 0:
        return {
            "exito": False,
            "mensaje": "❌❌ El ID de la planta/zona debe ser mayor a 0 ❌❌"
        }

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                cursor.execute("DELETE FROM planta WHERE id = %s", (id_planta,))

                if cursor.rowcount == 0:
                    return {
                        "exito": False,
                        "mensaje": f"❌❌ No se encontró la planta/zona con ID {id_planta} ❌❌"
                    }

                conexion.commit()

        return {
            "exito": True,
            "mensaje": f"✅✅ Planta con ID {id_planta} eliminada con éxito ✅✅"
        }
    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"❌❌ Error al eliminar planta: {e} ❌❌"
        }