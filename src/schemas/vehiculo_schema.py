from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class DocumentoVehiculoSchema(BaseModel):
    tipo_doc: str = Field(..., json_schema_extra={"example": "soat"})
    nom_documento: Optional[str] = Field(
        None, json_schema_extra={"example": "12345abcdef.pdf"}
    )
    nombre_archivo: Optional[str] = Field(
        None, json_schema_extra={"example": "12345abcdef.pdf"}
    )


class VehiculoInput(BaseModel):
    tipo: str = Field(..., json_schema_extra={"example": "Camioneta"})
    placa: str = Field(..., json_schema_extra={"example": "ABC-123"})
    documentos: Optional[List[DocumentoVehiculoSchema]] = Field(
        default_factory=list,
        json_schema_extra={
            "example": [
                {"tipo_doc": "soat", "nom_documento": "soat_2026.pdf"},
                {
                    "tipo_doc": "tecnomecanica",
                    "nom_documento": "tecno_2026.pdf",
                },
            ]
        },
    )
    documentos_ids: Optional[List[DocumentoVehiculoSchema]] = Field(
        default_factory=list
    )


class VehiculoUpdate(BaseModel):
    tipo: Optional[str] = None
    placa: Optional[str] = None
    documentos: Optional[List[DocumentoVehiculoSchema]] = None
    documentos_ids: Optional[List[DocumentoVehiculoSchema]] = None


# Alias de retrocompatibilidad
vehiculoInput = VehiculoInput