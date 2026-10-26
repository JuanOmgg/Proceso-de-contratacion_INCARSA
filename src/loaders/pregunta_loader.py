import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from database import GET_conexion


def _formatear_fecha(val):
    if val and hasattr(val, "isoformat"):
        return val.isoformat()
    return val


def GET_preguntas_por_formulario_db(
    id_formulario: int,
    solo_activas: bool = False,
    aleatorio: bool = False,
    ocultar_respuestas_correctas: bool = False,
    limite_preguntas: Optional[int] = None
) -> Dict[str, Any]:
    """
    Retorna la lista de preguntas con sus respectivas opciones asociadas a un formulario GESCO.
    Soporta:
    - Muestreo aleatorio independiente por categoría temática (config_cuotas: SST, AMBIENTAL, etc.)
    - Muestreo global por cantidad_preguntas (fallback si no hay cuotas específicas)
    - Ocultamiento de respuestas correctas para exámenes de candidatos
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Verificar existencia del formulario y obtener cuotas configuradas
                cursor.execute(
                    """
                    SELECT id, nombre, descripcion, vigencia, tipo_personal, Tipo_pregunta,
                           cantidad_preguntas, config_cuotas, es_interno, fecha_limite
                    FROM formularioGesco
                    WHERE id = %s
                    """,
                    (id_formulario,)
                )
                form = cursor.fetchone()
                if not form:
                    return {"exito": False, "mensaje": f"Formulario #{id_formulario} no encontrado.", "datos": []}

                form["es_interno"] = bool(form.get("es_interno"))
                if form.get("fecha_limite") and hasattr(form["fecha_limite"], "isoformat"):
                    form["fecha_limite"] = form["fecha_limite"].isoformat()

                # Si es un formulario interno, no aplica muestreo aleatorio (evalúa todas las preguntas)
                if form["es_interno"]:
                    aleatorio = False

                # Parsear config_cuotas si viene como string JSON
                cuotas_config: Dict[str, int] = {}
                raw_cuotas = form.get("config_cuotas")
                if raw_cuotas:
                    if isinstance(raw_cuotas, str):
                        try:
                            cuotas_config = json.loads(raw_cuotas)
                        except Exception:
                            cuotas_config = {}
                    elif isinstance(raw_cuotas, dict):
                        cuotas_config = raw_cuotas
                form["config_cuotas"] = cuotas_config

                # 2. Consultar preguntas con su tipo_pregunta, multimedia y estado de calificación
                query_preguntas = """
                    SELECT id, id_formulario, pregunta, tipo_respuesta, tipo_pregunta,
                           imagen_url, video_url, es_calificable, estado, created_at, updated_at
                    FROM preguntas
                    WHERE id_formulario = %s
                """
                params = [id_formulario]
                if solo_activas:
                    query_preguntas += " AND estado = 1"
                query_preguntas += " ORDER BY id ASC"

                cursor.execute(query_preguntas, tuple(params))
                preguntas = cursor.fetchall() or []

                if not preguntas:
                    return {"exito": True, "formulario": form, "datos": [], "total_banco": 0, "evaluadas": 0}

                total_banco = len(preguntas)

                # 3. Aplicar muestreo aleatorio independiente por categoría si fue solicitado
                if aleatorio:
                    # Filtrar cuotas válidas mayores a 0
                    cuotas_activas = {
                        str(k).strip().upper(): int(v)
                        for k, v in cuotas_config.items()
                        if v is not None and str(v).isdigit() and int(v) > 0
                    }

                    if cuotas_activas:
                        # Agrupar preguntas por categoría (SST, AMBIENTAL, SEGURIDAD_VIAL, etc.)
                        preguntas_por_cat: Dict[str, List[dict]] = {}
                        for p in preguntas:
                            cat = str(p.get("tipo_pregunta") or "GENERAL").strip().upper()
                            preguntas_por_cat.setdefault(cat, []).append(p)

                        preguntas_seleccionadas = []
                        # Cada categoría maneja su aleatoriedad de forma completamente independiente
                        for cat, cuota in cuotas_activas.items():
                            preguntas_cat = preguntas_por_cat.get(cat, [])
                            if preguntas_cat:
                                cant_a_tomar = min(len(preguntas_cat), cuota)
                                preguntas_seleccionadas.extend(random.sample(preguntas_cat, cant_a_tomar))

                        if preguntas_seleccionadas:
                            # Intercalar/mezclar aleatoriamente las preguntas seleccionadas
                            random.shuffle(preguntas_seleccionadas)
                            preguntas = preguntas_seleccionadas
                        else:
                            # Fallback si ninguna categoría con cuota tenía preguntas activas
                            cant_objetivo = limite_preguntas or form.get("cantidad_preguntas")
                            if cant_objetivo and int(cant_objetivo) > 0 and len(preguntas) > int(cant_objetivo):
                                preguntas = random.sample(preguntas, int(cant_objetivo))
                            else:
                                random.shuffle(preguntas)
                    else:
                        # Muestreo global estándar si no se definieron cuotas por categoría
                        cant_objetivo = limite_preguntas or form.get("cantidad_preguntas")
                        if cant_objetivo and int(cant_objetivo) > 0 and len(preguntas) > int(cant_objetivo):
                            preguntas = random.sample(preguntas, int(cant_objetivo))
                        else:
                            random.shuffle(preguntas)

                # 4. Consultar opciones asociadas a las preguntas seleccionadas
                ids_preguntas = [p["id"] for p in preguntas]
                placeholders = ",".join(["%s"] * len(ids_preguntas))
                query_opciones = f"""
                    SELECT id, id_pregunta, opcion, is_correct, created_at, updated_at
                    FROM opciones_formulario
                    WHERE id_pregunta IN ({placeholders})
                    ORDER BY id ASC
                """
                cursor.execute(query_opciones, tuple(ids_preguntas))
                opciones = cursor.fetchall() or []

                # Mapear opciones por id_pregunta
                opciones_map: Dict[int, List[dict]] = {pid: [] for pid in ids_preguntas}
                for opc in opciones:
                    opc["is_correct"] = bool(opc.get("is_correct"))
                    opc["created_at"] = _formatear_fecha(opc.get("created_at"))
                    opc["updated_at"] = _formatear_fecha(opc.get("updated_at"))
                    if opc["id_pregunta"] in opciones_map:
                        opciones_map[opc["id_pregunta"]].append(opc)

                # 5. Aleatorizar orden de opciones y ocultar respuestas correctas si aplica
                for pid in opciones_map:
                    if aleatorio:
                        random.shuffle(opciones_map[pid])
                    if ocultar_respuestas_correctas:
                        for opc in opciones_map[pid]:
                            opc.pop("is_correct", None)

                # 6. Ensamblar preguntas completas con sus opciones
                for p in preguntas:
                    p["tipo_pregunta"] = str(p.get("tipo_pregunta") or "GENERAL").strip().upper()
                    p["imagen_url"] = p.get("imagen_url")
                    p["video_url"] = p.get("video_url")
                    p["es_calificable"] = bool(p.get("es_calificable", True) if p.get("es_calificable") is not None else True)
                    p["estado"] = bool(p.get("estado"))
                    p["created_at"] = _formatear_fecha(p.get("created_at"))
                    p["updated_at"] = _formatear_fecha(p.get("updated_at"))
                    p["opciones"] = opciones_map.get(p["id"], [])

                return {
                    "exito": True,
                    "formulario": form,
                    "datos": preguntas,
                    "total_banco": total_banco,
                    "evaluadas": len(preguntas)
                }
    except Exception as e:
        print(f"❌ Error al consultar preguntas del formulario #{id_formulario}: {e}")
        return {"exito": False, "mensaje": f"Error al consultar preguntas: {str(e)}", "datos": []}


def GET_pregunta_por_id_db(id_pregunta: int) -> Dict[str, Any]:
    """
    Retorna los datos de una pregunta específica y sus opciones de respuesta.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, id_formulario, pregunta, tipo_respuesta, tipo_pregunta,
                           imagen_url, video_url, es_calificable, estado, created_at, updated_at
                    FROM preguntas
                    WHERE id = %s
                    """,
                    (id_pregunta,)
                )
                p = cursor.fetchone()
                if not p:
                    return {"exito": False, "mensaje": f"Pregunta #{id_pregunta} no encontrada.", "datos": None}

                cursor.execute(
                    """
                    SELECT id, id_pregunta, opcion, is_correct, created_at, updated_at
                    FROM opciones_formulario
                    WHERE id_pregunta = %s
                    ORDER BY id ASC
                    """,
                    (id_pregunta,)
                )
                opciones = cursor.fetchall() or []
                for opc in opciones:
                    opc["is_correct"] = bool(opc.get("is_correct"))
                    opc["created_at"] = _formatear_fecha(opc.get("created_at"))
                    opc["updated_at"] = _formatear_fecha(opc.get("updated_at"))

                p["tipo_pregunta"] = str(p.get("tipo_pregunta") or "GENERAL").strip().upper()
                p["imagen_url"] = p.get("imagen_url")
                p["video_url"] = p.get("video_url")
                p["es_calificable"] = bool(p.get("es_calificable", True) if p.get("es_calificable") is not None else True)
                p["estado"] = bool(p.get("estado"))
                p["created_at"] = _formatear_fecha(p.get("created_at"))
                p["updated_at"] = _formatear_fecha(p.get("updated_at"))
                p["opciones"] = opciones

                return {"exito": True, "datos": p}
    except Exception as e:
        print(f"❌ Error al consultar pregunta #{id_pregunta}: {e}")
        return {"exito": False, "mensaje": f"Error al consultar pregunta: {str(e)}", "datos": None}


def CREATE_pregunta_db(data: dict) -> Dict[str, Any]:
    """
    Crea una nueva pregunta con sus opciones de respuesta de forma transaccional.
    """
    try:
        id_formulario = int(data.get("id_formulario") or 0)
        pregunta = str(data.get("pregunta") or "").strip()
        tipo_respuesta = str(data.get("tipo_respuesta") or "MULTIPLE").strip().upper()
        tipo_pregunta = str(data.get("tipo_pregunta") or "GENERAL").strip().upper()
        imagen_url = str(data.get("imagen_url") or "").strip() or None
        video_url = str(data.get("video_url") or "").strip() or None
        # Exclusividad estricta: un solo formato multimedia por pregunta (foto O video)
        if video_url:
            imagen_url = None
        es_calificable = 1 if (data.get("es_calificable") is not False and str(data.get("es_calificable")).lower() not in ["false", "0"]) else 0
        estado = bool(data.get("estado", True))
        opciones = data.get("opciones") or []

        if not id_formulario:
            return {"exito": False, "mensaje": "El id_formulario es obligatorio."}
        if not pregunta:
            return {"exito": False, "mensaje": "El enunciado de la pregunta es obligatorio."}

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # Verificar formulario
                cursor.execute("SELECT id FROM formularioGesco WHERE id = %s", (id_formulario,))
                if not cursor.fetchone():
                    return {"exito": False, "mensaje": f"El formulario #{id_formulario} no existe."}

                # Insertar pregunta con multimedia y calificación
                cursor.execute(
                    """
                    INSERT INTO preguntas (id_formulario, pregunta, tipo_respuesta, tipo_pregunta, imagen_url, video_url, es_calificable, estado, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (id_formulario, pregunta, tipo_respuesta, tipo_pregunta, imagen_url, video_url, es_calificable, 1 if estado else 0)
                )
                new_pregunta_id = cursor.lastrowid

                # Insertar opciones si las hay
                for opc in opciones:
                    texto_opc = str(opc.get("opcion") or "").strip()
                    if texto_opc:
                        is_correct = bool(opc.get("is_correct", False))
                        cursor.execute(
                            """
                            INSERT INTO opciones_formulario (id_pregunta, opcion, is_correct, created_at)
                            VALUES (%s, %s, %s, NOW())
                            """,
                            (new_pregunta_id, texto_opc, 1 if is_correct else 0)
                        )

                conexion.commit()
                return {
                    "exito": True,
                    "mensaje": "Pregunta creada exitosamente.",
                    "id": new_pregunta_id
                }
    except Exception as e:
        print(f"❌ Error al crear pregunta: {e}")
        return {"exito": False, "mensaje": f"Error al crear pregunta: {str(e)}"}


def UPDATE_pregunta_db(id_pregunta: int, data: dict) -> Dict[str, Any]:
    """
    Actualiza el enunciado, tipo, categoría o estado de una pregunta y sincroniza sus opciones.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT id FROM preguntas WHERE id = %s", (id_pregunta,))
                if not cursor.fetchone():
                    return {"exito": False, "mensaje": f"La pregunta #{id_pregunta} no existe."}

                campos = []
                valores = []

                if "pregunta" in data and data["pregunta"] is not None:
                    campos.append("pregunta = %s")
                    valores.append(str(data["pregunta"]).strip())

                if "tipo_respuesta" in data and data["tipo_respuesta"] is not None:
                    campos.append("tipo_respuesta = %s")
                    valores.append(str(data["tipo_respuesta"]).strip().upper())

                if "tipo_pregunta" in data and data["tipo_pregunta"] is not None:
                    campos.append("tipo_pregunta = %s")
                    valores.append(str(data["tipo_pregunta"]).strip().upper())

                if "imagen_url" in data:
                    campos.append("imagen_url = %s")
                    valores.append(str(data["imagen_url"]).strip() if data["imagen_url"] else None)

                if "video_url" in data:
                    campos.append("video_url = %s")
                    valores.append(str(data["video_url"]).strip() if data["video_url"] else None)

                if "es_calificable" in data and data["es_calificable"] is not None:
                    campos.append("es_calificable = %s")
                    valores.append(1 if data["es_calificable"] else 0)

                if "estado" in data and data["estado"] is not None:
                    campos.append("estado = %s")
                    valores.append(1 if data["estado"] else 0)

                if campos:
                    campos.append("updated_at = NOW()")
                    query_update = f"UPDATE preguntas SET {', '.join(campos)} WHERE id = %s"
                    valores.append(id_pregunta)
                    cursor.execute(query_update, tuple(valores))

                # Sincronización de opciones si se enviaron en el payload
                if "opciones" in data and data["opciones"] is not None:
                    opciones_payload = data["opciones"]

                    cursor.execute("SELECT id FROM opciones_formulario WHERE id_pregunta = %s", (id_pregunta,))
                    opciones_db = cursor.fetchall() or []
                    ids_db = {o["id"] for o in opciones_db}

                    ids_payload = {int(o["id"]) for o in opciones_payload if o.get("id") and int(o["id"]) in ids_db}

                    # Eliminar las que ya no están
                    ids_a_eliminar = ids_db - ids_payload
                    if ids_a_eliminar:
                        placeholders = ",".join(["%s"] * len(ids_a_eliminar))
                        cursor.execute(
                            f"DELETE FROM opciones_formulario WHERE id IN ({placeholders}) AND id_pregunta = %s",
                            tuple(list(ids_a_eliminar) + [id_pregunta])
                        )

                    # Actualizar existentes o insertar nuevas
                    for opc in opciones_payload:
                        texto = str(opc.get("opcion") or "").strip()
                        if not texto:
                            continue
                        is_corr = 1 if opc.get("is_correct") else 0
                        opc_id = opc.get("id")

                        if opc_id and int(opc_id) in ids_db:
                            cursor.execute(
                                """
                                UPDATE opciones_formulario
                                SET opcion = %s, is_correct = %s, updated_at = NOW()
                                WHERE id = %s AND id_pregunta = %s
                                """,
                                (texto, is_corr, int(opc_id), id_pregunta)
                            )
                        else:
                            cursor.execute(
                                """
                                INSERT INTO opciones_formulario (id_pregunta, opcion, is_correct, created_at)
                                VALUES (%s, %s, %s, NOW())
                                """,
                                (id_pregunta, texto, is_corr)
                            )

                conexion.commit()
                return {"exito": True, "mensaje": f"Pregunta #{id_pregunta} actualizada exitosamente."}
    except Exception as e:
        print(f"❌ Error al actualizar pregunta #{id_pregunta}: {e}")
        return {"exito": False, "mensaje": f"Error al actualizar pregunta: {str(e)}"}


def TOGGLE_estado_pregunta_db(id_pregunta: int) -> Dict[str, Any]:
    """
    Alterna el estado activo/inactivo (1/0) de una pregunta.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT id, estado FROM preguntas WHERE id = %s", (id_pregunta,))
                p = cursor.fetchone()
                if not p:
                    return {"exito": False, "mensaje": f"Pregunta #{id_pregunta} no existe."}

                nuevo_estado = 0 if p.get("estado") else 1
                cursor.execute(
                    "UPDATE preguntas SET estado = %s, updated_at = NOW() WHERE id = %s",
                    (nuevo_estado, id_pregunta)
                )
                conexion.commit()
                return {
                    "exito": True,
                    "id": id_pregunta,
                    "nuevo_estado": bool(nuevo_estado),
                    "mensaje": f"Pregunta {'activada' if nuevo_estado else 'desactivada'} exitosamente."
                }
    except Exception as e:
        print(f"❌ Error al alternar estado de pregunta #{id_pregunta}: {e}")
        return {"exito": False, "mensaje": f"Error al alternar estado: {str(e)}"}


def DELETE_pregunta_db(id_pregunta: int) -> Dict[str, Any]:
    """
    Elimina una pregunta y todas sus opciones asociadas (en cascada).
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT id, pregunta FROM preguntas WHERE id = %s", (id_pregunta,))
                p = cursor.fetchone()
                if not p:
                    return {"exito": False, "mensaje": f"Pregunta #{id_pregunta} no existe."}

                cursor.execute("DELETE FROM opciones_formulario WHERE id_pregunta = %s", (id_pregunta,))
                cursor.execute("DELETE FROM preguntas WHERE id = %s", (id_pregunta,))
                conexion.commit()

                return {
                    "exito": True,
                    "mensaje": f"Pregunta #{id_pregunta} y sus opciones fueron eliminadas correctamente."
                }
    except Exception as e:
        print(f"❌ Error al eliminar pregunta #{id_pregunta}: {e}")
        return {"exito": False, "mensaje": f"Error al eliminar pregunta: {str(e)}"}


def SYNC_preguntas_formulario_db(id_formulario: int, preguntas_list: list) -> Dict[str, Any]:
    """
    Sincroniza en un solo lote atómico todo el cuestionario de un formulario:
    - Inserta preguntas nuevas con su tipo_pregunta
    - Actualiza preguntas existentes, categorías y opciones
    - Elimina preguntas que ya no se encuentren en la lista
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Verificar formulario
                cursor.execute("SELECT id, nombre FROM formularioGesco WHERE id = %s", (id_formulario,))
                if not cursor.fetchone():
                    return {"exito": False, "mensaje": f"Formulario #{id_formulario} no existe."}

                # 2. Consultar preguntas actuales en DB
                cursor.execute("SELECT id FROM preguntas WHERE id_formulario = %s", (id_formulario,))
                preguntas_db = cursor.fetchall() or []
                ids_preguntas_db = {p["id"] for p in preguntas_db}

                # 3. Filtrar preguntas que persisten
                ids_incoming = {
                    int(q["id"]) for q in preguntas_list
                    if q.get("id") and int(q["id"]) in ids_preguntas_db
                }

                # 4. Eliminar las que ya no están
                ids_a_eliminar = ids_preguntas_db - ids_incoming
                if ids_a_eliminar:
                    placeholders = ",".join(["%s"] * len(ids_a_eliminar))
                    cursor.execute(
                        f"DELETE FROM opciones_formulario WHERE id_pregunta IN ({placeholders})",
                        tuple(ids_a_eliminar)
                    )
                    cursor.execute(
                        f"DELETE FROM preguntas WHERE id IN ({placeholders}) AND id_formulario = %s",
                        tuple(list(ids_a_eliminar) + [id_formulario])
                    )

                # 5. Insertar o actualizar preguntas
                for q in preguntas_list:
                    pregunta_texto = str(q.get("pregunta") or "").strip()
                    if not pregunta_texto:
                        continue

                    tipo = str(q.get("tipo_respuesta") or "MULTIPLE").strip().upper()
                    tipo_pregunta = str(q.get("tipo_pregunta") or "GENERAL").strip().upper()
                    imagen_url = str(q.get("imagen_url") or "").strip() or None
                    video_url = str(q.get("video_url") or "").strip() or None
                    # Exclusividad estricta: un solo formato multimedia por pregunta (foto O video)
                    if video_url:
                        imagen_url = None
                    es_calificable = 1 if (q.get("es_calificable") is not False and str(q.get("es_calificable")).lower() not in ["false", "0"]) else 0
                    estado = 1 if q.get("estado", True) else 0
                    q_id = q.get("id")
                    opciones = q.get("opciones") or []

                    if q_id and int(q_id) in ids_preguntas_db:
                        # Actualizar pregunta existente
                        target_qid = int(q_id)
                        cursor.execute(
                            """
                            UPDATE preguntas
                            SET pregunta = %s, tipo_respuesta = %s, tipo_pregunta = %s,
                                imagen_url = %s, video_url = %s, es_calificable = %s, estado = %s, updated_at = NOW()
                            WHERE id = %s AND id_formulario = %s
                            """,
                            (pregunta_texto, tipo, tipo_pregunta, imagen_url, video_url, es_calificable, estado, target_qid, id_formulario)
                        )
                    else:
                        # Insertar nueva pregunta
                        cursor.execute(
                            """
                            INSERT INTO preguntas (id_formulario, pregunta, tipo_respuesta, tipo_pregunta, imagen_url, video_url, es_calificable, estado, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            """,
                            (id_formulario, pregunta_texto, tipo, tipo_pregunta, imagen_url, video_url, es_calificable, estado)
                        )
                        target_qid = cursor.lastrowid

                    # Sincronizar opciones de esta pregunta
                    cursor.execute("SELECT id FROM opciones_formulario WHERE id_pregunta = %s", (target_qid,))
                    opc_db = cursor.fetchall() or []
                    ids_opc_db = {o["id"] for o in opc_db}

                    ids_opc_incoming = {
                        int(o["id"]) for o in opciones
                        if o.get("id") and int(o["id"]) in ids_opc_db
                    }

                    ids_opc_del = ids_opc_db - ids_opc_incoming
                    if ids_opc_del:
                        ph_opc = ",".join(["%s"] * len(ids_opc_del))
                        cursor.execute(
                            f"DELETE FROM opciones_formulario WHERE id IN ({ph_opc}) AND id_pregunta = %s",
                            tuple(list(ids_opc_del) + [target_qid])
                        )

                    for o in opciones:
                        opc_texto = str(o.get("opcion") or "").strip()
                        if not opc_texto:
                            continue
                        is_corr = 1 if o.get("is_correct") else 0
                        o_id = o.get("id")

                        if o_id and int(o_id) in ids_opc_db:
                            cursor.execute(
                                """
                                UPDATE opciones_formulario
                                SET opcion = %s, is_correct = %s, updated_at = NOW()
                                WHERE id = %s AND id_pregunta = %s
                                """,
                                (opc_texto, is_corr, int(o_id), target_qid)
                            )
                        else:
                            cursor.execute(
                                """
                                INSERT INTO opciones_formulario (id_pregunta, opcion, is_correct, created_at)
                                VALUES (%s, %s, %s, NOW())
                                """,
                                (target_qid, opc_texto, is_corr)
                            )

                conexion.commit()
                return {
                    "exito": True,
                    "mensaje": f"Se sincronizaron {len(preguntas_list)} preguntas exitosamente.",
                    "total": len(preguntas_list)
                }
    except Exception as e:
        print(f"❌ Error al sincronizar preguntas del formulario #{id_formulario}: {e}")
        return {"exito": False, "mensaje": f"Error al sincronizar preguntas: {str(e)}"}


def CALCULAR_Y_REGISTRAR_EVALUACION_DB(
    id_formulario: int,
    id_persona: int,
    respuestas: List[dict]
) -> Dict[str, Any]:
    """
    Evalúa las respuestas de un cuestionario presentado por una persona:
    - Base de puntaje: Cada pregunta equivale a 1.0 punto base.
    - Preguntas abiertas (TEXTO / ABIERTA): Se les otorga automáticamente 1.0 punto (sin requerir auditor manual).
    - Preguntas de selección única / V/F: 1.0 punto si acertó, 0.0 si no.
    - Preguntas múltiples (MULTIPLE): El punto se divide equitativamente entre las respuestas correctas
      (ej. 2 correctas = 0.5 pts por acierto; 3 correctas = ~0.33 pts por acierto).
    - Aprobación: (total_puntos / total_preguntas) * 100 >= 80%.
    - Inserta resultado en resultados_formulario.
    - Si aprueba: actualiza o crea vigencia (+1 año) en inducciones y evalúa auto-aprobación GESCO.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Verificar formulario
                cursor.execute(
                    "SELECT id, nombre, vigencia, tipo_personal FROM formularioGesco WHERE id = %s",
                    (id_formulario,)
                )
                form = cursor.fetchone()
                if not form:
                    return {"exito": False, "mensaje": f"Formulario #{id_formulario} no encontrado."}

                # 2. Verificar persona
                cursor.execute(
                    "SELECT id, nombre, apellido, identificacion FROM personas WHERE id = %s",
                    (id_persona,)
                )
                persona = cursor.fetchone()
                if not persona:
                    return {"exito": False, "mensaje": f"Persona #{id_persona} no encontrada."}

                if not respuestas:
                    return {"exito": False, "mensaje": "No se recibieron respuestas para evaluar."}

                # 3. Identificar preguntas evaluadas (únicas por id_pregunta)
                ids_preguntas = list(dict.fromkeys(
                    int(r.get("id_pregunta")) for r in respuestas if r.get("id_pregunta")
                ))
                if not ids_preguntas:
                    return {"exito": False, "mensaje": "Las respuestas enviadas no contienen identificadores de pregunta válidos."}

                total_preguntas = len(ids_preguntas)
                ph_preg = ",".join(["%s"] * total_preguntas)

                # Consultar metadata de las preguntas (tipo_respuesta, tipo_pregunta, es_calificable)
                cursor.execute(
                    f"SELECT id, tipo_respuesta, tipo_pregunta, es_calificable FROM preguntas WHERE id IN ({ph_preg})",
                    tuple(ids_preguntas)
                )
                preguntas_db = cursor.fetchall() or []
                preguntas_map = {p["id"]: p for p in preguntas_db}

                # Consultar todas las opciones de estas preguntas
                cursor.execute(
                    f"SELECT id, id_pregunta, opcion, is_correct FROM opciones_formulario WHERE id_pregunta IN ({ph_preg})",
                    tuple(ids_preguntas)
                )
                todas_opciones = cursor.fetchall() or []

                # Mapear opciones correctas por pregunta: {id_pregunta: set of correct id_opciones}
                correctas_por_pregunta: Dict[int, set] = {pid: set() for pid in ids_preguntas}
                for opc in todas_opciones:
                    if opc.get("is_correct"):
                        correctas_por_pregunta[opc["id_pregunta"]].add(opc["id"])

                # Mapear respuestas enviadas por pregunta
                respuestas_por_pregunta: Dict[int, List[dict]] = {pid: [] for pid in ids_preguntas}
                for r in respuestas:
                    pid = int(r.get("id_pregunta") or 0)
                    if pid in respuestas_por_pregunta:
                        respuestas_por_pregunta[pid].append(r)

                puntos_totales = 0.0
                total_calificables = 0
                respuestas_detalle_a_guardar = []

                for pid in ids_preguntas:
                    p_info = preguntas_map.get(pid, {})
                    tipo_resp = (p_info.get("tipo_respuesta") or "MULTIPLE").strip().upper()
                    es_calif = bool(p_info.get("es_calificable", True) if p_info.get("es_calificable") is not None else True)
                    user_resps = respuestas_por_pregunta.get(pid, [])

                    if es_calif:
                        total_calificables += 1

                    # CASO A: Pregunta abierta (TEXTO / ABIERTA)
                    if tipo_resp in ["TEXTO", "ABIERTA"]:
                        texto_resp = ""
                        for ur in user_resps:
                            if ur.get("texto_respuesta"):
                                texto_resp = str(ur["texto_respuesta"]).strip()
                                break
                        tiene_texto = bool(texto_resp)
                        puntos_pregunta = 1.0 if tiene_texto else 0.0
                        es_acierto = 1 if tiene_texto else 0
                        if es_calif:
                            puntos_totales += puntos_pregunta

                        respuestas_detalle_a_guardar.append({
                            "id_pregunta": pid,
                            "id_opcion": None,
                            "texto_respuesta": texto_resp or None,
                            "es_acierto": es_acierto,
                            "puntos_obtenidos": puntos_pregunta
                        })
                        continue

                    # CASO B: Preguntas con opciones de selección
                    correctas = correctas_por_pregunta.get(pid, set())
                    opciones_seleccionadas = set()
                    for ur in user_resps:
                        if ur.get("id_opcion"):
                            opciones_seleccionadas.add(int(ur["id_opcion"]))

                    if tipo_resp in ["UNICA", "VERDADERO_FALSO"]:
                        # 1.0 punto si seleccionó la opción correcta, 0 si no
                        acerto = bool(opciones_seleccionadas and opciones_seleccionadas.issubset(correctas))
                        puntos_pregunta = 1.0 if acerto else 0.0
                        es_acierto = 1 if acerto else 0
                        if es_calif:
                            puntos_totales += puntos_pregunta

                    elif tipo_resp == "MULTIPLE":
                        k_correctas = len(correctas)
                        if k_correctas == 0:
                            puntos_pregunta = 1.0 if opciones_seleccionadas else 0.0
                        else:
                            valor_por_acierto = 1.0 / k_correctas
                            aciertos = len(opciones_seleccionadas.intersection(correctas))
                            fallos = len(opciones_seleccionadas - correctas)
                            puntos_calc = max(0.0, min(1.0, (aciertos - fallos) * valor_por_acierto))
                            puntos_pregunta = round(puntos_calc, 2)
                        es_acierto = 1 if puntos_pregunta >= 1.0 else 0
                        if es_calif:
                            puntos_totales += puntos_pregunta

                    # Registrar detalle para analíticas
                    if opciones_seleccionadas:
                        for opc_id in opciones_seleccionadas:
                            respuestas_detalle_a_guardar.append({
                                "id_pregunta": pid,
                                "id_opcion": opc_id,
                                "texto_respuesta": None,
                                "es_acierto": es_acierto,
                                "puntos_obtenidos": puntos_pregunta
                            })
                    else:
                        respuestas_detalle_a_guardar.append({
                            "id_pregunta": pid,
                            "id_opcion": None,
                            "texto_respuesta": None,
                            "es_acierto": 0,
                            "puntos_obtenidos": 0.0
                        })

                # Redondear puntaje total y calcular porcentaje sobre las preguntas calificables
                puntos_totales = round(puntos_totales, 2)
                porcentaje = round((puntos_totales / total_calificables) * 100, 1) if total_calificables > 0 else 100.0
                aprobado = (porcentaje >= 80.0)

                puntos_str = f"{int(puntos_totales)}" if puntos_totales.is_integer() else f"{puntos_totales}"
                resultado_str = f"{puntos_str}/{total_calificables} ({porcentaje}%)"

                # 4. Insertar en resultados_formulario
                cursor.execute(
                    """
                    INSERT INTO resultados_formulario (id_persona, id_formulario, resultado, estado, fecha_realizacion)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (id_persona, id_formulario, resultado_str, 1 if aprobado else 0)
                )
                id_resultado_generado = cursor.lastrowid

                # 4b. Guardar cada respuesta individual en respuestas_usuario_formulario para analíticas
                if id_resultado_generado and respuestas_detalle_a_guardar:
                    for rd in respuestas_detalle_a_guardar:
                        cursor.execute(
                            """
                            INSERT INTO respuestas_usuario_formulario
                            (id_resultado, id_pregunta, id_opcion, texto_respuesta, es_acierto, puntos_obtenidos, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, NOW())
                            """,
                            (
                                id_resultado_generado,
                                rd["id_pregunta"],
                                rd["id_opcion"],
                                rd["texto_respuesta"],
                                rd["es_acierto"],
                                rd["puntos_obtenidos"]
                            )
                        )

                # 5. Si aprueba, registrar/actualizar vigencia en inducciones (+1 año o form.vigencia)
                vigencia_dias = int(form.get("vigencia") or 365)
                if aprobado:
                    # Obtener el creador del formulario como responsable de la inducción
                    cursor.execute(
                        """
                        SELECT COALESCE(
                            fg.creador_nombre,
                            CONCAT(u.nombres, ' ', COALESCE(u.apellidos, '')),
                            'Auditor GESCO'
                        ) AS creador_responsable
                        FROM formularioGesco fg
                        LEFT JOIN usuarios u ON fg.id_creador = u.id
                        WHERE fg.id = %s
                        """,
                        (id_formulario,)
                    )
                    fg_resp_row = cursor.fetchone()
                    responsable_form = fg_resp_row["creador_responsable"] if fg_resp_row and fg_resp_row.get("creador_responsable") else "Auditor GESCO"

                    cursor.execute(
                        """
                        SELECT id FROM inducciones WHERE id_persona = %s AND id_formulario = %s
                        """,
                        (id_persona, id_formulario)
                    )
                    ind_existente = cursor.fetchone()
                    if ind_existente:
                        cursor.execute(
                            """
                            UPDATE inducciones
                            SET fecha_induccion = CURDATE(),
                                fecha_vigencia = DATE_ADD(CURDATE(), INTERVAL %s DAY),
                                responsable = %s,
                                fecha_creacion = NOW()
                            WHERE id = %s
                            """,
                            (vigencia_dias, responsable_form, ind_existente["id"])
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO inducciones (id_persona, id_empresa, id_formulario, responsable, fecha_induccion, fecha_vigencia, fecha_creacion)
                            VALUES (%s, NULL, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL %s DAY), NOW())
                            """,
                            (id_persona, id_formulario, responsable_form, vigencia_dias)
                        )

                    # 6. Evaluar auto-aprobación GESCO para cualquier solicitud activa de esta persona
                    try:
                        cursor.execute(
                            """
                            SELECT s.id, s.tipo_personal
                            FROM solicitudes s
                            INNER JOIN ingresantes ing ON ing.id_solicitud = s.id
                            WHERE ing.id_persona = %s AND s.estado NOT IN ('Aprobada', 'Rechazada', 'Cancelada')
                            GROUP BY s.id
                            """,
                            (id_persona,)
                        )
                        solicitudes_afectadas = cursor.fetchall() or []
                        from src.loaders.formulario_gesco_loader import EVALUAR_Y_APLICAR_AUTO_APROBACION_GESCO
                        for sol in solicitudes_afectadas:
                            EVALUAR_Y_APLICAR_AUTO_APROBACION_GESCO(
                                cursor,
                                id_solicitud=sol["id"],
                                tipo_personal=sol.get("tipo_personal") or "Contratista"
                            )
                    except Exception as auto_err:
                        print(f"⚠️ Aviso evaluando auto-aprobación GESCO tras aprobación de inducción: {auto_err}")

                conexion.commit()

                return {
                    "exito": True,
                    "aprobado": aprobado,
                    "aciertos": puntos_str,
                    "total": total_preguntas,
                    "porcentaje": porcentaje,
                    "resultado": resultado_str,
                    "mensaje": (
                        f"¡Felicitaciones! Has aprobado la inducción con {resultado_str}. Tu vigencia de inducción ha sido activada exitosamente."
                        if aprobado
                        else f"No has alcanzado el puntaje mínimo de aprobación (80%). Obtuviste {resultado_str}. Puedes intentarlo nuevamente."
                    )
                }
    except Exception as e:
        print(f"❌ Error al calificar y registrar evaluación del formulario #{id_formulario}: {e}")
        return {"exito": False, "mensaje": f"Error al calificar evaluación: {str(e)}"}


def SIMULAR_EVALUACION_DB(id_formulario: int, respuestas: List[dict]) -> dict:
    """
    Simula la calificación de una evaluación GESCO en memoria (Modo Prueba).
    - Valida respuestas contra el banco de preguntas.
    - Aplica las mismas reglas de calificación que producción (80% para aprobar, abierto = 1.0, múltiple proporcional).
    - Entrega un desglose detallado de cada pregunta (aciertos, fallos, opciones correctas).
    - NO inserta ni modifica nada en inducciones, solicitudes ni resultados_formulario.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Verificar formulario
                cursor.execute(
                    "SELECT id, nombre, vigencia, cantidad_preguntas, config_cuotas FROM formularioGesco WHERE id = %s",
                    (id_formulario,)
                )
                form = cursor.fetchone()
                if not form:
                    return {"exito": False, "mensaje": f"Formulario #{id_formulario} no encontrado."}

                if not respuestas:
                    return {"exito": False, "mensaje": "No se recibieron respuestas para simular la evaluación."}

                # 2. Identificar preguntas evaluadas
                ids_preguntas = list(dict.fromkeys(
                    int(r.get("id_pregunta")) for r in respuestas if r.get("id_pregunta")
                ))
                if not ids_preguntas:
                    return {"exito": False, "mensaje": "Las respuestas enviadas no contienen identificadores válidos."}

                total_preguntas = len(ids_preguntas)
                ph_preg = ",".join(["%s"] * total_preguntas)

                # Consultar metadata de las preguntas (incluyendo multimedia y calificable)
                cursor.execute(
                    f"SELECT id, pregunta, tipo_respuesta, tipo_pregunta, imagen_url, video_url, es_calificable FROM preguntas WHERE id IN ({ph_preg})",
                    tuple(ids_preguntas)
                )
                preguntas_db = cursor.fetchall() or []
                preguntas_map = {p["id"]: p for p in preguntas_db}

                # Identificar cuántas son calificables
                calificables_pids = [
                    pid for pid in ids_preguntas
                    if bool(preguntas_map.get(pid, {}).get("es_calificable", 1))
                ]
                total_calificables = len(calificables_pids)

                # Consultar todas las opciones
                cursor.execute(
                    f"SELECT id, id_pregunta, opcion, is_correct FROM opciones_formulario WHERE id_pregunta IN ({ph_preg})",
                    tuple(ids_preguntas)
                )
                todas_opciones = cursor.fetchall() or []

                opciones_por_pregunta: Dict[int, List[dict]] = {pid: [] for pid in ids_preguntas}
                correctas_por_pregunta: Dict[int, set] = {pid: set() for pid in ids_preguntas}
                for opc in todas_opciones:
                    pid = opc["id_pregunta"]
                    if pid in opciones_por_pregunta:
                        opciones_por_pregunta[pid].append(opc)
                    if opc.get("is_correct"):
                        correctas_por_pregunta[pid].add(opc["id"])

                respuestas_por_pregunta: Dict[int, List[dict]] = {pid: [] for pid in ids_preguntas}
                for r in respuestas:
                    pid = int(r.get("id_pregunta") or 0)
                    if pid in respuestas_por_pregunta:
                        respuestas_por_pregunta[pid].append(r)

                puntos_totales = 0.0
                desglose = []

                for pid in ids_preguntas:
                    p_info = preguntas_map.get(pid, {})
                    tipo_resp = (p_info.get("tipo_respuesta") or "MULTIPLE").strip().upper()
                    es_calificable = bool(p_info.get("es_calificable", 1))
                    user_resps = respuestas_por_pregunta.get(pid, [])
                    correctas = correctas_por_pregunta.get(pid, set())
                    todas_opcs_p = opciones_por_pregunta.get(pid, [])

                    opciones_seleccionadas = set()
                    texto_ingresado = None
                    for ur in user_resps:
                        if ur.get("id_opcion"):
                            opciones_seleccionadas.add(int(ur["id_opcion"]))
                        if ur.get("texto_respuesta"):
                            texto_ingresado = ur.get("texto_respuesta")

                    puntos_pregunta = 0.0
                    if not es_calificable:
                        puntos_pregunta = 0.0
                    elif tipo_resp in ["TEXTO", "ABIERTA"]:
                        puntos_pregunta = 1.0 if (texto_ingresado and str(texto_ingresado).strip()) else 0.0
                    elif tipo_resp in ["UNICA", "VERDADERO_FALSO"]:
                        if opciones_seleccionadas and opciones_seleccionadas.issubset(correctas):
                            puntos_pregunta = 1.0
                    elif tipo_resp == "MULTIPLE":
                        k_correctas = len(correctas)
                        if k_correctas == 0:
                            puntos_pregunta = 1.0 if opciones_seleccionadas else 0.0
                        else:
                            valor_por_acierto = 1.0 / k_correctas
                            aciertos = len(opciones_seleccionadas.intersection(correctas))
                            fallos = len(opciones_seleccionadas - correctas)
                            puntos_calc = max(0.0, min(1.0, (aciertos - fallos) * valor_por_acierto))
                            puntos_pregunta = round(puntos_calc, 2)

                    if es_calificable:
                        puntos_totales += puntos_pregunta

                    desglose.append({
                        "id_pregunta": pid,
                        "enunciado": p_info.get("pregunta"),
                        "tipo_respuesta": tipo_resp,
                        "tipo_pregunta": p_info.get("tipo_pregunta"),
                        "imagen_url": p_info.get("imagen_url"),
                        "video_url": p_info.get("video_url"),
                        "es_calificable": es_calificable,
                        "puntos_obtenidos": puntos_pregunta,
                        "es_correcta": (puntos_pregunta >= 1.0) if es_calificable else True,
                        "es_parcial": (0.0 < puntos_pregunta < 1.0) if es_calificable else False,
                        "correctas_ids": list(correctas),
                        "seleccionadas_ids": list(opciones_seleccionadas),
                        "texto_ingresado": texto_ingresado,
                        "opciones": [
                            {
                                "id": o["id"],
                                "opcion": o["opcion"],
                                "is_correct": bool(o["is_correct"]),
                                "seleccionada": o["id"] in opciones_seleccionadas
                            }
                            for o in todas_opcs_p
                        ]
                    })

                puntos_totales = round(puntos_totales, 2)
                porcentaje = (
                    round((puntos_totales / total_calificables) * 100, 1)
                    if total_calificables > 0
                    else 100.0
                )
                aprobado = (porcentaje >= 80.0)
                puntos_str = f"{int(puntos_totales)}" if puntos_totales.is_integer() else f"{puntos_totales}"
                resultado_str = f"{puntos_str}/{total_calificables} ({porcentaje}%)" if total_calificables > 0 else f"{puntos_str}/0 (Informativo)"

                return {
                    "exito": True,
                    "simulacion": True,
                    "aprobado": aprobado,
                    "aciertos": puntos_str,
                    "total": total_calificables,
                    "total_preguntas": total_preguntas,
                    "total_calificables": total_calificables,
                    "porcentaje": porcentaje,
                    "resultado": resultado_str,
                    "desglose": desglose,
                    "mensaje": (
                        f"Simulación finalizada: Puntaje de {resultado_str} — APROBADO"
                        if aprobado
                        else f"Simulación finalizada: Puntaje de {resultado_str} — NO APROBADO"
                    )
                }
    except Exception as e:
        print(f"❌ Error en SIMULAR_EVALUACION_DB #{id_formulario}: {e}")
        return {"exito": False, "mensaje": f"Error al simular evaluación: {str(e)}"}


def GET_estadisticas_formulario_db(id_formulario: int) -> Dict[str, Any]:
    """
    Calcula y compila estadísticas analíticas detalladas de un formulario GESCO:
    - Métricas globales de presentación (evaluaciones realizadas, personas evaluadas, aprobados, reprobados, % aprobación).
    - Métricas por cada pregunta:
        * Total de veces respondida
        * Porcentaje de acierto y tasa de error
        * Indicador si es calificable o informativa
        * Conteo de selecciones por cada opción (con porcentaje relativo de respuestas)
        * Clave correcta marcada
        * Muestra de respuestas abiertas/texto
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Metadatos del formulario
                cursor.execute(
                    "SELECT id, nombre, descripcion, vigencia, tipo_personal, Tipo_pregunta, is_active FROM formularioGesco WHERE id = %s",
                    (id_formulario,)
                )
                form_meta = cursor.fetchone()
                if not form_meta:
                    return {"exito": False, "mensaje": f"El formulario #{id_formulario} no existe."}

                # 2. Métricas globales de evaluaciones en resultados_formulario
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_evaluaciones,
                        COUNT(DISTINCT id_persona) as total_personas,
                        SUM(CASE WHEN estado = 1 THEN 1 ELSE 0 END) as total_aprobados,
                        SUM(CASE WHEN estado = 0 THEN 1 ELSE 0 END) as total_reprobados
                    FROM resultados_formulario
                    WHERE id_formulario = %s
                    """,
                    (id_formulario,)
                )
                metricas_globales = cursor.fetchone() or {
                    "total_evaluaciones": 0,
                    "total_personas": 0,
                    "total_aprobados": 0,
                    "total_reprobados": 0
                }

                total_evaluaciones = int(metricas_globales.get("total_evaluaciones") or 0)
                total_personas = int(metricas_globales.get("total_personas") or 0)
                total_aprobados = int(metricas_globales.get("total_aprobados") or 0)
                total_reprobados = int(metricas_globales.get("total_reprobados") or 0)
                porcentaje_aprobacion = round((total_aprobados / total_evaluaciones) * 100, 1) if total_evaluaciones > 0 else 0.0

                # 3. Consultar preguntas del formulario
                cursor.execute(
                    """
                    SELECT id, pregunta, tipo_respuesta, tipo_pregunta, imagen_url, video_url, es_calificable, estado
                    FROM preguntas
                    WHERE id_formulario = %s AND (estado = 1 OR estado IS NULL)
                    ORDER BY id ASC
                    """,
                    (id_formulario,)
                )
                preguntas_db = cursor.fetchall() or []

                if not preguntas_db:
                    return {
                        "exito": True,
                        "formulario": {
                            "id": form_meta["id"],
                            "titulo": form_meta["nombre"],
                            "nombre": form_meta["nombre"],
                            "descripcion": form_meta.get("descripcion"),
                            "vigencia": form_meta.get("vigencia"),
                            "tipo_personal": form_meta.get("tipo_personal"),
                            "is_active": bool(form_meta.get("is_active"))
                        },
                        "resumen": {
                            "total_evaluaciones": total_evaluaciones,
                            "total_personas": total_personas,
                            "total_aprobados": total_aprobados,
                            "total_reprobados": total_reprobados,
                            "porcentaje_aprobacion": porcentaje_aprobacion,
                            "total_preguntas": 0
                        },
                        "estadisticas_preguntas": []
                    }

                ids_preguntas = [p["id"] for p in preguntas_db]
                ph_preg = ",".join(["%s"] * len(ids_preguntas))

                # 4. Consultar opciones
                cursor.execute(
                    f"""
                    SELECT id, id_pregunta, opcion, is_correct
                    FROM opciones_formulario
                    WHERE id_pregunta IN ({ph_preg})
                    ORDER BY id ASC
                    """,
                    tuple(ids_preguntas)
                )
                todas_opciones = cursor.fetchall() or []
                opciones_por_pregunta: Dict[int, List[dict]] = {pid: [] for pid in ids_preguntas}
                for opc in todas_opciones:
                    pid = opc["id_pregunta"]
                    if pid in opciones_por_pregunta:
                        opciones_por_pregunta[pid].append(opc)

                # 5. Estadísticas de respuestas en respuestas_usuario_formulario
                cursor.execute(
                    f"""
                    SELECT 
                        id_pregunta,
                        COUNT(DISTINCT id_resultado) as veces_respondida,
                        SUM(CASE WHEN es_acierto = 1 THEN 1 ELSE 0 END) as veces_acierto,
                        SUM(CASE WHEN es_acierto = 0 THEN 1 ELSE 0 END) as veces_fallo,
                        AVG(puntos_obtenidos) as promedio_puntos
                    FROM respuestas_usuario_formulario
                    WHERE id_pregunta IN ({ph_preg})
                    GROUP BY id_pregunta
                    """,
                    tuple(ids_preguntas)
                )
                stats_preguntas_rows = cursor.fetchall() or []
                stats_preg_map = {row["id_pregunta"]: row for row in stats_preguntas_rows}

                # 6. Conteo de selecciones por opción
                cursor.execute(
                    f"""
                    SELECT id_pregunta, id_opcion, COUNT(*) as conteo_votos
                    FROM respuestas_usuario_formulario
                    WHERE id_pregunta IN ({ph_preg}) AND id_opcion IS NOT NULL
                    GROUP BY id_pregunta, id_opcion
                    """,
                    tuple(ids_preguntas)
                )
                votos_opciones_rows = cursor.fetchall() or []
                votos_map: Dict[int, int] = {row["id_opcion"]: int(row["conteo_votos"]) for row in votos_opciones_rows}

                # 7. Respuestas abiertas / texto
                cursor.execute(
                    f"""
                    SELECT id_pregunta, texto_respuesta, created_at
                    FROM respuestas_usuario_formulario
                    WHERE id_pregunta IN ({ph_preg}) 
                      AND texto_respuesta IS NOT NULL 
                      AND TRIM(texto_respuesta) != ''
                    ORDER BY id DESC
                    LIMIT 200
                    """,
                    tuple(ids_preguntas)
                )
                textos_rows = cursor.fetchall() or []
                textos_por_pregunta: Dict[int, List[dict]] = {pid: [] for pid in ids_preguntas}
                for tr in textos_rows:
                    pid = tr["id_pregunta"]
                    if pid in textos_por_pregunta and len(textos_por_pregunta[pid]) < 20:
                        textos_por_pregunta[pid].append({
                            "texto": tr["texto_respuesta"],
                            "fecha": _formatear_fecha(tr["created_at"])
                        })

                # 8. Ensamblar lista de estadísticas por pregunta
                lista_estadisticas = []
                for p in preguntas_db:
                    pid = p["id"]
                    tipo_resp = (p.get("tipo_respuesta") or "MULTIPLE").strip().upper()
                    es_calificable = bool(p.get("es_calificable", 1))
                    preg_stat = stats_preg_map.get(pid, {})

                    veces_respondida = int(preg_stat.get("veces_respondida") or 0)
                    aciertos = int(preg_stat.get("veces_acierto") or 0)
                    fallos = int(preg_stat.get("veces_fallo") or 0)
                    promedio_puntos = round(float(preg_stat.get("promedio_puntos") or 0.0), 2)

                    if veces_respondida > 0:
                        porcentaje_acierto = round((aciertos / veces_respondida) * 100, 1)
                        porcentaje_fallo = round((fallos / veces_respondida) * 100, 1)
                    else:
                        porcentaje_acierto = 0.0
                        porcentaje_fallo = 0.0

                    opcs_preg = opciones_por_pregunta.get(pid, [])
                    total_votos_pregunta = sum(votos_map.get(o["id"], 0) for o in opcs_preg)

                    opciones_stats = []
                    for o in opcs_preg:
                        oid = o["id"]
                        votos = votos_map.get(oid, 0)
                        pct_opc = (
                            round((votos / veces_respondida) * 100, 1)
                            if veces_respondida > 0
                            else (round((votos / total_votos_pregunta) * 100, 1) if total_votos_pregunta > 0 else 0.0)
                        )
                        opciones_stats.append({
                            "id": oid,
                            "opcion": o["opcion"],
                            "is_correct": bool(o["is_correct"]),
                            "votos": votos,
                            "porcentaje": pct_opc
                        })

                    lista_estadisticas.append({
                        "id_pregunta": pid,
                        "enunciado": p["pregunta"],
                        "tipo_respuesta": tipo_resp,
                        "tipo_pregunta": p.get("tipo_pregunta"),
                        "imagen_url": p.get("imagen_url"),
                        "video_url": p.get("video_url"),
                        "es_calificable": es_calificable,
                        "veces_respondida": veces_respondida,
                        "aciertos": aciertos,
                        "fallos": fallos,
                        "promedio_puntos": promedio_puntos,
                        "porcentaje_acierto": porcentaje_acierto,
                        "porcentaje_fallo": porcentaje_fallo,
                        "opciones": opciones_stats,
                        "respuestas_abiertas": textos_por_pregunta.get(pid, [])
                    })

                return {
                    "exito": True,
                    "formulario": {
                        "id": form_meta["id"],
                        "titulo": form_meta["nombre"],
                        "nombre": form_meta["nombre"],
                        "descripcion": form_meta.get("descripcion"),
                        "vigencia": form_meta.get("vigencia"),
                        "tipo_personal": form_meta.get("tipo_personal"),
                        "is_active": bool(form_meta.get("is_active"))
                    },
                    "resumen": {
                        "total_evaluaciones": total_evaluaciones,
                        "total_personas": total_personas,
                        "total_aprobados": total_aprobados,
                        "total_reprobados": total_reprobados,
                        "porcentaje_aprobacion": porcentaje_aprobacion,
                        "total_preguntas": len(preguntas_db)
                    },
                    "estadisticas_preguntas": lista_estadisticas
                }
    except Exception as e:
        print(f"[ERROR] Error en GET_estadisticas_formulario_db #{id_formulario}: {e}")
        return {"exito": False, "mensaje": f"Error al obtener estadísticas del formulario: {str(e)}"}


