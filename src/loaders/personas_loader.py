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