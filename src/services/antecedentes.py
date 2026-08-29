from typing import Dict, Any, Optional
from src.loaders.antecedentes_loader import (
    GET_OR_CREATE_antecedente_persona_db,
    UPDATE_antecedente_db,
    ADD_historial_solicitud_db,
    GET_ALL_antecedentes_db
)
from src.schemas.antecedentes_schema import AntecedenteUpdate, HistorialSolicitudCreate
from src.transformers.antecedentes_transformer import TRANSFORM_ANTECEDENTE_DATA


def OBTENER_ANTECEDENTE_PERSONA(id_persona: int, actualizar_revision: bool = False) -> Dict[str, Any]:
    return GET_OR_CREATE_antecedente_persona_db(id_persona, actualizar_revision=actualizar_revision)


def ACTUALIZAR_ANTECEDENTE(id_persona: int, payload: AntecedenteUpdate) -> Dict[str, Any]:
    data_raw = payload.model_dump(exclude_unset=True)
    data_limpia = TRANSFORM_ANTECEDENTE_DATA(data_raw)
    return UPDATE_antecedente_db(id_persona, data_limpia)


def REGISTRAR_HISTORIAL_SOLICITUD(id_persona: int, payload: HistorialSolicitudCreate) -> Dict[str, Any]:
    return ADD_historial_solicitud_db(
        id_persona=id_persona,
        id_solicitud=payload.id_solicitud,
        id_empresa=payload.id_empresa,
        observacion=payload.observacion
    )


def LISTAR_TODOS_ANTECEDENTES() -> Dict[str, Any]:
    return GET_ALL_antecedentes_db()
