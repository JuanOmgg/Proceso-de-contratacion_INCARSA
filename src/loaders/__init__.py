# src/loaders/__init__.py
from .solicitudes import (
    CREATE_solicitud,
    EDIT_solicitud,
    DELETE_solicitud,
    proceso_evaluo,
)

from .usuario import SAVE_user_db
from .roles_loader import GETALL_roles, GETROL_by_nombre, CREATEROL_IF_NoExiste
