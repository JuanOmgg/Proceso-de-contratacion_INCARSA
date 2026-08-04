from src.database import GET_conexion

def CREATE_solicitud_bd(solicitud: dict) -> dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                # Insertar en la Tabla Padre: solicitudes
                sql_solicitud = """
                        INSERT INTO solicitudes (
                        empresa_origen, diligenciado_por, nivel_de_riesgo, tipo_de_persona,
                        empresa_contratista, plantas_ids, fecha_inicio, fecha_fin, actividad, estado
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                """

                valores_solicitud = (
                    solicitud.get("empresa_origen", ""),
                    solicitud.get("diligenciado_por", ""),
                    solicitud.get("nivel_de_riesgo", ""),
                    solicitud.get("tipo_de_persona", ""),
                    solicitud.get("empresa_contratista", ""),
                    solicitud.get("plantas_ids", ""),
                    solicitud.get("fecha_inicio", ""),
                    solicitud.get("fecha_fin", ""),
                    solicitud.get("actividad", ""),
                    solicitud.get("estado", "ENVIADO"),
                )

                cursor.execute(sql_solicitud, valores_solicitud)
                solicitud_id = cursor.lastrowid

                vehiculo = solicitud.get("vehiculo", [])
                if vehiculo:
                    sql_vehiculo = """
                        INSERT INTO vehiculos_solicitud (solicitud_id, tipo, placa) 
                        VALUES (%s, %s, %s)
                    """
                    valores_vehiculo = [
                        (
                            solicitud_id,
                            v.get("tipo", ""),
                            v.get("placa", ""),
                        )
                        for v in vehiculo
                    ]
                    cursor.executemany(sql_vehiculo, valores_vehiculo)

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

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
            
                # 1. Obtener la solicitud principal
                cursor.execute("SELECT * FROM solicitudes WHERE id = %s", (solicitud_id,))
                solicitud = cursor.fetchone()

                if not solicitud:
                    return {
                        "exito": False,
                        "mensaje": f"Solicitud #{solicitud_id} no encontrada.",
                    }

                # 2. Obtener las plantas asociadas (vía tabla intermedia 'visita')
                cursor.execute(
                    """
                    SELECT p.id, p.nombre 
                    FROM visita v
                    INNER JOIN planta p ON v.id_planta = p.id
                    WHERE v.id_solicitud = %s
                    """,
                    (solicitud_id,),
                )
                solicitud["plantas"] = cursor.fetchall()

                # 3. Obtener los vehículos asociados
                cursor.execute(
                    "SELECT tipo, placa FROM vehiculos_solicitud WHERE solicitud_id = %s",
                    (solicitud_id,),
                )
                solicitud["vehiculo"] = cursor.fetchall()

                # 4. Obtener las personas asociadas
                cursor.execute(
                    "SELECT item, ap_nombre, tipo_doc, identificacion, cargo "
                    "FROM personas_solicitud WHERE solicitud_id = %s ORDER BY item ASC",
                    (solicitud_id,),
                )
                solicitud["personas"] = cursor.fetchall()

                # 5. Obtener los equipos asociados
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
            with conexion.cursor() as cursor:
                personas = campos.pop("personas", None)
                eq_computo = campos.pop("eq_computo", None)
                vehiculo = campos.pop("vehiculo", None)

                if campos:
                    columnas = [f"{col} = %s" for col in campos.keys()]
                    sql_update = f"UPDATE solicitudes SET {', '.join(columnas)} WHERE id = %s"
                    valores = list(campos.values()) + [solicitud_id]
                    cursor.execute(sql_update, valores)

                if vehiculo is not None:
                    cursor.execute(
                        "DELETE FROM vehiculos_solicitud WHERE solicitud_id = %s",
                        (solicitud_id,),
                    )
                    if vehiculo:
                        sql_vehiculo = """
                            INSERT INTO vehiculos_solicitud (solicitud_id, tipo, placa)
                            VALUES (%s, %s, %s)
                        """
                        valores_vehiculo = [
                            (
                                solicitud_id,
                                v.get("tipo", ""),
                                v.get("placa", ""),
                            )
                            for v in vehiculo
                        ]
                        cursor.executemany(sql_vehiculo, valores_vehiculo)

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

                conexion.commit()

            print(f"✅ Solicitud #{solicitud_id} actualizada con éxito en la base de datos.")
            return {
                "exito": True,
                "mensaje": f"✅✅ Solicitud #{solicitud_id} actualizada correctamente. ✅✅",
            }

    except Exception as e:
        print(f"❌ Error al actualizar la solicitud #{solicitud_id}: {e}")
        return {
            "exito": False,
            "mensaje": f"❌❌ Error al actualizar en la base de datos: {e} ❌❌",
        }
    
def DELETE_solicitud_bd(solicitud_id: int) -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:

                cursor.execute("DELETE FROM solicitudes WHERE id = %s", (solicitud_id,))

                if cursor.rowcount == 0:
                    return {
                        "exito": False,
                        "mensaje": f"❌❌ No existe la solicitud #{solicitud_id} para eliminar. ❌❌",
                    }

                conexion.commit()

            return {
                "exito": True,
                "mensaje": f"✅✅ Solicitud #{solicitud_id} eliminada correctamente. ✅✅",
            }

    except Exception as e:
        return {
            "exito": False, 
            "mensaje": f"❌❌ Error al eliminar solicitud: {e} ❌❌"
        }

def VINCULAR_solicitud_plantas_db(id_solicitud: int, plantas_ids: list[int]) -> dict:
    
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = "INSERT INTO visita (id_solicitud, id_planta) VALUES (%s, %s)"
                valores = [(id_solicitud, p_id) for p_id in plantas_ids]

                cursor.executemany(sql, valores)

                conexion.commit()

        return {
            "exito": True,
            "mensaje": f"✅ Plantas vinculadas a la solicitud #{id_solicitud}.",
        }

    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"❌❌ Error al relacionar plantas con la solicitud: {e} ❌❌",
        }