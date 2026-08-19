from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class VehiculoSchema(BaseModel):
    id_vehiculo: Optional[Union[int, str]] = None
    tipo: Optional[str] = None
    placa: Optional[str] = None
    conductor: Optional[str] = None
    licencia_doc: Optional[Union[str, int]] = None
    documentos: Optional[List[Any]] = None


class EquipoComputoSchema(BaseModel):
    marca: Optional[str] = "Genérica"
    modelo: Optional[str] = "General"
    serie: Optional[str] = "S/N"


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
    empresa_origen: Union[int, str]
    diligenciado_por: Optional[Union[int, str]] = 1
    nivel_de_riesgo: Optional[str] = "Bajo"
    tipo_personal: Optional[str] = "Contratista"
    empresa_contratista: Union[int, str]
    plantas_ids: Optional[List[Union[int, str]]] = Field(default_factory=list)
    personas_ids: Optional[List[Union[int, str]]] = Field(default_factory=list)
    vehiculos_ids: Optional[List[Union[int, str]]] = Field(default_factory=list)
    fecha_inicio: Union[str, date]
    fecha_fin: Union[str, date]
    actividad: str
    is_active: Optional[bool] = True

    vehiculo: Optional[List[Union[Dict[str, Any], VehiculoSchema, int, str]]] = Field(
        default_factory=list
    )
    vehiculos: Optional[List[Union[Dict[str, Any], VehiculoSchema, int, str]]] = None

    eq_computo: Optional[List[Union[Dict[str, Any], EquipoComputoSchema]]] = Field(
        default_factory=list
    )


class UPDATE_Schema_Optionals(BaseSolicitudSchema):
    empresa_origen: Optional[int] = None
    diligenciado_por: Optional[int] = None
    nivel_de_riesgo: Optional[str] = None
    tipo_personal: Optional[str] = None
    empresa_contratista: Optional[int] = None
    plantas_ids: Optional[list[int]] = None
    personas_ids: Optional[list[int]] = None
    vehiculos_ids: Optional[list[int]] = None
    fecha_inicio: Optional[Union[str, date]] = None
    fecha_fin: Optional[Union[str, date]] = None
    actividad: Optional[str] = None
    estado: Optional[str] = None
    is_active: Optional[bool] = None

    vehiculo: Optional[List[Union[VehiculoSchema, Dict[str, Any], int]]] = None
    eq_computo: Optional[List[EquipoComputoSchema]] = None