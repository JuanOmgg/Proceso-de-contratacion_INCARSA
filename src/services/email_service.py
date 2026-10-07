"""
src.services.email_service
Módulo puente / re-export de src.utils.email_service.
Centraliza la lógica de correos en un único lugar para evitar código duplicado
manteniendo total retrocompatibilidad con cualquier import existente.
"""
from src.utils.email_service import *  # noqa: F401, F403
