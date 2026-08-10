from pydantic import BaseModel, EmailStr, field_serializer, ConfigDict
from typing import List, Optional
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
    rol: Optional[str] = None
    fecha_creacion: Optional[datetime] = None

    # Formatea datetime a string solo con la fecha 'DD-MM-YY'
    @field_serializer('fecha_creacion')
    def serialize_fecha(self, fecha: Optional[datetime], _info) -> Optional[str]:
        if fecha:
            return fecha.strftime('%d-%m-%Y')
        return None

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