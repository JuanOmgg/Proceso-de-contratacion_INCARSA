from database import GET_conexion
from src.utils.file_manager import eliminar_documento_fisico


def CREATE_person_db(person: dict) -> dict:

    try:

        with GET_conexion() as conexion:

            with conexion.cursor() as cursor:
                correo = str(person.get("correo") or "").strip().lower()
                if not correo:
                    return {
                        "exito": False,
                        "mensaje": "El correo electrónico es obligatorio.",
                    }

                identificacion = str(person.get("identificacion") or "").strip()
                if not identificacion:
                    return {
                        "exito": False,
                        "mensaje": "El número de documento de identificación es obligatorio.",
                    }

                # Validar que no exista otra persona con el mismo documento
                cursor.execute(
                    "SELECT id, nombre, apellido FROM personas WHERE identificacion = %s LIMIT 1",
                    (identificacion,)
                )
                persona_existente = cursor.fetchone()
                if persona_existente:
                    nombre_exist = f"{persona_existente.get('nombre', '')} {persona_existente.get('apellido', '')}".strip()
                    return {
                        "exito": False,
                        "mensaje": f"Ya existe una persona registrada con el documento {identificacion} ({nombre_exist}). No se permiten duplicados.",
                    }

                sql_person = """
                    INSERT INTO personas (
                        nombre, apellido, tipo_doc, identificacion, cargo, observacion, correo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                valores_person = (
                    person.get("nombre", ""),
                    person.get("apellido", ""),
                    person.get("tipo_doc", ""),
                    person.get("identificacion", ""),
                    person.get("cargo", ""),
                    person.get("observacion", ""),
                    correo
                )

                cursor.execute(sql_person, valores_person)
                person_id = cursor.lastrowid

                documentos = person.get("documentos_ids", [])
                if documentos:
                    sql_docs = """
                        INSERT INTO documentos_persona (persona_id, tipo_doc, nombre_archivo, vigencia)
                        VALUES (%s, %s, %s, %s)
                    """
                    valores_docs = [
                        (person_id, doc.get("tipo_doc", ""), doc.get("nombre_archivo", ""), doc.get("vigencia") or None)
                        for doc in documentos if isinstance(doc, dict) and doc.get("nombre_archivo")
                    ]
                    if valores_docs:
                        cursor.executemany(sql_docs, valores_docs)

                conexion.commit()

        print(f"La persona {person_id} fue registrada con éxito.")
        return {
            "exito": True,
            "mensaje": "Persona guardada exitosamente.",
            "persona": person_id,
        }

    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"Error en la base de datos: {e}",
        }

def GET_ALL_person_db() -> dict:
    
    try:

        with GET_conexion() as conexion:

            with conexion.cursor() as cursor:

                cursor.execute("""
                    SELECT
                        p.id,
                        p.nombre,
                        p.apellido,
                        p.tipo_doc,
                        p.identificacion,
                        p.cargo,
                        p.correo,
                        p.observacion,
                        p.fecha_creacion
                    FROM personas p
                    ORDER BY p.id DESC
                """)

                datos_person = cursor.fetchall()

                # Obtener documentos de cada persona si existen
                cursor.execute("SELECT id, persona_id, tipo_doc, nombre_archivo, vigencia FROM documentos_persona")
                docs_db = cursor.fetchall()
                docs_por_persona = {}
                for doc in docs_db:
                    pid = doc["persona_id"]
                    if pid not in docs_por_persona:
                        docs_por_persona[pid] = []
                    docs_por_persona[pid].append({
                        "id": doc.get("id"),
                        "tipo_doc": doc["tipo_doc"],
                        "nombre_archivo": doc["nombre_archivo"],
                        "vigencia": doc.get("vigencia").isoformat() if hasattr(doc.get("vigencia"), "isoformat") else (str(doc.get("vigencia")) if doc.get("vigencia") else None),
                        "url_acceso": f"/uploads/documentos/{doc['nombre_archivo']}"
                    })

                for p in datos_person:
                    p["documentos"] = docs_por_persona.get(p["id"], [])
                    if p.get("fecha_creacion"):
                        p["fecha_creacion"] = p["fecha_creacion"].isoformat() if hasattr(p["fecha_creacion"], "isoformat") else str(p["fecha_creacion"])

                print(f"Se recuperaron {len(datos_person)} personas de la base de datos.")

                return {
                    "exito": True,
                    "mensaje": "Personas encontradas con éxito",
                    "datos_person": datos_person,
                    "datos": datos_person
                }

    except Exception as e:
        return {
            "exito": False,
            "mensaje": f"No fue posible encontrar a las personas: {e}"
        }

def GET_person_by_id_db(persona_id: int) -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        p.id,
                        p.nombre,
                        p.apellido,
                        p.tipo_doc,
                        p.identificacion,
                        p.cargo,
                        p.correo,
                        p.observacion,
                        p.fecha_creacion
                    FROM personas p
                    WHERE p.id = %s
                """, (persona_id,))
                p = cursor.fetchone()
                if not p:
                    return {"exito": False, "mensaje": f"Persona con ID {persona_id} no encontrada."}

                cursor.execute("SELECT id, tipo_doc, nombre_archivo, vigencia FROM documentos_persona WHERE persona_id = %s", (persona_id,))
                docs = cursor.fetchall() or []
                for d in docs:
                    d["url_acceso"] = f"/uploads/documentos/{d['nombre_archivo']}"
                    if d.get("vigencia"):
                        d["vigencia"] = d["vigencia"].isoformat() if hasattr(d["vigencia"], "isoformat") else str(d["vigencia"])
                p["documentos"] = docs
                if p.get("fecha_creacion"):
                    p["fecha_creacion"] = p["fecha_creacion"].isoformat() if hasattr(p["fecha_creacion"], "isoformat") else str(p["fecha_creacion"])

                return {"exito": True, "datos": p, "persona": p}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error en la base de datos: {e}"}

def UPDATE_person_db(persona_id: int, person: dict) -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                if "correo" in person and not str(person.get("correo") or "").strip():
                    return {
                        "exito": False,
                        "mensaje": "El correo electrónico es obligatorio.",
                    }

                # Si se actualiza la identificación, validar que no pertenezca a otra persona
                identificacion = str(person.get("identificacion") or "").strip()
                if identificacion:
                    cursor.execute(
                        "SELECT id, nombre, apellido FROM personas WHERE identificacion = %s AND id != %s LIMIT 1",
                        (identificacion, persona_id)
                    )
                    otra_persona = cursor.fetchone()
                    if otra_persona:
                        nombre_otro = f"{otra_persona.get('nombre', '')} {otra_persona.get('apellido', '')}".strip()
                        return {
                            "exito": False,
                            "mensaje": f"El documento {identificacion} ya pertenece a otra persona registrada ({nombre_otro}).",
                        }

                sql_update = """
                    UPDATE personas SET
                        nombre = %s,
                        apellido = %s,
                        tipo_doc = %s,
                        identificacion = %s,
                        cargo = %s,
                        correo = %s,
                        observacion = %s
                    WHERE id = %s
                """
                valores = (
                    person.get("nombre", ""),
                    person.get("apellido", ""),
                    person.get("tipo_doc", ""),
                    person.get("identificacion", ""),
                    person.get("cargo", ""),
                    person.get("correo") or None,
                    person.get("observacion", ""),
                    persona_id
                )
                cursor.execute(sql_update, valores)

                documentos = person.get("documentos_ids", [])
                if documentos is not None and isinstance(documentos, list):
                    # 1. Consultar archivos actuales de la persona
                    cursor.execute("SELECT nombre_archivo FROM documentos_persona WHERE persona_id = %s", (persona_id,))
                    docs_existentes = cursor.fetchall() or []
                    archivos_actuales = {d["nombre_archivo"] for d in docs_existentes if d.get("nombre_archivo")}

                    # 2. Identificar los nuevos archivos recibidos
                    archivos_nuevos = {
                        doc.get("nombre_archivo") for doc in documentos 
                        if isinstance(doc, dict) and doc.get("nombre_archivo")
                    }

                    # 3. Eliminar físicamente del servidor los archivos removidos
                    archivos_a_eliminar = archivos_actuales - archivos_nuevos
                    for archivo in archivos_a_eliminar:
                        eliminar_documento_fisico(archivo)

                    # 4. Actualizar tabla documentos_persona
                    cursor.execute("DELETE FROM documentos_persona WHERE persona_id = %s", (persona_id,))
                    valores_docs = [
                        (persona_id, doc.get("tipo_doc", ""), doc.get("nombre_archivo", ""), doc.get("vigencia") or None)
                        for doc in documentos if isinstance(doc, dict) and doc.get("nombre_archivo")
                    ]
                    if valores_docs:
                        cursor.executemany(
                            "INSERT INTO documentos_persona (persona_id, tipo_doc, nombre_archivo, vigencia) VALUES (%s, %s, %s, %s)",
                            valores_docs
                        )

                conexion.commit()

        return {"exito": True, "mensaje": "Persona actualizada exitosamente."}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al actualizar en la base de datos: {e}"}

def DELETE_person_db(persona_id: int) -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Obtener lista de archivos asociados antes de eliminarlos de la BD
                cursor.execute("SELECT nombre_archivo FROM documentos_persona WHERE persona_id = %s", (persona_id,))
                docs = cursor.fetchall() or []

                # 2. Eliminar registros de la base de datos
                cursor.execute("DELETE FROM documentos_persona WHERE persona_id = %s", (persona_id,))
                cursor.execute("DELETE FROM personas WHERE id = %s", (persona_id,))
                conexion.commit()

                # 3. Eliminar archivos físicos del disco/servidor
                for d in docs:
                    if d.get("nombre_archivo"):
                        eliminar_documento_fisico(d["nombre_archivo"])

        return {"exito": True, "mensaje": f"Persona {persona_id} eliminada exitosamente."}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al eliminar persona: {e}"}

def DELETE_documento_persona_db(documento_id: int, persona_id: int = None) -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                if persona_id:
                    cursor.execute(
                        "SELECT nombre_archivo FROM documentos_persona WHERE id = %s AND persona_id = %s",
                        (documento_id, persona_id)
                    )
                else:
                    cursor.execute(
                        "SELECT nombre_archivo FROM documentos_persona WHERE id = %s",
                        (documento_id,)
                    )
                doc = cursor.fetchone()
                if not doc:
                    return {"exito": False, "mensaje": "Documento no encontrado en la base de datos."}

                archivo = doc.get("nombre_archivo")

                if persona_id:
                    cursor.execute(
                        "DELETE FROM documentos_persona WHERE id = %s AND persona_id = %s",
                        (documento_id, persona_id)
                    )
                else:
                    cursor.execute(
                        "DELETE FROM documentos_persona WHERE id = %s",
                        (documento_id,)
                    )
                conexion.commit()

                # Eliminar archivo físico del servidor
                if archivo:
                    eliminar_documento_fisico(archivo)

        return {"exito": True, "mensaje": "Documento de la persona eliminado exitosamente."}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al eliminar documento de la persona: {e}"}