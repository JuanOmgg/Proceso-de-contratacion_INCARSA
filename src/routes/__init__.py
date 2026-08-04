from .usuario_route import router as usuario_router
from .emContr_route import router as emp_contratista_router
from .solicitud_route import router as solicitudes_router
from .planta_route import router as planta_router

__all__=[
    "usuario_router",
    "emp_contratista_router",
    "solicitudes_router",
    "planta_router"
]