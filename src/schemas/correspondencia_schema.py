from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CorrespondenciaInput(BaseModel):

    tipo_correspondencia: str
    asunto: str
    procedencia: str
    destino: str
    radicado: Optional[str] = None
    fecha_envio: Optional[str] = None

class UPDATE_correspondenciaInput(BaseModel):

    tipo_correspondencia: Optional[str] = None
    asunto: Optional[str] = None
    procedencia: Optional[str] = None
    destino: Optional[str] = None
    radicado: Optional[str] = None
    fecha_envio: Optional[str] = None

