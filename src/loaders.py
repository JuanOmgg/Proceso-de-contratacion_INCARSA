from src.database import obtener_conexion

def guardar_solicitud_bd(solicitud: dict) -> dict:

    conexion = obtener_conexion()
    
    if not conexion:
        return {"exito": False, "mensaje": "No se pudo establecer conexion con la base de datos"}

    cursor = conexion.cursor()

    try:
        # 1. Insertar en la Tabla Padre: solicitudes
        sql_solicitud = """
            INSERT INTO solicitudes (
                empresa_origen, diligenciado_por, nivel_de_riesgo, tipo_de_persona,
                empresa_contratista, planta_a_visitar, fecha_inicio, fecha_fin, actividad,
                tipo_vehiculo, placa, estado
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
        """
        valores_solicitud = (
            solicitud["empresa_origen"],
            solicitud["diligenciado_por"],
            solicitud["nivel_de_riesgo"],
            solicitud["tipo_de_persona"],
            solicitud["empresa_contratista"],
            solicitud["planta_a_visitar"],
            solicitud["fecha_inicio"],
            solicitud["fecha_fin"],
            solicitud["actividad"],
            solicitud["vehiculo"]["tipo"],
            solicitud["vehiculo"]["placa"],
            solicitud["estado"]
        )

        cursor.execute(sql_solicitud, valores_solicitud)

        solicitud_id = cursor.lastrowid #Se consulta cual fue el ultimo ID generado

        sql_persona = """
            INSERT INTO personas_solicitud (
                solicitud_id, item, ap_nombre, tipo_doc, identificacion, cargo
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        # Genera la lista de tuplas necesaria
        valores_personas = [
            (solicitud_id, p["item"], p["ap_nombre"], p["tipo_doc"], p["identificacion"], p["cargo"])
            for p in solicitud.get("personas", [])
        ]

        # Si la lista tiene elementos, hace la inserción en lote (optimizado)
        if valores_personas:
            cursor.executemany(sql_persona, valores_personas)

        equipos = solicitud.get("eq_computo", [])
        if equipos:
            sql_equipo = """
                INSERT INTO equipos_solicitud (solicitud_id, marca, modelo, serie)
                VALUES (%s, %s, %s, %s)
            """
            valores_equipos = [
                (solicitud_id, eq["marca"], eq["modelo"], eq["serie"])
                for eq in equipos
            ]
            cursor.executemany(sql_equipo, valores_equipos)
        
        # Confirmar la transacción completa en la Base de Datos
        conexion.commit() #Todo lo ejecutado en este bloque es correcto, se guarda permanentemente en el disco
        
        print(f"✅ Solicitud #{solicitud_id} guardada con éxito en la Base de Datos MySQL.")
        return {
            "exito": True,
            "mensaje": f"Solicitud #{solicitud_id} registrada exitosamente.",
            "id_generado": solicitud_id
        }

    except Exception as e:
        conexion.rollback()  
        print(f"❌ Error al intentar guardar en MySQL: {e}")
        return {"exito": False, "mensaje": f"Error en la base de datos: {e}"}

    finally:
        cursor.close()
        conexion.close()