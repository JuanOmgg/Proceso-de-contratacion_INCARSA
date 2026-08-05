from datetime import date, datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class DocumentoPersonaSchema(BaseModel):
    tipo_doc: str = Field(..., json_schema_extra={"example": "cedula"})
    nombre_archivo: str = Field(..., json_schema_extra={"example": "a1b2c3d4.pdf"})
    url_acceso: Optional[str] = Field(None, json_schema_extra={"example": "/uploads/documentos/cedulas/a1b2c3d4.pdf"})


class PersonaSchema(BaseModel):
    ap_nombre: str
    tipo_doc: str = Field(..., json_schema_extra={"example": "CC"})
    identificacion: Union[str, int] = Field(
        ..., json_schema_extra={"example": "1012345678"}
    )  
    cargo: str
    documentos: Optional[List[DocumentoPersonaSchema]] = []

    @field_validator("identificacion", mode="before")
    @classmethod
    def normalizar_identificacion(cls, v):
        return str(v) if v is not None else ""


class VehiculoSchema(BaseModel):
    tipo: str
    placa: str


class EquipoComputoSchema(BaseModel):
    marca: str
    modelo: str
    serie: str


class BaseSolicitudSchema(BaseModel):
    fecha_inicio: Optional[Union[str, date]] = None
    fecha_fin: Optional[Union[str, date]] = None

    @field_validator("fecha_inicio", "fecha_fin", mode="before")
    @classmethod
    def normalizar_fechas_input(cls, val_fecha: Optional[Union[str, date]]):
        if not val_fecha:
            return None

        # Si ya es un objeto date real, no lo toca
        if isinstance(val_fecha, date):
            return val_fecha

        if isinstance(val_fecha, str):
            val_limpia = val_fecha.strip().split("T")[0].split(" ")[0]
            fecha_normalizada = val_limpia.replace("/", "-")
            formatos = ["%Y-%m-%d", "%d-%m-%Y"]

            for fmt in formatos:
                try:
                    return datetime.strptime(fecha_normalizada, fmt).date()
                except ValueError:
                    continue

        raise ValueError(
            f"Formato de fecha inválido: {val_fecha}. Use YYYY-MM-DD o DD/MM/YYYY."
        )


class SolicitudInput(BaseSolicitudSchema):

    empresa_origen: int
    diligenciado_por: int
    nivel_de_riesgo: str
    tipo_personal: str = Field(
        ..., json_schema_extra={"example": "Contratista"}
    )
    empresa_contratista: int
    plantas_ids: list[int]
    fecha_inicio: Union[str, date]
    fecha_fin: Union[str, date]
    actividad: str
    is_active: Optional[bool] = True

    vehiculo: List[VehiculoSchema] = Field(
        default_factory=list,
        json_schema_extra={
            "example": [{"tipo": "Camioneta", "placa": "ABC-123"}]
        },
    )

    personas: List[PersonaSchema] = Field(
        default_factory=list,
        json_schema_extra={
            "example": [
                {
                    "ap_nombre": "Carlos Mendoza",
                    "tipo_doc": "CC",
                    "identificacion": "1012345678",
                    "cargo": "Técnico Electricista",
                }
            ]
        },
    )

    eq_computo: List[EquipoComputoSchema] = Field(
        default_factory=list,
        json_schema_extra={
            "example": [
                {
                    "marca": "Lenovo",
                    "modelo": "ThinkPad E14",
                    "serie": "SN-987654321",
                }
            ]
        },
    )


class UPDATE_Schema_Optionals(BaseSolicitudSchema):
    empresa_origen: Optional[int] = None
    diligenciado_por: Optional[int] = None
    nivel_de_riesgo: Optional[str] = None
    tipo_personal: Optional[str] = None
    empresa_contratista: Optional[int] = None
    plantas_ids: Optional[list[int]] = None
    fecha_inicio: Optional[Union[str, date]] = None
    fecha_fin: Optional[Union[str, date]] = None
    actividad: Optional[str] = None
    estado: Optional[str] = None
    is_active: Optional[bool] = None

    vehiculo: Optional[List[VehiculoSchema]] = None
    personas: Optional[List[PersonaSchema]] = None
    eq_computo: Optional[List[EquipoComputoSchema]] = None