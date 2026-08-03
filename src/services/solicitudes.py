from config import settings
from src.schemas.solicitud_schema import SolicitudInput
from src.transformers.solicitudes_transformer import transformar_solicitud  
from src.loaders.solicitudes_loaders import (
    CREATE_solicitud_bd,
    UPDATE_solicitud_bd,
    GET_solicitud_bd,
    DELETE_solicitud_bd,
)
from config.settings import (
    ESTADO_LISTO_PARA_SEGURIDAD,
    ESTADO_APROBADO,
    ESTADO_RECHAZADO,
    ESTADO_ENVIADO,
    ROL_SEGURIDAD_CORP,
)

LISTA_SOLICITUDES = []


def CREATE_solicitud(payload: SolicitudInput) -> dict:

    data_raw = payload.model_dump()

    data_raw.setdefault("estado", settings.ESTADO_ENVIADO)

    data_clean = transformar_solicitud(data_raw)

    return CREATE_solicitud_bd(data_clean)


def EDIT_solicitud(solicitud_id: int, datos_actualizados: dict) -> dict:
   
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
