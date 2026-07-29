from src.database import GET_conexion

def SAVE_solicitud_bd(solicitud: dict) -> dict:

    conexion = GET_conexion()

    if not conexion:
        return {"exito": False, "mensaje": "No se pudo establecer conexión con la base de datos"}

    cursor = conexion.cursor()

    try:
        # 1. Insertar en la Tabla Padre: solicitudes
        sql_solicitud = """
            INSERT INTO solicitudes (
                empresa_origen, diligenciado_por, nivel_de_riesgo, tipo_de_persona,
                empresa_contratista, planta_a_visitar, fecha_inicio, fecha_fin, actividad,
                tipo_vehiculo, placa, estado
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
        """
        valores_solicitud = (
            solicitud["empresa_origen"],
            solicitud["diligenciado_por"],
            solicitud["nivel_de_riesgo"],
            solicitud["tipo_de_persona"],
            solicitud["empresa_contratista"],
            solicitud["planta_a_visitar"],
            solicitud["fecha_inicio"],
            solicitud["fecha_fin"],
            solicitud["actividad"],
            solicitud["vehiculo"]["tipo"],
            solicitud["vehiculo"]["placa"],
            solicitud["estado"]
        )

        cursor.execute(sql_solicitud, valores_solicitud)

        solicitud_id = cursor.lastrowid #Se consulta cual fue el ultimo ID generado

        personas = solicitud.get("personas", [])

        if personas:

            sql_persona = """
                INSERT INTO personas_solicitud (
                    solicitud_id, item, ap_nombre, tipo_doc, identificacion, cargo
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
        
            valores_personas = [
                (solicitud_id, i, p["ap_nombre"], p["tipo_doc"], p["identificacion"], p["cargo"])
                for i, p in enumerate(personas, start=1)
            ]
            cursor.executemany(sql_persona, valores_personas)

        equipos = solicitud.get("eq_computo", [])
        if equipos:
            sql_equipo = """
                INSERT INTO equipos_solicitud (solicitud_id, marca, modelo, serie)
                VALUES (%s, %s, %s, %s)
            """
            valores_equipos = [
                (solicitud_id, eq["marca"], eq["modelo"], eq["serie"])
                for eq in equipos
            ]
            cursor.executemany(sql_equipo, valores_equipos)
        
        # Confirmar la transacción completa en la Base de Datos
        conexion.commit() #Todo lo ejecutado en este bloque es correcto, se guarda permanentemente en el disco
        
        print(f"✅ La solicitud #{solicitud_id} guardada con éxito en la Base de Datos.")
        return {
            "exito": True,
            "mensaje": f"Solicitud #{solicitud_id} registrada exitosamente.",
            "id_generado": solicitud_id
        }

    except Exception as e:
        conexion.rollback()  
        print(f"❌ Error al intentar guardar en MySQL: {e}")
        return {"exito": False, "mensaje": f"Error en la base de datos: {e}"}

    finally:
        cursor.close()
        conexion.close()

def GET_solicitud_bd(solicitud_id: int) -> dict:

    """Obtiene una solicitud completa (con sus personas y equipos) por ID."""

    conexion = GET_conexion()
    if not conexion:
        return {"exito": False, "mensaje": "Sin conexión a la Base de Datos"}

    cursor = conexion.cursor(dictionary=True)
    try:
        # 1. Obtener la solicitud principal
        cursor.execute("SELECT * FROM solicitudes WHERE id = %s", (solicitud_id,))
        solicitud = cursor.fetchone()

        if not solicitud:
            return {"exito": False, "mensaje": f"Solicitud #{solicitud_id} no encontrada."}

        # 2. Obtener las personas asociadas
        cursor.execute("SELECT item, ap_nombre, tipo_doc, identificacion, cargo FROM personas_solicitud WHERE solicitud_id = %s ORDER BY item ASC", (solicitud_id,))
        solicitud["personas"] = cursor.fetchall()

        # 3. Obtener los equipos asociados
        cursor.execute("SELECT marca, modelo, serie FROM equipos_solicitud WHERE solicitud_id = %s", (solicitud_id,))
        solicitud["eq_computo"] = cursor.fetchall()

        return {"exito": True, "datos": solicitud}

    except Exception as e:
        return {"exito": False, "mensaje": f"Error al consultar la solicitud: {e}"}
    finally:
        cursor.close()
        conexion.close()

def UPDATE_solicitud_bd(solicitud_id: int, datos_nuevos: dict) -> dict:

    conexion = GET_conexion()
    if not conexion:
        return {"exito": False, "mensaje": "Sin conexión a la Base de Datos"}

    # Obtener los datos actuales de la Base de Datos
    
    actual_res = GET_solicitud_bd(solicitud_id)
    if not actual_res["exito"]:
        return actual_res

    datos_actuales = actual_res["datos"]

    empresa_origen = datos_nuevos.get("empresa_origen", datos_actuales["empresa_origen"])
    diligenciado_por = datos_nuevos.get("diligenciado_por", datos_actuales["diligenciado_por"])
    nivel_de_riesgo = datos_nuevos.get("nivel_de_riesgo", datos_actuales["nivel_de_riesgo"])
    tipo_de_persona = datos_nuevos.get("tipo_de_persona", datos_actuales["tipo_de_persona"])
    empresa_contratista = datos_nuevos.get("empresa_contratista", datos_actuales["empresa_contratista"])
    planta_a_visitar = datos_nuevos.get("planta_a_visitar", datos_actuales["planta_a_visitar"])
    fecha_inicio = datos_nuevos.get("fecha_inicio", datos_actuales["fecha_inicio"])
    fecha_fin = datos_nuevos.get("fecha_fin", datos_actuales["fecha_fin"])
    actividad = datos_nuevos.get("actividad", datos_actuales["actividad"])

    vehiculo_nuevo = datos_nuevos.get("vehiculo", {})
    tipo_vehiculo = vehiculo_nuevo.get("tipo", datos_actuales.get("tipo_vehiculo", ""))
    placa = vehiculo_nuevo.get("placa", datos_actuales.get("placa", ""))

    cursor = conexion.cursor()

    try:
        
        sql_solicitud = """
            UPDATE solicitudes SET
                empresa_origen = %s,
                diligenciado_por = %s,
                nivel_de_riesgo = %s,
                tipo_de_persona = %s,
                empresa_contratista = %s,
                planta_a_visitar = %s,
                fecha_inicio = %s,
                fecha_fin = %s,
                actividad = %s,
                tipo_vehiculo = %s,
                placa = %s
            WHERE id = %s
        """
        valores_solicitud = (

            empresa_origen,
            diligenciado_por, 
            nivel_de_riesgo, 
            tipo_de_persona,
            empresa_contratista, 
            planta_a_visitar, 
            fecha_inicio, 
            fecha_fin,
            actividad, 
            tipo_vehiculo, 
            placa, 
            solicitud_id

        )
        cursor.execute(sql_solicitud, valores_solicitud)

        if "personas" in datos_nuevos:
            cursor.execute("DELETE FROM personas_solicitud WHERE solicitud_id = %s", (solicitud_id,))
            valores_personas = [
                (solicitud_id, i, p["ap_nombre"], p["tipo_doc"], p["identificacion"], p["cargo"])
                for i, p in enumerate(datos_nuevos["personas"], start=1)
            ]
            if valores_personas:
                sql_persona = """
                    INSERT INTO personas_solicitud (solicitud_id, item, ap_nombre, tipo_doc, identificacion, cargo)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.executemany(sql_persona, valores_personas)

        if "eq_computo" in datos_nuevos:
            cursor.execute("DELETE FROM equipos_solicitud WHERE solicitud_id = %s", (solicitud_id,))
            equipos = datos_nuevos["eq_computo"]
            if equipos:
                sql_equipo = """
                    INSERT INTO equipos_solicitud (solicitud_id, marca, modelo, serie)
                    VALUES (%s, %s, %s, %s)
                """
                valores_equipos = [
                    (solicitud_id, eq["marca"], eq["modelo"], eq["serie"])
                    for eq in equipos
                ]
                cursor.executemany(sql_equipo, valores_equipos)
        
        conexion.commit()

        print(f"✅✅ Solicitud #{solicitud_id} actualizada con éxito en la base de datos. ✅✅")
        return {"exito": True, "mensaje": f"✅✅ Solicitud #{solicitud_id} actualizada correctamente. ✅✅"}

    except Exception as e:
        conexion.rollback()
        print(f"❌❌ Error al actualizar la solicitud #{solicitud_id}: {e} ❌❌")
        return {"exito": False, "mensaje": f"❌❌ Error al actualizar en la base de datos: {e} ❌❌"}

    finally:
        cursor.close()
        conexion.close()

def DELETE_solicitud_bd(solicitud_id: int) -> dict:

    conexion = GET_conexion()
    if not conexion:
        return {"exito": False, "mensaje": "❌❌ Sin conexión a la Base de Datos ❌❌"}

    cursor = conexion.cursor()
    try:
        sql = "DELETE FROM solicitudes WHERE id = %s"
        cursor.execute(sql, (solicitud_id,))
        conexion.commit()

        if cursor.rowcount == 0:
            return {"exito": False, "mensaje": f"❌❌ No existe la solicitud #{solicitud_id} para eliminar. ❌❌"}

        return {"exito": True, "mensaje": f"✅✅ Solicitud #{solicitud_id} eliminada correctamente de la base de datos. ✅✅"}

    except Exception as e:

        conexion.rollback()
        return {"exito": False, "mensaje": f"❌❌ Error al eliminar solicitud: {e} ❌❌"}
    
    finally:

        cursor.close()
        conexion.close()