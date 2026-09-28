from typing import Dict, Any, Optional
from database import GET_conexion


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
                    SELECT ind.*, e.nombre_empresa
                    FROM inducciones ind
                    LEFT JOIN empresa e ON ind.id_empresa = e.id
                    WHERE ind.id_persona = %s
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
                            INSERT INTO inducciones (id_persona, responsable, id_empresa, fecha_induccion, fecha_vigencia, ultima_revision, fecha_creacion)
                            VALUES (%s, 'Auditor GESCO', %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR), NOW(), NOW())
                            """,
                            (id_persona, id_emp_init)
                        )
                        conexion.commit()
                        new_id = cursor.lastrowid
                        cursor.execute(
                            """
                            SELECT ind.*, e.nombre_empresa
                            FROM inducciones ind
                            LEFT JOIN empresa e ON ind.id_empresa = e.id
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
                            fecha_vigencia = DATE_ADD(CURDATE(), INTERVAL 1 YEAR),
                            ultima_revision = NOW()
                        WHERE id = %s
                        """,
                        (induccion["id"],)
                    )
                    conexion.commit()
                    cursor.execute(
                        """
                        SELECT ind.*, e.nombre_empresa
                        FROM inducciones ind
                        LEFT JOIN empresa e ON ind.id_empresa = e.id
                        WHERE ind.id = %s
                        """,
                        (induccion["id"],)
                    )
                    induccion = cursor.fetchone()

                datos = {
                    "id": induccion["id"],
                    "id_persona": persona["id"],
                    "persona_nombre": persona["nombre"],
                    "persona_apellido": persona.get("apellido", ""),
                    "persona_identificacion": persona["identificacion"],
                    "persona_tipo_doc": persona.get("tipo_doc", "CC"),
                    "persona_cargo": persona.get("cargo", "General"),
                    "responsable": induccion.get("responsable"),
                    "anotaciones": induccion.get("anotaciones"),
                    "id_empresa": induccion.get("id_empresa"),
                    "nombre_empresa": induccion.get("nombre_empresa"),
                    "ultima_empresa_contratista": ultima_empresa_contratista,
                    "fecha_induccion": _formatear_fecha(induccion.get("fecha_induccion")),
                    "fecha_vigencia": _formatear_fecha(induccion.get("fecha_vigencia")),
                    "ultima_revision": _formatear_fecha_hora(induccion.get("ultima_revision")),
                    "fecha_creacion": _formatear_fecha_hora(induccion.get("fecha_creacion"))
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

                cursor.execute("SELECT id FROM inducciones WHERE id_persona = %s", (id_persona,))
                ind_row = cursor.fetchone()

                responsable = data.get("responsable") or responsable_defecto
                anotaciones = data.get("anotaciones")
                id_empresa = data.get("id_empresa")
                fecha_ind = data.get("fecha_induccion")
                fecha_vig = data.get("fecha_vigencia")

                # Si no viene id_empresa, inferir empresa_origen de la última solicitud de la persona
                # NOTA: inducciones.id_empresa referencia a 'empresa' (mandante: INCARSA, MILPA, etc.), NO a 'emp_contratista'
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

                # Validar estrictamente que si id_empresa tiene valor, exista en tabla empresa (evita error FK 1452)
                if id_empresa is not None:
                    cursor.execute("SELECT id FROM empresa WHERE id = %s", (id_empresa,))
                    emp_val = cursor.fetchone()
                    if not emp_val:
                        # Si no es ID válido en 'empresa', intentar buscar empresa_origen como fallback
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

                # Si no hay fecha de inducción ni de vigencia, renovar por defecto a 1 año desde hoy
                if not fecha_ind and not fecha_vig:
                    if ind_row:
                        cursor.execute(
                            """
                            UPDATE inducciones
                            SET responsable = %s,
                                anotaciones = %s,
                                id_empresa = COALESCE(%s, id_empresa),
                                fecha_induccion = CURDATE(),
                                fecha_vigencia = DATE_ADD(CURDATE(), INTERVAL 1 YEAR),
                                ultima_revision = NOW()
                            WHERE id = %s
                            """,
                            (responsable, anotaciones, id_empresa, ind_row["id"])
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO inducciones (id_persona, responsable, anotaciones, id_empresa, fecha_induccion, fecha_vigencia, ultima_revision, fecha_creacion)
                            VALUES (%s, %s, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR), NOW(), NOW())
                            """,
                            (id_persona, responsable, anotaciones, id_empresa)
                        )
                else:
                    # Si viene fecha_induccion y no viene fecha_vigencia, calcular +1 año
                    if fecha_ind and not fecha_vig:
                        if ind_row:
                            cursor.execute(
                                """
                                UPDATE inducciones
                                SET responsable = %s,
                                    anotaciones = %s,
                                    id_empresa = COALESCE(%s, id_empresa),
                                    fecha_induccion = %s,
                                    fecha_vigencia = DATE_ADD(%s, INTERVAL 1 YEAR),
                                    ultima_revision = NOW()
                                WHERE id = %s
                                """,
                                (responsable, anotaciones, id_empresa, fecha_ind, fecha_ind, ind_row["id"])
                            )
                        else:
                            cursor.execute(
                                """
                                INSERT INTO inducciones (id_persona, responsable, anotaciones, id_empresa, fecha_induccion, fecha_vigencia, ultima_revision, fecha_creacion)
                                VALUES (%s, %s, %s, %s, %s, DATE_ADD(%s, INTERVAL 1 YEAR), NOW(), NOW())
                                """,
                                (id_persona, responsable, anotaciones, id_empresa, fecha_ind, fecha_ind)
                            )
                    else:
                        # Si vienen ambas fechas
                        if ind_row:
                            cursor.execute(
                                """
                                UPDATE inducciones
                                SET responsable = %s,
                                    anotaciones = %s,
                                    id_empresa = COALESCE(%s, id_empresa),
                                    fecha_induccion = %s,
                                    fecha_vigencia = %s,
                                    ultima_revision = NOW()
                                WHERE id = %s
                                """,
                                (responsable, anotaciones, id_empresa, fecha_ind, fecha_vig, ind_row["id"])
                            )
                        else:
                            cursor.execute(
                                """
                                INSERT INTO inducciones (id_persona, responsable, anotaciones, id_empresa, fecha_induccion, fecha_vigencia, ultima_revision, fecha_creacion)
                                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                                """,
                                (id_persona, responsable, anotaciones, id_empresa, fecha_ind, fecha_vig)
                            )

                conexion.commit()
                return {"exito": True, "mensaje": "Vigencia de inducción actualizada exitosamente (+1 año)."}

    except Exception as e:
        return {"exito": False, "mensaje": f"Error al actualizar inducción: {str(e)}"}


def GET_ALL_inducciones_db() -> Dict[str, Any]:
    """
    Retorna la lista de todas las personas con su estado de inducción,
    días restantes de vigencia, empresa asociada y total de solicitudes.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = """
                    SELECT 
                        p.id AS id_persona,
                        p.nombre,
                        p.apellido,
                        CONCAT(p.nombre, ' ', COALESCE(p.apellido, '')) AS nombre_completo,
                        p.identificacion,
                        p.tipo_doc,
                        p.cargo,
                        ind.id AS id_induccion,
                        ind.fecha_induccion,
                        ind.fecha_vigencia,
                        ind.responsable,
                        ind.anotaciones,
                        ind.ultima_revision,
                        DATEDIFF(ind.fecha_vigencia, CURDATE()) AS dias_restantes,
                        COALESCE(emp.nombre_empresa, (
                            SELECT ec.nombre 
                            FROM ingresantes ing2 
                            JOIN solicitudes s2 ON ing2.id_solicitud = s2.id 
                            JOIN emp_contratista ec ON s2.empresa_contratista = ec.id 
                            WHERE ing2.id_persona = p.id 
                            ORDER BY s2.id DESC 
                            LIMIT 1
                        ), 'Sin asignar') AS nombre_empresa,
                        (SELECT COUNT(DISTINCT ing3.id_solicitud) FROM ingresantes ing3 WHERE ing3.id_persona = p.id) AS total_solicitudes
                    FROM personas p
                    LEFT JOIN inducciones ind ON p.id = ind.id_persona
                    LEFT JOIN empresa emp ON ind.id_empresa = emp.id
                    ORDER BY p.id DESC
                """
                cursor.execute(sql)
                filas = cursor.fetchall() or []

                resultados = []
                for row in filas:
                    dias = row["dias_restantes"]
                    fecha_vig = row["fecha_vigencia"]
                    
                    if not fecha_vig:
                        estado = "sin_induccion"
                    elif dias is not None and dias < 0:
                        estado = "vencido"
                    elif dias is not None and dias <= 30:
                        estado = "por_vencer"
                    else:
                        estado = "vigente"

                    resultados.append({
                        "id_persona": row["id_persona"],
                        "id_induccion": row["id_induccion"],
                        "persona_nombre": row["nombre"],
                        "persona_apellido": row.get("apellido", ""),
                        "nombre_completo": row["nombre_completo"].strip(),
                        "identificacion": str(row["identificacion"]),
                        "tipo_doc": row.get("tipo_doc") or "CC",
                        "cargo": row.get("cargo") or "General",
                        "nombre_empresa": row["nombre_empresa"] or "Sin asignar",
                        "fecha_induccion": _formatear_fecha(row["fecha_induccion"]),
                        "fecha_vigencia": _formatear_fecha(row["fecha_vigencia"]),
                        "ultima_revision": _formatear_fecha_hora(row["ultima_revision"]),
                        "dias_restantes": dias,
                        "estado_vigencia": estado,
                        "responsable": row["responsable"] or "Sin auditor",
                        "anotaciones": row["anotaciones"],
                        "total_solicitudes": row["total_solicitudes"] or 0
                    })

                return {"exito": True, "datos": resultados}

    except Exception as e:
        return {"exito": False, "mensaje": f"Error al consultar listado de inducciones: {str(e)}"}

