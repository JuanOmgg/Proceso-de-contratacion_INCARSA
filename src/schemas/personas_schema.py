from typing import Optional
from pydantic import BaseModel

class DocumentosPersonsSchema(BaseModel):
    tipo_doc: str
    nombre_archivo: str

class PersonInput(BaseModel):
    nombre: str
    apellido: str
    tipo_doc: str
    identificacion: str
    cargo: str
    documentos_ids: list[DocumentosPersonsSchema]

class PersonInputUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    tipo_doc: Optional[str] = None
    identificacion: Optional[str] = None
    cargo: Optional[str] = None
    observacion: Optional[str] = None
    documentos_ids: Optional[DocumentosPersonsSchema] = None
