from datetime import date, datetime
from typing import Optional, List, Any, Union
from pydantic import BaseModel, Field, field_validator


class InduccionCreate(BaseModel):
    id_persona: int
    responsable: Optional[str] = None
    anotaciones: Optional[str] = None
    id_empresa: Optional[int] = None
    fecha_induccion: Optional[Union[date, datetime, str]] = None
    fecha_vigencia: Optional[Union[date, datetime, str]] = None

    @field_validator("fecha_induccion", "fecha_vigencia", mode="before")
    @classmethod
    def validar_fechas(cls, v):
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


class InduccionUpdate(BaseModel):
    responsable: Optional[str] = None
    anotaciones: Optional[str] = None
    id_empresa: Optional[int] = None
    fecha_induccion: Optional[Union[date, datetime, str]] = None
    fecha_vigencia: Optional[Union[date, datetime, str]] = None

    @field_validator("fecha_induccion", "fecha_vigencia", mode="before")
    @classmethod
    def validar_fechas(cls, v):
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


class InduccionResponse(BaseModel):
    id: Optional[int] = None
    id_persona: int
    responsable: Optional[str] = None
    anotaciones: Optional[str] = None
    id_empresa: Optional[int] = None
    nombre_empresa: Optional[str] = None
    fecha_induccion: Optional[str] = None
    fecha_vigencia: Optional[str] = None
    ultima_revision: Optional[str] = None
    fecha_creacion: Optional[str] = None
