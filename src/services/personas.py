from src.loaders.personas_loader import CREATE_person_db
from src.transformers.persona_transformer import TRANSFOR_PERSON
from src.schemas.personas_schema import PersonInput


def CREATE_person(payload: PersonInput) -> dict:

    data_raw = payload.model_dump()

    data_clean = TRANSFOR_PERSON(data_raw)

    return CREATE_person_db(data_clean)
