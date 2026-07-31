from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UsuarioCreateSchema(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    rol: str
class UsuarioResponse(BaseModel):

    exito : bool
    mensaje : str