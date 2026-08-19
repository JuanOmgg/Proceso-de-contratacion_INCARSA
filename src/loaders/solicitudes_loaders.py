import json
from database import GET_conexion
from typing import Dict, List, Any

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
                    # Pre-resolver los IDs de los vehículos para guardarlos en la columna 'vehiculos_ids' y en 'Veh_ingreso'
                    vehiculos_in = solicitud.get("vehiculos") or solicitud.get("vehiculo", [])
                    resolved_vehiculos = []
                    if vehiculos_in:
                        for v in vehiculos_in:
                            id_v = None
                            lic_doc = (
                                str(v.get("licencia_doc") or "").strip()
                                if isinstance(v, dict)
                                else ""
                            )

                            if isinstance(v, int):
                                id_v = v
                            elif isinstance(v, dict):
                                if v.get("id_vehiculo") and str(v.get("id_vehiculo")).isdigit():
                                    id_v = int(v["id_vehiculo"])
                                elif v.get("placa"):
                                    placa_norm = v.get("placa")
                                    tipo_norm = v.get("tipo", "VEHICULO")
                                    cursor.execute(
                                        "SELECT id FROM vehiculos WHERE placa = %s",
                                        (placa_norm,),
                                    )
                                    vehi_existente = cursor.fetchone()
                                    if vehi_existente:
                                        id_v = vehi_existente["id"]
                                    else:
                                        cursor.execute(
                                            "INSERT INTO vehiculos (tipo, placa) VALUES (%s, %s)",
                                            (tipo_norm, placa_norm),
                                        )
                                        id_v = cursor.lastrowid

                            if id_v:
                                resolved_vehiculos.append((id_v, lic_doc))

                    # 1. Resolver empresa_origen válida
                    cursor.execute("SELECT id FROM empresa WHERE id = %s", (emp_origen,))
                    if not cursor.fetchone():
                        cursor.execute("SELECT id FROM empresa LIMIT 1")
                        row_e = cursor.fetchone()
                        emp_origen = row_e["id"] if row_e else 1

                    # 2. Resolver empresa_contratista válida
                    raw_contratista = solicitud.get("empresa_contratista")
                    id_contratista = None
                    if str(raw_contratista).isdigit():
                        cursor.execute("SELECT id FROM emp_contratista WHERE id = %s", (int(raw_contratista),))
                        if cursor.fetchone():
                            id_contratista = int(raw_contratista)
                    if not id_contratista and raw_contratista:
                        cursor.execute("SELECT id FROM emp_contratista WHERE nombre = %s", (str(raw_contratista),))
                        row_c = cursor.fetchone()
                        if row_c:
                            id_contratista = row_c["id"]
                    if not id_contratista:
                        cursor.execute("SELECT id FROM emp_contratista LIMIT 1")
                        row_c_first = cursor.fetchone()
                        id_contratista = row_c_first["id"] if row_c_first else 1

                    # 3. Resolver diligenciado_por válido
                    raw_diligenciado = solicitud.get("diligenciado_por", 1)
                    id_diligenciado = int(raw_diligenciado) if str(raw_diligenciado).isdigit() and int(raw_diligenciado) > 0 else 1
                    cursor.execute("SELECT id FROM usuarios WHERE id = %s", (id_diligenciado,))
                    if not cursor.fetchone():
                        cursor.execute("SELECT id FROM usuarios LIMIT 1")
                        row_u = cursor.fetchone()
                        id_diligenciado = row_u["id"] if row_u else 1

                    str_plantas_ids = ",".join(map(str, sub_plantas)) if sub_plantas else ""

                    # Preparar IDs de personas como string CSV
                    personas_ids = solicitud.get("personas_ids", [])
                    str_personas_ids = ",".join(map(str, personas_ids)) if personas_ids else ""

                    # Preparar IDs de vehículos como string CSV
                    str_vehiculos_ids = (
                        ",".join(str(item[0]) for item in resolved_vehiculos)
                        if resolved_vehiculos
                        else ""
                    )

                    sql_solicitud = """
                        INSERT INTO solicitudes (
                            empresa_origen, diligenciado_por, nivel_de_riesgo, tipo_personal,
                            empresa_contratista, plantas_ids, personas_ids, vehiculos_ids,
                            fecha_inicio, fecha_fin, actividad, estado, is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    valores_solicitud = (
                        emp_origen,
                        id_diligenciado,
                        solicitud.get("nivel_de_riesgo", "BAJO"),
                        solicitud.get("tipo_personal", "Contratista"),
                        id_contratista,
                        str_plantas_ids,
                        str_personas_ids,
                        str_vehiculos_ids,
                        solicitud.get("fecha_inicio", ""),
                        solicitud.get("fecha_fin", ""),
                        solicitud.get("actividad", ""),
                        solicitud.get("estado", "ENVIADO"),
                        solicitud.get("is_active", True),
                    )

                    cursor.execute(sql_solicitud, valores_solicitud)
                    solicitud_id = cursor.lastrowid
                    ids_generados.append(solicitud_id)

                    # Registrar relaciones en tabla intermedia 'visita' validando FKs existentes
                    if sub_plantas:
                        try:
                            format_pl = ",".join(["%s"] * len(sub_plantas))
                            cursor.execute(f"SELECT id FROM planta WHERE id IN ({format_pl})", tuple(sub_plantas))
                            valid_plantas = [r["id"] for r in cursor.fetchall()]
                            if valid_plantas:
                                sql_visita = "INSERT INTO visita (id_solicitud, id_planta) VALUES (%s, %s)"
                                valores_visita = [(solicitud_id, p_id) for p_id in valid_plantas]
                                cursor.executemany(sql_visita, valores_visita)
                        except Exception as e_vis:
                            print(f"⚠️ Aviso al registrar en visita: {e_vis}")

                    # Registrar relaciones en tabla intermedia 'ingresantes' validando FKs existentes
                    if personas_ids:
                        try:
                            format_p = ",".join(["%s"] * len(personas_ids))
                            cursor.execute(f"SELECT id FROM personas WHERE id IN ({format_p})", tuple(personas_ids))
                            valid_personas = [r["id"] for r in cursor.fetchall()]
                            if valid_personas:
                                sql_ingresantes = "INSERT INTO ingresantes (id_solicitud, id_persona) VALUES (%s, %s)"
                                valores_ingresantes = [(solicitud_id, p_id) for p_id in valid_personas]
                                cursor.executemany(sql_ingresantes, valores_ingresantes)
                        except Exception as e_ing:
                            print(f"⚠️ Aviso al registrar en ingresantes: {e_ing}")

                    # Insertar vehículos en tabla de rompimiento 'Veh_ingreso'
                    if resolved_vehiculos:
                        try:
                            sql_vehingreso = """
                                INSERT INTO Veh_ingreso (id_solicitud, id_vehiculo, licencia_doc)
                                VALUES (%s, %s, %s)
                            """
                            for id_v, lic_doc in resolved_vehiculos:
                                cursor.execute(sql_vehingreso, (solicitud_id, id_v, lic_doc))

                            # Insertar documentos del vehículo si vienen adjuntos
                            for v_item in vehiculos_in:
                                if isinstance(v_item, dict) and v_item.get("documentos"):
                                    placa_v = v_item.get("placa")
                                    target_id_v = None
                                    if v_item.get("id_vehiculo") and str(v_item.get("id_vehiculo")).isdigit():
                                        target_id_v = int(v_item.get("id_vehiculo"))
                                    elif placa_v:
                                        cursor.execute("SELECT id FROM vehiculos WHERE placa = %s", (placa_v,))
                                        vehi_row = cursor.fetchone()
                                        if vehi_row:
                                            target_id_v = vehi_row["id"]
                                    if target_id_v:
                                        for doc_item in v_item["documentos"]:
                                            nom_doc = doc_item.get("nom_documento") or doc_item.get("nombre_archivo")
                                            tipo_doc = doc_item.get("tipo_doc") or "general"
                                            if nom_doc:
                                                cursor.execute(
                                                    "INSERT INTO documentos_vehiculo (id_vehiculo, tipo_doc, nom_documento) VALUES (%s, %s, %s)",
                                                    (target_id_v, tipo_doc, nom_doc)
                                                )
                        except Exception as e_veh:
                            print(f"⚠️ Aviso al registrar vehículos o documentos de vehículos: {e_veh}")

                    # Insertar equipos asociados a la solicitud
                    equipos = solicitud.get("eq_computo", [])
                    if equipos:
                        try:
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
                        except Exception as e_eq:
                            print(f"⚠️ Aviso al registrar equipos: {e_eq}")

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

                # 3. Obtener los vehículos asociados (vía tabla de rompimiento 'Veh_ingreso')
                cursor.execute(
                    """
                    SELECT v.id, v.tipo, v.placa, vi.licencia_doc
                    FROM Veh_ingreso vi
                    INNER JOIN vehiculos v ON vi.id_vehiculo = v.id
                    WHERE vi.id_solicitud = %s
                    """,
                    (solicitud_id,),
                )
                vehiculos = cursor.fetchall() or []
                for v in vehiculos:
                    lic = v.get("licencia_doc")
                    v["url_licencia"] = f"/uploads/documentos/vehiculos/{lic}" if lic else None
                    cursor.execute(
                        """
                        SELECT id, tipo_doc, nom_documento 
                        FROM documentos_vehiculo 
                        WHERE id_vehiculo = %s
                        """,
                        (v["id"],),
                    )
                    v_docs = cursor.fetchall() or []
                    for d in v_docs:
                        d["url_acceso"] = f"/uploads/documentos/vehiculos/{d['nom_documento']}"
                    v["documentos"] = v_docs

                solicitud["vehiculo"] = vehiculos
                solicitud["vehiculos"] = vehiculos

                # 4. Obtener ingresantes (personas) via tabla intermedia 'ingresantes'
                cursor.execute(
                    """
                    SELECT p.id, p.nombre, p.apellido, p.tipo_doc, p.identificacion, p.cargo
                    FROM ingresantes i
                    INNER JOIN personas p ON i.id_persona = p.id
                    WHERE i.id_solicitud = %s
                    """,
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
                        d["url_acceso"] = f"/uploads/documentos/{d['nombre_archivo']}"
                    p["documentos"] = docs
                solicitud["ingresantes"] = personas

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

def GET_ALL_solicitudes_bd(only_active: bool = True):

    try:

        with GET_conexion() as conexion:

            with conexion.cursor() as cursor:
                # Construir la query con filtro opcional de activos
                where_clause = ""
                if only_active:
                    where_clause = "WHERE CURDATE() BETWEEN so.fecha_inicio AND so.fecha_fin"

                query = f"""
                    SELECT
                        so.id,
                        e.nombre_empresa,
                        ec.nombre AS nombre_emContratista,
                        CONCAT(u.nombres, ' ', u.apellidos) AS diligenciador,
                        so.fecha_inicio   AS fecha_ingreso,
                        so.fecha_fin      AS fecha_salida,
                        so.nivel_de_riesgo AS riesgo,
                        so.actividad,
                        so.fecha_creacion,
                        so.estado,
                        IF(CURDATE() BETWEEN so.fecha_inicio AND so.fecha_fin, TRUE, FALSE) AS is_active,

                        GROUP_CONCAT(DISTINCT p.nombre SEPARATOR ', ') AS planta,

                        GROUP_CONCAT(DISTINCT
                            CONCAT_WS('|||',
                                per.id,
                                CONCAT(per.apellido, ' ', per.nombre),
                                per.tipo_doc,
                                per.identificacion,
                                per.cargo,
                                IFNULL(ing.autorizado, '')
                            )
                            SEPARATOR '###'
                        ) AS personas,

                        GROUP_CONCAT(DISTINCT
                            CONCAT_WS('|||',
                                vh.id,
                                vh.tipo,
                                vh.placa,
                                IFNULL(vi.licencia_doc, 0)
                            )
                            SEPARATOR '###'
                        ) AS vehiculos,

                        GROUP_CONCAT(DISTINCT
                            CONCAT_WS('|||',
                                es.id,
                                es.marca,
                                es.modelo,
                                es.serie
                            )
                            SEPARATOR '###'
                        ) AS computos
                        
                    FROM solicitudes so

                    LEFT JOIN equipos_solicitud es ON es.solicitud_id = so.id
                    INNER JOIN usuarios u ON so.diligenciado_por = u.id
                    INNER JOIN empresa e ON so.empresa_origen = e.id
                    INNER JOIN emp_contratista ec ON so.empresa_contratista = ec.id
                    
                    LEFT JOIN visita v ON v.id_solicitud = so.id
                    LEFT JOIN planta p ON v.id_planta = p.id
                    
                    LEFT JOIN ingresantes ing ON ing.id_solicitud = so.id
                    LEFT JOIN personas per ON ing.id_persona = per.id

                    LEFT JOIN Veh_ingreso vi ON vi.id_solicitud = so.id
                    LEFT JOIN vehiculos vh ON vi.id_vehiculo = vh.id

                    {where_clause}
                    GROUP BY so.id
                    ORDER BY so.id DESC
                """

                cursor.execute(query)

                datos = cursor.fetchall()  

                for row in datos:
                    if isinstance(row, dict) and 'personas' in row:
                        val_personas = row['personas']
                        if isinstance(val_personas, str):
                            if val_personas.strip() == "":
                                val_personas = []
                            else:
                                personas_list = []
                                for item in val_personas.split('###'):
                                    if not item:
                                        continue
                                    partes = item.split('|||')
                                    if len(partes) < 6:
                                        continue
                                    try:
                                        persona_id = int(partes[0]) if partes[0].isdigit() else None
                                    except Exception:
                                        persona_id = None
                                    personas_list.append({
                                        'id': persona_id,
                                        'ap_nombre': partes[1] or None,
                                        'tipo_doc': partes[2] or None,
                                        'identificacion': partes[3] or None,
                                        'cargo': partes[4] or None,
                                        'autorizado': partes[5] or None,
                                    })
                                val_personas = personas_list
                        
                        if isinstance(val_personas, list):
                            row['personas'] = [p for p in val_personas if p is not None]

                    if isinstance(row, dict) and 'vehiculos' in row:
                        val_vehiculos = row['vehiculos']
                        if isinstance(val_vehiculos, str):
                            if val_vehiculos.strip() == "":
                                val_vehiculos = []
                            else:
                                v_list = []
                                for item in val_vehiculos.split('###'):
                                    if not item:
                                        continue
                                    partes = item.split('|||')
                                    if len(partes) < 3:
                                        continue
                                    try:
                                        v_id = int(partes[0]) if partes[0].isdigit() else None
                                    except Exception:
                                        v_id = None
                                    lic_doc = partes[3].strip() if len(partes) > 3 and partes[3] else ""
                                    v_list.append({
                                        'id': v_id,
                                        'tipo': partes[1] or None,
                                        'placa': partes[2] or None,
                                        'licencia_doc': lic_doc,
                                        'licencia': lic_doc
                                    })
                                val_vehiculos = v_list
                        if isinstance(val_vehiculos, list):
                            row['vehiculos'] = [v for v in val_vehiculos if v is not None]
                            row['vehiculo'] = row['vehiculos']
                    
                    if isinstance(row, dict) and 'eq_computo' in row:
                        val_eq_computo = row['eq_computo']
                        if isinstance(val_eq_computo, str):
                            try:
                                val_eq_computo = json.loads(val_eq_computo)
                            except Exception:
                                val_eq_computo = []
                        
                        if isinstance(val_eq_computo, list):
                            row['eq_computo'] = [e for e in val_eq_computo if e is not None]

                # Asociar documentos de vehículos si existen
                try:
                    cursor.execute("SELECT id_vehiculo, tipo_doc, nom_documento FROM documentos_vehiculo")
                    docs_veh_db = cursor.fetchall()
                    docs_por_veh = {}
                    for d in docs_veh_db:
                        vid = d["id_vehiculo"]
                        if vid not in docs_por_veh:
                            docs_por_veh[vid] = []
                        docs_por_veh[vid].append({
                            "tipo_doc": d["tipo_doc"],
                            "nombre_archivo": d["nom_documento"],
                            "nom_documento": d["nom_documento"]
                        })
                    for row in datos:
                        for v in row.get("vehiculos", []):
                            if v.get("id") and v["id"] in docs_por_veh:
                                v["documentos"] = docs_por_veh[v["id"]]
                except Exception:
                    pass
                            
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

def GET_date_count_db() -> List[Dict[str, Any]]:

    try:

        with GET_conexion() as conexion:

            with conexion.cursor() as cursor:

                cursor.execute("SET lc_time_names = 'es_ES';")
                cursor.execute("""
                    SELECT 
                        DATE_FORMAT(s.fecha_creacion, '%Y-%m') AS month_key,
                        DATE_FORMAT(s.fecha_creacion, '%M') AS month,
                        COUNT(s.id) AS total
                    FROM solicitudes s
                    GROUP BY month_key, month
                    ORDER BY month_key ASC
                """)

                return cursor.fetchall()

    except Exception as e:
        print(f"❌ Error en GET_conteo_solicitudes_por_mes_db: {e}")
        raise e 

def UPDATE_solicitud_bd(solicitud_id: int, campos: dict) -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                personas = campos.pop("personas", None)
                eq_computo = campos.pop("eq_computo", None)
                vehiculo = campos.pop("vehiculo", None)
                if vehiculo is None:
                    vehiculo = campos.pop("vehiculos", None)

                # Sincronizar personas_ids y tabla intermedia ingresantes si vienen en el payload
                if "personas_ids" in campos:
                    raw_pids = campos["personas_ids"]
                    if isinstance(raw_pids, list):
                        campos["personas_ids"] = ",".join(map(str, raw_pids))
                        cursor.execute(
                            "DELETE FROM ingresantes WHERE id_solicitud = %s",
                            (solicitud_id,),
                        )
                        if raw_pids:
                            cursor.executemany(
                                "INSERT INTO ingresantes (id_solicitud, id_persona) VALUES (%s, %s)",
                                [(solicitud_id, p_id) for p_id in raw_pids],
                            )

                # Sincronizar plantas_ids y tabla intermedia visita si vienen en el payload
                if "plantas_ids" in campos:
                    raw_plids = campos["plantas_ids"]
                    if isinstance(raw_plids, list):
                        campos["plantas_ids"] = ",".join(map(str, raw_plids))
                        cursor.execute(
                            "DELETE FROM visita WHERE id_solicitud = %s",
                            (solicitud_id,),
                        )
                        if raw_plids:
                            cursor.executemany(
                                "INSERT INTO visita (id_solicitud, id_planta) VALUES (%s, %s)",
                                [(solicitud_id, p_id) for p_id in raw_plids],
                            )

                if campos:
                    columnas = [f"{col} = %s" for col in campos.keys()]
                    sql_update = f"UPDATE solicitudes SET {', '.join(columnas)} WHERE id = %s"
                    valores = list(campos.values()) + [solicitud_id]
                    cursor.execute(sql_update, valores)

                if vehiculo is not None:
                    cursor.execute(
                        "DELETE FROM Veh_ingreso WHERE id_solicitud = %s",
                        (solicitud_id,),
                    )
                    if vehiculo:
                        for v in vehiculo:
                            id_v = None
                            lic_doc = (
                                int(v.get("licencia_doc") or 0)
                                if isinstance(v, dict)
                                else 0
                            )

                            if isinstance(v, int):
                                id_v = v
                            elif isinstance(v, dict):
                                if v.get("id_vehiculo") and str(v.get("id_vehiculo")).isdigit():
                                    id_v = int(v["id_vehiculo"])
                                elif v.get("placa"):
                                    placa_norm = v.get("placa")
                                    tipo_norm = v.get("tipo", "VEHICULO")
                                    cursor.execute(
                                        "SELECT id FROM vehiculos WHERE placa = %s",
                                        (placa_norm,),
                                    )
                                    vehi_existente = cursor.fetchone()
                                    if vehi_existente:
                                        id_v = vehi_existente["id"]
                                    else:
                                        cursor.execute(
                                            "INSERT INTO vehiculos (tipo, placa) VALUES (%s, %s)",
                                            (tipo_norm, placa_norm),
                                        )
                                        id_v = cursor.lastrowid

                            if id_v:
                                sql_vehingreso = """
                                    INSERT INTO Veh_ingreso (id_solicitud, id_vehiculo, licencia_doc)
                                    VALUES (%s, %s, %s)
                                """
                                cursor.execute(
                                    sql_vehingreso, (solicitud_id, id_v, lic_doc)
                                )

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