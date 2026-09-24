from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class FiltroEstadisticasIngreso(BaseModel):
    fecha_inicio: Optional[date] = Field(None, description="Fecha inicio del rango a consultar")
    fecha_fin: Optional[date] = Field(None, description="Fecha fin del rango a consultar")
    id_planta: Optional[int] = Field(None, description="ID opcional de planta para filtrar")
    estado: Optional[str] = Field("APROBADO", description="Estado de las solicitudes (default: APROBADO, o 'TODOS')")


class RegistroIngresoDiario(BaseModel):
    fecha: str
    id_planta: int
    planta: str
    empresa: Optional[str] = None
    total_personas_unicas: int
    total_solicitudes: int


class PersonaIngresoDetalle(BaseModel):
    id_persona: int
    nombre_completo: str
    tipo_doc: str
    identificacion: str
    cargo: str
    empresa_contratista: str
    radicados: List[str]
    total_solicitudes: int


class EstadisticasResponse(BaseModel):
    exito: bool
    kpis: dict
    serie_tiempo: List[dict]
    distribucion_plantas: List[dict]
    registros: List[RegistroIngresoDiario]
