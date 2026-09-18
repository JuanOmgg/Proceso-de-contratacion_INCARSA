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

                if not induccion:
                    if auto_renovar:
                        cursor.execute(
                            """
                            INSERT INTO inducciones (id_persona, responsable, fecha_induccion, fecha_vigencia, ultima_revision, fecha_creacion)
                            VALUES (%s, 'Auditor GESCO', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR), NOW(), NOW())
                            """,
                            (id_persona,)
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
