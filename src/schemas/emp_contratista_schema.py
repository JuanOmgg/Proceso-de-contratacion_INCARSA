from pydantic import BaseModel, Field
from typing import List, Optional

class EmpContratistaInput(BaseModel):

    nombre: str
    observacion: str

class UpdateEmpContratistainput(BaseModel):

    nombre: Optional[str] = None
    observacion: Optional[str] = None

    