# src/loaders/__init__.py
from .solicitudes_loaders import (

    CREATE_solicitud_bd,
    UPDATE_solicitud_bd,
    GET_solicitud_bd,
    DELETE_solicitud_bd,
)

from .usuario_loader import  (

    GET_user_db, 
    DELETE_user_db, 
    UPDATE_user_db, 
    CREATE_user_db)

from .roles_loader import (

    GETALL_roles, 
    GETROL_by_nombre, 
    CREATEROL_IF_NoExiste
    )

from .emp_contratista_loader import (

    CREATE_empCont_db,
    GET_empCont_db,
    UPDATE_empCont_db
)


__all__ = [

    "CREATE_solicitud_bd",
    "UPDATE_solicitud_bd",
    "GET_solicitud_bd",
    "DELETE_solicitud_bd",  

    "CREATE_empCont_db",
    "GET_empCont_db",
    "UPDATE_empCont_db",

    "GET_user_db",
    "DELETE_user_db",
    "UPDATE_user_db",
    "CREATE_user_db",

    "GETALL_roles",
    "GETROL_by_nombre",
    "CREATEROL_IF_NoExiste"
]
