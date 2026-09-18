from typing import Dict, Any, Optional
from src.loaders.inducciones_loader import (
    GET_OR_CREATE_induccion_persona_db,
    UPDATE_induccion_persona_db
)
from src.schemas.inducciones_schema import InduccionUpdate


def OBTENER_INDUCCION_PERSONA(id_persona: int, auto_renovar: bool = False) -> Dict[str, Any]:
    return GET_OR_CREATE_induccion_persona_db(id_persona, auto_renovar=auto_renovar)


def ACTUALIZAR_INDUCCION(id_persona: int, payload: InduccionUpdate, responsable_defecto: str = "Auditor GESCO") -> Dict[str, Any]:
    data_raw = payload.model_dump(exclude_unset=True)
    # Limpiar campos strings vacíos
    data_limpia = {}
    for k, v in data_raw.items():
        if isinstance(v, str):
            v_stripped = v.strip()
            data_limpia[k] = v_stripped if v_stripped else None
        else:
            data_limpia[k] = v
    return UPDATE_induccion_persona_db(id_persona, data_limpia, responsable_defecto=responsable_defecto)
