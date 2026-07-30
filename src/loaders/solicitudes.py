from typing import TypedDict, List
from config import settings
from src.loaders.solicitudes_loaders import (
    SAVE_solicitud_bd,
    UPDATE_solicitud_bd,
    GET_solicitud_bd,
    DELETE_solicitud_bd,
)
from config.settings import (
    ESTADO_ENVIADO,
    ESTADO_EN_REVISION,
    ESTADO_LISTO_PARA_SEGURIDAD,
    ESTADO_APROBADO,
    ESTADO_RECHAZADO,
    ROL_SST,
    ROL_GESCO,
    ROL_SEGURIDAD_CORP,
)

LISTA_SOLICITUDES = []
# ========================================================


class equipoComputo(TypedDict):
    marca: str
    modelo: str
    serie: str


class personaIngreso(TypedDict):
    item: str
    ap_nombre: str
    tipo_doc: str
    identificacion: int
    cargo: str


# ========================================================


def CREATE_solicitud(
    empresa_orig: str,  # Para que empresa va
    id_user: int,  # ID del solicitante
    nivel_de_riesgo: str,
    tipo_de_persona: str,
    empresa: str,
    planta_a_visitar: str,
    fechaInicio: str,
    fechaFin: str,
    actividad: str,
    tipo_vehiculo: str,
    placa: str,
    eq_computo: List[equipoComputo],
    personas: List[personaIngreso],
    doc_adjuntos: List[str],
) -> dict:

    # =====================================================

    nueva_solicitud = {
        "empresa_origen": empresa_orig,
        "diligenciado_por": id_user,
        "nivel_de_riesgo": nivel_de_riesgo,
        "tipo_de_persona": tipo_de_persona,
        "empresa_contratista": empresa,
        "planta_a_visitar": planta_a_visitar,
        "fecha_inicio": fechaInicio,
        "fecha_fin": fechaFin,
        "actividad": actividad,
        "vehiculo": {
            "tipo": tipo_vehiculo,
            "placa": placa.upper()
            if placa
            else "",  # upper() para pasar el texto a mayuscula independientemente si se escribe en minuscula
        },
        "eq_computo": eq_computo,
        "personas": personas,
        "doc_adjuntos": doc_adjuntos,
        # Estado Inicial del Flujo
        "estado": settings.ESTADO_ENVIADO,
        "aprobaciones": {
            "SST": {"evaluado": False, "aprobado": False, "comentario": ""},
            "GESCO": {"evaluado": False, "aprobado": False, "comentario": ""},
            "SEGURIDAD_CORP": {"evaluado": False, "aprobado": False, "comentario": ""},
        },
    }

    print(f"==================================================")
    print(f"✅ [ÉXITO] Solicitud creada correctamente.")
    print(f"   Destino: {planta_a_visitar} | Contratista: {empresa}")
    print(f"   Personas registradas: {len(personas)} | Equipos: {len(eq_computo)}")
    print(f"==================================================")

    respuesta_bd = SAVE_solicitud_bd(nueva_solicitud)

    return respuesta_bd


def EDIT_solicitud(solicitud_id: int, datos_actualizados: dict) -> dict:
    """
    Permite editar la solicitud ÚNICAMENTE si su estado actual es 'ENVIADO'.
    Si ya pasó a 'EN REVISION' o cualquier otro estado, bloquea la edición.
    """

    # 1. Consultar el estado actual en la base de datos
    actual = GET_solicitud_bd(solicitud_id)
    if not actual["exito"]:
        return actual

    estado_actual = actual["datos"]["estado"]

    ESTADO_PERMITIDO = getattr(settings, "ESTADO_ENVIADO", "ENVIADO")

    if estado_actual != ESTADO_PERMITIDO:
        return {
            "exito": False,
            "mensaje": f"No se puede modificar la solicitud #{solicitud_id}. "
            f"Estado actual: '{estado_actual}'. Solo se permite editar cuando está en '{ESTADO_PERMITIDO}'.",
        }

    # Formatear la placa a mayúsculas si viene en los datos
    if "vehiculo" in datos_actualizados and "placa" in datos_actualizados["vehiculo"]:
        datos_actualizados["vehiculo"]["placa"] = datos_actualizados["vehiculo"][
            "placa"
        ].upper()

    return UPDATE_solicitud_bd(solicitud_id, datos_actualizados)


def DELETE_solicitud(solicitud_id: int) -> dict:
    """
    Permite eliminar una solicitud.
    Aplica reglas de negocio antes de borrar en la base de datos.
    """

    # Verificar si la solicitud existe y en qué estado está
    actual = GET_solicitud_bd(solicitud_id)
    if not actual.get("exito"):
        return actual

    estado_actual = actual["datos"]["estado"]

    estado_aprobado = getattr(settings, "ESTADO_APROBADO", "APROBADO")
    estado_revision = getattr(settings, "ESTADO_EN_REVISION", "EN REVISION")

    if estado_actual in [estado_aprobado, estado_revision]:
        return {
            "exito": False,
            "mensaje": f"No se puede eliminar la solicitud #{solicitud_id} porque ya ha sido APROBADA o se encuentra en REVISIÓN.",
        }

    respuesta_bd = DELETE_solicitud_bd(solicitud_id)

    if respuesta_bd.get("exito"):
        global LISTA_SOLICITUDES
        LISTA_SOLICITUDES = [s for s in LISTA_SOLICITUDES if s["id"] != solicitud_id]

    return respuesta_bd


def proceso_evaluo(estado_actual: str, usuario_rol: str, voto_aprobado: bool) -> dict:

    if usuario_rol != ROL_SEGURIDAD_CORP:
        return {
            "permitido": False,
            "mensaje": f"Acción denegada: El rol '{usuario_rol}' no corresponde con SEGURIDAD CORPORATIVA Y RIESO",
        }

    if estado_actual != ESTADO_LISTO_PARA_SEGURIDAD:
        return {
            "permitido": False,
            "mensaje": f"Acción bloqueada: No se puede dar el visto bueno en el estado {estado_actual}. Se requiere que SST y GESCO aprueben primero.",
        }

    nuevo_estado = ESTADO_APROBADO if voto_aprobado else ESTADO_RECHAZADO

    return {
        "permitido": True,
        "nuevo_estado": nuevo_estado,
        "mensaje": f"Solicitud {nuevo_estado} con éxito por seguridad corporativa y riesgo",
    }
