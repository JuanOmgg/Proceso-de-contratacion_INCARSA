from pydantic import BaseModel, EmailStr, field_serializer, field_validator, ConfigDict, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class UsuarioInput(BaseModel):
    nombres: str
    apellidos: str
    tipo_documento: str
    num_documento: str
    num_telefono: str
    correo: EmailStr
    contrasena: str
    id_rol: int
    plantas_ids: Optional[List[int]] = Field(default_factory=list)

    @field_validator('num_documento')
    @classmethod
    def validar_num_documento(cls, v: str) -> str:
        if v is not None:
            v_str = str(v).strip()
            if '.' in v_str or ',' in v_str or not v_str.isdigit():
                raise ValueError("El número de documento no debe contener puntos ni comas, solo números.")
            return v_str
        return v

# Modelo individual para la lectura del usuario
class UsuarioData(BaseModel):
    id: int
    nombre_completo: Optional[str] = None
    nombres: str
    apellidos: str
    tipo_documento: str
    num_documento: str
    num_telefono: str
    correo: EmailStr
    id_rol: Optional[int] = None
    rol: Optional[str] = None
    is_active: Optional[bool] = True
    fecha_creacion: Optional[Any] = None
    plantas_ids: Optional[List[int]] = Field(default_factory=list)
    plantas: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    # Formatea datetime a string solo con la fecha 'DD-MM-YY'
    @field_serializer('fecha_creacion')
    def serialize_fecha(self, fecha: Optional[Any], _info) -> Optional[str]:
        if isinstance(fecha, datetime):
            return fecha.strftime('%d-%m-%Y')
        return str(fecha) if fecha else None

    model_config = ConfigDict(from_attributes=True)
    
class UsuarioResponse(BaseModel):
    exito: bool
    mensaje: str
    datos_user: Optional[List[UsuarioData]]

class UpdateUsuarioInput(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    tipo_documento: Optional[str] = None
    num_documento: Optional[str] = None
    num_telefono: Optional[str] = None
    correo: Optional[EmailStr] = None
    contrasena: Optional[str] = None
    id_rol: Optional[int] = None
    is_active: Optional[bool] = None
    plantas_ids: Optional[List[int]] = None

    @field_validator('num_documento')
    @classmethod
    def validar_num_documento(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_str = str(v).strip()
            if '.' in v_str or ',' in v_str or not v_str.isdigit():
                raise ValueError("El número de documento no debe contener puntos ni comas, solo números.")
            return v_str
        return v