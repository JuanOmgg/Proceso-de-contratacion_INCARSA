from pydantic import BaseModel, Field
from typing import List, Optional

class EmpContratistaInput(BaseModel):

    nombre: str
    nit: str = ""
    observacion: Optional[str] = ""

class UpdateEmpContratistainput(BaseModel):

    nombre: Optional[str] = None
    nit: Optional[str] = None
    observacion: Optional[str] = None


    