from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class MantenimientoInput(BaseModel):
    activo: bool
    tipo: Optional[str] = "general"
    modulos: Optional[List[str]] = []
    mensaje: Optional[str] = None
    tiempo: Optional[str] = None
    temporizador_minutos: Optional[int] = None
    temporizador_fin: Optional[str] = None


class PermisosRolInput(BaseModel):
    permisos: Optional[List[Dict[str, Any]]] = None
    modulos: Optional[Dict[str, bool]] = None
    acciones: Optional[Dict[str, bool]] = None

class DosPasosConfigInput(BaseModel):
    activo: bool

