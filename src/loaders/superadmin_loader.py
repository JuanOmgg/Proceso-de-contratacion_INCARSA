import time
from typing import Dict, List, Any, Optional
from database import GET_conexion

# Cache en memoria para verificación ultra-rápida del modo mantenimiento (5 segundos TTL)
_MAINTENANCE_CACHE = {
    "activo": False,
    "mensaje": "Estamos realizando labores de optimización y mantenimiento programado.",
    "tiempo": "30 minutos aprox.",
    "expires_at": 0
}

def GET_mantenimiento_status() -> Dict[str, Any]:
    """Obtiene el estado del modo mantenimiento con caché en memoria."""
    global _MAINTENANCE_CACHE
    now = time.time()
    
    if now < _MAINTENANCE_CACHE["expires_at"]:
        return {
            "activo": _MAINTENANCE_CACHE["activo"],
            "mensaje": _MAINTENANCE_CACHE["mensaje"],
            "tiempo": _MAINTENANCE_CACHE["tiempo"]
        }

    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT clave, valor FROM sistema_config WHERE clave IN ('modo_mantenimiento', 'mantenimiento_mensaje', 'mantenimiento_tiempo')")
                rows = cur.fetchall()
                config = {r["clave"]: r["valor"] for r in rows}
                
                activo = str(config.get("modo_mantenimiento", "0")).strip() in ("1", "true", "True")
                mensaje = config.get("mantenimiento_mensaje", "Estamos realizando mejoras en el sistema.")
                tiempo = config.get("mantenimiento_tiempo", "30 minutos aprox.")

                _MAINTENANCE_CACHE = {
                    "activo": activo,
                    "mensaje": mensaje,
                    "tiempo": tiempo,
                    "expires_at": now + 5  # 5 segundos de cache
                }

                return {
                    "activo": activo,
                    "mensaje": mensaje,
                    "tiempo": tiempo
                }
    except Exception as e:
        print(f"❌ Error al consultar modo mantenimiento: {e}")
        return {
            "activo": False,
            "mensaje": "Sistema operativo.",
            "tiempo": ""
        }

def SET_mantenimiento_status(activo: bool, mensaje: Optional[str] = None, tiempo: Optional[str] = None) -> Dict[str, Any]:
    """Activa o desactiva el modo mantenimiento e invalida el caché."""
    global _MAINTENANCE_CACHE
    valor_activo = "1" if activo else "0"

    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE sistema_config SET valor = %s WHERE clave = 'modo_mantenimiento'", (valor_activo,))
                if mensaje is not None:
                    cur.execute("UPDATE sistema_config SET valor = %s WHERE clave = 'mantenimiento_mensaje'", (mensaje.strip(),))
                if tiempo is not None:
                    cur.execute("UPDATE sistema_config SET valor = %s WHERE clave = 'mantenimiento_tiempo'", (tiempo.strip(),))
                conn.commit()

        # Invalidar cache de inmediato
        _MAINTENANCE_CACHE["expires_at"] = 0
        return GET_mantenimiento_status()
    except Exception as e:
        print(f"❌ Error al actualizar modo mantenimiento: {e}")
        raise e

def GET_matriz_permisos_db() -> Dict[str, Any]:
    """Obtiene la matriz completa de roles y sus permisos configurados."""
MODULOS_SISTEMA = [
    "dashboard",
    "solicitudes",
    "nueva_solicitud",
    "usuarios",
    "nuevo_usuario",
    "plantas",
    "contratistas",
    "vehiculos",
    "personas",
    "procesamiento",
    "antecedentes",
    "revision_solicitud"
]

ACCIONES_SISTEMA = ["ver", "crear", "editar", "eliminar", "aprobar"]

def GET_matriz_permisos_db() -> Dict[str, Any]:
    """Obtiene la matriz completa de permisos organizada por rol, módulo y acción."""
    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nombre_rol, descripcion FROM roles ORDER BY id ASC")
                roles = cur.fetchall()

                cur.execute("SELECT id_rol, modulo, accion, permitido FROM rol_permisos")
                permisos_raw = cur.fetchall()

                # Mapa base de permisos: { id_rol: { modulo: { accion: bool } } }
                permisos_map = {}
                for p in permisos_raw:
                    r_id = p["id_rol"]
                    mod = p["modulo"]
                    acc = p["accion"]
                    val = bool(p["permitido"])
                    if r_id not in permisos_map:
                        permisos_map[r_id] = {}
                    if mod not in permisos_map[r_id]:
                        permisos_map[r_id][mod] = {}
                    permisos_map[r_id][mod][acc] = val

                resultado_roles = []
                matriz = {}

                for r in roles:
                    r_id = r["id"]
                    r_nom = r["nombre_rol"].strip().upper()
                    is_super = (r_nom == "SUPERADMIN")
                    
                    resultado_roles.append({
                        "id": r_id,
                        "nombre": r["nombre_rol"],
                        "nombre_rol": r["nombre_rol"],
                        "descripcion": r["descripcion"] or "",
                        "is_superadmin": is_super
                    })

                    matriz[r_id] = {}
                    for mod in MODULOS_SISTEMA:
                        matriz[r_id][mod] = {}
                        for acc in ACCIONES_SISTEMA:
                            if is_super:
                                matriz[r_id][mod][acc] = True
                            else:
                                rol_p = permisos_map.get(r_id, {}).get(mod, {})
                                matriz[r_id][mod][acc] = rol_p.get(acc, False)

                return {
                    "exito": True,
                    "roles": resultado_roles,
                    "modulos": MODULOS_SISTEMA,
                    "acciones": ACCIONES_SISTEMA,
                    "matriz": matriz
                }
    except Exception as e:
        print(f"❌ Error al obtener matriz de permisos: {e}")
        raise e

def UPDATE_permisos_rol_db(id_rol: int, permisos: Optional[List[Dict[str, Any]]] = None, modulos: Optional[Dict[str, bool]] = None, acciones: Optional[Dict[str, bool]] = None) -> bool:
    """Actualiza los permisos de módulos y acciones para un rol específico."""
    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                # Validar que el rol no sea SUPERADMIN
                cur.execute("SELECT nombre_rol FROM roles WHERE id = %s", (id_rol,))
                rol_info = cur.fetchone()
                if rol_info and rol_info["nombre_rol"].strip().upper() == "SUPERADMIN":
                    raise ValueError("Los permisos del rol SUPERADMIN no pueden ser modificados ni restringidos.")

                # 1. Si viene la lista estructurada de permisos [{modulo, accion, permitido}]
                if permisos and isinstance(permisos, list):
                    for p in permisos:
                        mod = p.get("modulo")
                        acc = p.get("accion", "ver")
                        permitido = 1 if p.get("permitido") else 0
                        if mod:
                            cur.execute("""
                                INSERT INTO rol_permisos (id_rol, modulo, accion, permitido)
                                VALUES (%s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE permitido = VALUES(permitido)
                            """, (id_rol, mod, acc, permitido))

                # 2. Si vienen diccionarios separados de modulos y acciones
                if modulos:
                    for mod, val in modulos.items():
                        permitido = 1 if val else 0
                        cur.execute("""
                            INSERT INTO rol_permisos (id_rol, modulo, accion, permitido)
                            VALUES (%s, %s, 'ver', %s)
                            ON DUPLICATE KEY UPDATE permitido = VALUES(permitido)
                        """, (id_rol, mod, permitido))

                if acciones:
                    for acc, val in acciones.items():
                        permitido = 1 if val else 0
                        # Se aplica la acción a los módulos correspondientes
                        for mod in MODULOS_SISTEMA:
                            cur.execute("""
                                INSERT INTO rol_permisos (id_rol, modulo, accion, permitido)
                                VALUES (%s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE permitido = VALUES(permitido)
                            """, (id_rol, mod, acc, permitido))

                conn.commit()
                return True
    except Exception as e:
        print(f"❌ Error al actualizar permisos del rol {id_rol}: {e}")
        raise e

def GET_permisos_rol_db(id_rol: int) -> Dict[str, Any]:
    """Obtiene los permisos específicos de un rol (utilizado en login o carga de sesión)."""
    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT nombre_rol FROM roles WHERE id = %s", (id_rol,))
                rol_info = cur.fetchone()
                if not rol_info:
                    return {"exito": False, "rol": "", "permisos": {}}

                r_nom = rol_info["nombre_rol"].strip().upper()
                is_super = (r_nom == "SUPERADMIN")

                if is_super:
                    permisos_super = {
                        mod: {acc: True for acc in ACCIONES_SISTEMA}
                        for mod in MODULOS_SISTEMA
                    }
                    return {
                        "exito": True,
                        "rol": r_nom,
                        "superadmin": True,
                        "permisos": permisos_super
                    }

                cur.execute("SELECT modulo, accion, permitido FROM rol_permisos WHERE id_rol = %s", (id_rol,))
                rows = cur.fetchall()

                permisos = {
                    mod: {acc: False for acc in ACCIONES_SISTEMA}
                    for mod in MODULOS_SISTEMA
                }

                for r in rows:
                    mod = r["modulo"]
                    acc = r["accion"]
                    val = bool(r["permitido"])
                    if mod in permisos:
                        permisos[mod][acc] = val

                return {
                    "exito": True,
                    "rol": r_nom,
                    "superadmin": False,
                    "permisos": permisos
                }
    except Exception as e:
        print(f"❌ Error al obtener permisos para rol {id_rol}: {e}")
        return {"exito": False, "rol": "", "permisos": {}}
