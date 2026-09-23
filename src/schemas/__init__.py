from .solicitud_schema import (
    SolicitudInput,
    UPDATE_Schema_Optionals,
    VehiculoSchema,
    EquipoComputoSchema,
    DictamenInput,
    RespuestaAutorizacionInput,
    CrearTokenFormularioInput,
)

from .usuario_schema import (
    UsuarioInput,
    UsuarioResponse,
    UpdateUsuarioInput,
    UsuarioData,
)

from .emp_contratista_schema import (
    EmpContratistaInput,
    UpdateEmpContratistainput,
)

from .planta_schema import (
    PlantaInput,
    UpdatePlantaInput,
)

from .personas_schema import (
    PersonInput,
    PersonInputUpdate,
)

from .correspondencia_schema import (
    CorrespondenciaInput,
    UPDATE_correspondenciaInput,
)

from .notificacion_schema import (
    NotificacionCreate,
    MarcarTodasRequest,
    MarcarPorSolicitudRequest,
    DifusionSuperadminRequest,
)

from .superadmin_schema import (
    MantenimientoInput,
    PermisosRolInput,
)

__all__ = [
    "SolicitudInput",
    "UPDATE_Schema_Optionals",
    "VehiculoSchema",
    "EquipoComputoSchema",
    "DictamenInput",
    "RespuestaAutorizacionInput",
    "CrearTokenFormularioInput",
    "EmpContratistaInput",
    "UpdateEmpContratistainput",
    "UsuarioInput",
    "UsuarioResponse",
    "UpdateUsuarioInput",
    "UsuarioData",
    "PlantaInput",
    "UpdatePlantaInput",
    "PersonInput",
    "PersonInputUpdate",
    "CorrespondenciaInput",
    "UPDATE_correspondenciaInput",
    "NotificacionCreate",
    "MarcarTodasRequest",
    "MarcarPorSolicitudRequest",
    "DifusionSuperadminRequest",
    "MantenimientoInput",
    "PermisosRolInput",
]