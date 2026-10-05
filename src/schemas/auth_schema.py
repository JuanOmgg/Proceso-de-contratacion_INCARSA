from pydantic import BaseModel, EmailStr, Field

class LoginInput(BaseModel):
    correo: EmailStr
    contrasena: str = Field(..., min_length=8, description="Contraseña del usuario")

class RecuperacionInput(BaseModel):
    correo: EmailStr

class VerificarCodigoInput(BaseModel):
    correo: EmailStr
    codigo: str = Field(..., min_length=6, max_length=8, description="Código de verificación")

class RestablecerPasswordInput(BaseModel):
    correo: EmailStr
    codigo: str = Field(..., min_length=6, max_length=8, description="Código de restauración")
    nueva_contrasena: str = Field(..., min_length=6, description="Nueva contraseña")

class PerfilUpdateInput(BaseModel):
    num_telefono: str | None = None
    contrasena: str | None = None
    confirmar_contrasena: str | None = None

class Verificar2FAInput(BaseModel):
    temp_token: str = Field(..., description="Token temporal emitido tras login")
    codigo: str = Field(..., min_length=6, max_length=6, description="Código OTP de 6 dígitos")

class Reenviar2FAInput(BaseModel):
    temp_token: str = Field(..., description="Token temporal emitido tras login")

