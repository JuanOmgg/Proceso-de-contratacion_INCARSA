from typing import Dict, Any, List
from src.schemas.vehiculo_schema import VehiculoInput, VehiculoUpdate
from src.transformers.vehiculo_transformer import (
    TRANSFORMER_vehiculo,
    TRANSFORMER_vehiculo_patch,
)
from src.loaders.vehiculo_loader import (
    CREATE_vehiculo_db,
    GET_all_vehiculos_db,
    GET_vehiculo_by_id_db,
    UPDATE_vehiculo_db,
    DELETE_vehiculo_db,
    INSERT_documento_vehiculo_db,
)


def CREATE_vehiculo(payload: VehiculoInput) -> dict:
    data_raw = payload.model_dump()
    data_clean = TRANSFORMER_vehiculo(data_raw)
    return CREATE_vehiculo_db(data_clean)


def GET_ALL_vehiculos() -> dict:
    return GET_all_vehiculos_db()


def GET_vehiculo_by_id(vehiculo_id: int) -> dict:
    return GET_vehiculo_by_id_db(vehiculo_id)


def UPDATE_vehiculo(vehiculo_id: int, payload: VehiculoUpdate) -> dict:
    data_raw = payload.model_dump(exclude_unset=True)
    if not data_raw:
        return {"exito": False, "mensaje": "No se proporcionaron datos para actualizar."}
    data_clean = TRANSFORMER_vehiculo_patch(data_raw)
    return UPDATE_vehiculo_db(vehiculo_id, data_clean)


def DELETE_vehiculo(vehiculo_id: int) -> dict:
    return DELETE_vehiculo_db(vehiculo_id)


def AGREGAR_documento_vehiculo(vehiculo_id: int, tipo_doc: str, nom_documento: str) -> dict:
    return INSERT_documento_vehiculo_db(vehiculo_id, tipo_doc, nom_documento)
