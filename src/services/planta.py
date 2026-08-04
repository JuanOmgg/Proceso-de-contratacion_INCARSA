from src.transformers import TRANSFORM_PLANTA
from src.schemas import PlantaInput
from src.loaders.planta_loader import CREATE_planta_db

def CREATE_planta(payload: PlantaInput) -> dict:

    data_raw = payload.model_dump()

    data_clean = TRANSFORM_PLANTA(data_raw)

    return CREATE_planta_db(data_clean)