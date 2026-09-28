from database import GET_conexion

def CREATE_empCont_db(empContratista: dict) -> dict:

    try:
        nombre = str(empContratista.get("nombre", "")).strip()
        nit = str(empContratista.get("nit", "")).strip()
        observacion = str(empContratista.get("observacion", "")).strip()

        if not nombre:
            return {
                "exito": False,
                "mensaje": "El nombre de la empresa contratista es obligatorio."
            }

        if not nit:
            return {
                "exito": False,
                "mensaje": "El NIT de la empresa contratista es obligatorio."
            }

        if not nit.isdigit():
            return {
                "exito": False,
                "mensaje": "El NIT debe contener únicamente números."
            }

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                # 1. Validar nombre único
                cursor.execute("SELECT id FROM emp_contratista WHERE nombre = %s", (nombre,))
                if cursor.fetchone():
                    return {
                        "exito": False,
                        "mensaje": f"Ya existe una empresa contratista con el nombre '{nombre}'."
                    }

                # 2. Validar NIT único
                cursor.execute("SELECT id, nombre FROM emp_contratista WHERE nit = %s", (nit,))
                dup_nit = cursor.fetchone()
                if dup_nit:
                    return {
                        "exito": False,
                        "mensaje": f"El NIT '{nit}' ya está registrado para la empresa '{dup_nit['nombre']}'."
                    }

                sql_empContratista = """
                    INSERT INTO emp_contratista (
                    nombre, observacion, nit
                ) VALUES (%s, %s, %s)
                """
                valores_empContratista = (nombre, observacion, nit)

                cursor.execute(sql_empContratista, valores_empContratista)
                empcont_id = cursor.lastrowid

                conexion.commit()

        print(f"[DB] Empresa contratista creada con exito. ID: {empcont_id}")
        return {
            "exito": True,
            "mensaje": "Empresa contratista creada con exito",
            "empcont_id": empcont_id
        }
    except Exception as e:
        print(f"[DB] Error al crear empresa contratista: {e}")
        return {
            "exito": False,
            "mensaje": f"Error al crear empresa contratista: {e}"
        }

def GET_empCont_db(empcont_id: int) -> dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                sql_empContratista = """
                    SELECT 
                        ec.id,
                        ec.nombre,
                        ec.nit,
                        ec.observacion
                    FROM emp_contratista ec
                    WHERE ec.id = %s
                """
                cursor.execute(sql_empContratista, (empcont_id,))

                empresaContratista = cursor.fetchone()

                if not empresaContratista:
                    return {
                        "exito": False,
                        "mensaje": f"No se encontró la empresa contratista con ID {empcont_id}"
                    }
                return {
                    "exito": True,
                    "mensaje": f"Empresa contratista con ID {empcont_id} encontrada con exito",
                    "empresa": empresaContratista
                }

    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"Error al obtener empresa contratista: {e}"
        }

def GET_ALL_empCont_db():

    try:

        with GET_conexion() as conexion:

            with conexion.cursor() as cursor:

                cursor.execute("""
                    SELECT 
                        ec.id,
                        ec.nombre,
                        ec.nit,
                        ec.observacion
                    FROM emp_contratista ec
                    ORDER BY ec.nombre ASC
                """)

                datos = cursor.fetchall()

                print(f"[LOADER] Se recuperaron {len(datos)} contratistas de la base de datos.")

                return{
                    "exito": True,
                    "data": datos,
                    "mensaje": "Contratistas recuperados con exito."
                }
    except Exception as e:
        return{
            "exito": False,
            "mensaje": f"Error al consultar la base de datos: {e}",
            "datos": []
        }

def UPDATE_empCont_db(empcont_id: int, new_updates: dict) -> dict:

    try:
        if not new_updates:
            return {
                "exito": False,
                "mensaje": "No hay campos para actualizar"
            }

        if "nit" in new_updates and new_updates["nit"]:
            nit_val = str(new_updates["nit"]).strip()
            if not nit_val.isdigit():
                return {
                    "exito": False,
                    "mensaje": "El NIT debe contener únicamente números."
                }

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                cursor.execute(      
                    "SELECT id FROM emp_contratista WHERE id = %s", (empcont_id,)   
                )

                if not cursor.fetchone():
                    return {
                        "exito": False,
                        "mensaje": f"No se encontró la empresa contratista con ID {empcont_id}"
                    }

                # Validar nombre único en edición
                if "nombre" in new_updates and new_updates["nombre"]:
                    cursor.execute("SELECT id FROM emp_contratista WHERE nombre = %s AND id != %s", (new_updates["nombre"], empcont_id))
                    if cursor.fetchone():
                        return {
                            "exito": False,
                            "mensaje": f"Ya existe otra empresa contratista con el nombre '{new_updates['nombre']}'."
                        }

                # Validar NIT único en edición
                if "nit" in new_updates and new_updates["nit"]:
                    cursor.execute("SELECT id, nombre FROM emp_contratista WHERE nit = %s AND id != %s", (new_updates["nit"], empcont_id))
                    dup_nit = cursor.fetchone()
                    if dup_nit:
                        return {
                            "exito": False,
                            "mensaje": f"El NIT '{new_updates['nit']}' ya está registrado para la empresa '{dup_nit['nombre']}'."
                        }

                campos_sql = [f"{campo} = %s" for campo in new_updates.keys()]
                valores = list(new_updates.values())
                valores.append(empcont_id)

                sql = (
                    f"UPDATE emp_contratista SET {', '.join(campos_sql)} WHERE id = %s"
                )

                cursor.execute(sql, valores)
                conexion.commit()

        return {
            "exito": True,
            "mensaje": f"Empresa contratista con ID {empcont_id} actualizada con exito"
        }
    
    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"Error al actualizar empresa contratista: {e}"
        }

def DELETE_empCont_db(empcont_id: int) -> dict:

    if empcont_id <= 0:
        return {
            "exito": False,
            "mensaje": "El ID de la empresa contratista debe ser mayor a 0"
        }

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                cursor.execute("DELETE FROM emp_contratista WHERE id = %s", (empcont_id,))

                if cursor.rowcount == 0:
                    return {
                        "exito": False,
                        "mensaje": f"No se encontró la empresa contratista con ID {empcont_id}",
                    }               

                conexion.commit()

        return {
            "exito": True,
            "mensaje": f"Empresa contratista con ID {empcont_id} eliminada con exito"
        }
    
    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"Error al eliminar empresa contratista: {e}"
        }
