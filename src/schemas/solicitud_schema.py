from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


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
    empresa_origen: Optional[Union[int, str]] = 1
    diligenciado_por: Optional[Union[int, str]] = 1
    nivel_de_riesgo: Optional[str] = "Bajo"
    tipo_personal: Optional[str] = "Contratista"
    empresa_contratista: Optional[Union[int, str]] = None
    plantas_ids: Optional[List[Union[int, str]]] = Field(default_factory=list)
    personas_ids: Optional[List[Union[int, str]]] = Field(default_factory=list)
    vehiculos_ids: Optional[List[Union[int, str]]] = Field(default_factory=list)
    fecha_inicio: Optional[Union[str, date]] = None
    fecha_fin: Optional[Union[str, date]] = None
    actividad: str
    observaciones: Optional[str] = None
    observacion: Optional[str] = None
    estado: Optional[str] = "ENVIADO"
    is_active: Optional[bool] = True

    @model_validator(mode="before")
    @classmethod
    def preparar_datos_solicitud(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("empresa_origen"):
                data["empresa_origen"] = 1
            if not data.get("fecha_inicio") and data.get("fecha_ingreso"):
                data["fecha_inicio"] = data["fecha_ingreso"]
            if not data.get("fecha_fin") and data.get("fecha_salida"):
                data["fecha_fin"] = data["fecha_salida"]
            if not data.get("nivel_de_riesgo") and data.get("nivel_riesgo"):
                data["nivel_de_riesgo"] = data["nivel_riesgo"]
            if not data.get("plantas_ids") and data.get("sub_plantas"):
                data["plantas_ids"] = data["sub_plantas"]
        return data

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
    id_planta: Optional[Union[int, str]] = None
    plantas_ids: Optional[List[int]] = None
    rol: str
    decision: str
    es_edicion: Optional[bool] = False
    motivo_rechazo: Optional[str] = None
    motivo_devolucion: Optional[str] = None
    observacion: Optional[str] = None
    id_usuario: Optional[int] = None
    nombre_revisor: Optional[str] = None
    personas: Optional[List[Dict[str, Any]]] = None
    vehiculos: Optional[List[Dict[str, Any]]] = None


class RespuestaAutorizacionInput(BaseModel):
    acepto: bool
    motivo_rechazo: Optional[str] = None


class CrearTokenFormularioInput(BaseModel):
    duracion_horas: Optional[float] = 24.0
    destinatario_nombre: Optional[str] = None
    destinatario_email: Optional[str] = None
    fecha_expiracion_personalizada: Optional[str] = None
    id_empresa_contratista: Optional[int] = None
