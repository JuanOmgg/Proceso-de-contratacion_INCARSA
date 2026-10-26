import json
import time
from typing import Dict, List, Any, Optional
from database import GET_conexion

# Cache en memoria para verificación ultra-rápida del modo mantenimiento (5 segundos TTL)
_MAINTENANCE_CACHE = {
    "activo": False,
    "tipo": "general",
    "modulos": [],
    "mensaje": "Estamos realizando labores de optimización y mantenimiento programado.",
    "tiempo": "30 minutos aprox.",
    "temporizador_minutos": 30,
    "temporizador_fin": None,
    "expires_at": 0
}

def GET_mantenimiento_status() -> Dict[str, Any]:
    """Obtiene el estado del modo mantenimiento (general o por módulos) con caché en memoria."""
    global _MAINTENANCE_CACHE
    now = time.time()
    
    if now < _MAINTENANCE_CACHE["expires_at"]:
        return {
            "activo": _MAINTENANCE_CACHE["activo"],
            "tipo": _MAINTENANCE_CACHE["tipo"],
            "modulos": _MAINTENANCE_CACHE["modulos"],
            "mensaje": _MAINTENANCE_CACHE["mensaje"],
            "tiempo": _MAINTENANCE_CACHE["tiempo"],
            "temporizador_minutos": _MAINTENANCE_CACHE.get("temporizador_minutos"),
            "temporizador_fin": _MAINTENANCE_CACHE.get("temporizador_fin")
        }

    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT clave, valor FROM sistema_config 
                    WHERE clave IN (
                        'modo_mantenimiento', 
                        'mantenimiento_tipo',
                        'mantenimiento_modulos',
                        'mantenimiento_mensaje', 
                        'mantenimiento_tiempo',
                        'mantenimiento_temporizador_minutos',
                        'mantenimiento_temporizador_fin'
                    )
                """)
                rows = cur.fetchall()
                config = {r["clave"]: r["valor"] for r in rows}
                
                activo = str(config.get("modo_mantenimiento", "0")).strip() in ("1", "true", "True")
                tipo = str(config.get("mantenimiento_tipo", "general")).strip().lower()
                if tipo not in ("general", "modulos"):
                    tipo = "general"

                modulos_raw = config.get("mantenimiento_modulos", "[]")
                try:
                    modulos = json.loads(modulos_raw) if modulos_raw else []
                    if not isinstance(modulos, list):
                        modulos = []
                except Exception:
                    modulos = []

                mensaje = config.get("mantenimiento_mensaje", "Estamos realizando labores de mantenimiento programado.")
                tiempo = config.get("mantenimiento_tiempo", "30 minutos aprox.")

                try:
                    temporizador_minutos = int(config.get("mantenimiento_temporizador_minutos", 30))
                except Exception:
                    temporizador_minutos = 30

                temporizador_fin_raw = config.get("mantenimiento_temporizador_fin")
                temporizador_fin = None
                if temporizador_fin_raw and str(temporizador_fin_raw).strip():
                    try:
                        temporizador_fin = int(float(str(temporizador_fin_raw).strip()))
                    except Exception:
                        temporizador_fin = None

                _MAINTENANCE_CACHE = {
                    "activo": activo,
                    "tipo": tipo,
                    "modulos": modulos,
                    "mensaje": mensaje,
                    "tiempo": tiempo,
                    "temporizador_minutos": temporizador_minutos,
                    "temporizador_fin": temporizador_fin,
                    "expires_at": now + 5  # 5 segundos de cache
                }

                return {
                    "activo": activo,
                    "tipo": tipo,
                    "modulos": modulos,
                    "mensaje": mensaje,
                    "tiempo": tiempo,
                    "temporizador_minutos": temporizador_minutos,
                    "temporizador_fin": temporizador_fin
                }
    except Exception as e:
        print(f"❌ Error al consultar modo mantenimiento: {e}")
        return {
            "activo": False,
            "tipo": "general",
            "modulos": [],
            "mensaje": "Sistema operativo.",
            "tiempo": "",
            "temporizador_minutos": 0,
            "temporizador_fin": None
        }

def SET_mantenimiento_status(
    activo: bool, 
    tipo: Optional[str] = "general",
    modulos: Optional[List[str]] = None,
    mensaje: Optional[str] = None, 
    tiempo: Optional[str] = None,
    temporizador_minutos: Optional[int] = None,
    temporizador_fin: Optional[str] = None
) -> Dict[str, Any]:
    """Activa o desactiva el modo mantenimiento (general o selectivo) e invalida el caché."""
    global _MAINTENANCE_CACHE
    valor_activo = "1" if activo else "0"
    tipo_val = "modulos" if str(tipo).lower() == "modulos" else "general"

    if modulos is None:
        modulos_val = json.dumps([])
    else:
        modulos_val = json.dumps(list(set(modulos)))

    # Si el mantenimiento está activo y se especifica temporizador_minutos:
    # Guardamos el epoch timestamp en milisegundos absoluto.
    if activo:
        if temporizador_minutos is not None and int(temporizador_minutos) > 0:
            fin_timestamp_ms = int((time.time() + (int(temporizador_minutos) * 60)) * 1000)
            temporizador_fin = str(fin_timestamp_ms)
    else:
        # Si el mantenimiento se desactiva/cancela, limpiamos la fecha fin
        temporizador_fin = None

    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                valores_a_guardar = [
                    ("modo_mantenimiento", valor_activo, "Estado del modo mantenimiento (0=inactivo, 1=activo)"),
                    ("mantenimiento_tipo", tipo_val, "Alcance del mantenimiento (general o modulos)"),
                    ("mantenimiento_modulos", modulos_val, "Lista JSON de modulos en mantenimiento"),
                ]

                if mensaje is not None:
                    valores_a_guardar.append(("mantenimiento_mensaje", mensaje.strip(), "Mensaje del mantenimiento"))
                if tiempo is not None:
                    valores_a_guardar.append(("mantenimiento_tiempo", tiempo.strip(), "Tiempo estimado de espera"))
                if temporizador_minutos is not None:
                    valores_a_guardar.append(("mantenimiento_temporizador_minutos", str(temporizador_minutos), "Minutos del cronómetro visual"))
                if temporizador_fin is not None or not activo:
                    valores_a_guardar.append(("mantenimiento_temporizador_fin", temporizador_fin or "", "Fecha fin para cronómetro visual"))

                for clave, val, desc in valores_a_guardar:
                    cur.execute("""
                        INSERT INTO sistema_config (clave, valor, descripcion)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE valor = VALUES(valor), descripcion = VALUES(descripcion)
                    """, (clave, val, desc))

                conn.commit()

        # Invalidar cache de inmediato
        _MAINTENANCE_CACHE["expires_at"] = 0
        return GET_mantenimiento_status()
    except Exception as e:
        print(f"❌ Error al actualizar modo mantenimiento: {e}")
        raise e

MODULOS_SISTEMA = [
    "dashboard",
    "solicitudes",
    "nueva_solicitud",
    "usuarios",
    "nuevo_usuario",
    "correspondencias",
    "nueva_correspondencia",
    "plantas",
    "contratistas",
    "vehiculos",
    "personas",
    "procesamiento",
    "antecedentes",
    "seguridad_social",
    "inducciones",
    "estadisticas",
    "formulario_temporal",
    "revision_solicitud",
    "dispositivos"
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

# Cache en memoria para verificación en 2 pasos (5 segundos TTL)
_DOS_PASOS_CACHE = {
    "activo": False,
    "expires_at": 0
}

def GET_dos_pasos_status() -> bool:
    """Obtiene el estado de la verificación en 2 pasos global con caché en memoria."""
    global _DOS_PASOS_CACHE
    now = time.time()
    if now < _DOS_PASOS_CACHE["expires_at"]:
        return _DOS_PASOS_CACHE["activo"]

    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT valor FROM sistema_config WHERE clave = 'verificacion_dos_pasos'")
                row = cur.fetchone()
                activo = str(row["valor"]).strip() in ("1", "true", "True") if row else False
                _DOS_PASOS_CACHE = {
                    "activo": activo,
                    "expires_at": now + 5
                }
                return activo
    except Exception as e:
        print(f"❌ Error al consultar estado de verificación en dos pasos: {e}")
        return False

def SET_dos_pasos_status(activo: bool) -> bool:
    """Actualiza el estado de la verificación en dos pasos en sistema_config."""
    global _DOS_PASOS_CACHE
    valor_str = "1" if activo else "0"
    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sistema_config (clave, valor, descripcion)
                    VALUES ('verificacion_dos_pasos', %s, 'Estado de verificación en 2 pasos: 0=Inactivo, 1=Activo')
                    ON DUPLICATE KEY UPDATE valor = VALUES(valor)
                """, (valor_str,))
                conn.commit()
                _DOS_PASOS_CACHE = {
                    "activo": activo,
                    "expires_at": time.time() + 5
                }
                return True
    except Exception as e:
        print(f"❌ Error al actualizar verificación en dos pasos: {e}")
        raise e


# =============================================================================
# GESTIÓN DE CONFIGURACIÓN DE CORREOS Y FLUJO DE INDUCCIONES (MODO PRUEBAS)
# =============================================================================
_CORREOS_INDUCCION_CACHE = {
    "correos_habilitados": True,
    "induccion_modo_entrega": "CORREO",
    "induccion_tipo_enlace": "GESCO",
    "expires_at": 0
}

def GET_configuracion_correos_induccion_db() -> Dict[str, Any]:
    """
    Retorna la directiva global para el despacho de correos y el modo de entrega
    de las evaluaciones de inducción (CORREO vs DIRECTO en pantalla para testing).
    """
    global _CORREOS_INDUCCION_CACHE
    now = time.time()
    if now < _CORREOS_INDUCCION_CACHE["expires_at"]:
        return {
            "correos_habilitados": _CORREOS_INDUCCION_CACHE["correos_habilitados"],
            "induccion_modo_entrega": _CORREOS_INDUCCION_CACHE["induccion_modo_entrega"],
            "induccion_tipo_enlace": _CORREOS_INDUCCION_CACHE["induccion_tipo_enlace"]
        }

    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT clave, valor FROM sistema_config
                    WHERE clave IN ('correos_habilitados', 'induccion_modo_entrega', 'induccion_tipo_enlace')
                """)
                rows = cur.fetchall() or []
                cfg = {r["clave"]: r["valor"] for r in rows}

                correos_hab = str(cfg.get("correos_habilitados", "1")).strip().lower() not in ("0", "false", "no")
                modo_entrega = str(cfg.get("induccion_modo_entrega", "CORREO")).strip().upper()
                if modo_entrega not in ("CORREO", "DIRECTO"):
                    modo_entrega = "CORREO"

                tipo_enlace = str(cfg.get("induccion_tipo_enlace", "GESCO")).strip().upper()
                if tipo_enlace not in ("GESCO", "WIX"):
                    tipo_enlace = "GESCO"

                _CORREOS_INDUCCION_CACHE = {
                    "correos_habilitados": correos_hab,
                    "induccion_modo_entrega": modo_entrega,
                    "induccion_tipo_enlace": tipo_enlace,
                    "expires_at": now + 5
                }

                return {
                    "correos_habilitados": correos_hab,
                    "induccion_modo_entrega": modo_entrega,
                    "induccion_tipo_enlace": tipo_enlace
                }
    except Exception as e:
        print(f"❌ Error al consultar configuración de correos e inducción: {e}")
        return {
            "correos_habilitados": True,
            "induccion_modo_entrega": "CORREO",
            "induccion_tipo_enlace": "GESCO"
        }


def SET_configuracion_correos_induccion_db(
    correos_habilitados: bool,
    induccion_modo_entrega: str = "CORREO",
    induccion_tipo_enlace: str = "GESCO"
) -> Dict[str, Any]:
    """
    Actualiza la configuración de despacho de correos y modo de entrega de inducciones.
    """
    global _CORREOS_INDUCCION_CACHE
    val_correos = "1" if correos_habilitados else "0"
    modo_clean = "DIRECTO" if str(induccion_modo_entrega).strip().upper() == "DIRECTO" else "CORREO"
    enlace_clean = "WIX" if str(induccion_tipo_enlace).strip().upper() == "WIX" else "GESCO"

    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                valores = [
                    ("correos_habilitados", val_correos, "Habilita o pausa el despacho SMTP de correos (1=Habilitado, 0=Pausado / Pruebas)"),
                    ("induccion_modo_entrega", modo_clean, "Modo de inducción: CORREO=enlace enviado por email, DIRECTO=formulario en pantalla para pruebas"),
                    ("induccion_tipo_enlace", enlace_clean, "Destino enlace inducción: GESCO=formulario oficial interno dinámico, WIX=portal externo")
                ]
                for c, v, d in valores:
                    cur.execute("""
                        INSERT INTO sistema_config (clave, valor, descripcion)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE valor = VALUES(valor), descripcion = VALUES(descripcion)
                    """, (c, v, d))
                conn.commit()

        _CORREOS_INDUCCION_CACHE = {
            "correos_habilitados": bool(correos_habilitados),
            "induccion_modo_entrega": modo_clean,
            "induccion_tipo_enlace": enlace_clean,
            "expires_at": 0
        }

        return GET_configuracion_correos_induccion_db()
    except Exception as e:
        print(f"❌ Error al guardar configuración de correos e inducción: {e}")
        raise e


def GET_formulario_asignado_por_tipo_db(tipo_personal: str) -> Dict[str, Any]:
    """
    Determina el formulario de evaluación de inducción GESCO activo asignado
    según el tipo de personal especificado (Contratista, Proveedor, Visitante, Interno, etc.).
    """
    tp_clean = (tipo_personal or "Contratista").strip()
    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT fg.id, fg.nombre, fg.descripcion, fg.vigencia, fg.tipo_personal, fg.Tipo_pregunta,
                           fg.cantidad_preguntas, fg.config_cuotas, fg.is_active, fg.es_interno,
                           fg.id_creador,
                           COALESCE(
                               fg.creador_nombre,
                               CONCAT(u.nombres, ' ', COALESCE(u.apellidos, '')),
                               'Auditor GESCO'
                           ) AS creador_nombre,
                           (SELECT COUNT(*) FROM preguntas p WHERE p.id_formulario = fg.id) AS total_preguntas
                    FROM formularioGesco fg
                    LEFT JOIN usuarios u ON fg.id_creador = u.id
                    WHERE fg.is_active = 1
                      AND (
                        (%s = 'Interno' AND fg.es_interno = 1)
                        OR (FIND_IN_SET(%s, REPLACE(fg.tipo_personal, ', ', ',')) > 0)
                        OR (fg.tipo_personal LIKE %s)
                        OR (fg.tipo_personal = 'TODOS')
                      )
                    ORDER BY 
                      (%s = 'Interno' AND fg.es_interno = 1) DESC,
                      (FIND_IN_SET(%s, REPLACE(fg.tipo_personal, ', ', ',')) > 0) DESC,
                      (fg.tipo_personal != 'TODOS') DESC,
                      fg.id DESC
                    LIMIT 1
                """
                cur.execute(query, (tp_clean, tp_clean, f"%{tp_clean}%", tp_clean, tp_clean))
                row = cur.fetchone()

                if not row:
                    return {
                        "exito": False,
                        "tipo_personal": tp_clean,
                        "mensaje": f"No se encontró un formulario de inducción GESCO activo asignado para '{tp_clean}'.",
                        "formulario": None
                    }

                form_id = row["id"]
                from src.loaders.formulario_gesco_loader import slugify_formulario
                form_slug = slugify_formulario(row["nombre"]) or str(form_id)
                return {
                    "exito": True,
                    "tipo_personal": tp_clean,
                    "formulario": {
                        "id": form_id,
                        "nombre": row["nombre"],
                        "slug": form_slug,
                        "descripcion": row.get("descripcion") or "",
                        "vigencia": row.get("vigencia") or "1 año",
                        "tipo_personal": row.get("tipo_personal") or "TODOS",
                        "es_interno": bool(row.get("es_interno")),
                        "cantidad_preguntas": int(row.get("cantidad_preguntas") or row.get("total_preguntas") or 0),
                        "total_preguntas_banco": int(row.get("total_preguntas") or 0),
                        "creador_nombre": (row.get("creador_nombre") or "").strip() or "Auditor GESCO",
                        "url_evaluacion": f"/evaluacion-induccion/{form_slug}",
                        "url_simulacion": f"/evaluacion-induccion/{form_slug}?simulacion=1"
                    }
                }
    except Exception as e:
        print(f"❌ Error al consultar formulario asignado para tipo '{tipo_personal}': {e}")
        return {
            "exito": False,
            "tipo_personal": tp_clean,
            "mensaje": f"Error en base de datos: {str(e)}",
            "formulario": None
        }


