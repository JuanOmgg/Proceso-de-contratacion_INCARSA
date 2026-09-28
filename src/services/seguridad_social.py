from typing import Dict, Any, Optional
from src.loaders.seguridad_social_loader import (
    GET_OR_CREATE_seguridad_social_persona_db,
    UPDATE_seguridad_social_db,
    ADD_historial_solicitud_ss_db,
    GET_ALL_seguridad_social_db
)
from src.schemas.seguridad_social_schema import SeguridadSocialUpdate, HistorialSolicitudSSCreate
from src.transformers.seguridad_social_transformer import TRANSFORM_SEGURIDAD_SOCIAL_DATA


def OBTENER_SEGURIDAD_SOCIAL_PERSONA(id_persona: int) -> Dict[str, Any]:
    return GET_OR_CREATE_seguridad_social_persona_db(id_persona)


def ACTUALIZAR_SEGURIDAD_SOCIAL(id_persona: int, payload: SeguridadSocialUpdate) -> Dict[str, Any]:
    data_raw = payload.model_dump(exclude_unset=True)
    data_limpia = TRANSFORM_SEGURIDAD_SOCIAL_DATA(data_raw)
    return UPDATE_seguridad_social_db(id_persona, data_limpia)


def REGISTRAR_HISTORIAL_SOLICITUD_SS(id_persona: int, payload: HistorialSolicitudSSCreate) -> Dict[str, Any]:
    return ADD_historial_solicitud_ss_db(
        id_persona=id_persona,
        id_solicitud=payload.id_solicitud,
        id_empresa=payload.id_empresa,
        observacion=payload.observacion
    )


def LISTAR_TODOS_SEGURIDAD_SOCIAL() -> Dict[str, Any]:
    return GET_ALL_seguridad_social_db()
