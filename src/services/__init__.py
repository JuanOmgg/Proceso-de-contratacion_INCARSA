from .solicitudes import (

    CREATE_solicitud,
    EDIT_solicitud,
    DELETE_solicitud,
    proceso_evaluo
)

from .usuario import (
    
    GET_user_db, 
    DELETE_user_db
    )

__all__ = [

    "CREATE_solicitud",
    "EDIT_solicitud",
    "DELETE_solicitud",
    "proceso_evaluo",

    "GET_user_db",
    "DELETE_user_db"

]