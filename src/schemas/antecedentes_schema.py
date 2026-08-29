from datetime import date, datetime
from typing import Optional, List, Any, Union
from pydantic import BaseModel, Field, field_validator


class HistorialSolicitudCreate(BaseModel):
    id_solicitud: Optional[int] = None
    id_empresa: int
    fecha_solicitud: Optional[datetime] = None
    observacion: Optional[str] = None


class AntecedenteCreate(BaseModel):
    id_persona: int
    responsable: Optional[str] = None
    anotaciones: Optional[str] = None
    id_empresa: Optional[int] = None
    ultima_revision: Optional[datetime] = None
    fecha_consulta: Optional[Union[date, datetime, str]] = None

    @field_validator("fecha_consulta", mode="before")
    @classmethod
    def validar_fecha_consulta(cls, v):
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


class AntecedenteUpdate(BaseModel):
    responsable: Optional[str] = None
    anotaciones: Optional[str] = None
    id_empresa: Optional[int] = None
    ultima_revision: Optional[datetime] = None
    fecha_consulta: Optional[Union[date, datetime, str]] = None

    @field_validator("fecha_consulta", mode="before")
    @classmethod
    def validar_fecha_consulta(cls, v):
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


class AntecedenteResponse(BaseModel):
    id: Optional[int] = None
    id_persona: int
    responsable: Optional[str] = None
    anotaciones: Optional[str] = None
    id_empresa: Optional[int] = None
    nombre_empresa: Optional[str] = None
    ultima_revision: Optional[str] = None
    fecha_consulta: Optional[str] = None
    fecha_creacion: Optional[str] = None
    total_solicitudes: int = 0
    historial: List[Any] = Field(default_factory=list)
