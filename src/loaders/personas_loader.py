from database import GET_conexion


def CREATE_person_db(person: dict) -> dict:

    try:

        with GET_conexion() as conexion:

            with conexion.cursor() as cursor:

                sql_person = """
                    INSERT INTO personas (
                        nombre, apellido, tipo_doc, identificacion, cargo, observacion
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """
                valores_person = (
                    person.get("nombre", ""),
                    person.get("apellido", ""),
                    person.get("tipo_doc", ""),
                    person.get("identificacion", ""),
                    person.get("cargo", ""),
                    person.get("observacion", "")
                )

                cursor.execute(sql_person, valores_person)
                person_id = cursor.lastrowid

                documentos = person.get("documentos_ids", [])
                if documentos:
                    sql_docs = """
                        INSERT INTO documentos_persona (persona_id, tipo_doc, nombre_archivo)
                        VALUES (%s, %s, %s)
                    """
                    valores_docs = [
                        (person_id, doc.get("tipo_doc", ""), doc.get("nombre_archivo", ""))
                        for doc in documentos
                    ]
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
                        p.observacion
                    FROM personas p
                    ORDER BY p.id DESC
                """)

                datos_person = cursor.fetchall()

                # Opcional: Obtener documentos de cada persona si existen
                cursor.execute("SELECT persona_id, tipo_doc, nombre_archivo FROM documentos_persona")
                docs_db = cursor.fetchall()
                docs_por_persona = {}
                for doc in docs_db:
                    pid = doc["persona_id"]
                    if pid not in docs_por_persona:
                        docs_por_persona[pid] = []
                    docs_por_persona[pid].append({
                        "tipo_doc": doc["tipo_doc"],
                        "nombre_archivo": doc["nombre_archivo"]
                    })

                for p in datos_person:
                    p["documentos"] = docs_por_persona.get(p["id"], [])

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