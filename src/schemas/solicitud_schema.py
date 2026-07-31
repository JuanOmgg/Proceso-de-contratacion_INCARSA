from pydantic import BaseModel, Field
from typing import List, Optional

class VehiculoSchema(BaseModel):
    tipo: Optional[str] = Field(default="", example="Camioneta")
    placa: Optional[str] = Field(default="", example="ABC-123")

class PersonaSchema(BaseModel):
    ap_nombre: str = Field(..., example="Carlos Mendoza")
    tipo_doc: str = Field(..., example="CC")
    identificacion: int = Field(..., example=1012345678)
    cargo: str = Field(..., example="Técnico Electricista")

class EquipoComputoSchema(BaseModel):
    marca: str = Field(..., example="Lenovo")
    modelo: str = Field(..., example="ThinkPad E14")
    serie: str = Field(..., example="SN-987654321")

# Esquema Principal de Solicitud
class SolicitudInput(BaseModel):
    empresa_origen: str = Field(..., example="INCARSA")
    diligenciado_por: str = Field(..., example="Juan Pérez")
    nivel_de_riesgo: str = Field(..., example="Alto")
    tipo_de_persona: str = Field(..., example="Contratista")
    empresa_contratista: Optional[str] = Field(default="", example="Soluciones Industriales SAS")
    planta_a_visitar: str = Field(..., example="Planta Central")
    fecha_inicio: str = Field(..., example="01/08/2026")
    fecha_fin: str = Field(..., example="24/08/2026")
    actividad: str = Field(..., example="Mantenimiento preventivo")
    vehiculo: Optional[VehiculoSchema] = None
    personas: List[PersonaSchema] = Field(
        default_factory=list,
        example=[
            {
                "ap_nombre": "Carlos Mendoza",
                "tipo_doc": "CC",
                "identificacion": 1012345678,
                "cargo": "Técnico Electricista"
            }
        ]
    )
    eq_computo: List[EquipoComputoSchema] = Field(
        default_factory=list,
        example=[
            {
                "marca": "Lenovo",
                "modelo": "ThinkPad E14",
                "serie": "SN-987654321"
            }
        ]
    )

class UPDATE_Schema_Optionals(BaseModel):
    empresa_origen: Optional[str] = None
    diligenciado_por: Optional[str] = None
    nivel_de_riesgo: Optional[str] = None
    tipo_de_persona: Optional[str] = None
    empresa_contratista: Optional[str] = None
    planta_a_visitar: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    actividad: Optional[str] = None
    estado: Optional[str] = None

    vehiculo: Optional[VehiculoSchema] = None
    personas: Optional[List[PersonaSchema]] = None
    eq_computo: Optional[List[EquipoComputoSchema]] = None
