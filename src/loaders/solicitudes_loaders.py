from src.database import GET_conexion

def SAVE_solicitud_bd(solicitud: dict) -> dict:

    try:
        with GET_conexion() as conexion:
            if not conexion:
                return {
                    "exito": False,
                    "mensaje": "No se pudo establecer conexión con la base de datos",
                }
            with conexion:
                with conexion.cursor() as cursor:
                    vehiculo = solicitud.get("vehiculo") or {}
                    tipo_vehiculo = vehiculo.get("tipo", "")
                    placa = vehiculo.get("placa", "")

                    # Insertar en la Tabla Padre: solicitudes
                    sql_solicitud = """
                            INSERT INTO solicitudes (
                            empresa_origen, diligenciado_por, nivel_de_riesgo, tipo_de_persona,
                            empresa_contratista, planta_a_visitar, fecha_inicio, fecha_fin, actividad,
                            tipo_vehiculo, placa, estado
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                    """

                    valores_solicitud = (
                        solicitud.get("empresa_origen", ""),
                        solicitud.get("diligenciado_por", ""),
                        solicitud.get("nivel_de_riesgo", ""),
                        solicitud.get("tipo_de_persona", ""),
                        solicitud.get("empresa_contratista", ""),
                        solicitud.get("planta_a_visitar", ""),
                        solicitud.get("fecha_inicio", ""),
                        solicitud.get("fecha_fin", ""),
                        solicitud.get("actividad", ""),
                        tipo_vehiculo,
                        placa,
                        solicitud.get("estado", "ENVIADO"),
                    )

                    cursor.execute(sql_solicitud, valores_solicitud)
                    solicitud_id = cursor.lastrowid

                    # Insertar personas asociadas a la solicitud
                    personas = solicitud.get("personas", [])
                    if personas:
                        sql_persona = """
                            INSERT INTO personas_solicitud (
                                solicitud_id, item, ap_nombre, tipo_doc, identificacion, cargo
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        valores_personas = [
                            (
                                solicitud_id,
                                i,
                                p.get("ap_nombre", ""),
                                p.get("tipo_doc", ""),
                                p.get("identificacion", 0),
                                p.get("cargo", ""),
                            )
                            for i, p in enumerate(personas, start=1)
                        ]
                        cursor.executemany(sql_persona, valores_personas)

                    # Insertar equipos asociados a la solicitud
                    equipos = solicitud.get("eq_computo", [])
                    if equipos:
                        sql_equipo = """
                            INSERT INTO equipos_solicitud (solicitud_id, marca, modelo, serie)
                            VALUES (%s, %s, %s, %s)
                            """
                        valores_equipos = [
                            (
                                solicitud_id,
                                eq.get("marca", ""),
                                eq.get("modelo", ""),
                                eq.get("serie", ""),
                            )
                            for eq in equipos
                        ]
                        cursor.executemany(sql_equipo, valores_equipos)

        print(f"✅ La solicitud #{solicitud_id} guardada con éxito en la Base de Datos.")
        return {
            "exito": True,
            "mensaje": f"Solicitud #{solicitud_id} registrada exitosamente.",
            "id_generado": solicitud_id,
        }

    except Exception as e:
        print(f"❌ Error al intentar guardar en MySQL: {e}")
        return {"exito": False, "mensaje": f"Error en la base de datos: {e}"}


def GET_solicitud_bd(solicitud_id: int) -> dict:

    # Obtiene una solicitud completa (con sus personas y equipos) por ID.

    try:

        with GET_conexion() as conexion:
            if not conexion:
                    return {"exito": False, "mensaje": "Sin conexión a la Base de Datos"}

            with conexion.cursor(dictionary=True) as cursor:
            
                # 1. Obtener la solicitud principal
                cursor.execute("SELECT * FROM solicitudes WHERE id = %s", (solicitud_id,))
                solicitud = cursor.fetchone()

                if not solicitud:
                    return {
                        "exito": False,
                        "mensaje": f"Solicitud #{solicitud_id} no encontrada.",
                    }

                solicitud["vehiculo"] = {
                    "tipo": solicitud.pop("tipo_vehiculo", ""),
                    "placa": solicitud.pop("placa", ""),
                }

                # 2. Obtener las personas asociadas
                cursor.execute(
                    "SELECT item, ap_nombre, tipo_doc, identificacion, cargo "
                    "FROM personas_solicitud WHERE solicitud_id = %s ORDER BY item ASC",
                    (solicitud_id,),
                )
                solicitud["personas"] = cursor.fetchall()

                # 3. Obtener los equipos asociados
                cursor.execute(
                    "SELECT marca, modelo, serie FROM equipos_solicitud WHERE solicitud_id = %s",
                    (solicitud_id,),
                )
                solicitud["eq_computo"] = cursor.fetchall()

                return {"exito": True, "datos": solicitud}

    except Exception as e:
        return {"exito": False, "mensaje": f"Error al consultar la solicitud: {e}"}

def UPDATE_solicitud_bd(solicitud_id: int, new_data: dict) -> dict:

    try:

        with GET_conexion() as conexion:
            if not conexion:
                return {
                    "exito" : False,
                    "mensaje" : "Sin conexión con la base de datos"
                }

            with conexion:
                with conexion.cursor(dictionary=True) as cursor:  

                    cursor.execute("SELECT * FROM solicitudes WHERE id = %s", (solicitud_id,)) # obetenr datos actuales en la misma conexion
                    datos_actuales = cursor.fetchone()

                    if not datos_actuales:
                        return {
                            "exito": False,
                            "mensaje": f"Solicitud #{solicitud_id} no encontrada.",
                        }    

                    # Combinación de datos recibidos con los ya existentes (fallback)
                    empresa_origen = new_data.get("empresa_origen") or datos_actuales.get("empresa_origen", "")
                    diligenciado_por = new_data.get("diligenciado_por") or datos_actuales.get("diligenciado_por", "")
                    nivel_de_riesgo = new_data.get("nivel_de_riesgo") or datos_actuales.get("nivel_de_riesgo", "")
                    tipo_de_persona = new_data.get("tipo_de_persona") or datos_actuales.get("tipo_de_persona", "")
                    empresa_contratista = new_data.get("empresa_contratista") or datos_actuales.get("empresa_contratista", "")
                    planta_a_visitar = new_data.get("planta_a_visitar") or datos_actuales.get("planta_a_visitar", "")
                    fecha_inicio = new_data.get("fecha_inicio") or datos_actuales.get("fecha_inicio", "")
                    fecha_fin = new_data.get("fecha_fin") or datos_actuales.get("fecha_fin", "")
                    actividad = new_data.get("actividad") or datos_actuales.get("actividad", "")

                    vehiculo_nuevo = new_data.get("vehiculo") or {}
                    tipo_vehiculo = vehiculo_nuevo.get("tipo") or datos_actuales.get("tipo_vehiculo", "")
                    placa = vehiculo_nuevo.get("placa") or datos_actuales.get("placa", "")

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
                        solicitud_id,
                    )
                    cursor.execute(sql_solicitud, valores_solicitud)

                    nuevas_personas = (new_data.get("personas") or [])  # AGREGAR nuevas personas (sin borrar las anteriores)
                    if nuevas_personas:
                    # Obtener el último 'item' registrado para esta solicitud
                        cursor.execute(
                            "SELECT COALESCE(MAX(item), 0) FROM personas_solicitud WHERE solicitud_id = %s",
                            (solicitud_id,),
                        )
                        ultimo_item = cursor.fetchone()[0]

                        valores_personas = [
                            (
                                solicitud_id,
                                ultimo_item + i,
                                p.get("ap_nombre", ""),
                                p.get("tipo_doc", ""),
                                p.get("identificacion", 0),
                                p.get("cargo", ""),
                            )
                            for i, p in enumerate(nuevas_personas, start=1)
                        ]

                        sql_persona = """
                            INSERT INTO personas_solicitud (solicitud_id, item, ap_nombre, tipo_doc, identificacion, cargo)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        cursor.executemany(sql_persona, valores_personas)

                    # AGREGAR nuevos equipos (sin borrar los anteriores)
                    nuevos_equipos = new_data.get("eq_computo") or []
                    if nuevos_equipos:
                        sql_equipo = """
                            INSERT INTO equipos_solicitud (solicitud_id, marca, modelo, serie)
                            VALUES (%s, %s, %s, %s)
                        """
                        valores_equipos = [
                            (
                                solicitud_id,
                                eq.get("marca", ""),
                                eq.get("modelo", ""),
                                eq.get("serie", ""),
                            )
                            for eq in nuevos_equipos
                        ]
                        cursor.executemany(sql_equipo, valores_equipos)

        print(f"✅ Solicitud #{solicitud_id} actualizada con éxito en la base de datos.")
        return {
            "exito": True,
            "mensaje": f"Solicitud #{solicitud_id} actualizada correctamente.",
        }

    except Exception as e:
        print(f"❌ Error al actualizar la solicitud #{solicitud_id}: {e}")
        return {
            "exito": False,
            "mensaje": f"Error al actualizar en la base de datos: {e}",
        }

def DELETE_solicitud_bd(solicitud_id: int) -> dict:
    try:

        with GET_conexion() as conexion:
            if not conexion:
                return {"exito": False, "mensaje": "Sin conexión a la Base de Datos"}

            with conexion:
                with conexion.cursor() as cursor:

                    sql = "DELETE FROM solicitudes WHERE id = %s"
                    cursor.execute(sql, (solicitud_id,))

                    if cursor.rowcount == 0:
                        return {
                            "exito": False,
                            "mensaje": f"No existe la solicitud #{solicitud_id} para eliminar.",
                        }

            return {
                "exito": True,
                "mensaje": f"Solicitud #{solicitud_id} eliminada correctamente de la base de datos.",
            }

    except Exception as e:
        return {"exito": False, "mensaje": f"Error al eliminar solicitud: {e}"}
