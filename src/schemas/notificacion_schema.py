from typing import List, Optional
from pydantic import BaseModel


class NotificacionCreate(BaseModel):
    titulo: str
    mensaje: str
    tipo: Optional[str] = "info"
    enlace: Optional[str] = None
    archivo_url: Optional[str] = None
    archivo_nombre: Optional[str] = None
    id_usuario: Optional[int] = None
    rol_destino: Optional[int] = None


class MarcarTodasRequest(BaseModel):
    id_usuario: Optional[int] = None
    id_rol: Optional[int] = None


class MarcarPorSolicitudRequest(BaseModel):
    id_o_codigo: str
    id_usuario: Optional[int] = None
    id_rol: Optional[int] = None


class DifusionSuperadminRequest(BaseModel):
    titulo: str
    mensaje: str
    tipo: Optional[str] = "info"
    enlace: Optional[str] = None
    archivo_url: Optional[str] = None
    archivo_nombre: Optional[str] = None
    destinatario_tipo: str = "rol"  # "rol", "usuarios", "todos"
    roles_ids: Optional[List[int]] = None
    usuarios_ids: Optional[List[int]] = None
