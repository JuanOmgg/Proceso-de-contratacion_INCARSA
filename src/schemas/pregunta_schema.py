from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class OpcionPreguntaInput(BaseModel):
    id: Optional[int] = Field(None, description="ID de la opción si ya existe (para actualización)")
    opcion: str = Field(..., min_length=1, max_length=255, description="Texto de la opción de respuesta")
    is_correct: bool = Field(False, description="Indica si esta opción es la respuesta correcta")


class OpcionPreguntaResponse(BaseModel):
    id: int
    id_pregunta: int
    opcion: str
    is_correct: bool
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


class PreguntaInput(BaseModel):
    id_formulario: int = Field(..., description="ID del formulario GESCO al que pertenece la pregunta")
    pregunta: str = Field(..., min_length=3, max_length=500, description="Enunciado de la pregunta")
    tipo_respuesta: str = Field("MULTIPLE", max_length=20, description="MULTIPLE, UNICA, VERDADERO_FALSO, TEXTO")
    tipo_pregunta: str = Field("GENERAL", max_length=50, description="SST, AMBIENTAL, SEGURIDAD_VIAL, CALIDAD, BIOMECANICA, GENERAL")
    imagen_url: Optional[str] = Field(None, max_length=500, description="URL de imagen ilustrativa")
    video_url: Optional[str] = Field(None, max_length=500, description="URL de video (YouTube o directo)")
    es_calificable: bool = Field(True, description="Indica si la pregunta suma al puntaje de la evaluación")
    estado: bool = Field(True, description="Estado activo de la pregunta")
    opciones: List[OpcionPreguntaInput] = Field(default_factory=list, description="Lista de opciones de respuesta")


class PreguntaUpdate(BaseModel):
    pregunta: Optional[str] = Field(None, min_length=3, max_length=500)
    tipo_respuesta: Optional[str] = Field(None, max_length=20)
    tipo_pregunta: Optional[str] = Field(None, max_length=50)
    imagen_url: Optional[str] = Field(None, max_length=500)
    video_url: Optional[str] = Field(None, max_length=500)
    es_calificable: Optional[bool] = None
    estado: Optional[bool] = None
    opciones: Optional[List[OpcionPreguntaInput]] = None


class PreguntaResponse(BaseModel):
    id: int
    id_formulario: int
    pregunta: str
    tipo_respuesta: str
    tipo_pregunta: str = "GENERAL"
    imagen_url: Optional[str] = None
    video_url: Optional[str] = None
    es_calificable: bool = True
    estado: bool
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    opciones: List[OpcionPreguntaResponse] = Field(default_factory=list)


class PreguntaSyncItem(BaseModel):
    id: Optional[int] = Field(None, description="ID de la pregunta si ya existe")
    pregunta: str = Field(..., min_length=3, max_length=500)
    tipo_respuesta: str = Field("MULTIPLE", max_length=20)
    tipo_pregunta: str = Field("GENERAL", max_length=50)
    imagen_url: Optional[str] = Field(None, max_length=500)
    video_url: Optional[str] = Field(None, max_length=500)
    es_calificable: bool = Field(True)
    estado: bool = Field(True)
    opciones: List[OpcionPreguntaInput] = Field(default_factory=list)


class PreguntasSyncPayload(BaseModel):
    preguntas: List[PreguntaSyncItem] = Field(..., description="Lista completa de preguntas a sincronizar para el formulario")

