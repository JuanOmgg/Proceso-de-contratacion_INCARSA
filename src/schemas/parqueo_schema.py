from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VehiculoIntInput(BaseModel):
    placa: str = Field(..., min_length=6, max_length=10, description="Placa o identificador del vehículo")
    zona: str = Field(..., min_length=2, max_length=50, description="Zona asignada oficial por defecto")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripción adicional")


class VehiculoIntUpdate(BaseModel):
    placa: Optional[str] = Field(None, min_length=6, max_length=20)
    zona: Optional[str] = Field(None, min_length=2, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=255)


class VehiculoIntResponse(BaseModel):
    id: int
    placa: str
    zona: str
    descripcion: Optional[str]
    created_at: Optional[datetime] = None


class VehiculoReporteItem(BaseModel):
    id_vehiculo: Optional[int] = None
    vehiculo: str = Field(..., min_length=2, max_length=20)
    zona_asignada: Optional[str] = Field(None, max_length=50)
    se_quedo: bool = Field(True, description="Si pernoctó en esta zona")
    observacion: Optional[str] = Field("", max_length=500)


class ReporteZonaInput(BaseModel):
    fecha: Optional[str] = Field(None, description="Fecha del reporte (YYYY-MM-DD)")
    zona: str = Field(..., min_length=2, max_length=50, description="Zona reportada")
    reportador: str = Field(..., min_length=2, max_length=100, description="Nombre de quien reporta")
    observaciones: Optional[str] = Field("", description="Observaciones generales del turno")
    vehiculos: List[VehiculoReporteItem] = Field(..., min_items=1, description="Lista de vehículos evaluados en esta zona")
