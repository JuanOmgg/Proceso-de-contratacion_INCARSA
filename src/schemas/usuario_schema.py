from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UsuarioInput(BaseModel):
    nombres: str
    apellidos: str
    tipo_documento: str
    num_documento: str
    num_telefono: str
    correo: EmailStr
    contrasena: str
    id_rol: int
class UsuarioResponse(BaseModel):
    exito: bool
    mensaje: str

class UpdateUsuarioInput(BaseModel):
    
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    tipo_documento: Optional[str] = None
    num_documento: Optional[str] = None
    num_telefono: Optional[str] = None
    correo: Optional[EmailStr] = None
    contrasena: Optional[str] = None
    id_rol: Optional[int] = None