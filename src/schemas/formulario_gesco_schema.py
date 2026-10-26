from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class FormularioGescoInput(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del formulario de inducción")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripción del formulario o alcance")
    vigencia: Optional[int] = Field(365, ge=1, le=3650, description="Vigencia (por defecto 365 = 1 año)")
    tipo_personal: Optional[str] = Field("TODOS", max_length=150, description="Tipo de personal: Contratista, Proveedor, Visitante, Interno, o separados por coma, o TODOS")
    Tipo_pregunta: Optional[str] = Field("GENERAL", max_length=45, description="Categoría temática general del formato")
    cantidad_preguntas: Optional[int] = Field(None, ge=1, le=500, description="Cantidad total de preguntas aleatorias a evaluar")
    config_cuotas: Optional[Dict[str, int]] = Field(None, description="Cuotas de aleatoriedad por categoría {'SST': 2, 'AMBIENTAL': 2, ...}")
    is_active: Optional[bool] = Field(True, description="Estado activo del formulario")
    es_interno: Optional[bool] = Field(False, description="Indica si es un diálogo o formulario interno para trabajadores de planta")
    fecha_limite: Optional[Any] = Field(None, description="Fecha/hora límite opcional para responder el formulario")
    id_creador: Optional[int] = Field(None, description="ID del usuario creador")
    creador_nombre: Optional[str] = Field(None, max_length=255, description="Nombre del usuario creador del formulario")


class FormularioGescoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    vigencia: Optional[int] = Field(None, ge=1, le=3650)
    tipo_personal: Optional[str] = Field(None, max_length=150)
    Tipo_pregunta: Optional[str] = Field(None, max_length=45)
    cantidad_preguntas: Optional[int] = Field(None, ge=1, le=500)
    config_cuotas: Optional[Dict[str, int]] = None
    is_active: Optional[bool] = None
    es_interno: Optional[bool] = None
    fecha_limite: Optional[Any] = None
    id_creador: Optional[int] = None
    creador_nombre: Optional[str] = None


class FormularioGescoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    vigencia: int = 365
    tipo_personal: str = "TODOS"
    Tipo_pregunta: str = "GENERAL"
    cantidad_preguntas: Optional[int] = None
    config_cuotas: Optional[Dict[str, int]] = None
    is_active: bool = True
    es_interno: bool = False
    fecha_limite: Optional[Any] = None
    id_creador: Optional[int] = None
    creador_nombre: Optional[str] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
