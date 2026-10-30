from typing import Dict, Any, Optional
from database import GET_conexion
from src.loaders.formulario_gesco_loader import slugify_formulario


def _formatear_fecha(valor) -> Optional[str]:
    if not valor or str(valor).strip() in ["None", "null", ""]:
        return None
    return str(valor).split(" ")[0]


def _formatear_fecha_hora(valor) -> Optional[str]:
    if not valor or str(valor).strip() in ["None", "null", ""]:
        return None
    return str(valor)


def GET_OR_CREATE_induccion_persona_db(id_persona: int, auto_renovar: bool = False) -> Dict[str, Any]:
    """
    Obtiene el registro de inducción de una persona.
    Si auto_renovar=True, actualiza o crea la inducción vigente a 1 año desde hoy.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Verificar si existe la persona
                cursor.execute(
                    "SELECT id, nombre, apellido, identificacion, tipo_doc, cargo FROM personas WHERE id = %s",
                    (id_persona,)
                )
                persona = cursor.fetchone()
                if not persona:
                    return {"exito": False, "mensaje": f"Persona con ID #{id_persona} no encontrada."}

                # 2. Consultar si ya tiene inducción
                cursor.execute(
                    """
                    SELECT ind.*, e.nombre_empresa, fg.nombre AS nombre_formulario,
                           COALESCE(
                               ind.responsable,
                               fg.creador_nombre,
                               CONCAT(u.nombres, ' ', COALESCE(u.apellidos, '')),
                               'Auditor GESCO'
                           ) AS auditor_responsable
                    FROM inducciones ind
                    LEFT JOIN empresa e ON ind.id_empresa = e.id
                    LEFT JOIN formularioGesco fg ON ind.id_formulario = fg.id
                    LEFT JOIN usuarios u ON fg.id_creador = u.id
                    WHERE ind.id_persona = %s
                    ORDER BY ind.id DESC LIMIT 1
                    """,
                    (id_persona,)
                )
                induccion = cursor.fetchone()

                # Obtener contratista vinculado de su última solicitud para display informativo
                cursor.execute(
                    """
                    SELECT ec.nombre AS contratista_nombre
                    FROM ingresantes ing
                    JOIN solicitudes s ON ing.id_solicitud = s.id
                    JOIN emp_contratista ec ON s.empresa_contratista = ec.id
                    WHERE ing.id_persona = %s
                    ORDER BY s.id DESC LIMIT 1
                    """,
                    (id_persona,)
                )
                contratista_row = cursor.fetchone()
                ultima_empresa_contratista = contratista_row["contratista_nombre"] if contratista_row else None

                if not induccion:
                    if auto_renovar:
                        # Buscar empresa_origen para id_empresa (referencia a tabla 'empresa')
                        cursor.execute(
                            """
                            SELECT s.empresa_origen
                            FROM ingresantes ing
                            INNER JOIN solicitudes s ON ing.id_solicitud = s.id
                            WHERE ing.id_persona = %s AND s.empresa_origen IS NOT NULL
                            ORDER BY s.id DESC LIMIT 1
                            """,
                            (id_persona,)
                        )
                        sol_emp = cursor.fetchone()
                        id_emp_init = sol_emp["empresa_origen"] if sol_emp else None
                        if id_emp_init:
                            cursor.execute("SELECT id FROM empresa WHERE id = %s", (id_emp_init,))
                            if not cursor.fetchone():
                                id_emp_init = None

                        cursor.execute(
                            """
                            SELECT fg.id, COALESCE(fg.creador_nombre, CONCAT(u.nombres, ' ', COALESCE(u.apellidos, '')), 'Auditor GESCO') AS creador_nombre
                            FROM formularioGesco fg
                            LEFT JOIN usuarios u ON fg.id_creador = u.id
                            WHERE fg.is_active = 1
                            ORDER BY fg.id ASC LIMIT 1
                            """
                        )
                        row_form_def = cursor.fetchone()
                        id_form_init = row_form_def["id"] if row_form_def else None
                        resp_init = row_form_def["creador_nombre"] if row_form_def else "Auditor GESCO"

                        cursor.execute(
                            """
                            INSERT INTO inducciones (id_persona, id_formulario, id_empresa, responsable, fecha_induccion, fecha_vigencia, fecha_creacion)
                            VALUES (%s, %s, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR), NOW())
                            """,
                            (id_persona, id_form_init, id_emp_init, resp_init)
                        )
                        conexion.commit()
                        new_id = cursor.lastrowid
                        cursor.execute(
                            """
                            SELECT ind.*, e.nombre_empresa, fg.nombre AS nombre_formulario,
                                   COALESCE(
                                       ind.responsable,
                                       fg.creador_nombre,
                                       CONCAT(u.nombres, ' ', COALESCE(u.apellidos, '')),
                                       'Auditor GESCO'
                                   ) AS auditor_responsable
                            FROM inducciones ind
                            LEFT JOIN empresa e ON ind.id_empresa = e.id
                            LEFT JOIN formularioGesco fg ON ind.id_formulario = fg.id
                            LEFT JOIN usuarios u ON fg.id_creador = u.id
                            WHERE ind.id = %s
                            """,
                            (new_id,)
                        )
                        induccion = cursor.fetchone()
                    else:
                        # Retornar estructura limpia sin revisión
                        return {
                            "exito": True,
                            "datos": {
                                "id": None,
                                "id_persona": persona["id"],
                                "persona_nombre": persona["nombre"],
                                "persona_apellido": persona.get("apellido", ""),
                                "persona_identificacion": persona["identificacion"],
                                "persona_tipo_doc": persona.get("tipo_doc", "CC"),
                                "persona_cargo": persona.get("cargo", "General"),
                                "responsable": None,
                                "anotaciones": None,
                                "id_formulario": None,
                                "nombre_formulario": None,
                                "id_empresa": None,
                                "nombre_empresa": None,
                                "ultima_empresa_contratista": ultima_empresa_contratista,
                                "fecha_induccion": None,
                                "fecha_vigencia": None,
                                "ultima_revision": None,
                                "fecha_creacion": None
                            }
                        }
                elif auto_renovar:
                    cursor.execute(
                        """
                        UPDATE inducciones
                        SET fecha_induccion = CURDATE(),
                            fecha_vigencia = DATE_ADD(CURDATE(), INTERVAL 1 YEAR)
                        WHERE id = %s
                        """,
                        (induccion["id"],)
                    )
                    conexion.commit()
                    cursor.execute(
                        """
                        SELECT ind.*, e.nombre_empresa, fg.nombre AS nombre_formulario,
                               COALESCE(
                                   ind.responsable,
                                   fg.creador_nombre,
                                   CONCAT(u.nombres, ' ', COALESCE(u.apellidos, '')),
                                   'Auditor GESCO'
                               ) AS auditor_responsable
                        FROM inducciones ind
                        LEFT JOIN empresa e ON ind.id_empresa = e.id
                        LEFT JOIN formularioGesco fg ON ind.id_formulario = fg.id
                        LEFT JOIN usuarios u ON fg.id_creador = u.id
                        WHERE ind.id = %s
                        """,
                        (induccion["id"],)
                    )
                    induccion = cursor.fetchone()

                # Consultar todos los formularios e inducciones registrados para esta persona
                cursor.execute("""
                    SELECT 
                        ind.id AS id_induccion,
                        ind.id_formulario,
                        COALESCE(fg.nombre, 'Inducción General') AS nombre_formulario,
                        ind.fecha_induccion,
                        ind.fecha_vigencia,
                        DATEDIFF(ind.fecha_vigencia, CURDATE()) AS dias_restantes,
                        COALESCE(
                            ind.responsable,
                            fg.creador_nombre,
                            CONCAT(u.nombres, ' ', COALESCE(u.apellidos, '')),
                            'Auditor GESCO'
                        ) AS responsable
                    FROM inducciones ind
                    LEFT JOIN formularioGesco fg ON ind.id_formulario = fg.id
                    LEFT JOIN usuarios u ON fg.id_creador = u.id
                    WHERE ind.id_persona = %s
                    ORDER BY ind.fecha_vigencia DESC, ind.id DESC
                """, (id_persona,))
                all_ind = cursor.fetchall() or []

                cursor.execute("""
                    SELECT id_formulario, resultado, estado, fecha_realizacion, foto_evidencia_url
                    FROM resultados_formulario
                    WHERE id_persona = %s
                    ORDER BY fecha_realizacion DESC
                """, (id_persona,))
                all_rf = cursor.fetchall() or []
                rf_map = {}
                for r in all_rf:
                    if r["id_formulario"] not in rf_map:
                        rf_map[r["id_formulario"]] = r

                forms_list = []
                for ind_item in all_ind:
                    dias = ind_item["dias_restantes"]
                    fecha_vig = ind_item["fecha_vigencia"]
                    if not fecha_vig:
                        est = "sin_induccion"
                    elif dias is not None and dias < 0:
                        est = "vencido"
                    elif dias is not None and dias <= 30:
                        est = "por_vencer"
                    else:
                        est = "vigente"

                    rf_item = rf_map.get(ind_item["id_formulario"])
                    forms_list.append({
                        "id_induccion": ind_item["id_induccion"],
                        "id_formulario": ind_item["id_formulario"],
                        "nombre_formulario": ind_item["nombre_formulario"],
                        "slug": slugify_formulario(ind_item["nombre_formulario"]),
                        "fecha_induccion": _formatear_fecha(ind_item["fecha_induccion"]),
                        "fecha_vigencia": _formatear_fecha(ind_item["fecha_vigencia"]),
                        "dias_restantes": dias,
                        "estado_vigencia": est,
                        "responsable": ind_item["responsable"],
                        "resultado": rf_item["resultado"] if rf_item else None,
                        "aprobado": bool(rf_item["estado"]) if rf_item else True,
                        "foto_evidencia_url": rf_item.get("foto_evidencia_url") if rf_item else None,
                        "url_certificado": f"/api/v1/inducciones/persona/{id_persona}/certificado" + (f"?id_form={ind_item['id_formulario']}" if ind_item['id_formulario'] else "")
                    })

                datos = {
                    "id": induccion["id"],
                    "id_persona": persona["id"],
                    "persona_nombre": persona["nombre"],
                    "persona_apellido": persona.get("apellido", ""),
                    "persona_identificacion": persona["identificacion"],
                    "persona_tipo_doc": persona.get("tipo_doc", "CC"),
                    "persona_cargo": persona.get("cargo", "General"),
                    "responsable": induccion.get("auditor_responsable") or induccion.get("responsable") or "Auditor GESCO",
                    "anotaciones": None,
                    "id_formulario": induccion.get("id_formulario"),
                    "nombre_formulario": induccion.get("nombre_formulario"),
                    "id_empresa": induccion.get("id_empresa"),
                    "nombre_empresa": induccion.get("nombre_empresa"),
                    "ultima_empresa_contratista": ultima_empresa_contratista,
                    "fecha_induccion": _formatear_fecha(induccion.get("fecha_induccion")),
                    "fecha_vigencia": _formatear_fecha(induccion.get("fecha_vigencia")),
                    "ultima_revision": None,
                    "fecha_creacion": _formatear_fecha_hora(induccion.get("fecha_creacion")),
                    "formularios_realizados": forms_list,
                    "total_formularios": len(forms_list)
                }
                return {"exito": True, "datos": datos}

    except Exception as e:
        return {"exito": False, "mensaje": f"Error al consultar inducción: {str(e)}"}


def UPDATE_induccion_persona_db(id_persona: int, data: Dict[str, Any], responsable_defecto: str = "Auditor GESCO") -> Dict[str, Any]:
    """
    Inserta o actualiza el registro de inducción de una persona.
    Si se suministra fecha_induccion pero no fecha_vigencia, calcula automáticamente +1 año.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT id FROM personas WHERE id = %s", (id_persona,))
                if not cursor.fetchone():
                    return {"exito": False, "mensaje": f"Persona #{id_persona} no existe."}

                id_formulario = data.get("id_formulario")
                if not id_formulario:
                    cursor.execute("SELECT id FROM formularioGesco WHERE is_active = 1 ORDER BY id ASC LIMIT 1")
                    row_fg = cursor.fetchone()
                    id_formulario = row_fg["id"] if row_fg else None

                if id_formulario:
                    cursor.execute("SELECT id FROM inducciones WHERE id_persona = %s AND id_formulario = %s", (id_persona, id_formulario))
                else:
                    cursor.execute("SELECT id FROM inducciones WHERE id_persona = %s ORDER BY id DESC LIMIT 1", (id_persona,))
                ind_row = cursor.fetchone()

                id_empresa = data.get("id_empresa")
                fecha_ind = data.get("fecha_induccion")
                fecha_vig = data.get("fecha_vigencia")

                # Si no viene id_empresa, inferir empresa_origen de la última solicitud de la persona
                if not id_empresa:
                    cursor.execute(
                        """
                        SELECT s.empresa_origen AS id_empresa
                        FROM ingresantes ing
                        INNER JOIN solicitudes s ON ing.id_solicitud = s.id
                        WHERE ing.id_persona = %s AND s.empresa_origen IS NOT NULL
                        ORDER BY s.id DESC LIMIT 1
                        """,
                        (id_persona,)
                    )
                    sol_emp = cursor.fetchone()
                    if sol_emp and sol_emp.get("id_empresa"):
                        id_empresa = sol_emp["id_empresa"]

                if id_empresa is not None:
                    cursor.execute("SELECT id FROM empresa WHERE id = %s", (id_empresa,))
                    emp_val = cursor.fetchone()
                    if not emp_val:
                        cursor.execute(
                            """
                            SELECT s.empresa_origen
                            FROM ingresantes ing
                            INNER JOIN solicitudes s ON ing.id_solicitud = s.id
                            WHERE ing.id_persona = %s AND s.empresa_origen IS NOT NULL
                            ORDER BY s.id DESC LIMIT 1
                            """,
                            (id_persona,)
                        )
                        sol_fallback = cursor.fetchone()
                        if sol_fallback and sol_fallback.get("empresa_origen"):
                            cursor.execute("SELECT id FROM empresa WHERE id = %s", (sol_fallback["empresa_origen"],))
                            id_empresa = sol_fallback["empresa_origen"] if cursor.fetchone() else None
                        else:
                            id_empresa = None

                # Obtener o resolver responsable (por defecto, el creador del formulario)
                responsable = data.get("responsable")
                if not responsable or responsable == "Auditor GESCO":
                    if id_formulario:
                        cursor.execute(
                            """
                            SELECT COALESCE(fg.creador_nombre, CONCAT(u.nombres, ' ', COALESCE(u.apellidos, '')), 'Auditor GESCO') AS creador_nombre
                            FROM formularioGesco fg
                            LEFT JOIN usuarios u ON fg.id_creador = u.id
                            WHERE fg.id = %s
                            """,
                            (id_formulario,)
                        )
                        fg_row = cursor.fetchone()
                        if fg_row and fg_row.get("creador_nombre"):
                            responsable = fg_row["creador_nombre"]
                if not responsable:
                    responsable = responsable_defecto or "Auditor GESCO"

                # Si no hay fecha de inducción ni de vigencia, renovar por defecto a 1 año desde hoy
                if not fecha_ind and not fecha_vig:
                    if ind_row:
                        cursor.execute(
                            """
                            UPDATE inducciones
                            SET id_formulario = COALESCE(%s, id_formulario),
                                id_empresa = COALESCE(%s, id_empresa),
                                responsable = %s,
                                fecha_induccion = CURDATE(),
                                fecha_vigencia = DATE_ADD(CURDATE(), INTERVAL 1 YEAR)
                            WHERE id = %s
                            """,
                            (id_formulario, id_empresa, responsable, ind_row["id"])
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO inducciones (id_persona, id_formulario, id_empresa, responsable, fecha_induccion, fecha_vigencia, fecha_creacion)
                            VALUES (%s, %s, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR), NOW())
                            """,
                            (id_persona, id_formulario, id_empresa, responsable)
                        )
                else:
                    if fecha_ind and not fecha_vig:
                        if ind_row:
                            cursor.execute(
                                """
                                UPDATE inducciones
                                SET id_formulario = COALESCE(%s, id_formulario),
                                    id_empresa = COALESCE(%s, id_empresa),
                                    responsable = %s,
                                    fecha_induccion = %s,
                                    fecha_vigencia = DATE_ADD(%s, INTERVAL 1 YEAR)
                                WHERE id = %s
                                """,
                                (id_formulario, id_empresa, responsable, fecha_ind, fecha_ind, ind_row["id"])
                            )
                        else:
                            cursor.execute(
                                """
                                INSERT INTO inducciones (id_persona, id_formulario, id_empresa, responsable, fecha_induccion, fecha_vigencia, fecha_creacion)
                                VALUES (%s, %s, %s, %s, %s, DATE_ADD(%s, INTERVAL 1 YEAR), NOW())
                                """,
                                (id_persona, id_formulario, id_empresa, responsable, fecha_ind, fecha_ind)
                            )
                    else:
                        if ind_row:
                            cursor.execute(
                                """
                                UPDATE inducciones
                                SET id_formulario = COALESCE(%s, id_formulario),
                                    id_empresa = COALESCE(%s, id_empresa),
                                    responsable = %s,
                                    fecha_induccion = %s,
                                    fecha_vigencia = %s
                                WHERE id = %s
                                """,
                                (id_formulario, id_empresa, responsable, fecha_ind, fecha_vig, ind_row["id"])
                            )
                        else:
                            cursor.execute(
                                """
                                INSERT INTO inducciones (id_persona, id_formulario, id_empresa, responsable, fecha_induccion, fecha_vigencia, fecha_creacion)
                                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                                """,
                                (id_persona, id_formulario, id_empresa, responsable, fecha_ind, fecha_vig)
                            )

                conexion.commit()



                return {"exito": True, "mensaje": "Vigencia de inducción actualizada exitosamente (+1 año)."}

    except Exception as e:
        return {"exito": False, "mensaje": f"Error al actualizar inducción: {str(e)}"}


def GET_ALL_inducciones_db() -> Dict[str, Any]:
    """
    Retorna la lista de todas las personas registradas, agrupadas individualmente (1 fila por persona),
    con la lista completa de inducciones/formularios que ha realizado cada una,
    el tiempo de vigencia restante por cada formulario, y su estado general consolidado.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Obtener todas las personas únicas del sistema
                cursor.execute("""
                    SELECT 
                        p.id AS id_persona,
                        p.nombre,
                        p.apellido,
                        CONCAT(p.nombre, ' ', COALESCE(p.apellido, '')) AS nombre_completo,
                        p.identificacion,
                        p.tipo_doc,
                        p.cargo,
                        p.correo,
                        COALESCE(
                            (SELECT emp.nombre_empresa 
                             FROM inducciones ind_e 
                             JOIN empresa emp ON ind_e.id_empresa = emp.id 
                             WHERE ind_e.id_persona = p.id AND emp.nombre_empresa IS NOT NULL 
                             ORDER BY ind_e.id DESC LIMIT 1),
                            (SELECT ec.nombre 
                             FROM ingresantes ing2 
                             JOIN solicitudes s2 ON ing2.id_solicitud = s2.id 
                             JOIN emp_contratista ec ON s2.empresa_contratista = ec.id 
                             WHERE ing2.id_persona = p.id 
                             ORDER BY s2.id DESC LIMIT 1),
                            'Sin asignar'
                        ) AS nombre_empresa,
                        (SELECT COUNT(DISTINCT ing3.id_solicitud) FROM ingresantes ing3 WHERE ing3.id_persona = p.id) AS total_solicitudes
                    FROM personas p
                    ORDER BY p.id DESC
                """)
                personas = cursor.fetchall() or []

                # 2. Consultar todas las inducciones registradas con su formulario y auditor
                cursor.execute("""
                    SELECT 
                        ind.id AS id_induccion,
                        ind.id_persona,
                        ind.id_formulario,
                        COALESCE(fg.nombre, 'Inducción General') AS nombre_formulario,
                        ind.fecha_induccion,
                        ind.fecha_vigencia,
                        DATEDIFF(ind.fecha_vigencia, CURDATE()) AS dias_restantes,
                        COALESCE(
                            ind.responsable,
                            fg.creador_nombre,
                            CONCAT(u.nombres, ' ', COALESCE(u.apellidos, '')),
                            'Auditor GESCO'
                        ) AS responsable
                    FROM inducciones ind
                    LEFT JOIN formularioGesco fg ON ind.id_formulario = fg.id
                    LEFT JOIN usuarios u ON fg.id_creador = u.id
                    ORDER BY ind.fecha_vigencia DESC, ind.id DESC
                """)
                inducciones_raw = cursor.fetchall() or []

                # 3. Consultar últimos resultados de evaluaciones realizadas
                cursor.execute("""
                    SELECT rf.id_persona, rf.id_formulario, rf.resultado, rf.estado, rf.fecha_realizacion, rf.foto_evidencia_url
                    FROM resultados_formulario rf
                    ORDER BY rf.fecha_realizacion DESC
                """)
                rf_raw = cursor.fetchall() or []

                resultados_map = {}
                for r in rf_raw:
                    k = (r["id_persona"], r["id_formulario"])
                    if k not in resultados_map:
                        resultados_map[k] = r

                # Agrupar inducciones por id_persona
                ind_por_persona = {}
                for ind in inducciones_raw:
                    pid = ind["id_persona"]
                    if pid not in ind_por_persona:
                        ind_por_persona[pid] = []

                    dias = ind["dias_restantes"]
                    fecha_vig = ind["fecha_vigencia"]
                    if not fecha_vig:
                        est = "sin_induccion"
                    elif dias is not None and dias < 0:
                        est = "vencido"
                    elif dias is not None and dias <= 30:
                        est = "por_vencer"
                    else:
                        est = "vigente"

                    rf_item = resultados_map.get((pid, ind["id_formulario"]))

                    ind_por_persona[pid].append({
                        "id_induccion": ind["id_induccion"],
                        "id_formulario": ind["id_formulario"],
                        "nombre_formulario": ind["nombre_formulario"],
                        "slug": slugify_formulario(ind["nombre_formulario"]),
                        "fecha_induccion": _formatear_fecha(ind["fecha_induccion"]),
                        "fecha_vigencia": _formatear_fecha(ind["fecha_vigencia"]),
                        "dias_restantes": dias,
                        "estado_vigencia": est,
                        "responsable": ind["responsable"],
                        "resultado": rf_item["resultado"] if rf_item else None,
                        "aprobado": bool(rf_item["estado"]) if rf_item else True,
                        "foto_evidencia_url": rf_item.get("foto_evidencia_url") if rf_item else None,
                        "url_certificado": f"/api/v1/inducciones/persona/{pid}/certificado" + (f"?id_form={ind['id_formulario']}" if ind['id_formulario'] else "")
                    })

                lista_final = []
                for p in personas:
                    pid = p["id_persona"]
                    forms = ind_por_persona.get(pid, [])
                    total_f = len(forms)

                    if total_f == 0:
                        est_consolidado = "sin_induccion"
                        dias_con = None
                        f_ind = None
                        f_vig = None
                        resp = "Auditor GESCO"
                        n_form = "Sin inducción"
                        id_ind_main = None
                        id_form_main = None
                    else:
                        # Determinar estado consolidado
                        tiene_vencido = any(f["estado_vigencia"] == "vencido" for f in forms)
                        tiene_por_vencer = any(f["estado_vigencia"] == "por_vencer" for f in forms)
                        tiene_vigente = any(f["estado_vigencia"] == "vigente" for f in forms)

                        if tiene_vencido:
                            est_consolidado = "vencido"
                        elif tiene_por_vencer:
                            est_consolidado = "por_vencer"
                        elif tiene_vigente:
                            est_consolidado = "vigente"
                        else:
                            est_consolidado = "sin_induccion"

                        dias_validos = [f["dias_restantes"] for f in forms if f["dias_restantes"] is not None]
                        dias_con = min(dias_validos) if dias_validos else None

                        primer_f = forms[0]
                        id_ind_main = primer_f["id_induccion"]
                        id_form_main = primer_f["id_formulario"]
                        f_ind = primer_f["fecha_induccion"]
                        f_vig = primer_f["fecha_vigencia"]
                        resp = primer_f["responsable"]
                        if total_f == 1:
                            n_form = primer_f["nombre_formulario"]
                        else:
                            n_form = f"{primer_f['nombre_formulario']} (+{total_f - 1} más)"

                    lista_final.append({
                        "id_persona": pid,
                        "id_induccion": id_ind_main,
                        "id_formulario": id_form_main,
                        "persona_nombre": p["nombre"],
                        "persona_apellido": p["apellido"] or "",
                        "nombre_completo": p["nombre_completo"].strip(),
                        "identificacion": str(p["identificacion"]),
                        "tipo_doc": p["tipo_doc"] or "CC",
                        "cargo": p["cargo"] or "General",
                        "correo": p["correo"] or "",
                        "nombre_empresa": p["nombre_empresa"] or "Sin asignar",
                        "total_solicitudes": p["total_solicitudes"] or 0,
                        "formularios_realizados": forms,
                        "total_formularios": total_f,
                        "estado_vigencia": est_consolidado,
                        "dias_restantes": dias_con,
                        "fecha_induccion": f_ind,
                        "fecha_vigencia": f_vig,
                        "responsable": resp,
                        "nombre_formulario": n_form,
                        "anotaciones": None,
                        "ultima_revision": None
                    })

                return {"exito": True, "datos": lista_final}

    except Exception as e:
        return {"exito": False, "mensaje": f"Error al consultar listado de inducciones: {str(e)}"}

