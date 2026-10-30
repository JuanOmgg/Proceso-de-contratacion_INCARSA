from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import date, datetime

from src.schemas.parqueo_schema import (
    VehiculoIntInput,
    VehiculoIntUpdate,
    ReporteZonaInput
)
from src.loaders.parqueo_loader import (
    GET_vehiculos_int_db,
    CREATE_vehiculo_int_db,
    UPDATE_vehiculo_int_db,
    DELETE_vehiculo_int_db,
    GET_ZONAS_PARQUEO_DB,
    GET_VEHICULOS_PARA_ZONA_DB,
    CREAR_REPORTE_ZONA_DB,
    GET_REPORTES_PARQUEO_DB,
    GET_DETALLE_REPORTE_ZONA_DB,
    DELETE_REPORTE_PARQUEO_DB,
    GENERAR_EXCEL_AUDITORIA_PARQUEO_DB
)

router = APIRouter(prefix="/parqueos", tags=["Módulo de Parqueos"])


# ------------------------------------------------------------------------------
# 1. Catálogo de Vehículos Internos
# ------------------------------------------------------------------------------

@router.get("/vehiculos", status_code=status.HTTP_200_OK)
def listar_vehiculos_internos():
    """Retorna la lista de vehículos internos con su zona asignada."""
    res = GET_vehiculos_int_db()
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=res.get("mensaje"))
    return res


@router.post("/vehiculos", status_code=status.HTTP_201_CREATED)
def crear_vehiculo_interno(payload: VehiculoIntInput):
    """Registra un nuevo vehículo interno y su zona asignada oficial."""
    res = CREATE_vehiculo_int_db(payload.model_dump())
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.put("/vehiculos/{id_vehiculo}", status_code=status.HTTP_200_OK)
def actualizar_vehiculo_interno(id_vehiculo: int, payload: VehiculoIntUpdate):
    """Actualiza datos o zona asignada de un vehículo interno."""
    res = UPDATE_vehiculo_int_db(id_vehiculo, payload.model_dump(exclude_unset=True))
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.delete("/vehiculos/{id_vehiculo}", status_code=status.HTTP_200_OK)
def eliminar_vehiculo_interno(id_vehiculo: int):
    """Elimina o desactiva un vehículo interno."""
    res = DELETE_vehiculo_int_db(id_vehiculo)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.get("/zonas", status_code=status.HTTP_200_OK)
def obtener_zonas_disponibles():
    """Retorna las zonas de parqueo disponibles."""
    zonas = GET_ZONAS_PARQUEO_DB()
    return {"exito": True, "zonas": zonas}


@router.get("/vehiculos-por-zona/{zona:path}", status_code=status.HTTP_200_OK)
def obtener_vehiculos_por_zona(
    zona: str,
    fecha: Optional[str] = Query(None, description="Fecha del reporte para verificar exclusiones de vehículos ya pernoctados")
):
    """
    Retorna los vehículos asignados a una zona para preparar el reporte nocturno,
    más los vehículos de otras zonas para permitir seleccionar si alguno pernoctó aquí.
    Excluye automáticamente los vehículos que ya hayan pernoctado en otra zona en esa fecha.
    """
    res = GET_VEHICULOS_PARA_ZONA_DB(zona, fecha)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


# ------------------------------------------------------------------------------
# 2. Reportes Nocturnos por Zona (Tabla principal y detalles)
# ------------------------------------------------------------------------------

@router.post("/reportar-zona", status_code=status.HTTP_200_OK)
def registrar_reporte_zona(payload: ReporteZonaInput):
    """
    Registra el reporte nocturno para una zona específica.
    """
    res = CREAR_REPORTE_ZONA_DB(payload.model_dump())
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.get("/reportes", status_code=status.HTTP_200_OK)
def consultar_reportes_parqueo(
    fecha: Optional[str] = Query(None, description="Fecha específica (YYYY-MM-DD)"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio rango (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin rango (YYYY-MM-DD)"),
    zona: Optional[str] = Query(None, description="Filtro por zona"),
    busqueda: Optional[str] = Query(None, description="Filtro de texto libre (reportador, zona)"),
    limit: int = Query(200, ge=1, le=1000)
):
    """
    Tabla principal solicitada:
    Enlista fecha, zona, nombre en 'reportador' y totales evaluados.
    """
    res = GET_REPORTES_PARQUEO_DB(
        fecha=fecha,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        zona=zona,
        busqueda=busqueda,
        limit=limit
    )
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=res.get("mensaje"))
    return res


@router.get("/reportes/{id_reporte}/detalle", status_code=status.HTTP_200_OK)
def obtener_detalle_reporte_zona(id_reporte: int):
    """
    Acción 'Ver carros de la zona':
    Muestra:
    - Cuáles carros se quedaron aquí y cuáles no ese día.
    - Si se quedó en su zona: SIN observación.
    - Si pernoctó en una zona diferente: observación en color AMARILLO.
    - Si al final del día no pernoctó en ninguna zona: observación en color ROJO ('No pernoctó en ninguna zona').
    """
    res = GET_DETALLE_REPORTE_ZONA_DB(id_reporte)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res.get("mensaje"))
    return res


@router.delete("/reportes/{id_reporte}", status_code=status.HTTP_200_OK)
def eliminar_reporte_parqueo(id_reporte: int):
    """Elimina un reporte nocturno."""
    res = DELETE_REPORTE_PARQUEO_DB(id_reporte)
    if not res.get("exito"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("mensaje"))
    return res


@router.get("/exportar-excel", status_code=status.HTTP_200_OK)
def exportar_reportes_excel(
    fecha: Optional[str] = Query(None, description="Fecha específica (YYYY-MM-DD)"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio rango (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin rango (YYYY-MM-DD)"),
    mes: Optional[str] = Query(None, description="Mes específico (YYYY-MM)"),
    zona: Optional[str] = Query(None, description="Filtro por zona"),
    busqueda: Optional[str] = Query(None, description="Filtro de texto libre")
):
    """
    Descarga el reporte y auditoría de parqueos en formato Excel (.xlsx)
    respetando los filtros de fecha, mes (YYYY-MM), periodo o zona.
    """
    try:
        buf = GENERAR_EXCEL_AUDITORIA_PARQUEO_DB(
            fecha=fecha,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            mes=mes,
            zona=zona,
            busqueda=busqueda
        )
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        zona_tag = f"_{zona.upper()}" if zona and zona.upper() != "TODAS" else ""
        
        if mes:
            nombre_archivo = f"Auditoria_Parqueos{zona_tag}_Mes_{mes}.xlsx"
        elif fecha_inicio and fecha_fin:
            nombre_archivo = f"Auditoria_Parqueos{zona_tag}_{fecha_inicio}_al_{fecha_fin}.xlsx"
        elif fecha:
            nombre_archivo = f"Auditoria_Parqueos{zona_tag}_{fecha}.xlsx"
        else:
            nombre_archivo = f"Auditoria_Parqueos{zona_tag}_{timestamp_str}.xlsx"

        headers = {
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }

        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar archivo Excel de auditoría: {str(e)}"
        )
