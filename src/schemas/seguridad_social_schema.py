from datetime import date, datetime
from typing import Optional, List, Any, Union
from pydantic import BaseModel, Field, field_validator


class HistorialSolicitudSSCreate(BaseModel):
    id_solicitud: Optional[int] = None
    id_empresa: int
    fecha_solicitud: Optional[datetime] = None
    observacion: Optional[str] = None


class SeguridadSocialCreate(BaseModel):
    id_persona: int
    responsable: Optional[str] = None
    anotaciones: Optional[str] = None
    id_empresa: Optional[int] = None
    ultima_revision: Optional[datetime] = None
    fecha_vigencia: Optional[Union[date, datetime, str]] = None

    @field_validator("fecha_vigencia", mode="before")
    @classmethod
    def validar_fecha_vigencia(cls, v):
        if v is None or v == "" or v == "null":
            return None
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            date_part = v.split("T")[0].split(" ")[0].strip()
            return date.fromisoformat(date_part)
        return v


class SeguridadSocialUpdate(BaseModel):
    responsable: Optional[str] = None
    anotaciones: Optional[str] = None
    id_empresa: Optional[int] = None
    ultima_revision: Optional[datetime] = None
    fecha_vigencia: Optional[Union[date, datetime, str]] = None
    fecha_consulta: Optional[Union[date, datetime, str]] = None  # Alias de compatibilidad

    @field_validator("fecha_vigencia", "fecha_consulta", mode="before")
    @classmethod
    def validar_fecha(cls, v):
        if v is None or v == "" or v == "null":
            return None
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            date_part = v.split("T")[0].split(" ")[0].strip()
            return date.fromisoformat(date_part)
        return v


class SeguridadSocialResponse(BaseModel):
    id: Optional[int] = None
    id_persona: int
    responsable: Optional[str] = None
    anotaciones: Optional[str] = None
    id_empresa: Optional[int] = None
    ultima_revision: Optional[str] = None
    fecha_vigencia: Optional[str] = None
    fecha_consulta: Optional[str] = None  # Alias para compatibilidad de frontend
    fecha_creacion: Optional[str] = None
    total_solicitudes: int = 0
    historial: List[Any] = []
