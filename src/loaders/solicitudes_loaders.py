import re
import json
import secrets
import string
from datetime import datetime
from database import GET_conexion
from typing import Dict, List, Any, Optional
from src.utils.broadcaster import notification_broadcaster
from src.transformers.vehiculo_transformer import FORMATEAR_PLACA

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
                            id_persona_conductor = None

                            if isinstance(v, int):
                                id_v = v
                            elif isinstance(v, dict):
                                cand_p = v.get("id_persona") or v.get("conductor_id")
                                if cand_p and str(cand_p).isdigit() and int(cand_p) > 0:
                                    id_persona_conductor = int(cand_p)
                                elif v.get("conductor"):
                                    cond_str = str(v.get("conductor")).strip()
                                    if cond_str.isdigit() and int(cond_str) > 0:
                                        id_persona_conductor = int(cond_str)
                                    else:
                                        cursor.execute(
                                            """
                                            SELECT id FROM personas 
                                            WHERE TRIM(CONCAT_WS(' ', COALESCE(nombre, ''), COALESCE(apellido, ''))) = %s 
                                               OR nombre = %s 
                                               OR CONCAT(COALESCE(nombre, ''), ' ', COALESCE(apellido, '')) = %s
                                               OR identificacion = %s
                                            ORDER BY id DESC LIMIT 1
                                            """,
                                            (cond_str, cond_str, cond_str, cond_str),
                                        )
                                        p_found = cursor.fetchone()
                                        if p_found:
                                            id_persona_conductor = p_found["id"]

                                target_id_v = v.get("id_vehiculo") or v.get("id")
                                if target_id_v and str(target_id_v).isdigit():
                                    id_v = int(target_id_v)
                                elif v.get("placa"):
                                    placa_norm = re.sub(r"[^A-Z0-9]", "", str(v.get("placa")).strip().upper())
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
                                resolved_vehiculos.append((id_v, lic_doc, id_persona_conductor))

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
                                                VALUES (%s, %s, NULL, NULL, NOW())
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
                                INSERT INTO Veh_ingreso (id_solicitud, id_vehiculo, licencia_doc, id_persona)
                                VALUES (%s, %s, %s, %s)
                            """
                            for id_v, lic_doc, id_persona_conductor in resolved_vehiculos:
                                cursor.execute(sql_vehingreso, (solicitud_id, id_v, lic_doc, id_persona_conductor))
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

                    # Notificar a los roles revisores (SST y GESCO) sobre la nueva solicitud
                    try:
                        cursor.execute("SELECT id, nombre_rol FROM roles WHERE nombre_rol IN ('SST', 'GESCO')")
                        roles_revisores = cursor.fetchall() or []
                        for r_rev in roles_revisores:
                            if cod_val:
                                tit_notif = f"Nueva solicitud para revisión ({r_rev['nombre_rol']})"
                                msg_notif = f"Se radicó la solicitud {cod_val} y requiere revisión de {r_rev['nombre_rol']}."
                                cursor.execute(
                                    """
                                    INSERT INTO notificaciones (rol_destino, titulo, mensaje, tipo, enlace)
                                    VALUES (%s, %s, %s, %s, %s)
                                    """,
                                    (
                                        r_rev["id"],
                                        tit_notif,
                                        msg_notif,
                                        "info",
                                        f"/solicitudes/revision/{cod_val}"
                                    )
                                )
                                # Notificar en caliente a cada rol revisor
                                notification_broadcaster.notificar_nueva(
                                    {
                                        "titulo": tit_notif,
                                        "mensaje": msg_notif,
                                        "tipo": "info",
                                        "enlace": f"/solicitudes/revision/{cod_val}",
                                        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "leido": False,
                                        "rol_destino": r_rev["id"]
                                    },
                                    target_role_id=r_rev["id"]
                                )

                        # Notificar cambio general de solicitudes para refrescar tablas y tableros en caliente
                        if cod_val:
                            notification_broadcaster.notificar_cambio_solicitud(
                                codigo_solicitud=cod_val,
                                nuevo_estado="ENVIADO",
                                detalle="Nueva solicitud radicada en el sistema"
                            )
                    except Exception as e_notif:
                        print(f"⚠️ Aviso al generar notificación de nueva solicitud: {e_notif}")

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
                        ec.nit AS nit_emContratista,
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
                solicitud["pre_aprobado"] = bool(solicitud.get("pre_aprobado", False))

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
                    SELECT v.id, v.tipo, v.placa, vi.licencia_doc,
                           COALESCE(vi.autorizado, 1) AS autorizado, vi.motivo,
                           vi.id_persona,
                           TRIM(CONCAT(COALESCE(p.nombre, ''), ' ', COALESCE(p.apellido, ''))) AS conductor
                    FROM Veh_ingreso vi
                    INNER JOIN vehiculos v ON vi.id_vehiculo = v.id
                    LEFT JOIN personas p ON vi.id_persona = p.id
                    WHERE vi.id_solicitud = %s
                    """,
                    (real_id,),
                )
                vehiculos = cursor.fetchall() or []
                for v in vehiculos:
                    v["autorizado"] = bool(v.get("autorizado", True))
                    v["motivo"] = v.get("motivo") or ""
                    v["motivo_rechazo"] = v["motivo"]
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
                           COALESCE(i.autorizado, 1) AS autorizado, i.motivo,
                           a.fecha_consulta, a.ultima_revision, a.responsable, a.anotaciones,
                           ind.fecha_induccion, ind.fecha_vigencia AS fecha_vigencia_induccion,
                           ind.responsable AS responsable_induccion, ind.anotaciones AS anotaciones_induccion
                    FROM ingresantes i
                    INNER JOIN personas p ON i.id_persona = p.id
                    LEFT JOIN antecedentes a ON a.id_persona = p.id
                    LEFT JOIN inducciones ind ON ind.id_persona = p.id
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
                            cursor.execute(
                                f"""
                                SELECT p.id, p.nombre, p.apellido, p.tipo_doc, p.identificacion, p.cargo,
                                       1 AS autorizado, NULL AS motivo,
                                       a.fecha_consulta, a.ultima_revision, a.responsable, a.anotaciones,
                                       ind.fecha_induccion, ind.fecha_vigencia AS fecha_vigencia_induccion,
                                       ind.responsable AS responsable_induccion, ind.anotaciones AS anotaciones_induccion
                                FROM personas p
                                LEFT JOIN antecedentes a ON a.id_persona = p.id
                                LEFT JOIN inducciones ind ON ind.id_persona = p.id
                                WHERE p.id IN ({fmt})
                                """,
                                tuple(p_ids)
                            )
                            personas = cursor.fetchall() or []
                    except Exception as e_pers:
                        print(f"⚠️ Error al resolver personas_ids de respaldo: {e_pers}")

                for p in personas:
                    p["autorizado"] = bool(p.get("autorizado", True))
                    p["motivo"] = p.get("motivo") or ""
                    if p.get("fecha_consulta"):
                        p["fecha_consulta"] = str(p["fecha_consulta"]).split(" ")[0]
                    else:
                        p["fecha_consulta"] = None
                    if p.get("ultima_revision"):
                        p["ultima_revision"] = str(p["ultima_revision"])
                    else:
                        p["ultima_revision"] = None
                    if p.get("fecha_induccion"):
                        p["fecha_induccion"] = str(p["fecha_induccion"]).split(" ")[0]
                    else:
                        p["fecha_induccion"] = None
                    if p.get("fecha_vigencia_induccion"):
                        p["fecha_vigencia_induccion"] = str(p["fecha_vigencia_induccion"]).split(" ")[0]
                    else:
                        p["fecha_vigencia_induccion"] = None

                    cursor.execute(
                        "SELECT id, tipo_doc, nombre_archivo, vigencia FROM documentos_persona WHERE persona_id = %s",
                        (p["id"],),
                    )
                    docs = cursor.fetchall() or []
                    for d in docs:
                        d["url_acceso"] = f"/uploads/documentos/{d['nombre_archivo']}"
                        if d.get("vigencia"):
                            d["vigencia"] = str(d["vigencia"]).split(" ")[0]
                    p["documentos"] = docs

                solicitud["ingresantes"] = personas
                solicitud["personas"] = personas

                # 6. Obtener los equipos asociados
                cursor.execute(
                    "SELECT id, marca, modelo, serie FROM equipos_solicitud WHERE solicitud_id = %s",
                    (real_id,),
                )
                eqs = cursor.fetchall() or []
                solicitud["eq_computo"] = eqs
                solicitud["equipos"] = eqs
                solicitud["computos"] = eqs

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

def NOTIFICAR_edicion_sst_gesco_db(
    cursor,
    real_id: int,
    codigo_sol: str,
    rol: str,
    nombre_revisor: str = "",
    detalle: Optional[str] = None
):
    """
    Envía una notificación a SCR y roles superiores (ADMINISTRADOR, SUPERADMIN, etc.)
    cada vez que SST o GESCO realiza una edición o autoriza personas en una solicitud.
    """
    try:
        cod_sol_clean = codigo_sol or f"RAD-{real_id:04d}"
        revisor_txt = f" ({nombre_revisor})" if nombre_revisor else ""
        tit_notif = f"⚠️ Edición de personal en {cod_sol_clean} ({rol})"
        msg_notif = f"{rol}{revisor_txt} ha modificado la autorización de personas en la solicitud {cod_sol_clean} tras haber emitido visto bueno previo."
        if detalle:
            msg_notif += f" ({detalle})"
        msg_notif += " Haz clic para revisar el expediente."

        enlace_notif = f"/solicitudes/revision/{cod_sol_clean}"
        now_notif_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Roles destinatarios: SCR y roles superiores
        cursor.execute(
            """
            SELECT id FROM roles 
            WHERE UPPER(nombre_rol) LIKE '%SCR%' 
               OR UPPER(nombre_rol) IN ('ADMINISTRADOR', 'ADMIN', 'SUPERADMIN')
            """
        )
        roles_dest = [r["id"] for r in (cursor.fetchall() or []) if r.get("id")]
        if not roles_dest:
            roles_dest = [8, 1, 2]

        for r_id in roles_dest:
            cursor.execute(
                """
                INSERT INTO notificaciones (rol_destino, titulo, mensaje, tipo, enlace, leido, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, FALSE, NOW())
                """,
                (r_id, tit_notif, msg_notif, "warning", enlace_notif)
            )

        notification_broadcaster.notificar_nueva(
            {
                "titulo": tit_notif,
                "mensaje": msg_notif,
                "tipo": "warning",
                "enlace": enlace_notif,
                "fecha_creacion": now_notif_str,
                "leido": False,
            },
            target_roles_ids=roles_dest
        )
        print(f"🔔 [NOTIFICACIÓN ENVIADA] Edición de {rol} en solicitud #{cod_sol_clean} notificada a roles {roles_dest}.")
    except Exception as e:
        print(f"⚠️ Error al notificar edición de SST/GESCO: {e}")

def REGISTRAR_dictamen_db(solicitud_id: Any, dictamen: dict) -> dict:
    try:
        id_planta = dictamen.get("id_planta")
        rol = str(dictamen.get("rol", "")).strip().upper()
        decision_raw = str(dictamen.get("decision", "")).strip().lower()
        if "devolv" in decision_raw or "devuelt" in decision_raw or "correcci" in decision_raw or "devolver" in decision_raw:
            decision = "DEVUELTO"
        elif "preaprob" in decision_raw or "pre-aprob" in decision_raw or "pre_aprob" in decision_raw:
            decision = "PREAPROBADO"
        elif "rechaz" in decision_raw:
            decision = "RECHAZADO"
        else:
            decision = "APROBADO"

        motivo_rechazo = dictamen.get("motivo_rechazo") or dictamen.get("motivo_devolucion") or ""
        observacion = dictamen.get("observacion") or ""
        id_usuario = dictamen.get("id_usuario")
        nombre_revisor = dictamen.get("nombre_revisor") or ""

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Verificar existencia de la solicitud y resolver ID numérico real
                id_num = int(solicitud_id) if str(solicitud_id).strip().isdigit() else None
                cod_str = str(solicitud_id).strip().upper()
                if id_num:
                    cursor.execute("SELECT id, codigo, estado, diligenciado_por, pre_aprobado FROM solicitudes WHERE id = %s OR codigo = %s", (id_num, cod_str))
                else:
                    cursor.execute("SELECT id, codigo, estado, diligenciado_por, pre_aprobado FROM solicitudes WHERE codigo = %s", (cod_str,))
                sol = cursor.fetchone()
                if not sol:
                    return {"exito": False, "mensaje": f"Solicitud #{solicitud_id} no encontrada."}

                real_id = int(sol["id"])

                # Si no viene nombre_revisor pero viene id_usuario, resolverlo
                if not nombre_revisor and id_usuario:
                    cursor.execute("SELECT nombres, apellidos FROM usuarios WHERE id = %s", (id_usuario,))
                    u = cursor.fetchone()
                    if u:
                        nombre_revisor = f"{u.get('nombres', '')} {u.get('apellidos', '')}".strip()

                # Si no viene id_planta y es SST o GESCO, resolver de visita o plantas_ids
                if (not id_planta or id_planta == 0) and rol in ("SST", "GESCO"):
                    cursor.execute("SELECT id_planta FROM visita WHERE id_solicitud = %s LIMIT 1", (real_id,))
                    v_p = cursor.fetchone()
                    if v_p:
                        id_planta = v_p["id_planta"]
                    else:
                        cursor.execute("SELECT plantas_ids FROM solicitudes WHERE id = %s", (real_id,))
                        sol_p = cursor.fetchone()
                        if sol_p and sol_p.get("plantas_ids"):
                            p_list = [int(x.strip()) for x in str(sol_p["plantas_ids"]).replace("[","").replace("]","").split(",") if x.strip().isdigit()]
                            if p_list:
                                id_planta = p_list[0]

                # Verificar si ya existía una revisión previa para este rol (visto bueno previo)
                habia_visto_bueno_previo = False
                if id_planta is None:
                    cursor.execute(
                        "SELECT id, decision FROM solicitud_revisiones WHERE id_solicitud = %s AND id_planta IS NULL AND UPPER(rol) = %s",
                        (real_id, rol)
                    )
                    rev_existente = cursor.fetchone()
                    if rev_existente and rev_existente.get("decision"):
                        habia_visto_bueno_previo = True
                else:
                    cursor.execute(
                        "SELECT id, decision FROM solicitud_revisiones WHERE id_solicitud = %s AND id_planta = %s AND UPPER(rol) = %s",
                        (real_id, id_planta, rol)
                    )
                    rev_existente = cursor.fetchone()
                    if rev_existente and rev_existente.get("decision"):
                        habia_visto_bueno_previo = True

                # 2. Insertar o actualizar en solicitud_revisiones
                if id_planta is None:
                    cursor.execute(
                        "SELECT id FROM solicitud_revisiones WHERE id_solicitud = %s AND id_planta IS NULL AND UPPER(rol) = %s",
                        (real_id, rol)
                    )
                    rev_existente = cursor.fetchone()
                    if rev_existente:
                        cursor.execute(
                            """
                            UPDATE solicitud_revisiones
                            SET id_usuario = %s, nombre_revisor = %s, decision = %s,
                                motivo_rechazo = %s, observacion = %s, fecha_revision = NOW()
                            WHERE id = %s
                            """,
                            (id_usuario, nombre_revisor, decision, motivo_rechazo, observacion, rev_existente["id"])
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO solicitud_revisiones (
                                id_solicitud, id_planta, rol, id_usuario, nombre_revisor,
                                decision, motivo_rechazo, observacion, fecha_revision
                            ) VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, NOW())
                            """,
                            (real_id, rol, id_usuario, nombre_revisor, decision, motivo_rechazo, observacion)
                        )
                else:
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
                        real_id, id_planta, rol, id_usuario, nombre_revisor,
                        decision, motivo_rechazo, observacion
                    ))

                # 2.1 Sincronizar autorizaciones individuales de personas (ingresantes)
                personas_input = dictamen.get("personas")
                es_scr_o_superior = rol in ("SCR", "SUPERADMIN", "ADMINISTRADOR", "ADMIN")
                hubo_cambio_personas_aut = False

                if personas_input and isinstance(personas_input, list):
                    cursor.execute("SELECT id_persona, COALESCE(autorizado, 1) AS autorizado FROM ingresantes WHERE id_solicitud = %s", (real_id,))
                    ingresantes_db = {int(r["id_persona"]): bool(r["autorizado"]) for r in (cursor.fetchall() or []) if r.get("id_persona") is not None}

                    for p_item in personas_input:
                        if not isinstance(p_item, dict):
                            continue
                        p_id = p_item.get("id") or p_item.get("id_persona")
                        if not p_id:
                            continue
                        try:
                            p_id = int(p_id)
                        except (ValueError, TypeError):
                            continue

                        p_aut = bool(p_item.get("autorizado", True))
                        p_motivo = p_item.get("motivo") or p_item.get("motivo_rechazo") or None

                        # Regla de negocio: GESCO, SST, SCR y roles superiores PUEDEN autorizar personas
                        # incluso si estaban sin autorización en una revisión previa.
                        if p_id in ingresantes_db and not ingresantes_db[p_id]:
                            if not (es_scr_o_superior or rol in ("SST", "GESCO")):
                                p_aut = False

                        if p_id in ingresantes_db and ingresantes_db[p_id] != p_aut:
                            hubo_cambio_personas_aut = True

                        cursor.execute(
                            """
                            INSERT INTO ingresantes (id_solicitud, id_persona, autorizado, motivo)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                autorizado = VALUES(autorizado),
                                motivo = VALUES(motivo)
                            """,
                            (real_id, p_id, 1 if p_aut else 0, p_motivo)
                        )

                # 2.2 Sincronizar autorizaciones individuales de vehículos (Veh_ingreso)
                vehiculos_input = dictamen.get("vehiculos")
                if vehiculos_input and isinstance(vehiculos_input, list):
                    cursor.execute("SELECT id_vehiculo, COALESCE(autorizado, 1) AS autorizado FROM Veh_ingreso WHERE id_solicitud = %s", (real_id,))
                    veh_db = {int(r["id_vehiculo"]): bool(r["autorizado"]) for r in (cursor.fetchall() or []) if r.get("id_vehiculo") is not None}

                    for v_item in vehiculos_input:
                        if not isinstance(v_item, dict):
                            continue
                        v_id = v_item.get("id") or v_item.get("id_vehiculo")
                        if not v_id:
                            continue
                        try:
                            v_id = int(v_id)
                        except (ValueError, TypeError):
                            continue

                        v_aut = bool(v_item.get("autorizado", True))
                        v_motivo = v_item.get("motivo") or v_item.get("motivo_rechazo") or None

                        if v_id in veh_db and not veh_db[v_id]:
                            if not es_scr_o_superior:
                                v_aut = False

                        cursor.execute(
                            """
                            INSERT INTO Veh_ingreso (id_solicitud, id_vehiculo, autorizado, motivo)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                autorizado = VALUES(autorizado),
                                motivo = VALUES(motivo)
                            """,
                            (real_id, v_id, 1 if v_aut else 0, v_motivo)
                        )

                # 3. Obtener todas las plantas de la solicitud (vía visita)
                cursor.execute("SELECT DISTINCT id_planta FROM visita WHERE id_solicitud = %s", (real_id,))
                plantas_sol = [r["id_planta"] for r in cursor.fetchall() or [] if r.get("id_planta")]

                # Fallback plantas vía solicitudes.plantas_ids si visita estaba vacía
                if not plantas_sol:
                    cursor.execute("SELECT plantas_ids FROM solicitudes WHERE id = %s", (real_id,))
                    sol_p = cursor.fetchone()
                    if sol_p and sol_p.get("plantas_ids"):
                        plantas_sol = [int(x.strip()) for x in str(sol_p["plantas_ids"]).replace("[","").replace("]","").split(",") if x.strip().isdigit()]

                if not plantas_sol and id_planta:
                    plantas_sol = [id_planta]

                # 4. Determinar nuevo estado global de la solicitud
                nuevo_estado = sol.get("estado", "EN REVISIÓN")
                token_edicion = None

                if decision == "DEVUELTO":
                    nuevo_estado = "DEVUELTO PARA CORRECCIÓN"
                    token_edicion = secrets.token_urlsafe(32)
                    obs_devolucion = f"[DEVUELTO por {rol} para corrección]: {motivo_rechazo}. {observacion}".strip()
                    cursor.execute(
                        """
                        UPDATE solicitudes 
                        SET estado = 'DEVUELTO PARA CORRECCIÓN',
                            token_edicion = %s,
                            token_edicion_usado = FALSE,
                            motivo_devolucion = %s,
                            observaciones = CONCAT(IFNULL(observaciones, ''), '\n', %s)
                        WHERE id = %s
                        """,
                        (token_edicion, motivo_rechazo or observacion, obs_devolucion, real_id)
                    )
                elif decision == "RECHAZADO":
                    nuevo_estado = "RECHAZADO"
                    obs_rechazo = f"[RECHAZADO por {rol}]: {motivo_rechazo}. {observacion}".strip()
                    cursor.execute(
                        "UPDATE solicitudes SET estado = 'RECHAZADO', observaciones = %s WHERE id = %s",
                        (obs_rechazo, real_id)
                    )
                elif decision == "PREAPROBADO":
                    # SCR o SuperAdmin pre-aprueba la solicitud en etapas previas
                    nuevo_estado = sol.get("estado", "EN REVISIÓN")
                    obs_pre = f"[PRE-APROBADO por {rol}]: {observacion}".strip()
                    cursor.execute(
                        """
                        UPDATE solicitudes 
                        SET pre_aprobado = 1,
                            observaciones = CONCAT(IFNULL(observaciones, ''), '\n', %s)
                        WHERE id = %s
                        """,
                        (obs_pre, real_id)
                    )
                elif rol in ("SCR", "SUPERADMIN", "ADMINISTRADOR", "ADMIN") or (id_planta is None and decision == "APROBADO"):
                    nuevo_estado = "APROBADO"
                    cursor.execute(
                        "UPDATE solicitudes SET estado = 'APROBADO' WHERE id = %s",
                        (real_id,)
                    )
                    # Desactivar botones de confirmación en notificaciones previas de esta solicitud
                    cod_sol_clean = sol.get("codigo") or f"RAD-{real_id:04d}"
                    cursor.execute(
                        """
                        UPDATE notificaciones
                        SET leido = TRUE,
                            enlace = REPLACE(enlace, '?confirmar=true', '')
                        WHERE enlace LIKE %s
                        """,
                        (f"%{cod_sol_clean}%",)
                    )
                else:
                    # Es SST o GESCO aprobando
                    cursor.execute(
                        """
                        SELECT id_planta, rol 
                        FROM solicitud_revisiones 
                        WHERE id_solicitud = %s AND decision = 'APROBADO'
                        """,
                        (real_id,)
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
                        (nuevo_estado, real_id)
                    )

                # Notificaciones automáticas basadas en el dictamen emitido
                try:
                    cod_sol = sol.get("codigo") or f"RAD-{real_id:04d}"
                    id_creador = sol.get("diligenciado_por")
                    
                    now_notif_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    if decision == "DEVUELTO":
                        tit = f"⚠️ Solicitud {cod_sol} devuelta para corrección"
                        msg = f"SCR ha devuelto la solicitud {cod_sol}. Motivo: {motivo_rechazo or 'Inconsistencias detectadas'}. Haz clic para ingresar a la edición única."
                        tipo_notif = "warning"
                        link_edicion = f"/solicitudes/editar/{cod_sol}?token={token_edicion}"
                        
                        if id_creador:
                            cursor.execute(
                                """
                                INSERT INTO notificaciones (id_usuario, titulo, mensaje, tipo, enlace)
                                VALUES (%s, %s, %s, %s, %s)
                                """,
                                (id_creador, tit, msg, tipo_notif, link_edicion)
                            )
                            notification_broadcaster.notificar_nueva(
                                {
                                    "titulo": tit,
                                    "mensaje": msg,
                                    "tipo": tipo_notif,
                                    "enlace": link_edicion,
                                    "fecha_creacion": now_notif_str,
                                    "leido": False,
                                    "id_usuario": id_creador
                                },
                                target_user_id=id_creador
                            )
                        
                        # También alertar al rol GESTION DOCUMENTAL
                        cursor.execute("SELECT id FROM roles WHERE UPPER(nombre_rol) LIKE '%DOCUMENTAL%' LIMIT 1")
                        r_gd = cursor.fetchone()
                        if r_gd:
                            cursor.execute(
                                """
                                INSERT INTO notificaciones (rol_destino, titulo, mensaje, tipo, enlace)
                                VALUES (%s, %s, %s, %s, %s)
                                """,
                                (r_gd["id"], tit, msg, tipo_notif, link_edicion)
                            )
                            notification_broadcaster.notificar_nueva(
                                {
                                    "titulo": tit,
                                    "mensaje": msg,
                                    "tipo": tipo_notif,
                                    "enlace": link_edicion,
                                    "fecha_creacion": now_notif_str,
                                    "leido": False,
                                    "rol_destino": r_gd["id"]
                                },
                                target_role_id=r_gd["id"]
                            )
                    elif decision == "PREAPROBADO":
                        tit = f"Solicitud {cod_sol} Pre-aprobada por SCR"
                        msg = f"SCR ha emitido visto bueno preliminar (Pre-aprobación) para {cod_sol}. Continuará con las revisiones técnicas de SST y GESCO."
                        tipo_notif = "info"
                        if id_creador:
                            cursor.execute(
                                """
                                INSERT INTO notificaciones (id_usuario, titulo, mensaje, tipo, enlace)
                                VALUES (%s, %s, %s, %s, %s)
                                """,
                                (id_creador, tit, msg, tipo_notif, f"/solicitudes/revision/{cod_sol}")
                            )
                            notification_broadcaster.notificar_nueva(
                                {
                                    "titulo": tit,
                                    "mensaje": msg,
                                    "tipo": tipo_notif,
                                    "enlace": f"/solicitudes/revision/{cod_sol}",
                                    "fecha_creacion": now_notif_str,
                                    "leido": False,
                                    "id_usuario": id_creador
                                },
                                target_user_id=id_creador
                            )
                    elif id_creador:
                        if decision == "RECHAZADO":
                            tit = f"Solicitud {cod_sol} Rechazada"
                            msg = f"{rol} ha rechazado la solicitud {cod_sol}. Motivo: {motivo_rechazo or 'Sin motivo detallado'}"
                            tipo_notif = "error"
                        elif nuevo_estado == "APROBADO":
                            tit = f"¡Solicitud {cod_sol} Aprobada!"
                            msg = f"Tu solicitud {cod_sol} completó todas las revisiones y fue Aprobada para ingreso."
                            tipo_notif = "success"
                        else:
                            tit = f"Revisión {rol} en {cod_sol}"
                            msg = f"{rol} ha emitido dictamen favorable para {cod_sol}. Estado: {nuevo_estado}."
                            tipo_notif = "info"

                        cursor.execute(
                            """
                            INSERT INTO notificaciones (id_usuario, titulo, mensaje, tipo, enlace)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (id_creador, tit, msg, tipo_notif, f"/solicitudes/revision/{cod_sol}")
                        )
                        notification_broadcaster.notificar_nueva(
                            {
                                "titulo": tit,
                                "mensaje": msg,
                                "tipo": tipo_notif,
                                "enlace": f"/solicitudes/revision/{cod_sol}",
                                "fecha_creacion": now_notif_str,
                                "leido": False,
                                "id_usuario": id_creador
                            },
                            target_user_id=id_creador
                        )

                    # Si pasó a POR APROBAR, alertar al rol SCR para el visto bueno final
                    if nuevo_estado == "POR APROBAR":
                        cursor.execute("SELECT id FROM roles WHERE UPPER(nombre_rol) = 'SCR' LIMIT 1")
                        r_scr = cursor.fetchone()
                        if r_scr:
                            cursor.execute("SELECT pre_aprobado FROM solicitudes WHERE id = %s", (real_id,))
                            sol_pre = cursor.fetchone()
                            esta_preaprobada = bool(sol_pre.get("pre_aprobado")) if sol_pre else False

                            if esta_preaprobada:
                                # Notificación especializada con observaciones de SST y GESCO
                                cursor.execute(
                                    """
                                    SELECT sr.rol, p.nombre AS planta_nombre, sr.nombre_revisor, sr.decision, sr.observacion
                                    FROM solicitud_revisiones sr
                                    LEFT JOIN planta p ON sr.id_planta = p.id
                                    WHERE sr.id_solicitud = %s AND UPPER(sr.rol) IN ('SST', 'GESCO')
                                    ORDER BY sr.fecha_revision ASC
                                    """,
                                    (real_id,)
                                )
                                revs_tecnicas = cursor.fetchall() or []
                                items_obs = []
                                for rt in revs_tecnicas:
                                    r_rol = rt.get("rol", "")
                                    r_pl = f" ({rt.get('planta_nombre')})" if rt.get("planta_nombre") else ""
                                    r_obs = (rt.get("observacion") or "").strip()
                                    if r_obs:
                                        items_obs.append(f"• {r_rol}{r_pl}: {r_obs}")

                                if items_obs:
                                    bloque_obs = "\nObservaciones remitidas por SST / GESCO:\n" + "\n".join(items_obs)
                                else:
                                    bloque_obs = "\nSin observaciones adicionales de SST ni GESCO."

                                tit_scr = f"⚡ Solicitud Preaprobada {cod_sol} en 'Por Aprobar'"
                                msg_scr = (
                                    f"La solicitud {cod_sol} que dejaste PREAPROBADA completó las revisiones de SST y GESCO y ya está en 'Por Aprobar'.\n"
                                    f"{bloque_obs}\n"
                                    f"Haz clic aquí para confirmar la aprobación definitiva o ingresar a revisarla."
                                )
                                cursor.execute(
                                    """
                                    INSERT INTO notificaciones (rol_destino, titulo, mensaje, tipo, enlace)
                                    VALUES (%s, %s, %s, %s, %s)
                                    """,
                                    (
                                        r_scr["id"],
                                        tit_scr,
                                        msg_scr,
                                        "info",
                                        f"/solicitudes/revision/{cod_sol}?confirmar=true"
                                    )
                                )
                                notification_broadcaster.notificar_nueva(
                                    {
                                        "titulo": tit_scr,
                                        "mensaje": msg_scr,
                                        "tipo": "info",
                                        "enlace": f"/solicitudes/revision/{cod_sol}?confirmar=true",
                                        "fecha_creacion": now_notif_str,
                                        "leido": False,
                                        "rol_destino": r_scr["id"]
                                    },
                                    target_role_id=r_scr["id"]
                                )
                            else:
                                # Notificación convencional
                                tit_conv = f"Solicitud {cod_sol} lista para visto bueno final"
                                msg_conv = f"La solicitud {cod_sol} completó revisiones de SST y GESCO. Requiere aprobación final de SCR."
                                cursor.execute(
                                    """
                                    INSERT INTO notificaciones (rol_destino, titulo, mensaje, tipo, enlace)
                                    VALUES (%s, %s, %s, %s, %s)
                                    """,
                                    (
                                        r_scr["id"],
                                        tit_conv,
                                        msg_conv,
                                        "warning",
                                        f"/solicitudes/revision/{cod_sol}"
                                    )
                                )
                                notification_broadcaster.notificar_nueva(
                                    {
                                        "titulo": tit_conv,
                                        "mensaje": msg_conv,
                                        "tipo": "warning",
                                        "enlace": f"/solicitudes/revision/{cod_sol}",
                                        "fecha_creacion": now_notif_str,
                                        "leido": False,
                                        "rol_destino": r_scr["id"]
                                    },
                                    target_role_id=r_scr["id"]
                                )

                    # Notificar en caliente a todas las vistas abiertas sobre el cambio de estado de la solicitud
                    notification_broadcaster.notificar_cambio_solicitud(
                        codigo_solicitud=cod_sol,
                        nuevo_estado=nuevo_estado,
                        detalle=f"Dictamen de {rol}: {decision}"
                    )

                    # Si SST o GESCO realiza una edición posterior a haber emitido dictamen previo,
                    # o si modificó la autorización de personas: notificar a SCR y roles superiores
                    if rol in ("SST", "GESCO") and (habia_visto_bueno_previo or dictamen.get("es_edicion") or hubo_cambio_personas_aut):
                        NOTIFICAR_edicion_sst_gesco_db(
                            cursor=cursor,
                            real_id=real_id,
                            codigo_sol=cod_sol,
                            rol=rol,
                            nombre_revisor=nombre_revisor,
                            detalle="Edición de dictamen / autorización de personal"
                        )
                except Exception as e_notif:
                    print(f"⚠️ Aviso al registrar notificación de dictamen: {e_notif}")

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
                    (real_id,),
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


def ACTUALIZAR_autorizacion_personas_db(solicitud_id: Any, payload: dict) -> dict:
    """
    Permite a SST, GESCO, SCR y roles superiores autorizar o denegar personas individualmente
    en una solicitud existente (incluso tras haber emitido dictamen previo).
    Si SST o GESCO realizan una edición, notifica inmediatamente a SCR y roles superiores.
    """
    try:
        rol = str(payload.get("rol", "")).strip().upper()
        id_usuario = payload.get("id_usuario")
        nombre_revisor = payload.get("nombre_revisor") or ""
        personas_input = payload.get("personas") or []

        if not personas_input or not isinstance(personas_input, list):
            return {"exito": False, "mensaje": "No se recibieron personas para actualizar."}

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Verificar existencia y resolver ID numérico real
                id_num = int(solicitud_id) if str(solicitud_id).strip().isdigit() else None
                cod_str = str(solicitud_id).strip().upper()
                if id_num:
                    cursor.execute("SELECT id, codigo, estado, diligenciado_por FROM solicitudes WHERE id = %s OR codigo = %s", (id_num, cod_str))
                else:
                    cursor.execute("SELECT id, codigo, estado, diligenciado_por FROM solicitudes WHERE codigo = %s", (cod_str,))
                sol = cursor.fetchone()
                if not sol:
                    return {"exito": False, "mensaje": f"Solicitud #{solicitud_id} no encontrada."}

                real_id = int(sol["id"])
                cod_sol = sol.get("codigo") or f"RAD-{real_id:04d}"

                if not nombre_revisor and id_usuario:
                    cursor.execute("SELECT nombres, apellidos FROM usuarios WHERE id = %s", (id_usuario,))
                    u = cursor.fetchone()
                    if u:
                        nombre_revisor = f"{u.get('nombres', '')} {u.get('apellidos', '')}".strip()

                # 2. Actualizar ingresantes
                hubo_cambios = False
                nombres_modificados = []

                cursor.execute(
                    """
                    SELECT i.id_persona, COALESCE(i.autorizado, 1) AS autorizado, p.nombre, p.apellido 
                    FROM ingresantes i 
                    LEFT JOIN personas p ON i.id_persona = p.id 
                    WHERE i.id_solicitud = %s
                    """,
                    (real_id,)
                )
                ing_db = {int(r["id_persona"]): r for r in (cursor.fetchall() or []) if r.get("id_persona") is not None}

                for p_item in personas_input:
                    if not isinstance(p_item, dict):
                        continue
                    p_id = p_item.get("id") or p_item.get("id_persona")
                    if not p_id:
                        continue
                    try:
                        p_id = int(p_id)
                    except (ValueError, TypeError):
                        continue

                    p_aut = bool(p_item.get("autorizado", True))
                    p_motivo = p_item.get("motivo") or p_item.get("motivo_rechazo") or None

                    if p_id in ing_db:
                        estado_prev = bool(ing_db[p_id]["autorizado"])
                        if estado_prev != p_aut:
                            hubo_cambios = True
                            nom_completo = f"{ing_db[p_id].get('nombre', '')} {ing_db[p_id].get('apellido', '')}".strip()
                            estado_txt = "Autorizado" if p_aut else "No Autorizado"
                            nombres_modificados.append(f"{nom_completo or f'ID {p_id}'} ({estado_txt})")

                    cursor.execute(
                        """
                        INSERT INTO ingresantes (id_solicitud, id_persona, autorizado, motivo)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            autorizado = VALUES(autorizado),
                            motivo = VALUES(motivo)
                        """,
                        (real_id, p_id, 1 if p_aut else 0, p_motivo)
                    )

                # 3. Si el rol es SST o GESCO, notificar a SCR y roles superiores
                if rol in ("SST", "GESCO"):
                    detalle_txt = f"{len(nombres_modificados)} ingresante(s) actualizados: {', '.join(nombres_modificados[:3])}" if nombres_modificados else "Actualización individual de autorizaciones"
                    NOTIFICAR_edicion_sst_gesco_db(
                        cursor=cursor,
                        real_id=real_id,
                        codigo_sol=cod_sol,
                        rol=rol,
                        nombre_revisor=nombre_revisor,
                        detalle=detalle_txt
                    )

                conexion.commit()

                return {
                    "exito": True,
                    "mensaje": "Autorizaciones de personas actualizadas con éxito.",
                    "solicitud_id": real_id,
                    "codigo": cod_sol,
                    "modificados": len(nombres_modificados)
                }

    except Exception as e:
        print(f"❌ Error en ACTUALIZAR_autorizacion_personas_db #{solicitud_id}: {e}")
        return {"exito": False, "mensaje": f"Error al actualizar personas: {e}"}


def VALIDAR_token_edicion_db(solicitud_id: Any, token: str) -> dict:
    try:
        if not token or not str(token).strip():
            return {"valido": False, "mensaje": "Token de edición no proporcionado."}
        
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                id_num = int(solicitud_id) if str(solicitud_id).strip().isdigit() else None
                cod_str = str(solicitud_id).strip().upper()
                if id_num:
                    cursor.execute("SELECT id, codigo, estado, token_edicion, token_edicion_usado, motivo_devolucion FROM solicitudes WHERE id = %s OR codigo = %s", (id_num, cod_str))
                else:
                    cursor.execute("SELECT id, codigo, estado, token_edicion, token_edicion_usado, motivo_devolucion FROM solicitudes WHERE codigo = %s", (cod_str,))
                sol = cursor.fetchone()
                if not sol:
                    return {"valido": False, "mensaje": f"Solicitud #{solicitud_id} no encontrada."}
                
                estado = str(sol.get("estado") or "").strip().upper()
                if estado != "DEVUELTO PARA CORRECCIÓN":
                    return {"valido": False, "mensaje": f"La solicitud no se encuentra en estado de corrección (estado actual: {estado})."}
                
                if sol.get("token_edicion_usado"):
                    return {"valido": False, "mensaje": "El enlace de edición única ya fue utilizado previamente para esta solicitud."}
                
                stored_token = sol.get("token_edicion")
                if not stored_token or stored_token != str(token).strip():
                    return {"valido": False, "mensaje": "El token de edición no es válido o ha expirado."}
                
                return {
                    "valido": True,
                    "id": sol["id"],
                    "codigo": sol.get("codigo"),
                    "motivo_devolucion": sol.get("motivo_devolucion") or ""
                }
    except Exception as e:
        print(f"❌ Error al validar token de edición: {e}")
        return {"valido": False, "mensaje": f"Error interno al validar token: {e}"}


def CONSUMIR_token_edicion_db(solicitud_id: Any, token: str, id_usuario: Optional[int] = None, nombre_usuario: Optional[str] = None) -> dict:
    try:
        if not token or not str(token).strip():
            return {"exito": False, "mensaje": "Token de edición no proporcionado."}

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                id_num = int(solicitud_id) if str(solicitud_id).strip().isdigit() else None
                cod_str = str(solicitud_id).strip().upper()
                if id_num:
                    cursor.execute("SELECT id, codigo, estado, token_edicion, token_edicion_usado, motivo_devolucion FROM solicitudes WHERE id = %s OR codigo = %s", (id_num, cod_str))
                else:
                    cursor.execute("SELECT id, codigo, estado, token_edicion, token_edicion_usado, motivo_devolucion FROM solicitudes WHERE codigo = %s", (cod_str,))
                sol = cursor.fetchone()
                if not sol:
                    return {"exito": False, "mensaje": f"Solicitud #{solicitud_id} no encontrada."}

                real_id = int(sol["id"])
                cod_sol = sol.get("codigo") or f"RAD-{real_id:04d}"
                stored_token = sol.get("token_edicion")

                if sol.get("token_edicion_usado"):
                    return {"exito": False, "mensaje": "El token de edición ya fue utilizado previamente para esta solicitud."}
                if not stored_token or stored_token != str(token).strip():
                    return {"exito": False, "mensaje": "Token de edición no válido o expirado."}

                # 1. Consumir token y pasar estado a 'POR APROBAR' (retorna directo a SCR)
                cursor.execute(
                    """
                    UPDATE solicitudes 
                    SET token_edicion_usado = TRUE,
                        token_edicion = NULL,
                        estado = 'POR APROBAR'
                    WHERE id = %s
                    """,
                    (real_id,)
                )

                # 2. Limpiar el dictamen previo de SCR para permitir nueva aprobación directa
                cursor.execute(
                    "DELETE FROM solicitud_revisiones WHERE id_solicitud = %s AND UPPER(rol) = 'SCR'",
                    (real_id,)
                )

                # 3. Registrar en auditoría de revisiones
                cursor.execute(
                    """
                    INSERT INTO solicitud_revisiones (
                        id_solicitud, rol, id_usuario, nombre_revisor,
                        decision, observacion, fecha_revision
                    ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        real_id,
                        "GESTION DOCUMENTAL",
                        id_usuario,
                        nombre_usuario or "Gestión Documental",
                        "CORREGIDO",
                        "Solicitud corregida mediante enlace de edición única y retornada directamente a SCR para aprobación final."
                    )
                )

                # 4. Notificar a SCR que la solicitud fue corregida y está lista para su aprobación final
                try:
                    cursor.execute("SELECT id FROM roles WHERE UPPER(nombre_rol) = 'SCR' LIMIT 1")
                    r_scr = cursor.fetchone()
                    if r_scr:
                        cursor.execute("SELECT pre_aprobado FROM solicitudes WHERE id = %s", (real_id,))
                        sol_pre = cursor.fetchone()
                        esta_preaprobada = bool(sol_pre.get("pre_aprobado")) if sol_pre else False

                        if esta_preaprobada:
                            cursor.execute(
                                """
                                SELECT sr.rol, p.nombre AS planta_nombre, sr.observacion
                                FROM solicitud_revisiones sr
                                LEFT JOIN planta p ON sr.id_planta = p.id
                                WHERE sr.id_solicitud = %s AND UPPER(sr.rol) IN ('SST', 'GESCO')
                                ORDER BY sr.fecha_revision ASC
                                """,
                                (real_id,)
                            )
                            revs_tecnicas = cursor.fetchall() or []
                            items_obs = []
                            for rt in revs_tecnicas:
                                r_rol = rt.get("rol", "")
                                r_pl = f" ({rt.get('planta_nombre')})" if rt.get("planta_nombre") else ""
                                r_obs = (rt.get("observacion") or "").strip()
                                if r_obs:
                                    items_obs.append(f"• {r_rol}{r_pl}: {r_obs}")

                            bloque_obs = ("\nObservaciones previas SST / GESCO:\n" + "\n".join(items_obs)) if items_obs else "\nSin observaciones adicionales de SST ni GESCO."

                            tit_corregida = f"⚡ Solicitud Preaprobada {cod_sol} corregida - En 'Por Aprobar'"
                            msg_corregida = f"Gestión Documental corrigió {cod_sol}. Como fue preaprobada, puedes confirmar la aprobación definitiva o revisarla.\n{bloque_obs}"
                            cursor.execute(
                                """
                                INSERT INTO notificaciones (rol_destino, titulo, mensaje, tipo, enlace)
                                VALUES (%s, %s, %s, %s, %s)
                                """,
                                (
                                    r_scr["id"],
                                    tit_corregida,
                                    msg_corregida,
                                    "info",
                                    f"/solicitudes/revision/{cod_sol}?confirmar=true"
                                )
                            )
                            notification_broadcaster.notificar_nueva(
                                {
                                    "titulo": tit_corregida,
                                    "mensaje": msg_corregida,
                                    "tipo": "info",
                                    "enlace": f"/solicitudes/revision/{cod_sol}?confirmar=true",
                                    "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "leido": False,
                                    "rol_destino": r_scr["id"]
                                },
                                target_role_id=r_scr["id"]
                            )
                        else:
                            tit_conv = f"Solicitud {cod_sol} corregida - Pendiente aprobación final SCR"
                            msg_conv = f"Gestión Documental corrigió la solicitud {cod_sol}. Se encuentra directamente en tu bandeja 'Por Aprobar' lista para tu dictamen final."
                            cursor.execute(
                                """
                                INSERT INTO notificaciones (rol_destino, titulo, mensaje, tipo, enlace)
                                VALUES (%s, %s, %s, %s, %s)
                                """,
                                (
                                    r_scr["id"],
                                    tit_conv,
                                    msg_conv,
                                    "warning",
                                    f"/solicitudes/revision/{cod_sol}"
                                )
                            )
                            notification_broadcaster.notificar_nueva(
                                {
                                    "titulo": tit_conv,
                                    "mensaje": msg_conv,
                                    "tipo": "warning",
                                    "enlace": f"/solicitudes/revision/{cod_sol}",
                                    "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "leido": False,
                                    "rol_destino": r_scr["id"]
                                },
                                target_role_id=r_scr["id"]
                            )

                    # Notificar en caliente cambio de solicitud
                    notification_broadcaster.notificar_cambio_solicitud(
                        codigo_solicitud=cod_sol,
                        nuevo_estado="POR APROBAR",
                        detalle="Solicitud corregida y retornada a revisión final de SCR"
                    )
                except Exception as e_notif:
                    print(f"⚠️ Aviso al registrar notificación a SCR tras corrección: {e_notif}")

                conexion.commit()
                return {"exito": True, "mensaje": "Token consumido y solicitud retornada directamente a SCR (POR APROBAR) con éxito."}
    except Exception as e:
        print(f"❌ Error al consumir token de edición: {e}")
        return {"exito": False, "mensaje": f"Error interno al consumir token: {e}"}


def GET_ALL_solicitudes_bd(
    only_active: Optional[bool] = None, 
    id_usuario: Optional[int] = None,
    diligenciado_por: Optional[int] = None
):

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

                # Filtro por usuario que diligenció la solicitud
                if diligenciado_por:
                    condiciones.append(f"so.diligenciado_por = {int(diligenciado_por)}")

                # Si se provee id_usuario, verificar si tiene rol SST (6) o GESCO (7)
                if id_usuario:
                    cursor.execute("SELECT u.id_rol, r.nombre_rol FROM usuarios u LEFT JOIN roles r ON u.id_rol = r.id WHERE u.id = %s", (id_usuario,))
                    u_row = cursor.fetchone()
                    es_sst_gesco = False
                    if u_row:
                        r_id = int(u_row.get("id_rol") or 0)
                        r_nom = str(u_row.get("nombre_rol") or "").strip().upper()
                        es_sst_gesco = (r_id in (6, 7)) or (r_nom in ("SST", "GESCO"))
                    if es_sst_gesco:
                        cursor.execute("SELECT id_planta FROM usuario_plantas WHERE id_usuario = %s", (id_usuario,))
                        p_rows = cursor.fetchall() or []
                        p_ids = [int(pr["id_planta"]) for pr in p_rows if pr.get("id_planta")]
                        if not p_ids:
                            # Usuario SST/GESCO sin plantas asignadas: no ve ninguna solicitud
                            return {"exito": True, "datos": [], "mensaje": "Usuario sin plantas asignadas."}
                        
                        # Filtrar solicitudes que contengan al menos una de las plantas asignadas
                        in_list = ",".join(map(str, p_ids))
                        find_set_exprs = " OR ".join([f"FIND_IN_SET('{pid}', so.plantas_ids)" for pid in p_ids])
                        condiciones.append(f"""
                            (
                                EXISTS (SELECT 1 FROM visita _v WHERE _v.id_solicitud = so.id AND _v.id_planta IN ({in_list}))
                                OR ({find_set_exprs})
                            )
                        """)

                where_clause = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

                query = f"""
                    SELECT
                        so.id,
                        COALESCE({codigo_expr}, CONCAT('RAD-', LPAD(so.id, 4, '0'))) AS codigo,
                        COALESCE({obs_expr}, '') AS observaciones,
                        e.nombre_empresa,
                        ec.nombre AS nombre_emContratista,
                        ec.nit AS nit_emContratista,
                        CONCAT(u.nombres, ' ', u.apellidos) AS diligenciador,
                        so.diligenciado_por,
                        so.fecha_inicio   AS fecha_ingreso,
                        so.fecha_fin      AS fecha_salida,
                        so.nivel_de_riesgo AS riesgo,
                        so.actividad,
                        so.fecha_creacion,
                        so.estado,
                        {is_active_expr} AS is_active,
                        COALESCE(so.pre_aprobado, 0) AS pre_aprobado,

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
                                IFNULL(vi.licencia_doc, 0),
                                IFNULL(vi.autorizado, 1),
                                IFNULL(vi.motivo, '')
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
                                    aut_val = partes[4].strip() if len(partes) > 4 else "1"
                                    mot_val = partes[5].strip() if len(partes) > 5 else ""
                                    is_aut = False if aut_val in ('0', 'false', 'False', 0) else True
                                    v_list.append({
                                        'id': v_id,
                                        'tipo': partes[1] or None,
                                        'placa': partes[2] or None,
                                        'licencia_doc': lic_doc,
                                        'licencia': lic_doc,
                                        'autorizado': is_aut,
                                        'motivo': mot_val,
                                    })
                                val_vehiculos = v_list
                        if isinstance(val_vehiculos, list):
                            row['vehiculos'] = [v for v in val_vehiculos if v is not None]
                            row['vehiculo'] = row['vehiculos']
                    
                    if isinstance(row, dict) and 'computos' in row:
                        val_c = row['computos']
                        if isinstance(val_c, str):
                            if val_c.strip() == "":
                                val_c = []
                            else:
                                c_list = []
                                for item in val_c.split('###'):
                                    if not item:
                                        continue
                                    partes = item.split('|||')
                                    if len(partes) < 4:
                                        continue
                                    c_id = int(partes[0]) if partes[0].isdigit() else None
                                    c_list.append({
                                        'id': c_id,
                                        'marca': partes[1] or "",
                                        'modelo': partes[2] or "",
                                        'serie': partes[3] or ""
                                    })
                                val_c = c_list
                        row['computos'] = val_c if isinstance(val_c, list) else []
                        row['eq_computo'] = row['computos']
                        row['equipos'] = row['computos']
                    elif isinstance(row, dict) and 'eq_computo' in row:
                        val_eq_computo = row['eq_computo']
                        if isinstance(val_eq_computo, str):
                            try:
                                val_eq_computo = json.loads(val_eq_computo)
                            except Exception:
                                val_eq_computo = []
                        row['eq_computo'] = val_eq_computo if isinstance(val_eq_computo, list) else []
                        row['computos'] = row['eq_computo']
                        row['equipos'] = row['eq_computo']
                    row['pre_aprobado'] = bool(row.get('pre_aprobado', False))

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

                # Asociar revisiones y visto bueno por solicitud
                try:
                    cursor.execute("""
                        SELECT sr.id, sr.id_solicitud, sr.id_planta, p.nombre AS nombre_planta,
                               sr.rol, sr.id_usuario, sr.nombre_revisor, sr.decision,
                               sr.motivo_rechazo, sr.observacion, sr.fecha_revision
                        FROM solicitud_revisiones sr
                        LEFT JOIN planta p ON sr.id_planta = p.id
                        ORDER BY sr.fecha_revision ASC
                    """)
                    revs_db = cursor.fetchall() or []
                    revs_por_sol = {}
                    for r in revs_db:
                        sid = r.get("id_solicitud")
                        if sid not in revs_por_sol:
                            revs_por_sol[sid] = []
                        if r.get("fecha_revision"):
                            r["fecha_revision"] = str(r["fecha_revision"])
                        revs_por_sol[sid].append(r)
                    
                    for row in datos:
                        row["revisiones"] = revs_por_sol.get(row["id"], [])
                except Exception as e_rev:
                    print(f"⚠️ Aviso al cargar revisiones en GET_ALL_solicitudes_bd: {e_rev}")
                            
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

def UPDATE_solicitud_bd(solicitud_id: Any, campos: dict) -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # Resolver ID numérico real
                id_num = int(solicitud_id) if str(solicitud_id).strip().isdigit() else None
                cod_str = str(solicitud_id).strip().upper()
                if id_num:
                    cursor.execute("SELECT id, estado, observaciones FROM solicitudes WHERE id = %s OR codigo = %s", (id_num, cod_str))
                else:
                    cursor.execute("SELECT id, estado, observaciones FROM solicitudes WHERE codigo = %s", (cod_str,))
                sol = cursor.fetchone()
                if not sol:
                    return {"exito": False, "mensaje": f"Solicitud #{solicitud_id} no encontrada."}
                real_id = int(sol["id"])
                estado_actual = str(sol.get("estado") or "").strip().upper()
                nuevo_estado = str(campos.get("estado") or "").strip().upper() if "estado" in campos else None

                # Lógica de transición de estados por SuperAdmin:
                if nuevo_estado and nuevo_estado != estado_actual:
                    # 1. Si el superadmin cambia el estado a revisión (o enviado), las aprobaciones hechas se desactivan
                    if nuevo_estado in ("EN REVISIÓN", "EN REVISION", "ENVIADO"):
                        print(f"🔄 [UPDATE] SuperAdmin cambió solicitud #{real_id} a '{nuevo_estado}'. Desactivando todas las aprobaciones emitidas...")
                        cursor.execute("DELETE FROM solicitud_revisiones WHERE id_solicitud = %s", (real_id,))
                        # Limpiar observaciones si eran de rechazo y no enviaron una nueva
                        if "observaciones" not in campos:
                            obs_actual = str(sol.get("observaciones") or "")
                            if "[RECHAZADO" in obs_actual:
                                campos["observaciones"] = ""

                    # 2. Si pasa de APROBADO o RECHAZADO a 'POR APROBAR' (o cambia a 'POR APROBAR'):
                    #    mantiene las aprobaciones de SST y GESCO, pero revierte la de SCR
                    elif nuevo_estado == "POR APROBAR":
                        print(f"🔄 [UPDATE] SuperAdmin cambió solicitud #{real_id} de '{estado_actual}' a 'POR APROBAR'. Manteniendo SST y GESCO y revirtiendo dictamen de SCR...")
                        cursor.execute(
                            "DELETE FROM solicitud_revisiones WHERE id_solicitud = %s AND UPPER(rol) = 'SCR'",
                            (real_id,)
                        )
                        # Asegurar que SST y GESCO mantengan su aprobación si habían sido observadas
                        cursor.execute(
                            "UPDATE solicitud_revisiones SET decision = 'APROBADO', motivo_rechazo = NULL WHERE id_solicitud = %s AND UPPER(rol) IN ('SST', 'GESCO') AND decision = 'RECHAZADO'",
                            (real_id,)
                        )
                        # Limpiar observación de rechazo si venía de RECHAZADO
                        if "observaciones" not in campos and estado_actual == "RECHAZADO":
                            obs_actual = str(sol.get("observaciones") or "")
                            if "[RECHAZADO por SCR]" in obs_actual or "[RECHAZADO" in obs_actual:
                                campos["observaciones"] = ""

                # Extraer y limpiar subtablas / relaciones
                personas = campos.pop("personas", None)
                if personas is None:
                    personas = campos.pop("ingresantes", None)
                raw_personas_ids = campos.pop("personas_ids", None)

                plantas = campos.pop("plantas", None)
                raw_plantas_ids = campos.pop("plantas_ids", None)

                vehiculo = campos.pop("vehiculo", None)
                if vehiculo is None:
                    vehiculo = campos.pop("vehiculos", None)
                raw_vehiculos_ids = campos.pop("vehiculos_ids", None)

                eq_computo = campos.pop("eq_computo", None)
                if eq_computo is None:
                    eq_computo = campos.pop("equipos", None)
                if eq_computo is None:
                    eq_computo = campos.pop("computos", None)

                # 1. Sincronizar personas / ingresantes
                resolved_personas_ids = []
                if personas is not None or raw_personas_ids is not None:
                    lista_p = personas
                    if lista_p is None and raw_personas_ids is not None:
                        if isinstance(raw_personas_ids, list):
                            lista_p = [{"id": pid, "autorizado": True, "motivo": None} for pid in raw_personas_ids]
                        elif isinstance(raw_personas_ids, str):
                            lista_p = [{"id": int(x.strip()), "autorizado": True, "motivo": None} for x in raw_personas_ids.split(",") if x.strip().isdigit()]

                    if isinstance(lista_p, list):
                        # Actualizar tabla ingresantes sin importar el estado
                        cursor.execute("DELETE FROM ingresantes WHERE id_solicitud = %s", (real_id,))
                        valores_ing = []
                        for item_p in lista_p:
                            if isinstance(item_p, dict):
                                p_id = item_p.get("id") or item_p.get("id_persona")
                                aut = item_p.get("autorizado", True)
                                aut_val = False if aut in (False, 0, "0", "false") else True
                                mot = item_p.get("motivo") or item_p.get("motivo_rechazo") or None
                                if p_id and str(p_id).isdigit():
                                    valores_ing.append((real_id, int(p_id), aut_val, mot))
                                    resolved_personas_ids.append(int(p_id))
                            elif isinstance(item_p, (int, str)) and str(item_p).isdigit():
                                valores_ing.append((real_id, int(item_p), True, None))
                                resolved_personas_ids.append(int(item_p))

                        if valores_ing:
                            cursor.executemany(
                                "INSERT INTO ingresantes (id_solicitud, id_persona, autorizado, motivo) VALUES (%s, %s, %s, %s)",
                                valores_ing,
                            )

                        if resolved_personas_ids:
                            campos["personas_ids"] = ",".join(map(str, resolved_personas_ids))
                        elif isinstance(raw_personas_ids, list):
                            campos["personas_ids"] = ",".join(map(str, raw_personas_ids))
                        elif isinstance(raw_personas_ids, str):
                            campos["personas_ids"] = raw_personas_ids

                # 2. Sincronizar plantas / visita
                if raw_plantas_ids is not None or plantas is not None:
                    pids = []
                    if raw_plantas_ids is not None:
                        if isinstance(raw_plantas_ids, list):
                            pids = [int(x) for x in raw_plantas_ids if str(x).isdigit()]
                        elif isinstance(raw_plantas_ids, str):
                            pids = [int(x.strip()) for x in raw_plantas_ids.split(",") if x.strip().isdigit()]
                    elif isinstance(plantas, list):
                        for pl in plantas:
                            if isinstance(pl, dict) and pl.get("id"):
                                pids.append(int(pl["id"]))
                            elif isinstance(pl, (int, str)) and str(pl).isdigit():
                                pids.append(int(pl))

                    if pids:
                        cursor.execute("DELETE FROM visita WHERE id_solicitud = %s", (real_id,))
                        cursor.executemany(
                            "INSERT INTO visita (id_solicitud, id_planta) VALUES (%s, %s)",
                            [(real_id, p_id) for p_id in pids],
                        )
                        campos["plantas_ids"] = ",".join(map(str, pids))

                # 3. Sincronizar vehículos / Veh_ingreso
                if vehiculo is not None or raw_vehiculos_ids is not None:
                    # Preservar autorización y motivo previos si ya existían para estos vehículos
                    cursor.execute("SELECT id_vehiculo, COALESCE(autorizado, 1) AS autorizado, motivo FROM Veh_ingreso WHERE id_solicitud = %s", (real_id,))
                    prev_veh_info = {r["id_vehiculo"]: r for r in (cursor.fetchall() or [])}

                    cursor.execute("DELETE FROM Veh_ingreso WHERE id_solicitud = %s", (real_id,))
                    resolved_vids = []
                    if vehiculo and isinstance(vehiculo, list):
                        for v in vehiculo:
                            id_v = None
                            lic_doc = 0
                            aut_v = True
                            mot_v = None

                            if isinstance(v, (int, str)) and str(v).isdigit():
                                id_v = int(v)
                            elif isinstance(v, dict):
                                lic_doc = v.get("licencia_doc") or 0
                                aut = v.get("autorizado")
                                if aut is not None:
                                    aut_v = False if aut in (False, 0, "0", "false") else True
                                id_persona_conductor = None

                                cand_p = v.get("id_persona") or v.get("conductor_id")
                                if cand_p and str(cand_p).isdigit() and int(cand_p) > 0:
                                    id_persona_conductor = int(cand_p)
                                elif v.get("conductor"):
                                    cond_str = str(v.get("conductor")).strip()
                                    if cond_str.isdigit() and int(cond_str) > 0:
                                        id_persona_conductor = int(cond_str)
                                    else:
                                        cursor.execute(
                                            "SELECT id FROM personas WHERE CONCAT(nombre, ' ', apellido) = %s OR nombre = %s LIMIT 1",
                                            (cond_str, cond_str),
                                        )
                                        p_found = cursor.fetchone()
                                        if p_found:
                                            id_persona_conductor = p_found["id"]

                                if v.get("id_vehiculo") and str(v.get("id_vehiculo")).isdigit():
                                    id_v = int(v["id_vehiculo"])
                                elif v.get("id") and str(v.get("id")).isdigit():
                                    id_v = int(v["id"])
                                elif v.get("placa"):
                                    placa_norm = re.sub(r"[^A-Z0-9]", "", str(v.get("placa")).strip().upper())
                                    tipo_norm = str(v.get("tipo", "Camioneta")).strip()
                                    cursor.execute("SELECT id FROM vehiculos WHERE placa = %s", (placa_norm,))
                                    vehi_existente = cursor.fetchone()
                                    if vehi_existente:
                                        id_v = vehi_existente["id"]
                                    else:
                                        cursor.execute(
                                            "INSERT INTO vehiculos (tipo, placa) VALUES (%s, %s)",
                                            (tipo_norm, placa_norm),
                                        )
                                        id_v = cursor.lastrowid

                                if id_v and aut is None and id_v in prev_veh_info:
                                    aut_v = bool(prev_veh_info[id_v].get("autorizado", 1))

                                mot_v = v.get("motivo") or v.get("motivo_rechazo") or (prev_veh_info.get(id_v, {}).get("motivo") if id_v in prev_veh_info else None)

                            if id_v:
                                resolved_vids.append(id_v)
                                cursor.execute(
                                    "INSERT INTO Veh_ingreso (id_solicitud, id_vehiculo, licencia_doc, autorizado, motivo, id_persona) VALUES (%s, %s, %s, %s, %s, %s)",
                                    (real_id, id_v, lic_doc, aut_v, mot_v, id_persona_conductor)
                                )

                    if resolved_vids:
                        campos["vehiculos_ids"] = ",".join(map(str, resolved_vids))
                    elif raw_vehiculos_ids:
                        if isinstance(raw_vehiculos_ids, list):
                            campos["vehiculos_ids"] = ",".join(map(str, raw_vehiculos_ids))
                        elif isinstance(raw_vehiculos_ids, str):
                            campos["vehiculos_ids"] = raw_vehiculos_ids

                # 4. Sincronizar equipos de cómputo
                if eq_computo is not None:
                    cursor.execute("DELETE FROM equipos_solicitud WHERE solicitud_id = %s", (real_id,))
                    if isinstance(eq_computo, list) and eq_computo:
                        valores_eq = []
                        for eq in eq_computo:
                            if isinstance(eq, dict):
                                m = str(eq.get("marca") or "").strip().upper()
                                mod = str(eq.get("modelo") or "").strip().upper()
                                s = str(eq.get("serie") or "").strip().upper()
                                if m or mod or s:
                                    valores_eq.append((real_id, m, mod, s))
                        if valores_eq:
                            cursor.executemany(
                                "INSERT INTO equipos_solicitud (solicitud_id, marca, modelo, serie) VALUES (%s, %s, %s, %s)",
                                valores_eq
                            )

                # 5. Normalizar FKs de empresa y contratista para solicitudes
                if "empresa_origen" in campos:
                    raw_eo = campos["empresa_origen"]
                    if str(raw_eo).isdigit():
                        campos["empresa_origen"] = int(raw_eo)
                    elif raw_eo:
                        cursor.execute("SELECT id FROM empresa WHERE nombre_empresa = %s LIMIT 1", (str(raw_eo),))
                        row_e = cursor.fetchone()
                        if row_e:
                            campos["empresa_origen"] = int(row_e["id"])

                if "empresa_contratista" in campos:
                    raw_ec = campos["empresa_contratista"]
                    if str(raw_ec).isdigit():
                        campos["empresa_contratista"] = int(raw_ec)
                    elif raw_ec:
                        cursor.execute("SELECT id FROM emp_contratista WHERE nombre = %s LIMIT 1", (str(raw_ec),))
                        row_c = cursor.fetchone()
                        if row_c:
                            campos["empresa_contratista"] = int(row_c["id"])

                # 5. Proteger el solicitante original: nunca alterar diligenciado_por en una actualización
                campos.pop("diligenciado_por", None)

                # 6. Filtrar solo columnas válidas escalares para la tabla solicitudes
                valid_cols = {
                    "codigo", "empresa_origen", "nivel_de_riesgo",
                    "tipo_personal", "empresa_contratista", "plantas_ids", "personas_ids",
                    "vehiculos_ids", "fecha_inicio", "fecha_fin", "actividad",
                    "observaciones", "estado", "is_active",
                    "token_edicion", "token_edicion_usado", "motivo_devolucion"
                }

                campos_filtrados = {}
                for k, v in campos.items():
                    if k in valid_cols:
                        if isinstance(v, list):
                            campos_filtrados[k] = ",".join(map(str, v))
                        else:
                            campos_filtrados[k] = v

                if campos_filtrados:
                    columnas = [f"{col} = %s" for col in campos_filtrados.keys()]
                    sql_update = f"UPDATE solicitudes SET {', '.join(columnas)} WHERE id = %s"
                    valores = list(campos_filtrados.values()) + [real_id]
                    cursor.execute(sql_update, valores)

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
    
def DELETE_solicitud_bd(solicitud_id: Any) -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                id_num = int(solicitud_id) if str(solicitud_id).strip().isdigit() else None
                cod_str = str(solicitud_id).strip().upper()
                if id_num:
                    cursor.execute("SELECT id FROM solicitudes WHERE id = %s OR codigo = %s", (id_num, cod_str))
                else:
                    cursor.execute("SELECT id FROM solicitudes WHERE codigo = %s", (cod_str,))
                sol = cursor.fetchone()
                if not sol:
                    return {"exito": False, "mensaje": f"Solicitud #{solicitud_id} no encontrada."}
                real_id = int(sol["id"])

                cursor.execute("DELETE FROM solicitudes WHERE id = %s", (real_id,))

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


def GET_resumen_verificacion_porteria_db(identificador: str) -> dict:
    """
    Obtiene el resumen público y rápido optimizado para porterías y vigilantes.
    Permite buscar por código ('RAD-XXXXXX') o por id numérico.
    Retorna estrictamente:
      - Empresa relacionada (Origen y Contratista con NIT)
      - Fechas de vigencia (con estado de vigencia hoy)
      - Estado de la solicitud y veredicto de ingreso
      - Integrantes: únicamente nombres y apellidos, identificación y si está autorizado
    """
    try:
        if not identificador:
            return {"exito": False, "mensaje": "Se requiere un código o ID de solicitud."}

        term = str(identificador).strip().upper()
        id_num = int(term) if term.isdigit() else None

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Consultar solicitud principal con datos de empresas
                if id_num:
                    sql_sol = """
                        SELECT s.id, s.codigo, s.estado, s.is_active, s.fecha_inicio, s.fecha_fin,
                               s.personas_ids, s.pre_aprobado,
                               em.nombre_empresa AS empresa_origen_nombre,
                               ec.nombre AS empresa_contratista_nombre,
                               ec.nit AS empresa_contratista_nit
                        FROM solicitudes s
                        LEFT JOIN empresa em ON em.id = s.empresa_origen
                        LEFT JOIN emp_contratista ec ON ec.id = s.empresa_contratista
                        WHERE s.id = %s OR s.codigo = %s
                        LIMIT 1
                    """
                    cursor.execute(sql_sol, (id_num, term))
                else:
                    sql_sol = """
                        SELECT s.id, s.codigo, s.estado, s.is_active, s.fecha_inicio, s.fecha_fin,
                               s.personas_ids, s.pre_aprobado,
                               em.nombre_empresa AS empresa_origen_nombre,
                               ec.nombre AS empresa_contratista_nombre,
                               ec.nit AS empresa_contratista_nit
                        FROM solicitudes s
                        LEFT JOIN empresa em ON em.id = s.empresa_origen
                        LEFT JOIN emp_contratista ec ON ec.id = s.empresa_contratista
                        WHERE s.codigo = %s
                        LIMIT 1
                    """
                    cursor.execute(sql_sol, (term,))

                sol = cursor.fetchone()
                if not sol:
                    return {
                        "exito": False,
                        "mensaje": f"No se encontró ninguna solicitud con el código o ID '{term}'.",
                    }

                sol_id = sol["id"]
                codigo_radicado = sol.get("codigo") or f"RAD-{sol_id:04d}"

                # 2. Consultar plantas autorizadas
                cursor.execute("""
                    SELECT pl.nombre AS nombre_planta
                    FROM visita v
                    INNER JOIN planta pl ON v.id_planta = pl.id
                    WHERE v.id_solicitud = %s
                    ORDER BY pl.nombre ASC
                """, (sol_id,))
                plantas = [r["nombre_planta"] for r in (cursor.fetchall() or []) if r.get("nombre_planta")]

                # 3.1 Consultar vehículos asociados (vía Veh_ingreso)
                cursor.execute("""
                    SELECT v.id, v.tipo, v.placa, vi.licencia_doc,
                           COALESCE(vi.autorizado, 1) AS autorizado, vi.motivo,
                           vi.id_persona,
                           TRIM(CONCAT(COALESCE(p.nombre, ''), ' ', COALESCE(p.apellido, ''))) AS conductor_nombre
                    FROM Veh_ingreso vi
                    INNER JOIN vehiculos v ON vi.id_vehiculo = v.id
                    LEFT JOIN personas p ON vi.id_persona = p.id
                    WHERE vi.id_solicitud = %s
                """, (sol_id,))
                filas_veh = cursor.fetchall() or []

                vehiculos = []
                conductores_dict = {}  # id_persona -> placa
                total_veh_autorizados = 0

                for v in filas_veh:
                    v_aut = bool(v.get("autorizado", True))
                    if v_aut:
                        total_veh_autorizados += 1
                    p_id_cond = v.get("id_persona")
                    placa_fmt = FORMATEAR_PLACA(v.get("placa") or "") or v.get("placa") or "—"
                    if p_id_cond:
                        conductores_dict[int(p_id_cond)] = placa_fmt

                    vehiculos.append({
                        "id": v.get("id"),
                        "tipo": str(v.get("tipo") or "Vehículo").strip(),
                        "placa": placa_fmt,
                        "conductor": str(v.get("conductor_nombre") or "").strip(),
                        "id_persona_conductor": p_id_cond,
                        "autorizado": v_aut,
                        "motivo": (v.get("motivo") or "").strip() if not v_aut else "",
                    })

                # 3.2 Consultar dispositivos / equipos de cómputo (vía equipos_solicitud)
                cursor.execute("""
                    SELECT id, marca, modelo, serie 
                    FROM equipos_solicitud 
                    WHERE solicitud_id = %s
                """, (sol_id,))
                filas_eq = cursor.fetchall() or []
                dispositivos = []
                for e in filas_eq:
                    dispositivos.append({
                        "id": e.get("id"),
                        "marca": str(e.get("marca") or "").strip(),
                        "modelo": str(e.get("modelo") or "").strip(),
                        "serie": str(e.get("serie") or "").strip(),
                    })

                # 3.3 Consultar integrantes (personas) con cargo y verificación de si es conductor
                cursor.execute("""
                    SELECT p.id, p.nombre, p.apellido, p.tipo_doc, p.identificacion, p.cargo,
                           COALESCE(i.autorizado, 1) AS autorizado, i.motivo
                    FROM ingresantes i
                    INNER JOIN personas p ON i.id_persona = p.id
                    WHERE i.id_solicitud = %s
                    ORDER BY p.apellido ASC, p.nombre ASC
                """, (sol_id,))
                filas_personas = cursor.fetchall() or []

                # Fallback con personas_ids si la tabla ingresantes está vacía para esta solicitud
                if not filas_personas and sol.get("personas_ids"):
                    try:
                        raw_pids = str(sol["personas_ids"]).replace("[", "").replace("]", "").split(",")
                        p_ids = [int(x.strip()) for x in raw_pids if x.strip().isdigit()]
                        if p_ids:
                            fmt = ",".join(["%s"] * len(p_ids))
                            cursor.execute(f"""
                                SELECT p.id, p.nombre, p.apellido, p.tipo_doc, p.identificacion, p.cargo,
                                       1 AS autorizado, NULL AS motivo
                                FROM personas p
                                WHERE p.id IN ({fmt})
                                ORDER BY p.apellido ASC, p.nombre ASC
                            """, tuple(p_ids))
                            filas_personas = cursor.fetchall() or []
                    except Exception as e_f:
                        print(f"⚠️ Fallback personas_ids portería: {e_f}")

                integrantes = []
                total_autorizados = 0
                for p in filas_personas:
                    es_aut = bool(p.get("autorizado", True))
                    if es_aut:
                        total_autorizados += 1
                    p_id = p.get("id")
                    nombres = str(p.get("nombre") or "").strip()
                    apellidos = str(p.get("apellido") or "").strip()
                    nombre_completo = f"{nombres} {apellidos}".strip() or "Sin nombre"
                    cargo_str = str(p.get("cargo") or "").strip()

                    # Determinar si la persona fue seleccionada explícitamente como conductor del vehículo
                    es_cond = bool(p_id and int(p_id) in conductores_dict)
                    veh_asig = conductores_dict.get(int(p_id)) if (p_id and int(p_id) in conductores_dict) else ""

                    integrantes.append({
                        "id": p_id,
                        "nombres": nombres,
                        "apellidos": apellidos,
                        "nombre_completo": nombre_completo,
                        "tipo_doc": str(p.get("tipo_doc") or "CC").strip(),
                        "identificacion": str(p.get("identificacion") or "—").strip(),
                        "cargo": cargo_str,
                        "es_conductor": es_cond,
                        "vehiculo_asignado": veh_asig,
                        "autorizado": es_aut,
                        "motivo": (p.get("motivo") or "").strip() if not es_aut else "",
                    })

                # 4. Cálculo de vigencia temporal
                hoy = datetime.now().date()
                fecha_ini = sol.get("fecha_inicio")
                fecha_fn = sol.get("fecha_fin")

                # Asegurar formato date
                if isinstance(fecha_ini, datetime):
                    fecha_ini = fecha_ini.date()
                elif isinstance(fecha_ini, str):
                    try:
                        fecha_ini = datetime.strptime(fecha_ini.split("T")[0], "%Y-%m-%d").date()
                    except Exception:
                        pass

                if isinstance(fecha_fn, datetime):
                    fecha_fn = fecha_fn.date()
                elif isinstance(fecha_fn, str):
                    try:
                        fecha_fn = datetime.strptime(fecha_fn.split("T")[0], "%Y-%m-%d").date()
                    except Exception:
                        pass

                vigente_hoy = False
                estado_vigencia = "DESCONOCIDA"
                dias_restantes = 0
                mensaje_vigencia = ""

                meses_abr = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
                f_ini_fmt = f"{fecha_ini.day} {meses_abr[fecha_ini.month - 1]} {fecha_ini.year}" if fecha_ini else ""
                f_fin_fmt = f"{fecha_fn.day} {meses_abr[fecha_fn.month - 1]} {fecha_fn.year}" if fecha_fn else ""

                if fecha_ini and fecha_fn:
                    if hoy < fecha_ini:
                        estado_vigencia = "POR_INICIAR"
                        dias_para_iniciar = (fecha_ini - hoy).days
                        mensaje_vigencia = f"Inicia en {dias_para_iniciar} día(s) (desde el {f_ini_fmt})"
                    elif hoy > fecha_fn:
                        estado_vigencia = "VENCIDA"
                        dias_vencida = (hoy - fecha_fn).days
                        mensaje_vigencia = f"Expiró hace {dias_vencida} día(s) (el {f_fin_fmt})"
                    else:
                        vigente_hoy = True
                        estado_vigencia = "VIGENTE"
                        dias_restantes = (fecha_fn - hoy).days
                        mensaje_vigencia = f"Vigente (quedan {dias_restantes} día(s) hasta el {f_fin_fmt})"

                # 5. Determinación del veredicto final para portería
                estado_raw = str(sol.get("estado") or "ENVIADO").strip().upper()
                is_active = bool(sol.get("is_active", 1))

                if not is_active:
                    resultado_ingreso = "NO_AUTORIZADO"
                    color_semaforo = "rojo"
                    mensaje_semaforo = "SOLICITUD INACTIVA - INGRESO DENEGADO"
                elif "RECHAZ" in estado_raw:
                    resultado_ingreso = "NO_AUTORIZADO"
                    color_semaforo = "rojo"
                    mensaje_semaforo = "SOLICITUD RECHAZADA - INGRESO DENEGADO"
                elif "POR APROBAR" in estado_raw or "REVISI" in estado_raw or "ENVIADO" in estado_raw or "DEVUELTO" in estado_raw:
                    resultado_ingreso = "EN_TRAMITE"
                    color_semaforo = "amarillo"
                    mensaje_semaforo = f"SOLICITUD EN TRÁMITE - INGRESO NO AUTORIZADO"
                elif estado_raw in ("APROBADO", "APROBADA", "PRE-APROBADO", "PRE-APROBADA") or (estado_raw.startswith("APROB") and "POR" not in estado_raw):
                    if vigente_hoy:
                        resultado_ingreso = "AUTORIZADO"
                        color_semaforo = "verde"
                        mensaje_semaforo = "INGRESO AUTORIZADO"
                    elif estado_vigencia == "POR_INICIAR":
                        resultado_ingreso = "POR_INICIAR"
                        color_semaforo = "amarillo"
                        mensaje_semaforo = "APROBADA PERO VIGENCIA AÚN NO INICIA"
                    else:
                        resultado_ingreso = "VENCIDO"
                        color_semaforo = "rojo"
                        mensaje_semaforo = "SOLICITUD APROBADA PERO VIGENCIA VENCIDA"
                else:
                    resultado_ingreso = "EN_TRAMITE"
                    color_semaforo = "amarillo"
                    mensaje_semaforo = "SOLICITUD EN TRÁMITE - INGRESO NO AUTORIZADO"

                return {
                    "exito": True,
                    "datos": {
                        "id": sol_id,
                        "codigo": codigo_radicado,
                        "estado": estado_raw,
                        "is_active": is_active,
                        "empresa_contratista": sol.get("empresa_contratista_nombre") or "No especificada",
                        "empresa_contratista_nit": sol.get("empresa_contratista_nit") or "",
                        "empresa_origen": sol.get("empresa_origen_nombre") or "INCARSA",
                        "fecha_inicio": str(fecha_ini) if fecha_ini else "",
                        "fecha_fin": str(fecha_fn) if fecha_fn else "",
                        "vigente_hoy": vigente_hoy,
                        "estado_vigencia": estado_vigencia,
                        "dias_restantes": dias_restantes,
                        "mensaje_vigencia": mensaje_vigencia,
                        "resultado_ingreso": resultado_ingreso,
                        "color_semaforo": color_semaforo,
                        "mensaje_semaforo": mensaje_semaforo,
                        "plantas": plantas,
                        "total_integrantes": len(integrantes),
                        "total_autorizados": total_autorizados,
                        "integrantes": integrantes,
                        "total_vehiculos": len(vehiculos),
                        "total_veh_autorizados": total_veh_autorizados,
                        "vehiculos": vehiculos,
                        "total_dispositivos": len(dispositivos),
                        "dispositivos": dispositivos,
                        "fecha_verificacion": datetime.now().strftime("%d/%m/%Y %I:%M:%S %p"),
                    }
                }

    except Exception as e:
        print(f"❌ Error en GET_resumen_verificacion_porteria_db: {e}")
        return {
            "exito": False,
            "mensaje": f"Error al consultar datos de portería: {str(e)}",
        }