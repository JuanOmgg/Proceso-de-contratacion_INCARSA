from pydantic import BaseModel
from typing import Optional

class PlantaInput(BaseModel):

    id_empresa: int
    nombre: str

class UpdatePlantaInput(BaseModel):

    id_empresa: Optional[int] = None
    nombre: Optional[str] = None
    