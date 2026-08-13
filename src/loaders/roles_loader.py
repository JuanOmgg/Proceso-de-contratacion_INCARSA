# src/loaders/roles_loader.py
from typing import List, Dict, Optional
from database import GET_conexion


def GETALL_roles() -> List[Dict]:
    """
    Recupera la lista de todos los roles registrados en la base de datos.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = "SELECT id, nombre_rol, descripcion FROM roles ORDER BY id ASC;"
                cursor.execute(sql)
                return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error al consultar roles: {e}")
        return []


def GET_rol_by_id(id_rol: int) -> Dict:
    """
    Recupera un rol específico por su ID.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = "SELECT id, nombre_rol, descripcion FROM roles WHERE id = %s;"
                cursor.execute(sql, (id_rol,))
                resultado = cursor.fetchone()
                if resultado:
                    return {"exito": True, "data": resultado}
                return {"exito": False, "mensaje": f"No se encontró el rol con ID {id_rol}."}
    except Exception as e:
        print(f"❌ Error al consultar rol por ID: {e}")
        return {"exito": False, "mensaje": f"Error al consultar la base de datos: {e}"}


def GETROL_by_nombre(nombre_rol: str) -> Optional[int]:

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = "SELECT id FROM roles WHERE nombre_rol = %s;"
                cursor.execute(sql, (nombre_rol.strip(),))
                resultado = cursor.fetchone()
                return resultado["id"] if resultado else None
    except Exception as e:
        print(f"❌❌ Error al buscar ID del rol '{nombre_rol}': {e} ❌❌")
        return None


def CREATEROL_IF_NoExiste(nombre_rol: str, descripcion: str = "") -> Dict:
    """
    Inserta un nuevo rol si no existe previamente en la base de datos.
    """

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                sql = """
                    INSERT INTO roles (nombre_rol, descripcion)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion);
                """
                cursor.execute(sql, (nombre_rol.strip(), descripcion.strip()))
                conexion.commit()
                return {
                    "status": "success",
                    "mensaje": f"✅✅ Rol '{nombre_rol}' procesado correctamente. ✅✅",
                }
    except Exception as e:
        return {"status": "error", "mensaje": f"❌❌ Error al insertar rol: {e} ❌❌"}
