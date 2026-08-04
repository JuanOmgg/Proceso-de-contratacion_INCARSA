from src.database import GET_conexion

def CREATE_empCont_db(empContratista: dict) -> dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                sql_empContratista = """
                    INSERT INTO emp_contratista (
                    nombre, observacion
                ) VALUES (%s, %s)
                """
                valores_empContratista = (
                    empContratista.get("nombre", ""),
                    empContratista.get("observacion", ""),
                )

                cursor.execute(sql_empContratista, valores_empContratista)
                empcont_id = cursor.lastrowid

                conexion.commit()

        print(f"✅✅ [DB] Empresa contratista creada con éxito. ID: {empcont_id} ✅✅")
        return {
            "exito": True,
            "mensaje": "✅✅ Empresa contratista creada con éxito ✅✅",
            "empcont_id": empcont_id
        }
    except Exception as e:
        print(f"❌❌ [DB] Error al crear empresa contratista: {e} ❌❌")
        return {
            "exito": False,
            "mensaje": f"❌❌ Error al crear empresa contratista: {e} ❌❌"
        }

def GET_empCont_db(empcont_id: int) -> dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                sql_empContratista = """
                    SELECT 
                        ec.id,
                        ec.nombre,
                        ec.observacion
                    FROM emp_contratista ec
                    WHERE ec.id = %s
                """
                cursor.execute(sql_empContratista, (empcont_id,))

                empresaContratista = cursor.fetchone()

                if not empresaContratista:
                    return {
                        "exito": False,
                        "mensaje": f"❌❌ No se encontró la empresa contratista con ID {empcont_id} ❌❌"
                    }
                return {
                    "exito": True,
                    "mensaje": f"✅✅ Empresa contratista con ID {empcont_id} encontrada con éxito ✅✅",
                    "empresa": empresaContratista
                }

    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"❌❌ Error al obtener empresa contratista: {e} ❌❌"
        }

def UPDATE_empCont_db(empcont_id: int, new_updates: dict) -> dict:

    try:
        if not new_updates:
            return {
                "exito": False,
                "mensaje": "❌❌ No hay campos para actualizar ❌❌"
            }

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                cursor.execute(      
                    "SELECT id FROM emp_contratista WHERE id = %s", (empcont_id,)   
                )

                if not cursor.fetchone():
                    return {
                        "exito": False,
                        "mensaje": f"❌❌ No se encontró la empresa contratista con ID {empcont_id} ❌❌"
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
            "mensaje": f"✅✅ Empresa contratista con ID {empcont_id} actualizada con éxito ✅✅"
        }
    
    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"❌❌ Error al actualizar empresa contratista: {e} ❌❌"
        }

def DELETE_empCont_db(empcont_id: int) -> dict:

    if empcont_id <= 0:
        return {
            "exito": False,
            "mensaje": "❌❌ El ID de la empresa contratista debe ser mayor a 0 ❌❌"
        }

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                cursor.execute("DELETE FROM emp_contratista WHERE id = %s", (empcont_id,))

                if cursor.rowcount == 0:
                    return {
                        "exito": False,
                        "mensaje": f"❌❌ No se encontró la empresa contratista con ID {empcont_id} ❌❌",
                    }               

                conexion.commit()

        return {
            "exito": True,
            "mensaje": f"✅✅ Empresa contratista con ID {empcont_id} eliminada con éxito ✅✅"
        }
    
    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"❌❌ Error al eliminar empresa contratista: {e} ❌❌"
        }
