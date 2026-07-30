# src/loaders/roles_loader.py
from typing import List, Dict, Optional
from src.database import GET_conexion


def GETALL_roles() -> List[Dict]:
    """
    Recupera la lista de todos los roles registrados en la base de datos.
    """

    conexion = GET_conexion()

    if not conexion:
        return {
            "estado": False,
            "mensaje": f"No se puede establecer conexión con la base de datos.",
        }

    try:
        with (
            conexion.cursor(dictionary=True) as cursor
        ):  # with - garantiza que el objeto cursor cierre automaticamente cuando se termina la consulta SQL
            sql = (
                "SELECT id_rol, nombre_rol, descripcion FROM roles ORDER BY id_rol ASC;"
            )
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error al consultar roles: {e}")
        return []
    finally:
        conexion.close()


def GETROL_by_nombre(nombre_rol: str) -> Optional[int]:

    conexion = GET_conexion()
    if not conexion:
        return None

    try:
        with conexion.cursor(dictionary=True) as cursor:
            sql = "SELECT id FROM roles WHERE nombre_rol = %s;"
            cursor.execute(sql, (nombre_rol.strip(),))
            resultado = cursor.fetchone()
            return resultado["id"] if resultado else None
    except Exception as e:
        print(f"❌❌ Error al buscar ID del rol '{nombre_rol}': {e} ❌❌")
        return None
    finally:
        conexion.close()


def CREATEROL_IF_NoExiste(nombre_rol: str, descripcion: str = "") -> Dict:
    """
    Inserta un nuevo rol si no existe previamente en la base de datos.
    """

    conexion = GET_conexion()
    if not conexion:
        return {
            "status": "error",
            "mensaje": "❌❌ Error de conexión a la base de datos ❌❌",
        }

    try:
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
        conexion.rollback()
        return {"status": "error", "mensaje": f"❌❌ Error al insertar rol: {e} ❌❌"}
    finally:
        conexion.close()
