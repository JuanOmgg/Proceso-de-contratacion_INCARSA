import json
import secrets
import string
from database import GET_conexion
from typing import Dict, List, Any, Optional

def Generate_unique_code(cursor) -> str:
    """
    Genera un código de radicado aleatorio y no predecible (ej: RAD-7K9M2P),
    garantizando que no colisione con códigos existentes en la base de datos.
    Excluye caracteres ambiguos (0, O, 1, I) para máxima legibilidad.
    """
    caracteres = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    while True:
        sufijo = "".join(secrets.choice(caracteres) for _ in range(6))
        codigo = f"RAD-{sufijo}"
        cursor.execute("SELECT id FROM solicitudes WHERE codigo = %s", (codigo,))
        if not cursor.fetchone():
            return codigo

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
                codigos_generados = []

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

                    # Determinar código radicado (si no viene, generar código aleatorio único)
                    raw_codigo = solicitud.get("codigo")
                    cod_val = str(raw_codigo).strip().upper() if raw_codigo and str(raw_codigo).strip() else None
                    if not cod_val:
                        cod_val = Generate_unique_code(cursor)

                    sql_solicitud = """
                        INSERT INTO solicitudes (
                            codigo, empresa_origen, diligenciado_por, nivel_de_riesgo, tipo_personal,
                            empresa_contratista, plantas_ids, personas_ids, vehiculos_ids,
                            fecha_inicio, fecha_fin, actividad, estado, is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    valores_solicitud = (
                        cod_val,
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
                    codigos_generados.append(cod_val)

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

                                # Sincronizar automáticamente antecedentes y antecedentes_historial_solicitudes
                                for p_id in valid_personas:
                                    try:
                                        cursor.execute("SELECT id FROM antecedentes WHERE id_persona = %s", (p_id,))
                                        ant_row = cursor.fetchone()
                                        if not ant_row:
                                            cursor.execute("""
                                                INSERT INTO antecedentes (id_persona, id_empresa, ultima_revision, fecha_consulta, fecha_creacion)
                                                VALUES (%s, %s, NOW(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR), NOW())
                                            """, (p_id, emp_origen))
                                            ant_id = cursor.lastrowid
                                        else:
                                            ant_id = ant_row["id"]
                                            cursor.execute("UPDATE antecedentes SET id_empresa = %s WHERE id = %s", (emp_origen, ant_id))

                                        cursor.execute("""
                                            INSERT INTO antecedentes_historial_solicitudes (id_antecedente, id_solicitud, id_empresa, fecha_solicitud)
                                            VALUES (%s, %s, %s, NOW())
                                        """, (ant_id, solicitud_id, emp_origen))
                                    except Exception as e_ant:
                                        print(f"⚠️ Aviso al sincronizar antecedentes para persona {p_id}: {e_ant}")
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
                                if lic_doc:
                                    cursor.execute(
                                        "SELECT id FROM documentos_vehiculo WHERE id_vehiculo = %s AND nom_documento = %s",
                                        (id_v, str(lic_doc)),
                                    )
                                    if not cursor.fetchone():
                                        cursor.execute(
                                            "INSERT INTO documentos_vehiculo (id_vehiculo, tipo_doc, nom_documento) VALUES (%s, %s, %s)",
                                            (id_v, "licencia", str(lic_doc)),
                                        )

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
            "codigos_generados": codigos_generados,
            "codigo": codigos_generados[0] if codigos_generados else None,
        }

    except Exception as e:
        print(f"❌ Error al intentar guardar en MySQL: {e}")
        return {"exito": False, "mensaje": f"Error en la base de datos: {e}"}


def GET_solicitud_bd(solicitud_id: int) -> dict:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Detectar columnas reales existentes en solicitudes
                cursor.execute("SHOW COLUMNS FROM solicitudes")
                cols = {r["Field"] for r in cursor.fetchall()}
                codigo_expr = "s.codigo" if "codigo" in cols else "CONCAT('RAD-', LPAD(s.id, 4, '0'))"
                obs_expr = "s.observaciones" if "observaciones" in cols else "''"
            
                # 2. Obtener la solicitud principal uniendo nombres de empresa, contratista y diligenciador
                id_num = int(solicitud_id) if str(solicitud_id).isdigit() else None
                cod_str = str(solicitud_id).strip().upper()
                where_clause = "WHERE s.id = %s OR s.codigo = %s" if id_num else "WHERE s.codigo = %s"
                params = (id_num, cod_str) if id_num else (cod_str,)

                sql_main = f"""
                    SELECT 
                        s.*,
                        COALESCE({codigo_expr}, CONCAT('RAD-', LPAD(s.id, 4, '0'))) AS codigo,
                        COALESCE({obs_expr}, '') AS observaciones,
                        e.nombre_empresa,
                        ec.nombre AS nombre_emContratista,
                        CONCAT(u.nombres, ' ', u.apellidos) AS diligenciador,
                        u.correo AS diligenciador_correo
                    FROM solicitudes s
                    LEFT JOIN empresa e ON s.empresa_origen = e.id
                    LEFT JOIN emp_contratista ec ON s.empresa_contratista = ec.id
                    LEFT JOIN usuarios u ON s.diligenciado_por = u.id
                    {where_clause}
                """
                cursor.execute(sql_main, params)
                solicitud = cursor.fetchone()

                if not solicitud:
                    return {
                        "exito": False,
                        "mensaje": f"Solicitud #{solicitud_id} no encontrada.",
                    }

                real_id = solicitud["id"]

                # Formatear fechas a texto
                if solicitud.get("fecha_inicio"):
                    solicitud["fecha_inicio"] = str(solicitud["fecha_inicio"])
                if solicitud.get("fecha_fin"):
                    solicitud["fecha_fin"] = str(solicitud["fecha_fin"])
                if solicitud.get("fecha_creacion"):
                    solicitud["fecha_creacion"] = str(solicitud["fecha_creacion"])

                # 3. Obtener las plantas asociadas (vía tabla intermedia 'visita')
                cursor.execute(
                    """
                    SELECT p.id, p.nombre 
                    FROM visita v
                    INNER JOIN planta p ON v.id_planta = p.id
                    WHERE v.id_solicitud = %s
                    """,
                    (real_id,),
                )
                solicitud["plantas"] = cursor.fetchall() or []

                # Fallback de plantas vía plantas_ids
                if not solicitud["plantas"] and solicitud.get("plantas_ids"):
                    try:
                        raw_ids = str(solicitud["plantas_ids"]).replace("[", "").replace("]", "").split(",")
                        p_ids = [int(x.strip()) for x in raw_ids if x.strip().isdigit()]
                        if p_ids:
                            fmt = ",".join(["%s"] * len(p_ids))
                            cursor.execute(f"SELECT id, nombre FROM planta WHERE id IN ({fmt})", tuple(p_ids))
                            solicitud["plantas"] = cursor.fetchall() or []
                    except Exception as e_p:
                        print(f"⚠️ Error al resolver plantas_ids de respaldo: {e_p}")

                # 4. Obtener los vehículos asociados (vía tabla de rompimiento 'Veh_ingreso')
                cursor.execute(
                    """
                    SELECT v.id, v.tipo, v.placa, vi.licencia_doc
                    FROM Veh_ingreso vi
                    INNER JOIN vehiculos v ON vi.id_vehiculo = v.id
                    WHERE vi.id_solicitud = %s
                    """,
                    (real_id,),
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

                # 5. Obtener ingresantes (personas) via tabla intermedia 'ingresantes'
                cursor.execute(
                    """
                    SELECT p.id, p.nombre, p.apellido, p.tipo_doc, p.identificacion, p.cargo,
                           COALESCE(i.autorizado, 1) AS autorizado, i.motivo
                    FROM ingresantes i
                    INNER JOIN personas p ON i.id_persona = p.id
                    WHERE i.id_solicitud = %s
                    """,
                    (real_id,),
                )
                personas = cursor.fetchall() or []

                # Fallback de personas vía personas_ids
                if not personas and solicitud.get("personas_ids"):
                    try:
                        raw_pids = str(solicitud["personas_ids"]).replace("[", "").replace("]", "").split(",")
                        p_ids = [int(x.strip()) for x in raw_pids if x.strip().isdigit()]
                        if p_ids:
                            fmt = ",".join(["%s"] * len(p_ids))
                            cursor.execute(f"SELECT p.id, p.nombre, p.apellido, p.tipo_doc, p.identificacion, p.cargo, 1 AS autorizado, NULL AS motivo FROM personas p WHERE p.id IN ({fmt})", tuple(p_ids))
                            personas = cursor.fetchall() or []
                    except Exception as e_pers:
                        print(f"⚠️ Error al resolver personas_ids de respaldo: {e_pers}")

                for p in personas:
                    p["autorizado"] = bool(p.get("autorizado", True))
                    p["motivo"] = p.get("motivo") or ""
                    cursor.execute(
                        "SELECT id, tipo_doc, nombre_archivo FROM documentos_persona WHERE persona_id = %s",
                        (p["id"],),
                    )
                    docs = cursor.fetchall() or []
                    for d in docs:
                        d["url_acceso"] = f"/uploads/documentos/{d['nombre_archivo']}"
                    p["documentos"] = docs
                solicitud["ingresantes"] = personas

                # 6. Obtener los equipos asociados
                cursor.execute(
                    "SELECT marca, modelo, serie FROM equipos_solicitud WHERE solicitud_id = %s",
                    (real_id,),
                )
                solicitud["eq_computo"] = cursor.fetchall() or []

                # 7. Obtener revisiones / dictámenes por planta
                cursor.execute(
                    """
                    SELECT sr.id, sr.id_solicitud, sr.id_planta, p.nombre AS nombre_planta,
                           sr.rol, sr.id_usuario, sr.nombre_revisor, sr.decision,
                           sr.motivo_rechazo, sr.observacion, sr.fecha_revision
                    FROM solicitud_revisiones sr
                    LEFT JOIN planta p ON sr.id_planta = p.id
                    WHERE sr.id_solicitud = %s
                    ORDER BY sr.fecha_revision ASC
                    """,
                    (real_id,),
                )
                raw_revs = cursor.fetchall() or []
                for r in raw_revs:
                    if r.get("fecha_revision"):
                        r["fecha_revision"] = str(r["fecha_revision"])
                solicitud["revisiones"] = raw_revs

                return {"exito": True, "datos": solicitud}

    except Exception as e:
        print(f"❌ Error en GET_solicitud_bd #{solicitud_id}: {e}")
        return {"exito": False, "mensaje": f"Error al consultar la solicitud: {e}"}

def REGISTRAR_dictamen_db(solicitud_id: int, dictamen: dict) -> dict:
    try:
        id_planta = dictamen.get("id_planta")
        rol = str(dictamen.get("rol", "")).strip().upper()
        decision_raw = str(dictamen.get("decision", "")).strip().lower()
        decision = "RECHAZADO" if "rechaz" in decision_raw else "APROBADO"
        motivo_rechazo = dictamen.get("motivo_rechazo") or ""
        observacion = dictamen.get("observacion") or ""
        id_usuario = dictamen.get("id_usuario")
        nombre_revisor = dictamen.get("nombre_revisor") or ""

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Verificar existencia de la solicitud
                cursor.execute("SELECT id, estado FROM solicitudes WHERE id = %s", (solicitud_id,))
                sol = cursor.fetchone()
                if not sol:
                    return {"exito": False, "mensaje": f"Solicitud #{solicitud_id} no encontrada."}

                # Si no viene nombre_revisor pero viene id_usuario, resolverlo
                if not nombre_revisor and id_usuario:
                    cursor.execute("SELECT nombres, apellidos FROM usuarios WHERE id = %s", (id_usuario,))
                    u = cursor.fetchone()
                    if u:
                        nombre_revisor = f"{u.get('nombres', '')} {u.get('apellidos', '')}".strip()

                # Si no viene id_planta y es SST o GESCO, y la solicitud solo tiene 1 planta, resolverla
                if (not id_planta or id_planta == 0) and rol in ("SST", "GESCO"):
                    cursor.execute("SELECT id_planta FROM visita WHERE id_solicitud = %s LIMIT 1", (solicitud_id,))
                    v_p = cursor.fetchone()
                    if v_p:
                        id_planta = v_p["id_planta"]

                # 2. Insertar o actualizar en solicitud_revisiones
                sql_upsert = """
                    INSERT INTO solicitud_revisiones (
                        id_solicitud, id_planta, rol, id_usuario, nombre_revisor,
                        decision, motivo_rechazo, observacion, fecha_revision
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                        id_usuario = VALUES(id_usuario),
                        nombre_revisor = VALUES(nombre_revisor),
                        decision = VALUES(decision),
                        motivo_rechazo = VALUES(motivo_rechazo),
                        observacion = VALUES(observacion),
                        fecha_revision = NOW()
                """
                cursor.execute(sql_upsert, (
                    solicitud_id, id_planta, rol, id_usuario, nombre_revisor,
                    decision, motivo_rechazo, observacion
                ))

                # 3. Obtener todas las plantas de la solicitud (vía visita)
                cursor.execute("SELECT DISTINCT id_planta FROM visita WHERE id_solicitud = %s", (solicitud_id,))
                plantas_sol = [r["id_planta"] for r in cursor.fetchall() or [] if r.get("id_planta")]

                # Fallback plantas vía solicitudes.plantas_ids si visita estaba vacía
                if not plantas_sol:
                    cursor.execute("SELECT plantas_ids FROM solicitudes WHERE id = %s", (solicitud_id,))
                    sol_p = cursor.fetchone()
                    if sol_p and sol_p.get("plantas_ids"):
                        plantas_sol = [int(x.strip()) for x in str(sol_p["plantas_ids"]).replace("[","").replace("]","").split(",") if x.strip().isdigit()]

                # 4. Determinar nuevo estado global de la solicitud
                nuevo_estado = sol.get("estado", "EN REVISIÓN")

                if decision == "RECHAZADO":
                    nuevo_estado = "RECHAZADO"
                    obs_rechazo = f"[RECHAZADO por {rol}]: {motivo_rechazo}. {observacion}".strip()
                    cursor.execute(
                        "UPDATE solicitudes SET estado = 'RECHAZADO', observaciones = %s WHERE id = %s",
                        (obs_rechazo, solicitud_id)
                    )
                elif rol == "SCR":
                    nuevo_estado = "APROBADO"
                    cursor.execute(
                        "UPDATE solicitudes SET estado = 'APROBADO' WHERE id = %s",
                        (solicitud_id,)
                    )
                else:
                    # Es SST o GESCO aprobando
                    cursor.execute(
                        """
                        SELECT id_planta, rol 
                        FROM solicitud_revisiones 
                        WHERE id_solicitud = %s AND decision = 'APROBADO'
                        """,
                        (solicitud_id,)
                    )
                    revs_aprobadas = cursor.fetchall() or []
                    
                    mapa_aprobaciones = {pid: {"SST": False, "GESCO": False} for pid in plantas_sol}
                    for ra in revs_aprobadas:
                        pid = ra.get("id_planta")
                        r_rol = ra.get("rol")
                        if pid in mapa_aprobaciones and r_rol in ("SST", "GESCO"):
                            mapa_aprobaciones[pid][r_rol] = True

                    todas_listas = False
                    if plantas_sol:
                        todas_listas = all(
                            mapa_aprobaciones[pid]["SST"] and mapa_aprobaciones[pid]["GESCO"]
                            for pid in plantas_sol
                        )

                    if todas_listas:
                        nuevo_estado = "POR APROBAR"
                    else:
                        nuevo_estado = "EN REVISIÓN"

                    cursor.execute(
                        "UPDATE solicitudes SET estado = %s WHERE id = %s",
                        (nuevo_estado, solicitud_id)
                    )

                conexion.commit()

                # 5. Obtener lista actualizada de revisiones
                cursor.execute(
                    """
                    SELECT sr.id, sr.id_solicitud, sr.id_planta, p.nombre AS nombre_planta,
                           sr.rol, sr.id_usuario, sr.nombre_revisor, sr.decision,
                           sr.motivo_rechazo, sr.observacion, sr.fecha_revision
                    FROM solicitud_revisiones sr
                    LEFT JOIN planta p ON sr.id_planta = p.id
                    WHERE sr.id_solicitud = %s
                    ORDER BY sr.fecha_revision ASC
                    """,
                    (solicitud_id,),
                )
                revs_actualizadas = cursor.fetchall() or []
                for r in revs_actualizadas:
                    if r.get("fecha_revision"):
                        r["fecha_revision"] = str(r["fecha_revision"])

                return {
                    "exito": True,
                    "mensaje": f"Dictamen registrado correctamente. Estado: {nuevo_estado}",
                    "nuevo_estado": nuevo_estado,
                    "revisiones": revs_actualizadas
                }

    except Exception as e:
        print(f"❌ Error al registrar dictamen para solicitud #{solicitud_id}: {e}")
        return {"exito": False, "mensaje": f"Error al registrar dictamen: {e}"}

def GET_ALL_solicitudes_bd(only_active: Optional[bool] = None, id_usuario: Optional[int] = None):

    try:

        with GET_conexion() as conexion:

            with conexion.cursor() as cursor:
                # Detectar columnas dinámicas
                cursor.execute("SHOW COLUMNS FROM solicitudes")
                cols = {r["Field"] for r in cursor.fetchall()}
                is_active_expr = "COALESCE(so.is_active, 1)" if "is_active" in cols else "IF(CURDATE() BETWEEN so.fecha_inicio AND so.fecha_fin, 1, 0)"
                codigo_expr = "so.codigo" if "codigo" in cols else "CONCAT('RAD-', LPAD(so.id, 4, '0'))"
                obs_expr = "so.observaciones" if "observaciones" in cols else "''"

                condiciones = []
                if only_active is True:
                    condiciones.append(f"{is_active_expr} = 1")
                elif only_active is False:
                    condiciones.append(f"{is_active_expr} = 0")

                # Si se provee id_usuario, verificar si tiene rol SST (3) o GESCO (4)
                if id_usuario:
                    cursor.execute("SELECT id_rol FROM usuarios WHERE id = %s", (id_usuario,))
                    u_row = cursor.fetchone()
                    if u_row and int(u_row.get("id_rol", 0)) in (3, 4):
                        cursor.execute("SELECT id_planta FROM usuario_plantas WHERE id_usuario = %s", (id_usuario,))
                        p_rows = cursor.fetchall() or []
                        p_ids = [int(pr["id_planta"]) for pr in p_rows if pr.get("id_planta")]
                        if not p_ids:
                            # Usuario SST/GESCO sin plantas asignadas: no ve ninguna solicitud
                            return {"exito": True, "datos": [], "mensaje": "Usuario sin plantas asignadas."}
                        
                        # Filtrar solicitudes que contengan al menos una de las plantas asignadas
                        in_list = ",".join(map(str, p_ids))
                        find_set_exprs = " OR ".join([f"FIND_IN_SET('{pid}', so.plantas_ids)" for pid in p_ids])
                        condiciones.append(f"(v.id_planta IN ({in_list}) OR ({find_set_exprs}))")

                where_clause = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

                query = f"""
                    SELECT
                        so.id,
                        COALESCE({codigo_expr}, CONCAT('RAD-', LPAD(so.id, 4, '0'))) AS codigo,
                        COALESCE({obs_expr}, '') AS observaciones,
                        e.nombre_empresa,
                        ec.nombre AS nombre_emContratista,
                        CONCAT(u.nombres, ' ', u.apellidos) AS diligenciador,
                        so.fecha_inicio   AS fecha_ingreso,
                        so.fecha_fin      AS fecha_salida,
                        so.nivel_de_riesgo AS riesgo,
                        so.actividad,
                        so.fecha_creacion,
                        so.estado,
                        {is_active_expr} AS is_active,

                        GROUP_CONCAT(DISTINCT p.nombre SEPARATOR ', ') AS planta,
                        GROUP_CONCAT(DISTINCT p.id SEPARATOR ',') AS plantas_ids,

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
                if personas is None:
                    personas = campos.pop("ingresantes", None)
                eq_computo = campos.pop("eq_computo", None)
                vehiculo = campos.pop("vehiculo", None)
                if vehiculo is None:
                    vehiculo = campos.pop("vehiculos", None)

                # Sincronizar personas e ingresantes (con estado autorizado y motivo)
                if personas is not None or "personas_ids" in campos:
                    lista_p = personas
                    if lista_p is None and "personas_ids" in campos:
                        raw_pids = campos["personas_ids"]
                        if isinstance(raw_pids, list):
                            campos["personas_ids"] = ",".join(map(str, raw_pids))
                            lista_p = [{"id": pid, "autorizado": True, "motivo": None} for pid in raw_pids]
                        elif isinstance(raw_pids, str):
                            lista_p = [{"id": int(x.strip()), "autorizado": True, "motivo": None} for x in raw_pids.split(",") if x.strip().isdigit()]

                    if isinstance(lista_p, list):
                        cursor.execute(
                            "DELETE FROM ingresantes WHERE id_solicitud = %s",
                            (solicitud_id,),
                        )
                        valores_ing = []
                        for item_p in lista_p:
                            if isinstance(item_p, dict):
                                p_id = item_p.get("id") or item_p.get("id_persona")
                                aut = item_p.get("autorizado", True)
                                if aut is False or aut == 0 or aut == "0" or aut == "false":
                                    aut_val = False
                                else:
                                    aut_val = True
                                mot = item_p.get("motivo") or item_p.get("motivo_rechazo") or None
                                if p_id:
                                    valores_ing.append((solicitud_id, int(p_id), aut_val, mot))
                            elif isinstance(item_p, (int, str)) and str(item_p).isdigit():
                                valores_ing.append((solicitud_id, int(item_p), True, None))

                        if valores_ing:
                            cursor.executemany(
                                "INSERT INTO ingresantes (id_solicitud, id_persona, autorizado, motivo) VALUES (%s, %s, %s, %s)",
                                valores_ing,
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