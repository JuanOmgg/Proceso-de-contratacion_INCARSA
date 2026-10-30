import re
import json
import unicodedata
from typing import Dict, List, Any, Optional
from datetime import datetime
from database import GET_conexion


def slugify_formulario(nombre: str) -> str:
    """
    Convierte el nombre de un formulario en un slug amigable para URLs.
    Ej: 'Formulario Test Preguntas Back' -> 'formulario-test-preguntas-back'
    """
    if not nombre:
        return ""
    text = unicodedata.normalize('NFKD', str(nombre)).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def GET_formularios_gesco_db(tipo_personal: Optional[str] = None, solo_activos: bool = False) -> Dict[str, Any]:
    """
    Retorna la lista de formularios GESCO registrados, opcionalmente filtrados por tipo de personal o estado.
    Incluye conteos de preguntas asociadas, slug URL y enlaces directos de evaluación.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                query = """
                    SELECT fg.id, fg.nombre, fg.descripcion, fg.vigencia, fg.tipo_personal, fg.Tipo_pregunta,
                           fg.cantidad_preguntas, fg.config_cuotas, fg.is_active,
                           fg.es_interno, fg.fecha_limite,
                           fg.id_creador,
                           COALESCE(
                               fg.creador_nombre,
                               CONCAT(u.nombres, ' ', COALESCE(u.apellidos, '')),
                               'Auditor GESCO'
                           ) AS creador_nombre,
                           fg.created_at, fg.updated_at,
                           (SELECT COUNT(*) FROM preguntas p WHERE p.id_formulario = fg.id) AS total_preguntas,
                           (SELECT COUNT(*) FROM inducciones ind WHERE ind.id_formulario = fg.id) AS total_inducciones
                    FROM formularioGesco fg
                    LEFT JOIN usuarios u ON fg.id_creador = u.id
                    WHERE 1=1
                """
                params = []

                if solo_activos:
                    query += " AND fg.is_active = 1"

                if tipo_personal:
                    tp_clean = tipo_personal.strip()
                    query += " AND (fg.tipo_personal = 'TODOS' OR FIND_IN_SET(%s, fg.tipo_personal) > 0 OR fg.tipo_personal LIKE %s)"
                    params.extend([tp_clean, f"%{tp_clean}%"])

                query += " ORDER BY fg.id ASC"
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall() or []

                for r in rows:
                    if r.get("created_at") and hasattr(r["created_at"], "isoformat"):
                        r["created_at"] = r["created_at"].isoformat()
                    if r.get("updated_at") and hasattr(r["updated_at"], "isoformat"):
                        r["updated_at"] = r["updated_at"].isoformat()
                    if r.get("fecha_limite") and hasattr(r["fecha_limite"], "isoformat"):
                        r["fecha_limite"] = r["fecha_limite"].isoformat()
                    elif r.get("fecha_limite"):
                        r["fecha_limite"] = str(r["fecha_limite"])
                    r["is_active"] = bool(r.get("is_active"))
                    r["es_interno"] = bool(r.get("es_interno"))
                    r["Tipo_pregunta"] = r.get("Tipo_pregunta") or "GENERAL"
                    r["cantidad_preguntas"] = int(r["cantidad_preguntas"]) if r.get("cantidad_preguntas") is not None else None
                    if r.get("config_cuotas") and isinstance(r["config_cuotas"], str):
                        try:
                            r["config_cuotas"] = json.loads(r["config_cuotas"])
                        except Exception:
                            r["config_cuotas"] = None
                    r["total_preguntas"] = int(r.get("total_preguntas") or 0)
                    r["total_inducciones"] = int(r.get("total_inducciones") or 0)
                    r["creador_nombre"] = (r.get("creador_nombre") or "").strip() or "Auditor GESCO"
                    
                    slug_val = slugify_formulario(r.get("nombre") or "") or str(r["id"])
                    r["slug"] = slug_val
                    r["url_evaluacion"] = f"/evaluacion-induccion/{slug_val}"
                    r["url_simulacion"] = f"/evaluacion-induccion/{slug_val}?simulacion=1"

                return {"exito": True, "datos": rows}
    except Exception as e:
        print(f"❌ Error al consultar formularios GESCO: {e}")
        return {"exito": False, "mensaje": f"Error al consultar formularios: {str(e)}", "datos": []}


def GET_formulario_gesco_por_id_db(id_form: Any) -> Dict[str, Any]:
    """
    Retorna un formulario GESCO específico por su ID numérico o por su Nombre/Slug.
    """
    try:
        ident_str = str(id_form or "").strip()
        if not ident_str:
            return {"exito": False, "mensaje": "Identificador de formulario no especificado.", "datos": None}

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                base_query = """
                    SELECT fg.id, fg.nombre, fg.descripcion, fg.vigencia, fg.tipo_personal, fg.Tipo_pregunta,
                           fg.cantidad_preguntas, fg.config_cuotas, fg.is_active,
                           fg.es_interno, fg.fecha_limite,
                           fg.id_creador,
                           COALESCE(
                               fg.creador_nombre,
                               CONCAT(u.nombres, ' ', COALESCE(u.apellidos, '')),
                               'Auditor GESCO'
                           ) AS creador_nombre,
                           fg.created_at, fg.updated_at,
                           (SELECT COUNT(*) FROM preguntas p WHERE p.id_formulario = fg.id) AS total_preguntas,
                           (SELECT COUNT(*) FROM inducciones ind WHERE ind.id_formulario = fg.id) AS total_inducciones
                    FROM formularioGesco fg
                    LEFT JOIN usuarios u ON fg.id_creador = u.id
                """

                row = None

                # 1. Búsqueda directa por ID si es un valor numérico
                if ident_str.isdigit():
                    cursor.execute(base_query + " WHERE fg.id = %s", (int(ident_str),))
                    row = cursor.fetchone()

                # 2. Búsqueda por Nombre exacto
                if not row:
                    cursor.execute(
                        base_query + " WHERE fg.nombre = %s ORDER BY fg.is_active DESC, fg.id DESC LIMIT 1",
                        (ident_str,)
                    )
                    row = cursor.fetchone()

                # 3. Búsqueda por Slug amigable en la lista de formularios
                if not row:
                    cursor.execute(base_query + " ORDER BY fg.is_active DESC, fg.id DESC")
                    all_forms = cursor.fetchall() or []
                    target_slug = slugify_formulario(ident_str)
                    for cand in all_forms:
                        if slugify_formulario(cand.get("nombre") or "") == target_slug:
                            row = cand
                            break

                if not row:
                    return {"exito": False, "mensaje": f"Formulario '{ident_str}' no encontrado.", "datos": None}

                if row.get("created_at") and hasattr(row["created_at"], "isoformat"):
                    row["created_at"] = row["created_at"].isoformat()
                if row.get("updated_at") and hasattr(row["updated_at"], "isoformat"):
                    row["updated_at"] = row["updated_at"].isoformat()
                if row.get("fecha_limite") and hasattr(row["fecha_limite"], "isoformat"):
                    row["fecha_limite"] = row["fecha_limite"].isoformat()
                elif row.get("fecha_limite"):
                    row["fecha_limite"] = str(row["fecha_limite"])
                row["is_active"] = bool(row.get("is_active"))
                row["es_interno"] = bool(row.get("es_interno"))
                row["Tipo_pregunta"] = row.get("Tipo_pregunta") or "GENERAL"
                row["cantidad_preguntas"] = int(row["cantidad_preguntas"]) if row.get("cantidad_preguntas") is not None else None
                if row.get("config_cuotas") and isinstance(row["config_cuotas"], str):
                    try:
                        row["config_cuotas"] = json.loads(row["config_cuotas"])
                    except Exception:
                        row["config_cuotas"] = None
                row["total_preguntas"] = int(row.get("total_preguntas") or 0)
                row["total_inducciones"] = int(row.get("total_inducciones") or 0)
                row["creador_nombre"] = (row.get("creador_nombre") or "").strip() or "Auditor GESCO"

                slug_val = slugify_formulario(row.get("nombre") or "") or str(row["id"])
                row["slug"] = slug_val
                row["url_evaluacion"] = f"/evaluacion-induccion/{slug_val}"
                row["url_simulacion"] = f"/evaluacion-induccion/{slug_val}?simulacion=1"

                return {"exito": True, "datos": row}
    except Exception as e:
        return {"exito": False, "mensaje": str(e), "datos": None}


def CREATE_formulario_gesco_db(data: dict) -> Dict[str, Any]:
    """
    Crea un nuevo formulario GESCO en base de datos.
    """
    try:
        nombre = str(data.get("nombre") or "").strip()
        if not nombre:
            return {"exito": False, "mensaje": "El nombre del formulario es obligatorio."}

        descripcion = str(data.get("descripcion") or "").strip() or None
        vigencia = int(data.get("vigencia") or 365)
        es_interno = bool(data.get("es_interno", False))
        tipo_personal = "Interno" if es_interno else str(data.get("tipo_personal") or "TODOS").strip()
        tipo_pregunta = str(data.get("Tipo_pregunta") or "GENERAL").strip()
        raw_cant = data.get("cantidad_preguntas")
        cantidad_preguntas = (None if es_interno else (int(raw_cant) if raw_cant is not None and str(raw_cant).strip() != "" and int(raw_cant) > 0 else None))
        config_cuotas_raw = data.get("config_cuotas")
        config_cuotas_json = (None if es_interno else (json.dumps(config_cuotas_raw) if config_cuotas_raw and isinstance(config_cuotas_raw, dict) else None))
        is_active = bool(data.get("is_active", True))
        fecha_limite = data.get("fecha_limite") or None
        if fecha_limite and isinstance(fecha_limite, str) and not fecha_limite.strip():
            fecha_limite = None
        id_creador = data.get("id_creador")
        creador_nombre = str(data.get("creador_nombre") or "").strip() or None

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO formularioGesco (
                        nombre, descripcion, vigencia, tipo_personal, Tipo_pregunta,
                        cantidad_preguntas, config_cuotas, is_active, es_interno, fecha_limite,
                        id_creador, creador_nombre, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        nombre, descripcion, vigencia, tipo_personal, tipo_pregunta,
                        cantidad_preguntas, config_cuotas_json, 1 if is_active else 0,
                        1 if es_interno else 0, fecha_limite,
                        id_creador, creador_nombre
                    )
                )
                conexion.commit()
                new_id = cursor.lastrowid
                return {
                    "exito": True,
                    "mensaje": f"Formulario '{nombre}' creado exitosamente.",
                    "id": new_id
                }
    except Exception as e:
        print(f"❌ Error al crear formulario GESCO: {e}")
        return {"exito": False, "mensaje": f"Error al crear formulario: {str(e)}"}


def UPDATE_formulario_gesco_db(id_form: int, data: dict) -> Dict[str, Any]:
    """
    Actualiza datos de un formulario GESCO existente.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT id FROM formularioGesco WHERE id = %s", (id_form,))
                if not cursor.fetchone():
                    return {"exito": False, "mensaje": f"Formulario #{id_form} no existe."}

                campos = []
                valores = []

                if "nombre" in data and data["nombre"] is not None:
                    campos.append("nombre = %s")
                    valores.append(str(data["nombre"]).strip())
                if "descripcion" in data and data["descripcion"] is not None:
                    campos.append("descripcion = %s")
                    valores.append(str(data["descripcion"]).strip())
                if "vigencia" in data and data["vigencia"] is not None:
                    campos.append("vigencia = %s")
                    valores.append(int(data["vigencia"]))
                if "tipo_personal" in data and data["tipo_personal"] is not None:
                    campos.append("tipo_personal = %s")
                    valores.append(str(data["tipo_personal"]).strip())
                if "Tipo_pregunta" in data and data["Tipo_pregunta"] is not None:
                    campos.append("Tipo_pregunta = %s")
                    valores.append(str(data["Tipo_pregunta"]).strip())
                if "cantidad_preguntas" in data:
                    campos.append("cantidad_preguntas = %s")
                    raw_cant = data["cantidad_preguntas"]
                    cant_val = int(raw_cant) if raw_cant is not None and str(raw_cant).strip() != "" and int(raw_cant) > 0 else None
                    valores.append(cant_val)
                if "config_cuotas" in data:
                    campos.append("config_cuotas = %s")
                    c_raw = data["config_cuotas"]
                    valores.append(json.dumps(c_raw) if c_raw and isinstance(c_raw, dict) else None)
                if "es_interno" in data and data["es_interno"] is not None:
                    es_int = bool(data["es_interno"])
                    campos.append("es_interno = %s")
                    valores.append(1 if es_int else 0)
                    if es_int:
                        campos.append("tipo_personal = %s")
                        valores.append("Interno")
                        campos.append("cantidad_preguntas = %s")
                        valores.append(None)
                        campos.append("config_cuotas = %s")
                        valores.append(None)
                if "fecha_limite" in data:
                    fl = data["fecha_limite"]
                    if fl and isinstance(fl, str) and not fl.strip():
                        fl = None
                    campos.append("fecha_limite = %s")
                    valores.append(fl)
                if "is_active" in data and data["is_active"] is not None:
                    campos.append("is_active = %s")
                    valores.append(1 if data["is_active"] else 0)
                if "id_creador" in data and data["id_creador"] is not None:
                    campos.append("id_creador = %s")
                    valores.append(int(data["id_creador"]))
                if "creador_nombre" in data and data["creador_nombre"] is not None:
                    campos.append("creador_nombre = %s")
                    valores.append(str(data["creador_nombre"]).strip())

                if not campos:
                    return {"exito": True, "mensaje": "Sin cambios para actualizar."}

                valores.append(id_form)
                sql = f"UPDATE formularioGesco SET {', '.join(campos)}, updated_at = NOW() WHERE id = %s"
                cursor.execute(sql, tuple(valores))
                conexion.commit()
                return {"exito": True, "mensaje": f"Formulario #{id_form} actualizado exitosamente."}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al actualizar formulario: {str(e)}"}


def DELETE_formulario_gesco_db(id_form: int) -> Dict[str, Any]:
    """
    Elimina o desactiva un formulario GESCO.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # Comprobar si tiene inducciones asociadas
                cursor.execute("SELECT COUNT(*) AS total FROM inducciones WHERE id_formulario = %s", (id_form,))
                row = cursor.fetchone()
                total_ind = row["total"] if row else 0

                if total_ind > 0:
                    # Si ya tiene personas asociadas, hacemos soft delete (desactivar)
                    cursor.execute("UPDATE formularioGesco SET is_active = 0, updated_at = NOW() WHERE id = %s", (id_form,))
                    conexion.commit()
                    return {"exito": True, "mensaje": f"Formulario #{id_form} desactivado porque contiene registros históricos de inducción."}
                else:
                    cursor.execute("DELETE FROM formularioGesco WHERE id = %s", (id_form,))
                    conexion.commit()
                    return {"exito": True, "mensaje": f"Formulario #{id_form} eliminado correctamente."}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al eliminar formulario: {str(e)}"}


def EVALUAR_Y_APLICAR_AUTO_APROBACION_GESCO(
    cursor,
    id_solicitud: int,
    tipo_personal: str,
    plantas_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Función desactivada: La auto-aprobación automática de solicitudes por parte de GESCO
    ha sido deshabilitada a solicitud del usuario. Toda solicitud requiere revisión manual
    y visto bueno explícito de un usuario con rol GESCO.
    """
    return {
        "auto_aprobado": False,
        "motivo": "Auto-aprobación GESCO deshabilitada. Requiere revisión manual.",
        "personas_evaluadas": 0
    }
