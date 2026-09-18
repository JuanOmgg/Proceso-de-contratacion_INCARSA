from .usuario_route import router as usuario_router
from .emContr_route import router as emp_contratista_router
from .solicitud_route import router as solicitudes_router
from .planta_route import router as planta_router
from .roles_route import router as roles_router
from .vehiculo_router import router as vehiculo_router
from .correspondencia_route import router as correspondencia_router

__all__ = [
    "usuario_router",
    "emp_contratista_router",
    "solicitudes_router",
    "planta_router",
    "roles_router",
    "vehiculo_router",
    "correspondencia_router",
]