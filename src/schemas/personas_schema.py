from typing import Optional, List, Any
from pydantic import BaseModel, Field, EmailStr

class DocumentosPersonsSchema(BaseModel):
    tipo_doc: Optional[str] = "Cédula"
    nombre_archivo: Optional[str] = ""
    vigencia: Optional[str] = None

class PersonInput(BaseModel):
    nombre: str
    apellido: str
    tipo_doc: Optional[str] = "CC"
    identificacion: str
    cargo: Optional[str] = "Personal"
    correo: EmailStr
    observacion: Optional[str] = None
    documentos_ids: Optional[List[Any]] = Field(default_factory=list)

class PersonInputUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    tipo_doc: Optional[str] = None
    identificacion: Optional[str] = None
    cargo: Optional[str] = None
    correo: Optional[EmailStr] = None
    observacion: Optional[str] = None
    documentos_ids: Optional[List[Any]] = None
