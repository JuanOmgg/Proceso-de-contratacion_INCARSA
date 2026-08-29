from database import GET_conexion
from typing import Optional, Dict, Any, List
from datetime import datetime
from src.transformers.antecedentes_transformer import FORMATEAR_FECHA_STR


def OBTENER_HISTORIAL_COMPLETO_PERSONA(cursor, id_persona: int, id_antecedente: Optional[int]) -> list:
    """
    Obtiene todas las solicitudes en las que la persona ha participado:
    1. A través de la tabla 'ingresantes' (relación directa con solicitudes).
    2. A través de 'solicitudes.personas_ids' (CSV de personas asociadas).
    3. A través de 'antecedentes_historial_solicitudes'.
    Consolida y elimina duplicados ordenando de la más reciente a la más antigua.
    """
    solicitudes_map = {}

    # 1. Consulta desde tabla ingresantes
    sql_ing = """
        SELECT 
            s.id AS id_solicitud,
            CONCAT('RAD-', LPAD(s.id, 4, '0')) AS codigo_radicado,
            s.fecha_inicio,
            s.fecha_fin,
            s.estado AS estado_solicitud,
            ec.nombre AS nombre_contratista,
            s.empresa_origen AS id_empresa,
            emp.nombre_empresa,
            COALESCE(s.fecha_creacion, s.fecha_inicio) AS fecha_solicitud,
            '' AS observacion
        FROM ingresantes ing
        INNER JOIN solicitudes s ON ing.id_solicitud = s.id
        LEFT JOIN empresa emp ON s.empresa_origen = emp.id
        LEFT JOIN emp_contratista ec ON s.empresa_contratista = ec.id
        WHERE ing.id_persona = %s
    """
    try:
        cursor.execute(sql_ing, (id_persona,))
        for row in cursor.fetchall():
            key = f"sol_{row['id_solicitud']}"
            solicitudes_map[key] = dict(row)
    except Exception as e:
        print(f"⚠️ Aviso al consultar ingresantes para persona {id_persona}: {e}")

    # 2. Consulta desde solicitudes (personas_ids mediante FIND_IN_SET y LIKE)
    sql_csv = """
        SELECT 
            s.id AS id_solicitud,
            CONCAT('RAD-', LPAD(s.id, 4, '0')) AS codigo_radicado,
            s.fecha_inicio,
            s.fecha_fin,
            s.estado AS estado_solicitud,
            ec.nombre AS nombre_contratista,
            s.empresa_origen AS id_empresa,
            emp.nombre_empresa,
            COALESCE(s.fecha_creacion, s.fecha_inicio) AS fecha_solicitud,
            '' AS observacion
        FROM solicitudes s
        LEFT JOIN empresa emp ON s.empresa_origen = emp.id
        LEFT JOIN emp_contratista ec ON s.empresa_contratista = ec.id
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
        print(f"⚠️ Aviso al consultar personas_ids para persona {id_persona}: {e}")

    # 3. Consulta desde antecedentes_historial_solicitudes
    if id_antecedente:
        sql_ant = """
            SELECT 
                h.id,
                h.id_solicitud,
                CONCAT('RAD-', LPAD(COALESCE(s.id, h.id_solicitud, 0), 4, '0')) AS codigo_radicado,
                s.fecha_inicio,
                s.fecha_fin,
                COALESCE(s.estado, 'REGISTRADO') AS estado_solicitud,
                ec.nombre AS nombre_contratista,
                h.id_empresa,
                emp.nombre_empresa,
                h.fecha_solicitud,
                h.observacion
            FROM antecedentes_historial_solicitudes h
            LEFT JOIN empresa emp ON h.id_empresa = emp.id
            LEFT JOIN solicitudes s ON h.id_solicitud = s.id
            LEFT JOIN emp_contratista ec ON s.empresa_contratista = ec.id
            WHERE h.id_antecedente = %s
        """
        try:
            cursor.execute(sql_ant, (id_antecedente,))
            for row in cursor.fetchall():
                if row.get("id_solicitud"):
                    key = f"sol_{row['id_solicitud']}"
                    if key not in solicitudes_map:
                        solicitudes_map[key] = dict(row)
                else:
                    key = f"hist_{row.get('id', id(row))}"
                    solicitudes_map[key] = dict(row)
        except Exception as e:
            print(f"⚠️ Aviso al consultar antecedentes_historial_solicitudes: {e}")

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


def GET_OR_CREATE_antecedente_persona_db(id_persona: int, actualizar_revision: bool = False) -> Dict[str, Any]:
    """
    Obtiene el registro de antecedentes de una persona.
    Si no existe, lo crea automáticamente.
    Si actualizar_revision=True (por ejemplo al abrir el modal), actualiza:
      - ultima_revision = NOW()
      - fecha_consulta = DATE_ADD(NOW(), INTERVAL 1 YEAR)
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Verificar si existe la persona
                cursor.execute("SELECT id, nombre, apellido, identificacion, tipo_doc FROM personas WHERE id = %s", (id_persona,))
                persona = cursor.fetchone()
                if not persona:
                    return {"exito": False, "mensaje": f"Persona con ID #{id_persona} no encontrada."}

                # 2. Consultar si ya tiene registro de antecedentes
                cursor.execute("SELECT * FROM antecedentes WHERE id_persona = %s", (id_persona,))
                antecedente = cursor.fetchone()

                if not antecedente:
                    # Crear el registro inicial con fecha_consulta = +1 año
                    cursor.execute("""
                        INSERT INTO antecedentes (id_persona, ultima_revision, fecha_consulta, fecha_creacion)
                        VALUES (%s, NOW(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR), NOW())
                    """, (id_persona,))
                    conexion.commit()
                    antecedente_id = cursor.lastrowid
                    cursor.execute("SELECT * FROM antecedentes WHERE id = %s", (antecedente_id,))
                    antecedente = cursor.fetchone()
                else:
                    antecedente_id = antecedente["id"]
                    if actualizar_revision:
                        # Auto-actualizar ultima_revision y fecha_consulta a 1 año desde hoy
                        cursor.execute("""
                            UPDATE antecedentes 
                            SET ultima_revision = NOW(),
                                fecha_consulta = DATE_ADD(CURDATE(), INTERVAL 1 YEAR)
                            WHERE id = %s
                        """, (antecedente_id,))
                        conexion.commit()
                        cursor.execute("SELECT * FROM antecedentes WHERE id = %s", (antecedente_id,))
                        antecedente = cursor.fetchone()

                # 3. Obtener el historial completo consolidado de solicitudes
                historial = OBTENER_HISTORIAL_COMPLETO_PERSONA(cursor, id_persona, antecedente_id)

                # 4. Determinar la última empresa solicitante y auto-actualizar id_empresa
                if historial:
                    ultima_solicitud = historial[0]
                    ultima_empresa_id = ultima_solicitud.get("id_empresa")
                    if ultima_empresa_id and antecedente.get("id_empresa") != ultima_empresa_id:
                        cursor.execute("""
                            UPDATE antecedentes SET id_empresa = %s WHERE id = %s
                        """, (ultima_empresa_id, antecedente_id))
                        conexion.commit()
                        antecedente["id_empresa"] = ultima_empresa_id

                # 5. Obtener nombre de la última empresa si existe
                nombre_empresa = None
                if antecedente.get("id_empresa"):
                    cursor.execute("SELECT nombre_empresa FROM empresa WHERE id = %s", (antecedente["id_empresa"],))
                    emp_row = cursor.fetchone()
                    if emp_row:
                        nombre_empresa = emp_row["nombre_empresa"]

                # 6. Formatear campos para la respuesta
                resultado = {
                    "id": antecedente["id"],
                    "id_persona": persona["id"],
                    "nombre_persona": f"{persona['nombre']} {persona['apellido']}".strip(),
                    "identificacion": persona["identificacion"],
                    "tipo_doc": persona["tipo_doc"],
                    "responsable": antecedente.get("responsable"),
                    "anotaciones": antecedente.get("anotaciones"),
                    "id_empresa": antecedente.get("id_empresa"),
                    "nombre_empresa": nombre_empresa or "Sin registro de empresa",
                    "ultima_revision": FORMATEAR_FECHA_STR(antecedente.get("ultima_revision")),
                    "fecha_consulta": FORMATEAR_FECHA_STR(antecedente.get("fecha_consulta")),
                    "fecha_creacion": FORMATEAR_FECHA_STR(antecedente.get("fecha_creacion")),
                    "total_solicitudes": len(historial),
                    "historial": historial
                }

                return {"exito": True, "datos": resultado}

    except Exception as e:
        print(f"❌ Error en GET_OR_CREATE_antecedente_persona_db: {e}")
        return {"exito": False, "mensaje": f"Error al consultar antecedentes: {str(e)}"}


def UPDATE_antecedente_db(id_persona: int, campos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Actualiza manualmente responsable, anotaciones y recalcula fecha_consulta si se modifica ultima_revision.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # Verificar existencia del antecedente
                cursor.execute("SELECT id FROM antecedentes WHERE id_persona = %s", (id_persona,))
                row = cursor.fetchone()
                if not row:
                    # Si no existía, crearlo
                    cursor.execute("INSERT INTO antecedentes (id_persona) VALUES (%s)", (id_persona,))
                    conexion.commit()
                    antecedente_id = cursor.lastrowid
                else:
                    antecedente_id = row["id"]

                # Preparar campos a actualizar
                updates = []
                valores = []

                if "responsable" in campos:
                    updates.append("responsable = %s")
                    valores.append(campos["responsable"])

                if "anotaciones" in campos:
                    updates.append("anotaciones = %s")
                    valores.append(campos["anotaciones"])

                if "id_empresa" in campos and campos["id_empresa"] is not None:
                    updates.append("id_empresa = %s")
                    valores.append(campos["id_empresa"])

                if "fecha_consulta" in campos and campos["fecha_consulta"]:
                    updates.append("fecha_consulta = %s")
                    valores.append(campos["fecha_consulta"])

                if "ultima_revision" in campos and campos["ultima_revision"]:
                    updates.append("ultima_revision = %s")
                    valores.append(campos["ultima_revision"])
                    if "fecha_consulta" not in campos or not campos["fecha_consulta"]:
                        updates.append("fecha_consulta = DATE_ADD(%s, INTERVAL 1 YEAR)")
                        valores.append(campos["ultima_revision"])

                if updates:
                    sql = f"UPDATE antecedentes SET {', '.join(updates)} WHERE id = %s"
                    valores.append(antecedente_id)
                    cursor.execute(sql, tuple(valores))
                    conexion.commit()

                return {"exito": True, "mensaje": "Antecedentes actualizados exitosamente."}

    except Exception as e:
        print(f"❌ Error en UPDATE_antecedente_db: {e}")
        return {"exito": False, "mensaje": f"Error al actualizar antecedentes: {str(e)}"}


def ADD_historial_solicitud_db(id_persona: int, id_solicitud: int, id_empresa: int, observacion: Optional[str] = None) -> Dict[str, Any]:
    """
    Registra una solicitud en el historial de antecedentes de una persona.
    Auto-actualiza la última empresa en la tabla antecedentes.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # Obtener o crear el antecedente
                cursor.execute("SELECT id FROM antecedentes WHERE id_persona = %s", (id_persona,))
                ant = cursor.fetchone()
                if not ant:
                    cursor.execute("""
                        INSERT INTO antecedentes (id_persona, id_empresa, ultima_revision, fecha_consulta)
                        VALUES (%s, %s, NOW(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR))
                    """, (id_persona, id_empresa))
                    antecedente_id = cursor.lastrowid
                else:
                    antecedente_id = ant["id"]
                    # Actualizar id_empresa a la más reciente
                    cursor.execute("UPDATE antecedentes SET id_empresa = %s WHERE id = %s", (id_empresa, antecedente_id))

                # Insertar en historial de solicitudes
                cursor.execute("""
                    INSERT INTO antecedentes_historial_solicitudes 
                        (id_antecedente, id_solicitud, id_empresa, fecha_solicitud, observacion)
                    VALUES (%s, %s, %s, NOW(), %s)
                """, (antecedente_id, id_solicitud, id_empresa, observacion))

                conexion.commit()
                return {"exito": True, "mensaje": "Historial de solicitud registrado en antecedentes."}

    except Exception as e:
        print(f"❌ Error en ADD_historial_solicitud_db: {e}")
        return {"exito": False, "mensaje": f"Error al registrar historial: {str(e)}"}


def GET_ALL_antecedentes_db() -> Dict[str, Any]:
    """
    Retorna la lista de todas las personas con sus antecedentes resumidos y conteo total de solicitudes.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # Obtenemos todas las personas registradas junto a sus datos de antecedentes
                sql = """
                    SELECT 
                        p.id AS id_persona,
                        CONCAT(p.nombre, ' ', p.apellido) AS nombre_persona,
                        p.identificacion,
                        p.tipo_doc,
                        p.cargo,
                        a.id AS id_antecedente,
                        a.responsable,
                        a.anotaciones,
                        a.id_empresa,
                        emp.nombre_empresa,
                        a.ultima_revision,
                        a.fecha_consulta
                    FROM personas p
                    LEFT JOIN antecedentes a ON p.id = a.id_persona
                    LEFT JOIN empresa emp ON a.id_empresa = emp.id
                    ORDER BY p.id DESC
                """
                cursor.execute(sql)
                personas_db = cursor.fetchall() or []

                resultados = []
                for p in personas_db:
                    id_per = p["id_persona"]
                    id_ant = p.get("id_antecedente")

                    # Consultamos el historial completo para conteo real
                    historial = OBTENER_HISTORIAL_COMPLETO_PERSONA(cursor, id_per, id_ant)

                    # Si hay historial pero no tenía empresa en antecedente, tomamos la última
                    nombre_empresa_final = p.get("nombre_empresa")
                    if not nombre_empresa_final and historial:
                        nombre_empresa_final = historial[0].get("nombre_empresa")

                    resultados.append({
                        "id": id_ant,
                        "id_persona": id_per,
                        "nombre_persona": p["nombre_persona"],
                        "identificacion": p["identificacion"],
                        "tipo_doc": p["tipo_doc"],
                        "cargo": p["cargo"],
                        "responsable": p.get("responsable") or "Sin asignar",
                        "anotaciones": p.get("anotaciones") or "",
                        "id_empresa": p.get("id_empresa"),
                        "nombre_empresa": nombre_empresa_final or "Sin registros",
                        "ultima_revision": FORMATEAR_FECHA_STR(p.get("ultima_revision")) or "No registrada",
                        "fecha_consulta": FORMATEAR_FECHA_STR(p.get("fecha_consulta")) or "Pendiente",
                        "total_solicitudes": len(historial)
                    })

                return {"exito": True, "datos": resultados}

    except Exception as e:
        print(f"❌ Error en GET_ALL_antecedentes_db: {e}")
        return {"exito": False, "mensaje": f"Error al consultar listado de antecedentes: {str(e)}", "datos": []}
