from database import GET_conexion

def CREATE_solicitud_bd(solicitud: dict) -> dict:

    try:
        raw_plantas = solicitud.get("plantas_ids", [])
        plantas_ids = []
        if isinstance(raw_plantas, list):
            plantas_ids = [int(p) for p in raw_plantas if str(p).isdigit()]
        elif isinstance(raw_plantas, (int, str)):
            for p in str(raw_plantas).split(","):
                if p.strip().isdigit():
                    plantas_ids.append(int(p.strip()))

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Obtener la relación de cada planta con su id_empresa
                empresa_plantas_map = {}
                if plantas_ids:
                    format_strings = ",".join(["%s"] * len(plantas_ids))
                    cursor.execute(
                        f"SELECT id, id_empresa FROM planta WHERE id IN ({format_strings})",
                        tuple(plantas_ids),
                    )
                    plantas_db = cursor.fetchall()
                    for p in plantas_db:
                        emp_id = p["id_empresa"]
                        p_id = p["id"]
                        if emp_id not in empresa_plantas_map:
                            empresa_plantas_map[emp_id] = []
                        empresa_plantas_map[emp_id].append(p_id)

                # Si no se encontraron plantas en BD o no venían plantas, usar empresa_origen proporcionada
                if not empresa_plantas_map:
                    emp_origen_default = solicitud.get("empresa_origen", 0)
                    empresa_plantas_map[emp_origen_default] = plantas_ids

                ids_generados = []

                # 2. Crear una solicitud independiente por cada empresa_origen
                for emp_origen, sub_plantas in empresa_plantas_map.items():
                    sql_solicitud = """
                        INSERT INTO solicitudes (
                            empresa_origen, diligenciado_por, nivel_de_riesgo, tipo_personal,
                            empresa_contratista, plantas_ids, fecha_inicio, fecha_fin, actividad, estado, is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    str_plantas_ids = ",".join(map(str, sub_plantas)) if sub_plantas else ""

                    valores_solicitud = (
                        emp_origen,
                        solicitud.get("diligenciado_por", ""),
                        solicitud.get("nivel_de_riesgo", ""),
                        solicitud.get("tipo_personal", ""),
                        solicitud.get("empresa_contratista", ""),
                        str_plantas_ids,
                        solicitud.get("fecha_inicio", ""),
                        solicitud.get("fecha_fin", ""),
                        solicitud.get("actividad", ""),
                        solicitud.get("estado", "ENVIADO"),
                        solicitud.get("is_active", True),
                    )

                    cursor.execute(sql_solicitud, valores_solicitud)
                    solicitud_id = cursor.lastrowid
                    ids_generados.append(solicitud_id)

                    # Registrar relaciones en tabla intermedia 'visita'
                    if sub_plantas:
                        sql_visita = "INSERT INTO visita (id_solicitud, id_planta) VALUES (%s, %s)"
                        valores_visita = [(solicitud_id, p_id) for p_id in sub_plantas]
                        cursor.executemany(sql_visita, valores_visita)

                    # Insertar vehículos
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

                    # Insertar personas y sus documentos asociados
                    personas = solicitud.get("personas", [])
                    if personas:
                        sql_persona = """
                            INSERT INTO personas_solicitud (
                                solicitud_id, item, ap_nombre, tipo_doc, identificacion, cargo
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        sql_doc = """
                            INSERT INTO documentos_persona (persona_id, tipo_doc, nombre_archivo)
                            VALUES (%s, %s, %s)
                        """
                        for i, p in enumerate(personas, start=1):
                            cursor.execute(
                                sql_persona,
                                (
                                    solicitud_id,
                                    i,
                                    p.get("ap_nombre", ""),
                                    p.get("tipo_doc", ""),
                                    p.get("identificacion", 0),
                                    p.get("cargo", ""),
                                ),
                            )
                            persona_id = cursor.lastrowid
                            docs = p.get("documentos", [])
                            if docs:
                                valores_docs = [
                                    (
                                        persona_id,
                                        d.get("tipo_doc", "general"),
                                        d.get("nombre_archivo") or d.get("url_doc", ""),
                                    )
                                    for d in docs
                                ]
                                cursor.executemany(sql_doc, valores_docs)

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

        print(f"✅ Se registraron {len(ids_generados)} solicitud(es) con éxito: IDs {ids_generados}")
        return {
            "exito": True,
            "mensaje": f"Se registraron {len(ids_generados)} solicitud(es) exitosamente.",
            "ids_generados": ids_generados,
            "id_generado": ids_generados[0] if ids_generados else None,
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

                # 4. Obtener personas y sus documentos asociados desde documentos_persona
                mapeo_sub = {
                    "cedula": "cedulas",
                    "doc_identidad": "cedulas",
                    "identificacion": "cedulas",
                    "arl": "arl",
                    "examen": "examenes_medicos",
                    "examenes": "examenes_medicos",
                    "examenes_medicos": "examenes_medicos",
                    "medico": "examenes_medicos",
                    "otros": "otros",
                    "otro": "otros",
                    "actividad": "otros",
                }
                cursor.execute(
                    "SELECT id, item, ap_nombre, tipo_doc, identificacion, cargo "
                    "FROM personas_solicitud WHERE solicitud_id = %s ORDER BY item ASC",
                    (solicitud_id,),
                )
                personas = cursor.fetchall()
                for p in personas:
                    cursor.execute(
                        "SELECT id, tipo_doc, nombre_archivo FROM documentos_persona WHERE persona_id = %s",
                        (p["id"],),
                    )
                    docs = cursor.fetchall()
                    for d in docs:
                        sub = mapeo_sub.get(str(d["tipo_doc"]).lower(), "general")
                        d["url_acceso"] = f"/uploads/documentos/{sub}/{d['nombre_archivo']}"
                    p["documentos"] = docs
                solicitud["personas"] = personas

                # 5. Obtener los equipos asociados
                cursor.execute(
                    "SELECT marca, modelo, serie FROM equipos_solicitud WHERE solicitud_id = %s",
                    (solicitud_id,),
                )
                solicitud["eq_computo"] = cursor.fetchall()

                # 6. Recalcular is_active dinámicamente según la fecha actual y el rango de la solicitud
                from src.transformers.solicitudes_transformer import calcular_is_active
                solicitud["is_active"] = calcular_is_active(
                    solicitud.get("fecha_inicio"), solicitud.get("fecha_fin")
                )

                return {"exito": True, "datos": solicitud}

    except Exception as e:
        return {"exito": False, "mensaje": f"Error al consultar la solicitud: {e}"}

def GET_ALL_solicitudes_bd():

    try:

        with GET_conexion() as conexion:

            with conexion.cursor() as cursor: 

                cursor.execute("""
                    SELECT
                        so.id,
                        e.nombre_empresa,
                        ec.nombre,
                        CONCAT(u.nombres, ' ', u.apellidos) AS diligenciador,
                        so.fecha_inicio   AS fecha_ingreso,
                        so.fecha_fin      AS fecha_salida,
                        so.nivel_de_riesgo AS riesgo,
                        so.actividad,
                        so.fecha_creacion,
                        
                        GROUP_CONCAT(p.nombre SEPARATOR ', ') AS planta,
                        so.estado
                    FROM solicitudes so
                    INNER JOIN usuarios u ON so.diligenciado_por = u.id
                    INNER JOIN empresa e ON so.empresa_origen = e.id
                    INNER JOIN emp_contratista ec ON so.empresa_contratista = ec.id
                    LEFT JOIN visita v ON v.id_solicitud = so.id
                    LEFT JOIN planta p ON v.id_planta = p.id
                    GROUP BY so.id
                    ORDER BY so.id DESC
                """)

                datos = cursor.fetchall()  

                print(f"📦 [LOADER] Se recuperaron {len(datos)} solicitudes de la base de datos.")
        
                return {
                    "exito": True,
                    "datos": datos,
                    "mensaje": "Solicitudes recuperadas exitosamente."
                }

    except Exception as e:
        print(f"❌ [LOADER Error] Error consultando solicitudes: {e}")
        return {
            "exito": False,
            "mensaje": f"Error al consultar la base de datos: {str(e)}",
            "datos": []
        }

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
                            INSERT INTO personas_solicitud (
                                solicitud_id, item, ap_nombre, tipo_doc, identificacion, cargo
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        sql_doc = """
                            INSERT INTO documentos_persona (persona_id, tipo_doc, nombre_archivo)
                            VALUES (%s, %s, %s)
                        """
                        for idx, p in enumerate(personas, start=1):
                            cursor.execute(
                                sql_p,
                                (
                                    solicitud_id,
                                    idx,
                                    p.get("ap_nombre", ""),
                                    p.get("tipo_doc", ""),
                                    str(p.get("identificacion", "")),
                                    p.get("cargo", ""),
                                ),
                            )
                            persona_id = cursor.lastrowid
                            docs = p.get("documentos", [])
                            if docs:
                                valores_docs = [
                                    (
                                        persona_id,
                                        d.get("tipo_doc", "general"),
                                        d.get("nombre_archivo") or d.get("url_doc", ""),
                                    )
                                    for d in docs
                                ]
                                cursor.executemany(sql_doc, valores_docs)

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