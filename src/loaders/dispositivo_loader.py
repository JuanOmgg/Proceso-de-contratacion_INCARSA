from typing import Dict, List, Any
from database import GET_conexion

def GET_ALL_dispositivos_db() -> List[Dict[str, Any]]:
    """
    Obtiene el listado consolidado de todos los dispositivos y equipos de cómputo
    registrados en el sistema, vinculados a sus respectivas solicitudes.
    """
    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        es.id,
                        es.solicitud_id,
                        es.marca,
                        es.modelo,
                        es.serie,
                        COALESCE(s.codigo, CONCAT('#', s.id)) AS codigo_radicado,
                        COALESCE(ec.nombre, s.empresa_contratista, 'Contratista no asignado') AS contratista,
                        COALESCE(s.estado, 'Pendiente') AS estado_solicitud,
                        s.fecha_creacion,
                        s.fecha_inicio,
                        s.fecha_fin,
                        s.actividad
                    FROM equipos_solicitud es
                    LEFT JOIN solicitudes s ON s.id = es.solicitud_id
                    LEFT JOIN emp_contratista ec ON ec.id = s.empresa_contratista
                    ORDER BY es.id DESC
                """)
                rows = cur.fetchall() or []

                # Normalizar fechas para serialización JSON limpia
                for r in rows:
                    if r.get("fecha_creacion"):
                        r["fecha_creacion"] = str(r["fecha_creacion"])
                    if r.get("fecha_inicio"):
                        r["fecha_inicio"] = str(r["fecha_inicio"])
                    if r.get("fecha_fin"):
                        r["fecha_fin"] = str(r["fecha_fin"])

                return rows
    except Exception as e:
        print(f"❌ Error al consultar dispositivos en base de datos: {e}")
        raise e
