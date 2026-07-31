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
                        
                    conexion.commit()

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

            with conexion.cursor() as cursor:
            
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

def UPDATE_solicitud_bd(solicitud_id: int, campos: dict) -> dict:
    try:
        with GET_conexion() as conexion:
            if not conexion:
                return {
                    "exito": False,
                    "mensaje": "Sin conexión con la base de datos",
                }

            with conexion.cursor() as cursor:
                personas = campos.pop("personas", None)
                eq_computo = campos.pop("eq_computo", None)
                vehiculo = campos.pop("vehiculo", None)

                if vehiculo and isinstance(vehiculo, dict):
                    if "tipo" in vehiculo:
                        campos["tipo_vehiculo"] = vehiculo["tipo"]
                    if "placa" in vehiculo:
                        campos["placa"] = vehiculo["placa"]

                if campos:
                    columnas = [f"{col} = %s" for col in campos.keys()]
                    sql_update = f"UPDATE solicitudes SET {', '.join(columnas)} WHERE id = %s"
                    valores = list(campos.values()) + [solicitud_id]
                    cursor.execute(sql_update, valores)

                if personas is not None:
                    cursor.execute(
                        "DELETE FROM personas_solicitud WHERE solicitud_id = %s",
                        (solicitud_id,),
                    )
                    if personas:
                        sql_p = """
                            INSERT INTO personas_solicitud (solicitud_id, item, ap_nombre, tipo_doc, identificacion, cargo)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        valores_p = [
                            (
                                solicitud_id,
                                idx,
                                p.get("ap_nombre", ""),
                                p.get("tipo_doc", ""),
                                str(p.get("identificacion", "")),
                                p.get("cargo", ""),
                            )
                            for idx, p in enumerate(personas, start=1)
                        ]
                        cursor.executemany(sql_p, valores_p)

                if eq_computo is not None:
                    cursor.execute(
                        "DELETE FROM equipos_solicitud WHERE solicitud_id = %s",
                        (solicitud_id,),
                    )
                    if eq_computo:
                        sql_eq = """
                            INSERT INTO equipos_solicitud (solicitud_id, marca, modelo, serie)
                            VALUES (%s, %s, %s, %s)
                        """
                        valores_eq = [
                            (
                                solicitud_id,
                                eq.get("marca", ""),
                                eq.get("modelo", ""),
                                eq.get("serie", ""),
                            )
                            for eq in eq_computo
                        ]
                        cursor.executemany(sql_eq, valores_eq)

            # 💡 El commit DEBE ir dentro del 'with GET_conexion()', antes de cerrar la conexión
            conexion.commit()

            print(
                f"✅ Solicitud #{solicitud_id} actualizada con éxito en la base de datos."
            )
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
                return {
                    "exito": False,
                    "mensaje": "Sin conexión a la base de datos",
                }

            with conexion.cursor() as cursor:

                sql = "DELETE FROM solicitudes WHERE id = %s"
                cursor.execute(sql, (solicitud_id,))

                if cursor.rowcount == 0:
                    return {
                        "exito": False,
                        "mensaje": f"No existe la solicitud #{solicitud_id} para eliminar.",
                    }

            conexion.commit()

            return {
                "exito": True,
                "mensaje": f"Solicitud #{solicitud_id} eliminada correctamente.",
            }

    except Exception as e:
        print(f"❌ Error al eliminar solicitud #{solicitud_id}: {e}")
        return {"exito": False, "mensaje": f"Error al eliminar solicitud: {e}"}
