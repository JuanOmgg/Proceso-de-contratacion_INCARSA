from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional
from datetime import datetime, date
from src.utils.security import get_current_user
from src.loaders.estadisticas_loader import (
    GET_estadisticas_ingresos_plantas_db,
    GET_detalle_personas_dia_planta_db,
    GET_plantas_disponibles_db
)

router = APIRouter(prefix="/estadisticas", tags=["Estadísticas"])


def _parse_date(d_str: Optional[str]) -> Optional[date]:
    if not d_str or not d_str.strip():
        return None
    try:
        return datetime.strptime(d_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


@router.get("/ingresos-diarios", status_code=status.HTTP_200_OK)
def GET_estadisticas_ingresos_endpoint(
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    id_planta: Optional[int] = Query(None, description="ID de planta opcional"),
    estado: Optional[str] = Query("APROBADO", description="Estado de las solicitudes (APROBADO, TODOS, etc.)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Retorna los KPIs, series de tiempo diaria para gráficos y desglose de afluencia por planta y día,
    con deduplicación estricta de personas registradas en múltiples solicitudes.
    """
    f_ini = _parse_date(fecha_inicio)
    f_fin = _parse_date(fecha_fin)

    resultado = GET_estadisticas_ingresos_plantas_db(
        fecha_inicio=f_ini,
        fecha_fin=f_fin,
        id_planta=id_planta,
        estado=estado
    )

    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al procesar estadísticas de ingresos.")
        )

    return resultado


@router.get("/detalle-dia-planta", status_code=status.HTTP_200_OK)
def GET_detalle_personas_endpoint(
    fecha: str = Query(..., description="Fecha específica (YYYY-MM-DD)"),
    id_planta: int = Query(..., description="ID de la planta"),
    estado: Optional[str] = Query("APROBADO", description="Estado de las solicitudes"),
    current_user: dict = Depends(get_current_user)
):
    """
    Retorna el listado consolidado de personas que ingresan a una planta en una fecha determinada,
    junto con los radicados en los que figura cada una.
    """
    resultado = GET_detalle_personas_dia_planta_db(
        fecha=fecha,
        id_planta=id_planta,
        estado=estado
    )

    if not resultado.get("exito"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensaje", "Error al obtener detalle de personas.")
        )

    return resultado


@router.get("/plantas", status_code=status.HTTP_200_OK)
def GET_plantas_estadisticas_endpoint(current_user: dict = Depends(get_current_user)):
    """
    Retorna el listado de plantas para poblar los filtros interactivos.
    """
    return GET_plantas_disponibles_db()
