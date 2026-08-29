from database import GET_conexion
from typing import Dict, List, Any, Optional


def CREATE_vehiculo_db(vehiculo: dict) -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                placa = vehiculo.get("placa")
                # 0. Verificar si la placa ya existe en la base de datos
                cursor.execute("SELECT id, tipo, placa FROM vehiculos WHERE placa = %s", (placa,))
                vehi_existente = cursor.fetchone()
                if vehi_existente:
                    return {
                        "exito": False,
                        "duplicado": True,
                        "mensaje": f"El vehículo con placa '{placa}' ya se encuentra registrado con ID #{vehi_existente['id']}.",
                        "data": vehi_existente,
                    }

                # 1. Insertar el vehículo principal
                sql_vehi = """
                INSERT INTO vehiculos (tipo, placa)
                VALUES (%s, %s)
                """
                valores_vehiculo = (
                    vehiculo.get("tipo"),
                    placa,
                )
                cursor.execute(sql_vehi, valores_vehiculo)
                vehi_id = cursor.lastrowid

                # 2. Insertar documentos anidados en la tabla 'documentos_vehiculo'
                documentos = (
                    vehiculo.get("documentos")
                    or vehiculo.get("documentos_ids")
                    or []
                )
                docs_guardados = []

                if documentos:
                    sql_docs = """
                    INSERT INTO documentos_vehiculo (id_vehiculo, tipo_doc, nom_documento)
                    VALUES (%s, %s, %s)
                    """
                    for doc in documentos:
                        nom = doc.get("nom_documento") or doc.get("nombre_archivo")
                        t_doc = str(doc.get("tipo_doc") or "general").strip().lower()
                        if nom:
                            nom_limpio = str(nom).strip()
                            cursor.execute(sql_docs, (vehi_id, t_doc, nom_limpio))
                            doc_id = cursor.lastrowid
                            docs_guardados.append(
                                {
                                    "id": doc_id,
                                    "tipo_doc": t_doc,
                                    "nom_documento": nom_limpio,
                                    "url_acceso": f"/uploads/documentos/vehiculos/{nom_limpio}",
                                }
                            )

                conexion.commit()

                return {
                    "exito": True,
                    "mensaje": f"✅ Vehículo #{vehi_id} registrado con éxito con {len(docs_guardados)} documento(s).",
                    "data": {
                        "id": vehi_id,
                        "tipo": vehiculo.get("tipo"),
                        "placa": vehiculo.get("placa"),
                        "documentos": docs_guardados,
                    },
                }

    except Exception as e:
        print(f"❌ Error al guardar vehículo en la base de datos: {e}")
        return {
            "exito": False,
            "mensaje": f"Error en la base de datos: {e}",
        }


def GET_all_vehiculos_db() -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = """
                SELECT 
                    v.id, 
                    v.tipo, 
                    v.placa,
                    COALESCE(
                        (SELECT vi.licencia_doc FROM Veh_ingreso vi WHERE vi.id_vehiculo = v.id AND vi.licencia_doc IS NOT NULL AND vi.licencia_doc != '' ORDER BY vi.id_solicitud DESC LIMIT 1),
                        (SELECT dv.nom_documento FROM documentos_vehiculo dv WHERE dv.id_vehiculo = v.id AND (dv.tipo_doc LIKE '%licencia%' OR dv.tipo_doc = 'general') ORDER BY dv.id DESC LIMIT 1),
                        ''
                    ) AS licencia_doc
                FROM vehiculos v
                ORDER BY v.id DESC
                """
                cursor.execute(sql)
                vehiculos = cursor.fetchall() or []

                # Anidar los documentos correspondientes a cada vehículo
                for v in vehiculos:
                    cursor.execute(
                        """
                        SELECT id, tipo_doc, nom_documento 
                        FROM documentos_vehiculo 
                        WHERE id_vehiculo = %s
                        """,
                        (v["id"],),
                    )
                    docs = cursor.fetchall() or []
                    for d in docs:
                        d["url_acceso"] = f"/uploads/documentos/vehiculos/{d['nom_documento']}"
                    v["documentos"] = docs

                return {
                    "exito": True,
                    "datos": vehiculos,
                    "mensaje": "Vehículos recuperados con éxito.",
                }
    except Exception as e:
        print(f"❌ Error al obtener vehículos: {e}")
        return {
            "exito": False,
            "mensaje": f"Error en la base de datos: {e}",
            "datos": [],
        }


def GET_vehiculo_by_id_db(vehiculo_id: int) -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        v.id, 
                        v.tipo, 
                        v.placa,
                        COALESCE(
                            (SELECT vi.licencia_doc FROM Veh_ingreso vi WHERE vi.id_vehiculo = v.id AND vi.licencia_doc IS NOT NULL AND vi.licencia_doc != '' ORDER BY vi.id_solicitud DESC LIMIT 1),
                            (SELECT dv.nom_documento FROM documentos_vehiculo dv WHERE dv.id_vehiculo = v.id AND (dv.tipo_doc LIKE '%licencia%' OR dv.tipo_doc = 'general') ORDER BY dv.id DESC LIMIT 1),
                            ''
                        ) AS licencia_doc
                    FROM vehiculos v 
                    WHERE v.id = %s
                    """,
                    (vehiculo_id,),
                )
                vehiculo = cursor.fetchone()

                if not vehiculo:
                    return {
                        "exito": False,
                        "mensaje": f"Vehículo #{vehiculo_id} no encontrado.",
                    }

                # Documentos anidados
                cursor.execute(
                    """
                    SELECT id, tipo_doc, nom_documento 
                    FROM documentos_vehiculo 
                    WHERE id_vehiculo = %s
                    """,
                    (vehiculo_id,),
                )
                docs = cursor.fetchall() or []
                for d in docs:
                    d["url_acceso"] = f"/uploads/documentos/vehiculos/{d['nom_documento']}"
                vehiculo["documentos"] = docs

                return {"exito": True, "datos": vehiculo}
    except Exception as e:
        print(f"❌ Error al consultar vehículo #{vehiculo_id}: {e}")
        return {
            "exito": False,
            "mensaje": f"Error en la base de datos: {e}",
        }


def UPDATE_vehiculo_db(vehiculo_id: int, campos: dict) -> dict:
    try:
        if not campos:
            return {
                "exito": False,
                "mensaje": "No se enviaron campos para actualizar.",
            }

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                documentos = campos.pop("documentos", None)
                if documentos is None:
                    documentos = campos.pop("documentos_ids", None)

                if campos:
                    columnas = [f"{k} = %s" for k in campos.keys()]
                    sql = f"UPDATE vehiculos SET {', '.join(columnas)} WHERE id = %s"
                    valores = list(campos.values()) + [vehiculo_id]
                    cursor.execute(sql, valores)

                if documentos is not None:
                    cursor.execute(
                        "DELETE FROM documentos_vehiculo WHERE id_vehiculo = %s",
                        (vehiculo_id,),
                    )
                    if documentos:
                        sql_docs = """
                        INSERT INTO documentos_vehiculo (id_vehiculo, tipo_doc, nom_documento)
                        VALUES (%s, %s, %s)
                        """
                        valores_docs = [
                            (
                                vehiculo_id,
                                doc.get("tipo_doc", "general"),
                                doc.get("nom_documento") or doc.get("nombre_archivo", ""),
                            )
                            for doc in documentos
                            if (doc.get("nom_documento") or doc.get("nombre_archivo"))
                        ]
                        if valores_docs:
                            cursor.executemany(sql_docs, valores_docs)

                conexion.commit()
                return {
                    "exito": True,
                    "mensaje": f"✅ Vehículo #{vehiculo_id} actualizado con éxito.",
                }
    except Exception as e:
        print(f"❌ Error al actualizar vehículo #{vehiculo_id}: {e}")
        return {
            "exito": False,
            "mensaje": f"Error en la base de datos: {e}",
        }


def DELETE_vehiculo_db(vehiculo_id: int) -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("DELETE FROM vehiculos WHERE id = %s", (vehiculo_id,))
                if cursor.rowcount == 0:
                    return {
                        "exito": False,
                        "mensaje": f"Vehículo #{vehiculo_id} no existe para eliminar.",
                    }
                conexion.commit()
                return {
                    "exito": True,
                    "mensaje": f"✅ Vehículo #{vehiculo_id} eliminado exitosamente.",
                }
    except Exception as e:
        print(f"❌ Error al eliminar vehículo #{vehiculo_id}: {e}")
        return {
            "exito": False,
            "mensaje": f"Error en la base de datos: {e}",
        }


def INSERT_documento_vehiculo_db(id_vehiculo: int, tipo_doc: str, nom_documento: str) -> dict:
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = """
                INSERT INTO documentos_vehiculo (id_vehiculo, tipo_doc, nom_documento)
                VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (id_vehiculo, tipo_doc, nom_documento))
                doc_id = cursor.lastrowid
                conexion.commit()

                return {
                    "exito": True,
                    "id": doc_id,
                    "mensaje": "Documento registrado con éxito.",
                }
    except Exception as e:
        print(f"❌ Error al registrar documento de vehículo: {e}")
        return {
            "exito": False,
            "mensaje": f"Error en la base de datos: {e}",
        }