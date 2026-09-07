from database import GET_conexion
from typing import List, Dict, Any, Optional
from datetime import datetime


def crear_notificacion_db(
    titulo: str,
    mensaje: str,
    tipo: str = "info",
    enlace: Optional[str] = None,
    archivo_url: Optional[str] = None,
    archivo_nombre: Optional[str] = None,
    id_usuario: Optional[int] = None,
    rol_destino: Optional[int] = None,
) -> Optional[int]:
    """
    Inserta una notificación en la base de datos.
    Puede ir dirigida a un id_usuario específico, a un rol_destino, o a ambos.
    """
    sql = """
        INSERT INTO notificaciones (id_usuario, rol_destino, titulo, mensaje, tipo, enlace, archivo_url, archivo_nombre, leido)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE)
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario, rol_destino, titulo, mensaje, tipo, enlace, archivo_url, archivo_nombre))
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
        SELECT id, id_usuario, rol_destino, titulo, mensaje, tipo, enlace, archivo_url, archivo_nombre, leido, fecha_creacion
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


def marcar_leida_por_solicitud_db(
    id_o_codigo: str,
    id_usuario: Optional[int] = None,
    id_rol: Optional[int] = None,
) -> int:
    """
    Marca como leídas las notificaciones asociadas a una solicitud cuando
    un usuario entra a revisarla desde cualquier parte que no sea el menú
    de notificaciones (ej: listado, dashboard, modal, URL directa).
    """
    if not id_o_codigo:
        return 0

    id_o_codigo_str = str(id_o_codigo).strip()
    sol_id = None
    sol_cod = None

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # 1. Obtener id numérico y código de la solicitud
                cursor.execute(
                    "SELECT id, codigo FROM solicitudes WHERE CAST(id AS CHAR) = %s OR codigo = %s LIMIT 1",
                    (id_o_codigo_str, id_o_codigo_str)
                )
                row = cursor.fetchone()
                if row:
                    sol_id = str(row.get("id"))
                    sol_cod = str(row.get("codigo") or "")
                else:
                    if id_o_codigo_str.isdigit():
                        sol_id = id_o_codigo_str
                    else:
                        sol_cod = id_o_codigo_str

                # Construir patrones para enlace y mensaje
                patterns = []
                if sol_cod:
                    patterns.append(f"%{sol_cod}%")
                if sol_id:
                    patterns.append(f"%/{sol_id}%")
                    patterns.append(f"%={sol_id}%")

                if not patterns:
                    return 0

                or_like_clauses = []
                params_like = []
                for p in patterns:
                    or_like_clauses.append("enlace LIKE %s")
                    params_like.append(p)
                    or_like_clauses.append("mensaje LIKE %s")
                    params_like.append(p)

                cond_like = " OR ".join(or_like_clauses)

                # Condición de destinatario
                if id_usuario is not None and id_rol is not None:
                    if int(id_rol) == 2:
                        cond_dest = "(id_usuario = %s OR rol_destino = %s OR rol_destino IS NULL)"
                        params_dest = [id_usuario, id_rol]
                    else:
                        cond_dest = "((%s IS NOT NULL AND id_usuario = %s) OR (%s IS NOT NULL AND rol_destino = %s))"
                        params_dest = [id_usuario, id_usuario, id_rol, id_rol]
                elif id_usuario is not None:
                    cond_dest = "(id_usuario = %s)"
                    params_dest = [id_usuario]
                elif id_rol is not None:
                    cond_dest = "(rol_destino = %s)"
                    params_dest = [id_rol]
                else:
                    cond_dest = "1=1"
                    params_dest = []

                sql_update = f"""
                    UPDATE notificaciones
                    SET leido = TRUE
                    WHERE leido = FALSE
                      AND {cond_dest}
                      AND ({cond_like})
                """
                cursor.execute(sql_update, params_dest + params_like)
                conexion.commit()
                filas_afectadas = cursor.rowcount
                if filas_afectadas > 0:
                    print(f"🔔 [NOTIFICACIONES] Se marcaron {filas_afectadas} notificación(es) como leídas para solicitud '{id_o_codigo_str}' (usuario={id_usuario}, rol={id_rol}).")
                return filas_afectadas
    except Exception as e:
        print(f"❌ Error al marcar notificaciones como leídas para solicitud '{id_o_codigo}': {e}")
        return 0


def emitir_difusion_superadmin_db(
    titulo: str,
    mensaje: str,
    tipo: str = "info",
    enlace: Optional[str] = None,
    archivo_url: Optional[str] = None,
    archivo_nombre: Optional[str] = None,
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
    archivo_url_final = archivo_url.strip() if archivo_url and archivo_url.strip() else None
    archivo_nombre_final = archivo_nombre.strip() if archivo_nombre and archivo_nombre.strip() else None

    sql = """
        INSERT INTO notificaciones (id_usuario, rol_destino, titulo, mensaje, tipo, enlace, archivo_url, archivo_nombre, leido)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE)
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
                        cursor.execute(sql, (None, r["id"], titulo, mensaje, tipo_final, enlace_final, archivo_url_final, archivo_nombre_final))
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
                        cursor.execute(sql, (None, r_id, titulo, mensaje, tipo_final, enlace_final, archivo_url_final, archivo_nombre_final))
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
                        cursor.execute(sql, (u_id, None, titulo, mensaje, tipo_final, enlace_final, archivo_url_final, archivo_nombre_final))
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
        SELECT n.id, n.id_usuario, n.rol_destino, n.titulo, n.mensaje, n.tipo, n.enlace, n.archivo_url, n.archivo_nombre, n.leido, n.fecha_creacion,
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

