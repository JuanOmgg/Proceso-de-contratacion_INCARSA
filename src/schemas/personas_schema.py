from typing import Optional, List, Any
from pydantic import BaseModel, Field, EmailStr, field_validator

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

    @field_validator('identificacion')
    @classmethod
    def validar_identificacion(cls, v: str) -> str:
        if v is not None:
            v_str = str(v).strip()
            if '.' in v_str or ',' in v_str or not v_str.isdigit():
                raise ValueError("El número de documento de identidad no debe contener puntos ni comas, solo números.")
            return v_str
        return v

class PersonInputUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    tipo_doc: Optional[str] = None
    identificacion: Optional[str] = None
    cargo: Optional[str] = None
    correo: Optional[EmailStr] = None
    observacion: Optional[str] = None
    documentos_ids: Optional[List[Any]] = None

    @field_validator('identificacion')
    @classmethod
    def validar_identificacion(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_str = str(v).strip()
            if '.' in v_str or ',' in v_str or not v_str.isdigit():
                raise ValueError("El número de documento de identidad no debe contener puntos ni comas, solo números.")
            return v_str
        return v
