from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class VehiculoSchema(BaseModel):
    id: Optional[Union[int, str]] = None
    id_vehiculo: Optional[Union[int, str]] = None
    tipo: Optional[str] = None
    placa: Optional[str] = None
    conductor: Optional[str] = None
    licencia_doc: Optional[Union[str, int]] = None
    documentos: Optional[List[Any]] = None
    autorizado: Optional[Union[bool, int, str]] = True
    motivo: Optional[str] = None
    motivo_rechazo: Optional[str] = None


class EquipoComputoSchema(BaseModel):
    model_config = {"extra": "ignore"}
    id: Optional[Union[int, str]] = None
    marca: Optional[str] = "Genérica"
    modelo: Optional[str] = "General"
    serie: Optional[str] = "S/N"


class BaseSolicitudSchema(BaseModel):
    model_config = {"extra": "ignore"}
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
    codigo: Optional[str] = None
    codigo_radicado: Optional[str] = None
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
    observaciones: Optional[str] = None
    observacion: Optional[str] = None
    estado: Optional[str] = "ENVIADO"
    is_active: Optional[bool] = True

    personas: Optional[List[Any]] = None
    ingresantes: Optional[List[Any]] = None

    vehiculo: Optional[List[Union[Dict[str, Any], VehiculoSchema, int, str]]] = Field(
        default_factory=list
    )
    vehiculos: Optional[List[Union[Dict[str, Any], VehiculoSchema, int, str]]] = None

    eq_computo: Optional[List[Union[Dict[str, Any], EquipoComputoSchema]]] = Field(
        default_factory=list
    )
    equipos: Optional[List[Union[Dict[str, Any], EquipoComputoSchema]]] = None
    computos: Optional[List[Union[Dict[str, Any], EquipoComputoSchema]]] = None


class UPDATE_Schema_Optionals(BaseSolicitudSchema):
    model_config = {"extra": "ignore"}
    codigo: Optional[str] = None
    codigo_radicado: Optional[str] = None
    empresa_origen: Optional[Union[int, str]] = None
    diligenciado_por: Optional[Union[int, str]] = None
    nivel_de_riesgo: Optional[str] = None
    tipo_personal: Optional[str] = None
    empresa_contratista: Optional[Union[int, str]] = None
    plantas_ids: Optional[List[Union[int, str]]] = None
    personas_ids: Optional[List[Union[int, str]]] = None
    vehiculos_ids: Optional[List[Union[int, str]]] = None
    fecha_inicio: Optional[Union[str, date]] = None
    fecha_fin: Optional[Union[str, date]] = None
    actividad: Optional[str] = None
    observaciones: Optional[str] = None
    observacion: Optional[str] = None
    estado: Optional[str] = None
    is_active: Optional[bool] = None

    personas: Optional[List[Any]] = None
    ingresantes: Optional[List[Any]] = None

    vehiculo: Optional[List[Union[VehiculoSchema, Dict[str, Any], int, str]]] = None
    vehiculos: Optional[List[Union[VehiculoSchema, Dict[str, Any], int, str]]] = None
    eq_computo: Optional[List[Union[EquipoComputoSchema, Dict[str, Any]]]] = None
    equipos: Optional[List[Union[EquipoComputoSchema, Dict[str, Any]]]] = None
    computos: Optional[List[Union[EquipoComputoSchema, Dict[str, Any]]]] = None
    token_edicion: Optional[str] = None


class DictamenInput(BaseModel):
    id_planta: Optional[int] = None
    rol: str
    decision: str
    motivo_rechazo: Optional[str] = None
    motivo_devolucion: Optional[str] = None
    observacion: Optional[str] = None
    id_usuario: Optional[int] = None
    nombre_revisor: Optional[str] = None
    personas: Optional[List[Dict[str, Any]]] = None
    vehiculos: Optional[List[Dict[str, Any]]] = None
