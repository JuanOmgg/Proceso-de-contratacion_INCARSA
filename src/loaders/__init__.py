# src/loaders/__init__.py
from .solicitudes import (
    CREATE_solicitud,
    EDIT_solicitud,
    DELETE_solicitud,
    proceso_evaluo,
)

from .solicitudes_loaders import (

    CREATE_solicitud_bd,
    UPDATE_solicitud_bd,
    GET_solicitud_bd,
    DELETE_solicitud_bd,
)

from .usuario import  GET_user_db, DELETE_user_db

from .usuario_loader import  GET_user_db, DELETE_user_db

from .roles_loader import GETALL_roles, GETROL_by_nombre, CREATEROL_IF_NoExiste
