from database import GET_conexion
from typing import Optional, Dict, Any, List
from datetime import datetime
from src.transformers.seguridad_social_transformer import FORMATEAR_FECHA_STR


def OBTENER_HISTORIAL_COMPLETO_PERSONA_SS(cursor, id_persona: int, id_seguridad_social: Optional[int]) -> list:
    """
    Obtiene todas las solicitudes en las que la persona ha participado:
    1. A través de la tabla 'ingresantes' (relación directa con solicitudes).
    2. A través de 'solicitudes.personas_ids' (CSV de personas asociadas).
    3. A través de 'seguridad_social_historial_solicitudes'.
    Consolida y elimina duplicados ordenando de la más reciente a la más antigua.
    """
    solicitudes_map = {}

    # 1. Consulta desde tabla ingresantes
    sql_ing = """
        SELECT 
            s.id AS id_solicitud,
            COALESCE(s.codigo, CONCAT('RAD-', LPAD(s.id, 4, '0'))) AS codigo_radicado,
            s.fecha_inicio,
            s.fecha_fin,
            s.estado AS estado_solicitud,
            ec.nombre AS nombre_contratista,
            s.empresa_origen AS id_empresa,
            emp.nombre_empresa,
            s.diligenciado_por AS id_usuario_registro,
            TRIM(CONCAT(COALESCE(u.nombres, ''), ' ', COALESCE(u.apellidos, ''))) AS usuario_registro,
            TRIM(CONCAT(COALESCE(u.nombres, ''), ' ', COALESCE(u.apellidos, ''))) AS diligenciador,
            COALESCE(s.fecha_creacion, s.fecha_inicio) AS fecha_solicitud,
            '' AS observacion
        FROM ingresantes ing
        INNER JOIN solicitudes s ON ing.id_solicitud = s.id
        LEFT JOIN empresa emp ON s.empresa_origen = emp.id
        LEFT JOIN emp_contratista ec ON s.empresa_contratista = ec.id
        LEFT JOIN usuarios u ON s.diligenciado_por = u.id
        WHERE ing.id_persona = %s
    """
    try:
        cursor.execute(sql_ing, (id_persona,))
        for row in cursor.fetchall():
            key = f"sol_{row['id_solicitud']}"
            solicitudes_map[key] = dict(row)
    except Exception as e:
        print(f"⚠️ Aviso al consultar ingresantes para persona {id_persona} (SS): {e}")

    # 2. Consulta desde solicitudes (personas_ids mediante FIND_IN_SET y LIKE)
    sql_csv = """
        SELECT 
            s.id AS id_solicitud,
            COALESCE(s.codigo, CONCAT('RAD-', LPAD(s.id, 4, '0'))) AS codigo_radicado,
            s.fecha_inicio,
            s.fecha_fin,
            s.estado AS estado_solicitud,
            ec.nombre AS nombre_contratista,
            s.empresa_origen AS id_empresa,
            emp.nombre_empresa,
            s.diligenciado_por AS id_usuario_registro,
            TRIM(CONCAT(COALESCE(u.nombres, ''), ' ', COALESCE(u.apellidos, ''))) AS usuario_registro,
            TRIM(CONCAT(COALESCE(u.nombres, ''), ' ', COALESCE(u.apellidos, ''))) AS diligenciador,
            COALESCE(s.fecha_creacion, s.fecha_inicio) AS fecha_solicitud,
            '' AS observacion
        FROM solicitudes s
        LEFT JOIN empresa emp ON s.empresa_origen = emp.id
        LEFT JOIN emp_contratista ec ON s.empresa_contratista = ec.id
        LEFT JOIN usuarios u ON s.diligenciado_por = u.id
        WHERE (FIND_IN_SET(%s, REPLACE(REPLACE(REPLACE(s.personas_ids, '[', ''), ']', ''), ' ', '')) > 0)
           OR (s.personas_ids LIKE %s)
    """
    try:
        pattern_like = f"%{id_persona}%"
        cursor.execute(sql_csv, (str(id_persona), pattern_like))
        for row in cursor.fetchall():
            key = f"sol_{row['id_solicitud']}"
            if key not in solicitudes_map:
                solicitudes_map[key] = dict(row)
    except Exception as e:
        print(f"⚠️ Aviso al consultar personas_ids para persona {id_persona} (SS): {e}")

    # 3. Consulta desde seguridad_social_historial_solicitudes
    if id_seguridad_social:
        sql_ant = """
            SELECT 
                h.id,
                h.id_solicitud,
                COALESCE(s.codigo, CONCAT('RAD-', LPAD(COALESCE(s.id, h.id_solicitud, 0), 4, '0'))) AS codigo_radicado,
                s.fecha_inicio,
                s.fecha_fin,
                COALESCE(s.estado, 'REGISTRADO') AS estado_solicitud,
                ec.nombre AS nombre_contratista,
                h.id_empresa,
                emp.nombre_empresa,
                s.diligenciado_por AS id_usuario_registro,
                TRIM(CONCAT(COALESCE(u.nombres, ''), ' ', COALESCE(u.apellidos, ''))) AS usuario_registro,
                TRIM(CONCAT(COALESCE(u.nombres, ''), ' ', COALESCE(u.apellidos, ''))) AS diligenciador,
                h.fecha_solicitud,
                h.observacion
            FROM seguridad_social_historial_solicitudes h
            LEFT JOIN empresa emp ON h.id_empresa = emp.id
            LEFT JOIN solicitudes s ON h.id_solicitud = s.id
            LEFT JOIN emp_contratista ec ON s.empresa_contratista = ec.id
            LEFT JOIN usuarios u ON s.diligenciado_por = u.id
            WHERE h.id_seguridad_social = %s
        """
        try:
            cursor.execute(sql_ant, (id_seguridad_social,))
            for row in cursor.fetchall():
                if row.get("id_solicitud"):
                    key = f"sol_{row['id_solicitud']}"
                    if key not in solicitudes_map:
                        solicitudes_map[key] = dict(row)
                else:
                    key = f"hist_{row.get('id', id(row))}"
                    solicitudes_map[key] = dict(row)
        except Exception as e:
            print(f"⚠️ Aviso al consultar seguridad_social_historial_solicitudes: {e}")

    # Ordenar solicitudes por fecha descendente
    lista_historial = list(solicitudes_map.values())
    lista_historial.sort(key=lambda x: str(x.get("fecha_solicitud") or x.get("fecha_inicio") or ""), reverse=True)

    # Formatear fechas a strings
    for item in lista_historial:
        if item.get("fecha_solicitud"):
            item["fecha_solicitud"] = str(item["fecha_solicitud"])
        if item.get("fecha_inicio"):
            item["fecha_inicio"] = str(item["fecha_inicio"])
        if item.get("fecha_fin"):
            item["fecha_fin"] = str(item["fecha_fin"])
        if not item.get("codigo_radicado") and item.get("id_solicitud"):
            item["codigo_radicado"] = f"RAD-{str(item['id_solicitud']).zfill(4)}"

    return lista_historial


def GET_OR_CREATE_seguridad_social_persona_db(id_persona: int) -> Dict[str, Any]:
    """
    Obtiene el registro de seguridad social de una persona.
    Si no existe, crea el registro inicial en blanco (sin forzar vigencia de 1 año).
    La vigencia la dictamina SST directamente.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Verificar si existe la persona
                cursor.execute("SELECT id, nombre, apellido, identificacion, tipo_doc, cargo FROM personas WHERE id = %s", (id_persona,))
                persona = cursor.fetchone()
                if not persona:
                    return {"exito": False, "mensaje": f"Persona con ID #{id_persona} no encontrada."}

                # 2. Consultar si ya tiene registro de seguridad social
                cursor.execute("SELECT * FROM seguridad_social WHERE id_persona = %s", (id_persona,))
                ss = cursor.fetchone()

                if not ss:
                    cursor.execute("""
                        INSERT INTO seguridad_social (id_persona, responsable, anotaciones, id_empresa, ultima_revision, fecha_vigencia, fecha_creacion)
                        VALUES (%s, NULL, NULL, NULL, NULL, NULL, NOW())
                    """, (id_persona,))
                    conexion.commit()
                    ss_id = cursor.lastrowid
                    cursor.execute("SELECT * FROM seguridad_social WHERE id = %s", (ss_id,))
                    ss = cursor.fetchone()
                else:
                    ss_id = ss["id"]

                # 3. Obtener el historial completo consolidado de solicitudes
                historial = OBTENER_HISTORIAL_COMPLETO_PERSONA_SS(cursor, id_persona, ss_id)

                # 4. Determinar la última empresa, contratista y usuario responsable desde el historial
                nombre_contratista = None
                ultimo_responsable = None
                if historial:
                    ultima_solicitud = historial[0]
                    nombre_contratista = ultima_solicitud.get("nombre_contratista")
                    ultima_empresa_id = ultima_solicitud.get("id_empresa")
                    raw_user = (ultima_solicitud.get("usuario_registro") or ultima_solicitud.get("diligenciador") or "").strip()
                    if raw_user:
                        ultimo_responsable = raw_user

                    # Actualizar empresa en seguridad_social si aplica
                    updates_ss = []
                    params_ss = []
                    if ultima_empresa_id and ss.get("id_empresa") != ultima_empresa_id:
                        updates_ss.append("id_empresa = %s")
                        params_ss.append(ultima_empresa_id)
                        ss["id_empresa"] = ultima_empresa_id

                    if updates_ss:
                        params_ss.append(ss_id)
                        cursor.execute(f"UPDATE seguridad_social SET {', '.join(updates_ss)} WHERE id = %s", tuple(params_ss))
                        conexion.commit()

                # 5. Obtener nombre de la última empresa solicitante si existe
                nombre_empresa = None
                if ss.get("id_empresa"):
                    cursor.execute("SELECT nombre_empresa FROM empresa WHERE id = %s", (ss["id_empresa"],))
                    emp_row = cursor.fetchone()
                    if emp_row:
                        nombre_empresa = emp_row["nombre_empresa"]

                responsable_final = ss.get("responsable") or "Sin asignar"
                fecha_vigencia_str = FORMATEAR_FECHA_STR(ss.get("fecha_vigencia"))

                # 6. Formatear campos para la respuesta
                resultado = {
                    "id": ss["id"],
                    "id_persona": persona["id"],
                    "nombre_persona": f"{persona['nombre']} {persona['apellido']}".strip(),
                    "identificacion": persona["identificacion"],
                    "tipo_doc": persona["tipo_doc"],
                    "cargo": persona.get("cargo") or "General",
                    "responsable": responsable_final,
                    "ultimo_usuario_solicitud": ultimo_responsable or "Sin registro",
                    "anotaciones": ss.get("anotaciones") or "",
                    "id_empresa": ss.get("id_empresa"),
                    "nombre_empresa": nombre_empresa or "Sin registro de empresa",
                    "nombre_contratista": nombre_contratista or "Sin contratista registrado",
                    "ultima_empresa_contratista": nombre_contratista or "Sin contratista registrado",
                    "ultima_empresa_solicitante": nombre_contratista or "Sin contratista registrado",
                    "ultima_revision": FORMATEAR_FECHA_STR(ss.get("ultima_revision")),
                    "fecha_vigencia": fecha_vigencia_str,
                    "fecha_consulta": fecha_vigencia_str,  # Alias para compatibilidad
                    "fecha_creacion": FORMATEAR_FECHA_STR(ss.get("fecha_creacion")),
                    "total_solicitudes": len(historial),
                    "historial": historial
                }

                return {"exito": True, "datos": resultado}

    except Exception as e:
        print(f"❌ Error en GET_OR_CREATE_seguridad_social_persona_db: {e}")
        return {"exito": False, "mensaje": f"Error al consultar seguridad social: {str(e)}"}


def UPDATE_seguridad_social_db(id_persona: int, campos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Actualiza manualmente responsable, anotaciones, fecha_vigencia (dictaminada por SST)
    y registra la fecha/hora de la revisión en ultima_revision.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # Verificar existencia del registro de seguridad social
                cursor.execute("SELECT id FROM seguridad_social WHERE id_persona = %s", (id_persona,))
                row = cursor.fetchone()
                if not row:
                    cursor.execute("INSERT INTO seguridad_social (id_persona, fecha_creacion) VALUES (%s, NOW())", (id_persona,))
                    conexion.commit()
                    ss_id = cursor.lastrowid
                else:
                    ss_id = row["id"]

                # Preparar campos a actualizar
                updates = []
                valores = []

                if "responsable" in campos and campos["responsable"] is not None:
                    updates.append("responsable = %s")
                    valores.append(campos["responsable"])

                if "anotaciones" in campos:
                    updates.append("anotaciones = %s")
                    valores.append(campos["anotaciones"])

                if "id_empresa" in campos and campos["id_empresa"] is not None:
                    updates.append("id_empresa = %s")
                    valores.append(campos["id_empresa"])

                # Fecha de vigencia dictaminada por SST (se acepta fecha_vigencia o fecha_consulta)
                fv = campos.get("fecha_vigencia") or campos.get("fecha_consulta")
                if fv is not None:
                    updates.append("fecha_vigencia = %s")
                    valores.append(fv)

                # Registrar fecha de última revisión (si viene o por defecto NOW())
                if "ultima_revision" in campos and campos["ultima_revision"]:
                    updates.append("ultima_revision = %s")
                    valores.append(campos["ultima_revision"])
                else:
                    updates.append("ultima_revision = NOW()")

                if updates:
                    sql = f"UPDATE seguridad_social SET {', '.join(updates)} WHERE id = %s"
                    valores.append(ss_id)
                    cursor.execute(sql, tuple(valores))
                    conexion.commit()

                return {"exito": True, "mensaje": "Seguridad social actualizada exitosamente por SST."}

    except Exception as e:
        print(f"❌ Error en UPDATE_seguridad_social_db: {e}")
        return {"exito": False, "mensaje": f"Error al actualizar seguridad social: {str(e)}"}


def ADD_historial_solicitud_ss_db(id_persona: int, id_solicitud: int, id_empresa: int, observacion: Optional[str] = None) -> Dict[str, Any]:
    """
    Registra una solicitud en el historial de seguridad social de una persona.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # Obtener o crear seguridad social
                cursor.execute("SELECT id FROM seguridad_social WHERE id_persona = %s", (id_persona,))
                ss = cursor.fetchone()
                if not ss:
                    cursor.execute("""
                        INSERT INTO seguridad_social (id_persona, id_empresa, fecha_creacion)
                        VALUES (%s, %s, NOW())
                    """, (id_persona, id_empresa))
                    ss_id = cursor.lastrowid
                else:
                    ss_id = ss["id"]
                    cursor.execute("UPDATE seguridad_social SET id_empresa = %s WHERE id = %s", (id_empresa, ss_id))

                cursor.execute("""
                    INSERT INTO seguridad_social_historial_solicitudes 
                        (id_seguridad_social, id_solicitud, id_empresa, fecha_solicitud, observacion)
                    VALUES (%s, %s, %s, NOW(), %s)
                """, (ss_id, id_solicitud, id_empresa, observacion))

                conexion.commit()
                return {"exito": True, "mensaje": "Historial de solicitud registrado en seguridad social."}

    except Exception as e:
        print(f"❌ Error en ADD_historial_solicitud_ss_db: {e}")
        return {"exito": False, "mensaje": f"Error al registrar historial en seguridad social: {str(e)}"}


def GET_ALL_seguridad_social_db() -> Dict[str, Any]:
    """
    Retorna la lista de todas las personas con su estado de seguridad social resumido y conteo total de solicitudes.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = """
                    SELECT 
                        p.id AS id_persona,
                        CONCAT(p.nombre, ' ', p.apellido) AS nombre_persona,
                        p.identificacion,
                        p.tipo_doc,
                        p.cargo,
                        ss.id AS id_seguridad_social,
                        ss.responsable,
                        ss.anotaciones,
                        ss.id_empresa,
                        emp.nombre_empresa,
                        ss.ultima_revision,
                        ss.fecha_vigencia
                    FROM personas p
                    LEFT JOIN seguridad_social ss ON p.id = ss.id_persona
                    LEFT JOIN empresa emp ON ss.id_empresa = emp.id
                    ORDER BY p.id DESC
                """
                cursor.execute(sql)
                personas_db = cursor.fetchall() or []

                resultados = []
                for p in personas_db:
                    id_per = p["id_persona"]
                    id_ss = p.get("id_seguridad_social")

                    historial = OBTENER_HISTORIAL_COMPLETO_PERSONA_SS(cursor, id_per, id_ss)

                    nombre_contratista_final = None
                    nombre_empresa_final = p.get("nombre_empresa")
                    ultimo_responsable_final = None
                    if historial:
                        nombre_contratista_final = historial[0].get("nombre_contratista")
                        if not nombre_empresa_final:
                            nombre_empresa_final = historial[0].get("nombre_empresa")
                        raw_u = (historial[0].get("usuario_registro") or historial[0].get("diligenciador") or "").strip()
                        if raw_u:
                            ultimo_responsable_final = raw_u

                    responsable_final = p.get("responsable") or "Sin asignar"
                    fecha_vigencia_str = FORMATEAR_FECHA_STR(p.get("fecha_vigencia"))

                    resultados.append({
                        "id": id_ss,
                        "id_persona": id_per,
                        "nombre_persona": p["nombre_persona"],
                        "identificacion": p["identificacion"],
                        "tipo_doc": p["tipo_doc"],
                        "cargo": p["cargo"] or "General",
                        "responsable": responsable_final,
                        "ultimo_usuario_solicitud": ultimo_responsable_final or "Sin registro",
                        "anotaciones": p.get("anotaciones") or "",
                        "id_empresa": p.get("id_empresa"),
                        "nombre_empresa": nombre_empresa_final or "Sin registros",
                        "nombre_contratista": nombre_contratista_final or "Sin contratista",
                        "ultima_empresa_contratista": nombre_contratista_final or "Sin contratista",
                        "ultima_empresa_solicitante": nombre_contratista_final or "Sin contratista",
                        "ultima_revision": FORMATEAR_FECHA_STR(p.get("ultima_revision")) or "No registrada",
                        "fecha_vigencia": fecha_vigencia_str or "Pendiente",
                        "fecha_consulta": fecha_vigencia_str or "Pendiente",  # Alias de compatibilidad
                        "total_solicitudes": len(historial)
                    })

                return {"exito": True, "datos": resultados}

    except Exception as e:
        print(f"❌ Error en GET_ALL_seguridad_social_db: {e}")
        return {"exito": False, "mensaje": f"Error al consultar listado de seguridad social: {str(e)}", "datos": []}
