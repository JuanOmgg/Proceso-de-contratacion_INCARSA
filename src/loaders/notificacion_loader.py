from database import GET_conexion
from typing import List, Dict, Any, Optional
from datetime import datetime


def crear_notificacion_db(
    titulo: str,
    mensaje: str,
    tipo: str = "info",
    enlace: Optional[str] = None,
    id_usuario: Optional[int] = None,
    rol_destino: Optional[int] = None,
) -> Optional[int]:
    """
    Inserta una notificación en la base de datos.
    Puede ir dirigida a un id_usuario específico, a un rol_destino, o a ambos.
    """
    sql = """
        INSERT INTO notificaciones (id_usuario, rol_destino, titulo, mensaje, tipo, enlace, leido)
        VALUES (%s, %s, %s, %s, %s, %s, FALSE)
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario, rol_destino, titulo, mensaje, tipo, enlace))
                conexion.commit()
                return cursor.lastrowid
    except Exception as e:
        print(f"❌ Error al crear notificación: {e}")
        return None


def obtener_notificaciones_db(
    id_usuario: Optional[int] = None,
    id_rol: Optional[int] = None,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """
    Obtiene las notificaciones dirigidas al usuario o a su rol,
    ordenadas de la más reciente a la más antigua.
    """
    sql = """
        SELECT id, id_usuario, rol_destino, titulo, mensaje, tipo, enlace, leido, fecha_creacion
        FROM notificaciones
        WHERE (%s IS NOT NULL AND id_usuario = %s)
           OR (%s IS NOT NULL AND rol_destino = %s)
        ORDER BY fecha_creacion DESC
        LIMIT %s
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario, id_usuario, id_rol, id_rol, limit))
                filas = cursor.fetchall() or []
                
                # Formatear datetime a string para serialización JSON limpia
                for fila in filas:
                    if isinstance(fila.get("fecha_creacion"), datetime):
                        fila["fecha_creacion"] = fila["fecha_creacion"].strftime("%Y-%m-%d %H:%M:%S")
                    fila["leido"] = bool(fila.get("leido"))
                return filas
    except Exception as e:
        print(f"❌ Error al obtener notificaciones: {e}")
        return []


def contar_no_leidas_db(
    id_usuario: Optional[int] = None,
    id_rol: Optional[int] = None,
) -> int:
    """
    Cuenta cuántas notificaciones no leídas tiene el usuario o su rol.
    """
    sql = """
        SELECT COUNT(*) as total
        FROM notificaciones
        WHERE leido = FALSE
          AND ((%s IS NOT NULL AND id_usuario = %s)
            OR (%s IS NOT NULL AND rol_destino = %s))
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario, id_usuario, id_rol, id_rol))
                res = cursor.fetchone()
                return int(res.get("total", 0)) if res else 0
    except Exception as e:
        print(f"❌ Error al contar notificaciones no leídas: {e}")
        return 0


def marcar_leida_db(id_notificacion: int) -> bool:
    """
    Marca una notificación específica como leída.
    """
    sql = "UPDATE notificaciones SET leido = TRUE WHERE id = %s"
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_notificacion,))
                conexion.commit()
                return cursor.rowcount > 0
    except Exception as e:
        print(f"❌ Error al marcar notificación como leída: {e}")
        return False


def marcar_todas_leidas_db(
    id_usuario: Optional[int] = None,
    id_rol: Optional[int] = None,
) -> bool:
    """
    Marca todas las notificaciones pendientes de un usuario o rol como leídas.
    """
    sql = """
        UPDATE notificaciones
        SET leido = TRUE
        WHERE leido = FALSE
          AND ((%s IS NOT NULL AND id_usuario = %s)
            OR (%s IS NOT NULL AND rol_destino = %s))
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario, id_usuario, id_rol, id_rol))
                conexion.commit()
                return True
    except Exception as e:
        print(f"❌ Error al marcar todas las notificaciones como leídas: {e}")
        return False
