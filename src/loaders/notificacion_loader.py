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


def emitir_difusion_superadmin_db(
    titulo: str,
    mensaje: str,
    tipo: str = "info",
    enlace: Optional[str] = None,
    destinatario_tipo: str = "rol",
    roles_ids: Optional[List[int]] = None,
    usuarios_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Permite al SuperAdmin emitir comunicados y mensajes personalizados
    hacia roles específicos, usuarios individuales o a todo el sistema.
    """
    titulo = (titulo or "").strip()[:100]
    mensaje = (mensaje or "").strip()
    if not titulo or not mensaje:
        return {"exito": False, "mensaje": "El título y el mensaje son obligatorios."}

    tipos_validos = ("info", "warning", "error", "success")
    tipo_final = tipo.lower().strip() if tipo and tipo.lower().strip() in tipos_validos else "info"
    enlace_final = enlace.strip() if enlace and enlace.strip() else None

    sql = """
        INSERT INTO notificaciones (id_usuario, rol_destino, titulo, mensaje, tipo, enlace, leido)
        VALUES (%s, %s, %s, %s, %s, %s, FALSE)
    """

    registros_insertados = 0
    detalles = []

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                if destinatario_tipo == "todos":
                    # Broadcast a todos los roles operativos
                    cursor.execute("SELECT id, nombre_rol FROM roles WHERE UPPER(nombre_rol) != 'SUPERADMIN' ORDER BY id ASC")
                    roles_op = cursor.fetchall() or []
                    for r in roles_op:
                        cursor.execute(sql, (None, r["id"], titulo, mensaje, tipo_final, enlace_final))
                        registros_insertados += 1
                        detalles.append(f"Rol: {r.get('nombre_rol')}")

                elif destinatario_tipo == "rol":
                    roles_ids = roles_ids or []
                    if not roles_ids:
                        return {"exito": False, "mensaje": "Debe seleccionar al menos un rol de destino."}

                    for r_id in roles_ids:
                        cursor.execute("SELECT nombre_rol FROM roles WHERE id = %s", (r_id,))
                        r_info = cursor.fetchone()
                        nom_rol = r_info["nombre_rol"] if r_info else f"ID {r_id}"
                        cursor.execute(sql, (None, r_id, titulo, mensaje, tipo_final, enlace_final))
                        registros_insertados += 1
                        detalles.append(f"Rol: {nom_rol}")

                elif destinatario_tipo == "usuarios":
                    usuarios_ids = usuarios_ids or []
                    if not usuarios_ids:
                        return {"exito": False, "mensaje": "Debe seleccionar al menos un usuario de destino."}

                    for u_id in usuarios_ids:
                        cursor.execute("SELECT CONCAT(nombres, ' ', apellidos) AS nombre FROM usuarios WHERE id = %s", (u_id,))
                        u_info = cursor.fetchone()
                        nom_u = u_info["nombre"] if u_info else f"Usuario #{u_id}"
                        cursor.execute(sql, (u_id, None, titulo, mensaje, tipo_final, enlace_final))
                        registros_insertados += 1
                        detalles.append(nom_u)

                else:
                    return {"exito": False, "mensaje": f"Tipo de destinatario '{destinatario_tipo}' no válido."}

                conexion.commit()

        return {
            "exito": True,
            "mensaje": f"Se emitieron {registros_insertados} notificación(es) exitosamente.",
            "total_enviados": registros_insertados,
            "destinatarios": detalles,
        }

    except Exception as e:
        print(f"❌ Error al emitir difusión SuperAdmin: {e}")
        return {"exito": False, "mensaje": f"Error en base de datos al enviar mensaje: {str(e)}"}


def obtener_historial_difusion_db(limit: int = 25) -> List[Dict[str, Any]]:
    """
    Retorna el historial de las últimas notificaciones emitidas en la plataforma.
    """
    sql = """
        SELECT n.id, n.id_usuario, n.rol_destino, n.titulo, n.mensaje, n.tipo, n.enlace, n.leido, n.fecha_creacion,
               CONCAT(u.nombres, ' ', u.apellidos) AS usuario_nombre,
               u.correo AS usuario_correo,
               r.nombre_rol AS rol_nombre
        FROM notificaciones n
        LEFT JOIN usuarios u ON n.id_usuario = u.id
        LEFT JOIN roles r ON n.rol_destino = r.id
        ORDER BY n.id DESC
        LIMIT %s
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(sql, (limit,))
                filas = cursor.fetchall() or []
                for fila in filas:
                    if isinstance(fila.get("fecha_creacion"), datetime):
                        fila["fecha_creacion"] = fila["fecha_creacion"].strftime("%Y-%m-%d %H:%M:%S")
                    fila["leido"] = bool(fila.get("leido"))
                return filas
    except Exception as e:
        print(f"❌ Error al obtener historial de notificaciones: {e}")
        return []

