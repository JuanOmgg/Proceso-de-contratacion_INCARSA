import datetime
from typing import Optional, Dict, Any, List
from database import GET_conexion


def GET_plantas_disponibles_db() -> List[Dict[str, Any]]:
    """
    Obtiene el listado de plantas para poblar los filtros del panel.
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("""
                    SELECT p.id, p.nombre, p.id_empresa, e.nombre_empresa AS empresa
                    FROM planta p
                    LEFT JOIN empresa e ON p.id_empresa = e.id
                    ORDER BY p.nombre ASC
                """)
                return cursor.fetchall() or []
    except Exception as e:
        print(f"❌ Error al obtener plantas para estadísticas: {e}")
        return []


def GET_estadisticas_ingresos_plantas_db(
    fecha_inicio: Optional[datetime.date] = None,
    fecha_fin: Optional[datetime.date] = None,
    id_planta: Optional[int] = None,
    estado: Optional[str] = "APROBADO"
) -> Dict[str, Any]:
    """
    Calcula las estadísticas diarias de personas que ingresan a las plantas,
    garantizando que si una persona aparece en 2 o más solicitudes en el mismo día,
    se contabilice exactamente UNA SOLA VEZ (deduplicación estricta).
    """
    try:
        # 1. Definir rango de fechas por defecto (mes actual si no se especifica)
        hoy = datetime.date.today()
        if not fecha_inicio:
            fecha_inicio = datetime.date(hoy.year, hoy.month, 1)
        if not fecha_fin:
            # Fin de mes actual o 30 días después
            if hoy.month == 12:
                fecha_fin = datetime.date(hoy.year, 12, 31)
            else:
                siguiente_mes = datetime.date(hoy.year, hoy.month + 1, 1)
                fecha_fin = siguiente_mes - datetime.timedelta(days=1)

        if fecha_inicio > fecha_fin:
            fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

        # 2. Construir la consulta SQL para traer todas las solicitudes en el rango (excluyendo rechazadas)
        # Incluye tanto solicitudes activas vigentes como solicitudes activas/programadas que aún no entran en vigencia
        filtros_sql = [
            "(s.is_active = 1 OR s.fecha_fin >= CURDATE())",
            "s.fecha_inicio <= %(fecha_fin)s",
            "s.fecha_fin >= %(fecha_inicio)s",
            "s.estado != 'RECHAZADO'"
        ]
        params: Dict[str, Any] = {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        }

        if id_planta and int(id_planta) > 0:
            filtros_sql.append("v.id_planta = %(id_planta)s")
            params["id_planta"] = int(id_planta)

        where_clause = " AND ".join(filtros_sql)

        query = f"""
            SELECT 
                s.id AS id_solicitud,
                s.codigo AS radicado,
                s.fecha_inicio,
                s.fecha_fin,
                s.estado,
                v.id_planta,
                pl.nombre AS planta,
                emp.nombre_empresa AS empresa_origen,
                i.id_persona,
                i.autorizado,
                p.nombre,
                p.apellido,
                p.tipo_doc,
                p.identificacion,
                p.cargo,
                ec.nombre AS contratista
            FROM solicitudes s
            JOIN visita v ON s.id = v.id_solicitud
            JOIN planta pl ON v.id_planta = pl.id
            LEFT JOIN empresa emp ON pl.id_empresa = emp.id
            JOIN ingresantes i ON s.id = i.id_solicitud
            JOIN personas p ON i.id_persona = p.id
            LEFT JOIN emp_contratista ec ON s.empresa_contratista = ec.id
            WHERE {where_clause}
            ORDER BY s.fecha_inicio ASC
        """

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(query, params)
                filas = cursor.fetchall() or []

        # 3. Estructuras de acumulación y deduplicación por día
        dias_map: Dict[datetime.date, Dict[str, Any]] = {}
        
        # Generar todos los días del rango continuo
        dias_totales = (fecha_fin - fecha_inicio).days + 1
        for i in range(dias_totales):
            dia_actual = fecha_inicio + datetime.timedelta(days=i)
            dias_map[dia_actual] = {
                "personas_aprobadas": set(),
                "personas_pendientes": set(),
                "personas_global": set(),
                "solicitudes_global": set(),
                "plantas": {}
            }

        todas_personas_periodo = set()
        personas_en_espera_periodo = set()
        solicitudes_en_espera_periodo = set()
        plantas_acumulado: Dict[int, Dict[str, Any]] = {}

        # 4. Asignar cada fila a los días correspondientes dentro de su vigencia
        for row in filas:
            f_ini = row["fecha_inicio"]
            f_fin = row["fecha_fin"]
            pid = row["id_planta"]
            pnom = row["planta"]
            pemp = row["empresa_origen"] or ""
            persona_id = row["id_persona"]
            solicitud_id = row["id_solicitud"]
            st_upper = str(row["estado"] or "").strip().upper()
            aut_val = row.get("autorizado")

            is_aprobado = (st_upper == "APROBADO") and (aut_val is None or aut_val == 1)

            if is_aprobado:
                todas_personas_periodo.add(persona_id)
                if pid not in plantas_acumulado:
                    plantas_acumulado[pid] = {
                        "id_planta": pid,
                        "planta": pnom,
                        "empresa": pemp,
                        "personas_unicas": set(),
                        "total_visitas": 0
                    }
                plantas_acumulado[pid]["personas_unicas"].add(persona_id)
            else:
                personas_en_espera_periodo.add(persona_id)
                solicitudes_en_espera_periodo.add(solicitud_id)

            # Acotar al rango seleccionado
            d_start = max(fecha_inicio, f_ini)
            d_end = min(fecha_fin, f_fin)

            cur_date = d_start
            while cur_date <= d_end:
                if cur_date in dias_map:
                    dia_entry = dias_map[cur_date]
                    if is_aprobado:
                        dia_entry["personas_aprobadas"].add(persona_id)
                    else:
                        dia_entry["personas_pendientes"].add(persona_id)

                    dia_entry["personas_global"].add(persona_id)
                    dia_entry["solicitudes_global"].add(solicitud_id)

                    if pid not in dia_entry["plantas"]:
                        dia_entry["plantas"][pid] = {
                            "id_planta": pid,
                            "planta": pnom,
                            "empresa": pemp,
                            "personas": set(),
                            "solicitudes": set()
                        }
                    if is_aprobado:
                        dia_entry["plantas"][pid]["personas"].add(persona_id)
                    dia_entry["plantas"][pid]["solicitudes"].add(solicitud_id)

                cur_date += datetime.timedelta(days=1)

        # 5. Construir registros diarios para la tabla y series para los gráficos
        registros_tabla = []
        serie_tiempo = []
        meses_es = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"]

        dia_pico_fecha = None
        dia_pico_fecha_formateada = None
        dia_pico_conteo = 0
        total_ingresos_acumulados = 0

        for dia in sorted(dias_map.keys()):
            info_dia = dias_map[dia]
            cant_aprobadas = len(info_dia["personas_aprobadas"])
            cant_pendientes = len(info_dia["personas_pendientes"] - info_dia["personas_aprobadas"])
            total_unicas_dia = cant_aprobadas
            total_solic_dia = len(info_dia["solicitudes_global"])

            total_ingresos_acumulados += total_unicas_dia

            if total_unicas_dia > dia_pico_conteo:
                dia_pico_conteo = total_unicas_dia
                dia_pico_fecha = dia.strftime("%Y-%m-%d")
                dia_pico_fecha_formateada = f"{dia.day:02d} {meses_es[dia.month - 1].capitalize()} {dia.year}"

            dia_str = dia.strftime("%Y-%m-%d")
            dia_corta = f"{dia.day} {meses_es[dia.month - 1]}"

            serie_tiempo.append({
                "fecha": dia_str,
                "fecha_corta": dia_corta,
                "total_personas": cant_aprobadas,
                "personas_aprobadas": cant_aprobadas,
                "personas_pendientes": cant_pendientes,
                "total_combinado": cant_aprobadas + cant_pendientes,
                "total_solicitudes": total_solic_dia
            })

            # Filas por planta para ese día
            for pid, pdata in info_dia["plantas"].items():
                cant_personas_planta = len(pdata["personas"])
                cant_solic_planta = len(pdata["solicitudes"])
                if cant_personas_planta > 0:
                    registros_tabla.append({
                        "fecha": dia_str,
                        "fecha_formateada": f"{dia.day} de {meses_es[dia.month - 1]} de {dia.year}",
                        "id_planta": pid,
                        "planta": pdata["planta"],
                        "empresa": pdata["empresa"],
                        "total_personas_unicas": cant_personas_planta,
                        "total_solicitudes": cant_solic_planta
                    })

        # Ordenar registros de tabla: fecha descendente, luego planta
        registros_tabla.sort(key=lambda r: (r["fecha"], r["planta"]), reverse=True)

        # 6. Distribución por planta para el gráfico de barras/dona
        distribucion_plantas = []
        planta_mayor_afluencia_nom = "Ninguna"
        planta_mayor_afluencia_conteo = 0

        for pid, pdata in plantas_acumulado.items():
            cant_unicas = len(pdata["personas_unicas"])
            if cant_unicas > planta_mayor_afluencia_conteo:
                planta_mayor_afluencia_conteo = cant_unicas
                planta_mayor_afluencia_nom = pdata["planta"]

            distribucion_plantas.append({
                "id_planta": pid,
                "planta": pdata["planta"],
                "empresa": pdata["empresa"],
                "total_personas_unicas": cant_unicas
            })

        distribucion_plantas.sort(key=lambda x: x["total_personas_unicas"], reverse=True)

        # 7. Métricas y KPIs consolidados
        promedio_diario = round(total_ingresos_acumulados / max(1, dias_totales), 1)

        kpis = {
            "total_personas_unicas_periodo": len(todas_personas_periodo),
            "total_ingresos_acumulados": total_ingresos_acumulados,
            "total_personas_en_espera": len(personas_en_espera_periodo),
            "total_solicitudes_en_espera": len(solicitudes_en_espera_periodo),
            "promedio_diario": promedio_diario,
            "dias_consultados": dias_totales,
            "dia_pico": {
                "fecha": dia_pico_fecha,
                "fecha_formateada": dia_pico_fecha_formateada,
                "total": dia_pico_conteo
            },
            "planta_mayor_afluencia": {
                "planta": planta_mayor_afluencia_nom,
                "total": planta_mayor_afluencia_conteo
            },
            "filtro_aplicado": {
                "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d"),
                "fecha_fin": fecha_fin.strftime("%Y-%m-%d"),
                "id_planta": id_planta,
                "estado": estado
            }
        }

        return {
            "exito": True,
            "kpis": kpis,
            "serie_tiempo": serie_tiempo,
            "distribucion_plantas": distribucion_plantas,
            "registros": registros_tabla
        }

    except Exception as e:
        print(f"❌ Error en GET_estadisticas_ingresos_plantas_db: {e}")
        return {
            "exito": False,
            "mensaje": f"Error al generar estadísticas: {str(e)}",
            "kpis": {},
            "serie_tiempo": [],
            "distribucion_plantas": [],
            "registros": []
        }


def GET_detalle_personas_dia_planta_db(
    fecha: str,
    id_planta: int,
    estado: Optional[str] = "APROBADO"
) -> Dict[str, Any]:
    """
    Retorna el listado exacto de personas deduplicadas que ingresan en una fecha y planta dada,
    incluyendo los números de radicado (solicitudes) en los que figura cada persona.
    """
    try:
        filtros_sql = [
            "(s.is_active = 1 OR s.fecha_fin >= CURDATE())",
            "%(fecha)s BETWEEN s.fecha_inicio AND s.fecha_fin",
            "v.id_planta = %(id_planta)s",
            "i.autorizado = 1"
        ]
        params: Dict[str, Any] = {
            "fecha": fecha,
            "id_planta": int(id_planta)
        }

        if estado and estado.strip().upper() not in ("TODOS", "ALL", ""):
            filtros_sql.append("s.estado = %(estado)s")
            params["estado"] = estado.strip().upper()

        where_clause = " AND ".join(filtros_sql)

        query = f"""
            SELECT 
                p.id AS id_persona,
                CONCAT(p.nombre, ' ', p.apellido) AS nombre_completo,
                p.tipo_doc,
                p.identificacion,
                p.cargo,
                COALESCE(ec.nombre, 'Sin contratista') AS empresa_contratista,
                s.codigo AS radicado,
                s.id AS id_solicitud,
                COALESCE(i.autorizado, 1) AS autorizado,
                COALESCE(i.estado_datos, 'PENDIENTE') AS estado_datos
            FROM personas p
            JOIN ingresantes i ON p.id = i.id_persona
            JOIN solicitudes s ON i.id_solicitud = s.id
            JOIN visita v ON s.id = v.id_solicitud
            LEFT JOIN emp_contratista ec ON s.empresa_contratista = ec.id
            WHERE {where_clause}
            ORDER BY p.nombre ASC, p.apellido ASC
        """

        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(query, params)
                filas = cursor.fetchall() or []

                # Obtener nombre de la planta
                cursor.execute("SELECT nombre FROM planta WHERE id = %s", (int(id_planta),))
                row_planta = cursor.fetchone()
                nombre_planta = row_planta["nombre"] if row_planta else f"Planta #{id_planta}"

        # Deduplicar personas agrupando radicados
        personas_map: Dict[int, Dict[str, Any]] = {}
        for row in filas:
            pid = row["id_persona"]
            if pid not in personas_map:
                personas_map[pid] = {
                    "id_persona": pid,
                    "nombre_completo": row["nombre_completo"].strip(),
                    "tipo_doc": row["tipo_doc"],
                    "identificacion": str(row["identificacion"]),
                    "cargo": row["cargo"],
                    "empresa_contratista": row["empresa_contratista"],
                    "autorizado": int(row.get("autorizado", 1)),
                    "estado_datos": row.get("estado_datos", "PENDIENTE"),
                    "radicados": set()
                }
            else:
                if not row.get("autorizado", 1):
                    personas_map[pid]["autorizado"] = 0
                if row.get("estado_datos") != "AUTORIZADO":
                    personas_map[pid]["estado_datos"] = row.get("estado_datos", "PENDIENTE")

            if row.get("radicado"):
                personas_map[pid]["radicados"].add(row["radicado"])

        personas_list = []
        for pdata in personas_map.values():
            rads = sorted(list(pdata["radicados"]))
            personas_list.append({
                "id_persona": pdata["id_persona"],
                "nombre_completo": pdata["nombre_completo"],
                "tipo_doc": pdata["tipo_doc"],
                "identificacion": pdata["identificacion"],
                "cargo": pdata["cargo"],
                "empresa_contratista": pdata["empresa_contratista"],
                "autorizado": pdata["autorizado"],
                "estado_datos": pdata["estado_datos"],
                "radicados": rads,
                "total_solicitudes": len(rads)
            })

        return {
            "exito": True,
            "fecha": fecha,
            "id_planta": id_planta,
            "planta": nombre_planta,
            "total_personas_unicas": len(personas_list),
            "personas": personas_list
        }

    except Exception as e:
        print(f"❌ Error en GET_detalle_personas_dia_planta_db: {e}")
        return {
            "exito": False,
            "mensaje": f"Error al obtener detalle de personas: {str(e)}",
            "personas": []
        }
