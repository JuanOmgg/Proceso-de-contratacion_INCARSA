from pydantic import BaseModel, EmailStr, Field

class LoginInput(BaseModel):
    correo: EmailStr
    contrasena: str = Field(..., min_length=8, description="Contraseña del usuario")

class RecuperacionInput(BaseModel):
    correo: EmailStr

class VerificarCodigoInput(BaseModel):
    correo: EmailStr
    codigo: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="Código de verificación de 6 dígitos")

class RestablecerPasswordInput(BaseModel):
    correo: EmailStr
    codigo: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="Código de restauración de 6 dígitos")
    nueva_contrasena: str = Field(..., min_length=8, description="Nueva contraseña (mínimo 8 caracteres)")

class PerfilUpdateInput(BaseModel):
    num_telefono: str | None = None
    contrasena: str | None = Field(None, min_length=8, description="Nueva contraseña (mínimo 8 caracteres)")
    confirmar_contrasena: str | None = None

class Verificar2FAInput(BaseModel):
    temp_token: str = Field(..., description="Token temporal emitido tras login")
    codigo: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="Código OTP de 6 dígitos")

class Reenviar2FAInput(BaseModel):
    temp_token: str = Field(..., description="Token temporal emitido tras login")

