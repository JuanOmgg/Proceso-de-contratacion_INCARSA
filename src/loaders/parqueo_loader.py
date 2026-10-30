from typing import Optional, List, Dict, Any
from datetime import date, datetime, time
import os
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as OpenPyXlImage
from openpyxl.drawing.spreadsheet_drawing import OneCellAnchor, AnchorMarker
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils.units import pixels_to_EMU
from database import GET_conexion


# ==============================================================================
# CONSTANTES Y NORMALIZACIÓN DE ZONAS OFICIALES
# ==============================================================================
ZONAS_OFICIALES = ["UBATÉ", "SAMACÁ", "VALDERRAMA"]

def normalizar_zona(zona_raw: str) -> str:
    """Normaliza texto de zona al estándar oficial con tildes."""
    z = str(zona_raw or "").strip().upper()
    if z in ("UBATE", "UBATÉ"):
        return "UBATÉ"
    if z in ("SAMACA", "SAMACÁ"):
        return "SAMACÁ"
    if z in ("VALDERRAMA",):
        return "VALDERRAMA"
    return z


# ==============================================================================
# CRUD DE VEHÍCULOS INTERNOS (Catálogo oficial y zona asignada)
# ==============================================================================

def GET_vehiculos_int_db() -> Dict[str, Any]:
    """
    Retorna la lista de vehículos internos con su zona asignada oficial.
    """
    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                sql = """
                    SELECT id, placa, zona, descripcion, created_at
                    FROM vehiculo_int
                    ORDER BY zona ASC, placa ASC
                """
                cur.execute(sql)
                rows = cur.fetchall()
                return {"exito": True, "datos": rows or []}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al consultar vehículos internos: {str(e)}"}


def CREATE_vehiculo_int_db(data: dict) -> Dict[str, Any]:
    """
    Crea un nuevo vehículo interno con su zona asignada (UBATÉ, SAMACÁ, VALDERRAMA).
    """
    try:
        placa = str(data.get("placa", "")).strip().upper()
        zona = normalizar_zona(data.get("zona", ""))
        descripcion = str(data.get("descripcion", "") or "").strip()

        if not placa or not zona:
            return {"exito": False, "mensaje": "La placa y la zona asignada son obligatorias."}

        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM vehiculo_int WHERE placa = %s", (placa,))
                if cur.fetchone():
                    return {"exito": False, "mensaje": f"Ya existe un vehículo con la placa '{placa}'."}

                sql = """
                    INSERT INTO vehiculo_int (placa, zona, descripcion)
                    VALUES (%s, %s, %s)
                """
                cur.execute(sql, (placa, zona, descripcion or None))
                conn.commit()
                nuevo_id = cur.lastrowid

                return {
                    "exito": True,
                    "mensaje": f"Vehículo '{placa}' registrado exitosamente en zona '{zona}'.",
                    "id": nuevo_id
                }
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al crear vehículo interno: {str(e)}"}


def UPDATE_vehiculo_int_db(id_vehiculo: int, data: dict) -> Dict[str, Any]:
    """
    Actualiza la información o zona asignada de un vehículo interno.
    """
    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM vehiculo_int WHERE id = %s", (id_vehiculo,))
                if not cur.fetchone():
                    return {"exito": False, "mensaje": "Vehículo interno no encontrado."}

                campos = []
                valores = []

                if "placa" in data and data["placa"] is not None:
                    placa = str(data["placa"]).strip().upper()
                    cur.execute("SELECT id FROM vehiculo_int WHERE placa = %s AND id != %s", (placa, id_vehiculo))
                    if cur.fetchone():
                        return {"exito": False, "mensaje": f"La placa '{placa}' ya está asignada a otro vehículo."}
                    campos.append("placa = %s")
                    valores.append(placa)

                if "zona" in data and data["zona"] is not None:
                    campos.append("zona = %s")
                    valores.append(normalizar_zona(data["zona"]))

                if "descripcion" in data and data["descripcion"] is not None:
                    campos.append("descripcion = %s")
                    valores.append(str(data["descripcion"]).strip() or None)

                if not campos:
                    return {"exito": True, "mensaje": "Sin cambios que actualizar."}

                valores.append(id_vehiculo)
                sql = f"UPDATE vehiculo_int SET {', '.join(campos)} WHERE id = %s"
                cur.execute(sql, tuple(valores))
                conn.commit()

                return {"exito": True, "mensaje": "Vehículo actualizado exitosamente."}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al actualizar vehículo interno: {str(e)}"}


def DELETE_vehiculo_int_db(id_vehiculo: int) -> Dict[str, Any]:
    """
    Elimina un vehículo interno.
    """
    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM vehiculo_int WHERE id = %s", (id_vehiculo,))
                conn.commit()
                return {"exito": True, "mensaje": "Vehículo eliminado exitosamente."}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al eliminar vehículo interno: {str(e)}"}


def GET_ZONAS_PARQUEO_DB() -> List[str]:
    """
    Retorna la lista oficial de zonas de parqueo disponibles: UBATÉ, SAMACÁ y VALDERRAMA.
    """
    return list(ZONAS_OFICIALES)


def GET_VEHICULOS_PARA_ZONA_DB(zona: str, fecha: Optional[str] = None) -> Dict[str, Any]:
    """
    Retorna los vehículos asignados a una zona específica para preparar el formulario,
    más la lista de vehículos de otras zonas para permitir seleccionar si alguno pernoctó aquí.

    Regla de exclusión y prevención de doble reporte:
    Si un vehículo ya fue reportado pernoctando (se_quedo = 1) en otra zona en la fecha evaluada,
    no debe aparecer disponible para reportar en esta zona (evitando confusión o reportar
    el mismo vehículo en dos zonas).
    """
    try:
        zona_limpia = normalizar_zona(zona)
        fecha_eval = (fecha or "").strip() or date.today().isoformat()
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                # 1. Consultar vehículos que YA fueron reportados pernoctando en CUALQUIER zona en esta fecha
                # Regla estricta: solo deben aparecer disponibles vehículos que no hayan pernoctado en ninguna zona
                cur.execute("""
                    SELECT 
                        p.vehiculo,
                        r.zona AS zona_reportada,
                        r.reportador,
                        DATE_FORMAT(r.created_at, '%%H:%%i') AS hora_reporte,
                        p.observacion
                    FROM parqueos p
                    JOIN reportes_parqueo r ON p.id_reporte = r.id
                    WHERE DATE(r.created_at) = %s
                      AND (p.se_quedo = 1 OR p.observacion LIKE 'Pernoctó en %%')
                    ORDER BY r.id DESC
                """, (fecha_eval,))
                ya_reportados_filas = cur.fetchall() or []

                vehiculos_ya_reportados = {}
                for row in ya_reportados_filas:
                    placa_key = str(row["vehiculo"] or "").strip().upper()
                    if placa_key and placa_key not in vehiculos_ya_reportados:
                        obs_txt = str(row.get("observacion") or "")
                        if "Pernoctó en " in obs_txt:
                            partes_obs = obs_txt.split("Pernoctó en ")
                            z_destino = normalizar_zona(partes_obs[1].split()[0] if len(partes_obs) > 1 else "")
                        else:
                            z_destino = normalizar_zona(row["zona_reportada"])

                        vehiculos_ya_reportados[placa_key] = {
                            "placa": placa_key,
                            "zona": z_destino or normalizar_zona(row["zona_reportada"]),
                            "reportador": row.get("reportador") or "Personal de turno",
                            "hora": row.get("hora_reporte") or ""
                        }

                # 2. Catálogo oficial de vehículos
                cur.execute("""
                    SELECT id, placa, zona, descripcion
                    FROM vehiculo_int
                    ORDER BY placa ASC
                """)
                todos = cur.fetchall() or []

                # Excluir vehículos que ya pernoctaron en otra zona en la fecha evaluada
                asignados = [
                    v for v in todos 
                    if normalizar_zona(v.get("zona", "")) == zona_limpia 
                    and v["placa"].strip().upper() not in vehiculos_ya_reportados
                ]
                otros = [
                    v for v in todos 
                    if normalizar_zona(v.get("zona", "")) != zona_limpia 
                    and v["placa"].strip().upper() not in vehiculos_ya_reportados
                ]

                return {
                    "exito": True,
                    "zona": zona_limpia,
                    "fecha": fecha_eval,
                    "asignados": asignados,
                    "otros_disponibles": otros,
                    "vehiculos_ya_reportados": vehiculos_ya_reportados
                }
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al cargar vehículos para zona: {str(e)}"}


# ==============================================================================
# REPORTES NOCTURNOS POR ZONA
# ==============================================================================

def CREAR_REPORTE_ZONA_DB(payload: dict) -> Dict[str, Any]:
    """
    Registra el reporte nocturno para una zona específica.
    Reglas de negocio:
    1. Si un vehículo pertenece a esta zona y se quedó aquí: se_quedo = 1.
    2. Si un vehículo pertenece a esta zona y NO se quedó aquí:
       - Si fue reportado pernoctando físicamente en otra zona ese día:
         en su zona de origen se guarda como no pernoctó en este patio (se_quedo = 0),
         con observación en amarillo: 'Pernoctó en {otra_zona} '.
       - Si no fue reportado en ninguna zona:
         se guarda como no pernoctó (se_quedo = 0) en rojo: 'No pernoctó en ninguna zona'.
    3. Si un vehículo pertenece a OTRA zona (foráneo) y pernoctó en esta zona:
       - En esta zona se guarda como PERNOCTÓ (se_quedo = 1) con evidencia completa:
         'Pernoctó en {zona} (Asignado a: {zona_asignada})' y aparecerá en 'vehiculos_foraneos'.
       - En su zona correspondiente (zona_asignada):
         Si existe reporte para esa fecha, se sincroniza con se_quedo = 0 y 'Pernoctó en {zona}'.
    4. Validación anti-duplicados:
       Ningún vehículo puede reportarse como pernoctado (se_quedo = 1) en dos zonas diferentes
       para la misma fecha.
    """
    try:
        fecha = str(payload.get("fecha", "") or "").strip()
        zona = normalizar_zona(payload.get("zona", ""))
        reportador = str(payload.get("reportador", "")).strip()
        observaciones = str(payload.get("observaciones", "") or "").strip()
        vehiculos = payload.get("vehiculos", [])

        if not zona or not reportador:
            return {"exito": False, "mensaje": "Zona y nombre del reportador son obligatorios."}

        if not vehiculos:
            return {"exito": False, "mensaje": "Debe incluir al menos un vehículo en el reporte de la zona."}

        fecha_rep_target = fecha if fecha else date.today().isoformat()

        with GET_conexion() as conn:
            with conn.cursor() as cur:
                # 0.1 Validación de conflicto: ningún vehículo que se quedó puede haber sido ya reportado en otra zona
                for it in vehiculos:
                    placa_chk = str(it.get("vehiculo", "")).strip().upper()
                    se_quedo_chk = bool(it.get("se_quedo", True))
                    if placa_chk and se_quedo_chk:
                        cur.execute("""
                            SELECT r.zona, r.reportador, DATE_FORMAT(r.created_at, '%%H:%%i') AS hora_rep
                            FROM parqueos p
                            JOIN reportes_parqueo r ON p.id_reporte = r.id
                            WHERE DATE(r.created_at) = %s
                              AND p.vehiculo = %s
                              AND p.se_quedo = 1
                              AND UPPER(r.zona) != %s
                            ORDER BY r.id DESC
                            LIMIT 1
                        """, (fecha_rep_target, placa_chk, zona))
                        conflicto = cur.fetchone()
                        if conflicto:
                            otra_z = normalizar_zona(conflicto["zona"])
                            rep_nom = conflicto.get("reportador") or "Personal de turno"
                            hora_txt = f" a las {conflicto['hora_rep']}" if conflicto.get("hora_rep") else ""
                            return {
                                "exito": False,
                                "mensaje": f"Conflicto: El vehículo '{placa_chk}' ya fue reportado pernoctando en la zona '{otra_z}'{hora_txt} (por {rep_nom}) para la fecha {fecha_rep_target}. No es posible registrar el mismo vehículo en dos zonas."
                            }

                # 0.2 Si existía un reporte previo de "Cierre Automático" para esta zona y fecha,
                # eliminarlo para que prevalezca el reporte oficial diligenciado por el personal
                cur.execute("""
                    SELECT id FROM reportes_parqueo
                    WHERE UPPER(zona) = %s AND DATE(created_at) = %s AND reportador LIKE '%%Cierre Automático%%'
                """, (zona, fecha_rep_target))
                prev_auto = cur.fetchall() or []
                for p_auto in prev_auto:
                    cur.execute("DELETE FROM parqueos WHERE id_reporte = %s", (p_auto["id"],))
                    cur.execute("DELETE FROM reportes_parqueo WHERE id = %s", (p_auto["id"],))

                # 1. Verificar si YA existe un reporte para esta misma zona y fecha.
                # Si 2 o más formularios reportan a la misma zona en un día, se complementan en uno solo.
                cur.execute("""
                    SELECT id, reportador, observaciones
                    FROM reportes_parqueo
                    WHERE UPPER(zona) = %s AND DATE(created_at) = %s
                    ORDER BY id ASC
                    LIMIT 1
                """, (zona, fecha_rep_target))
                rep_existente = cur.fetchone()

                if rep_existente:
                    id_reporte = rep_existente["id"]
                    # Unificar nombres de reportadores sin duplicar
                    rep_prev = (rep_existente.get("reportador") or "").strip()
                    reportadores_actuales = [r.strip() for r in rep_prev.split("/") if r.strip() and "Cierre Automático" not in r]
                    if reportador and reportador not in reportadores_actuales:
                        reportadores_actuales.append(reportador)
                    nuevo_reportador = " / ".join(reportadores_actuales)[:250] if reportadores_actuales else reportador

                    # Unificar observaciones sin duplicar
                    obs_prev = (rep_existente.get("observaciones") or "").strip()
                    obs_list = [o.strip() for o in obs_prev.split("|") if o.strip() and "Cierre Automático" not in o]
                    if observaciones and observaciones not in obs_list:
                        obs_list.append(observaciones)
                    nueva_observacion = " | ".join(obs_list) if obs_list else (obs_prev or None)

                    cur.execute("""
                        UPDATE reportes_parqueo
                        SET reportador = %s, observaciones = %s
                        WHERE id = %s
                    """, (nuevo_reportador, nueva_observacion, id_reporte))
                else:
                    # Crear cabecera inicial en reportes_parqueo
                    if fecha and fecha != date.today().isoformat():
                        cur.execute("""
                            INSERT INTO reportes_parqueo (zona, reportador, observaciones, created_at)
                            VALUES (%s, %s, %s, CONCAT(%s, ' ', CURTIME()))
                        """, (zona, reportador, observaciones or None, fecha))
                    else:
                        cur.execute("""
                            INSERT INTO reportes_parqueo (zona, reportador, observaciones, created_at)
                            VALUES (%s, %s, %s, NOW())
                        """, (zona, reportador, observaciones or None))

                    id_reporte = cur.lastrowid

                # 2. Insertar detalles en parqueos aplicando las reglas de pernocta
                for it in vehiculos:
                    placa = str(it.get("vehiculo", "")).strip().upper()
                    if not placa:
                        continue

                    id_vehiculo = it.get("id_vehiculo")
                    zona_asignada = normalizar_zona(it.get("zona_asignada", "") or "")

                    if not zona_asignada or not id_vehiculo:
                        cur.execute("SELECT id, zona FROM vehiculo_int WHERE placa = %s LIMIT 1", (placa,))
                        v_row = cur.fetchone()
                        if v_row:
                            id_vehiculo = id_vehiculo or v_row["id"]
                            zona_asignada = zona_asignada or normalizar_zona(v_row["zona"])
                        else:
                            zona_asignada = zona_asignada or zona

                    se_quedo_marcado = bool(it.get("se_quedo", True))

                    # ¿Es vehículo de otra zona (foráneo)?
                    if zona_asignada != zona:
                        if se_quedo_marcado:
                            # 1. En esta zona donde pernocta físicamente SÍ PERNOCTÓ (se_quedo = 1)
                            # Deja la evidencia física en este reporte
                            se_quedo_final = 1
                            obs_user = str(it.get("observacion", "") or "").strip()
                            if obs_user and not obs_user.startswith("Pernoctó en") and not obs_user.startswith("Asignado a") and not obs_user.startswith("(Asignado a"):
                                obs_final = f"{obs_user} - Asignado a {zona_asignada}"
                            else:
                                obs_final = f"Asignado a {zona_asignada}"

                            # 2. Si ya existía un reporte previo para su sede oficial en esta fecha,
                            # asegurarse de que no quede duplicado como pernoctado allí
                            obs_home = f"Pernoctó en {zona}"
                            cur.execute("""
                                SELECT id FROM reportes_parqueo
                                WHERE UPPER(zona) = %s AND DATE(created_at) = %s
                                ORDER BY id DESC LIMIT 1
                            """, (zona_asignada, fecha_rep_target))
                            home_rep = cur.fetchone()
                            if home_rep:
                                id_rep_home = home_rep["id"]
                                cur.execute("SELECT id FROM parqueos WHERE id_reporte = %s AND vehiculo = %s LIMIT 1", (id_rep_home, placa))
                                p_existente = cur.fetchone()
                                if p_existente:
                                    cur.execute("UPDATE parqueos SET se_quedo = 0, observacion = %s WHERE id = %s", (obs_home, p_existente["id"]))
                        else:
                            se_quedo_final = 0
                            obs_final = f"Vehículo (Asignado a: {zona_asignada}) - No pernoctó aquí"
                    else:
                        # Vehículo pertenece a esta misma zona
                        if se_quedo_marcado:
                            se_quedo_final = 1
                            obs_final = str(it.get("observacion", "") or "").strip() or None
                        else:
                            # El vigilante de su zona indicó que NO amaneció en su patio.
                            # Verificar si amaneció físicamente en alguna de las otras zonas
                            cur.execute("""
                                SELECT r.zona
                                FROM parqueos p
                                JOIN reportes_parqueo r ON p.id_reporte = r.id
                                WHERE DATE(r.created_at) = %s 
                                  AND p.vehiculo = %s 
                                  AND p.se_quedo = 1
                                  AND UPPER(r.zona) != %s
                                ORDER BY r.id DESC LIMIT 1
                            """, (fecha_rep_target, placa, zona))
                            otra_z = cur.fetchone()
                            if otra_z and otra_z.get("zona"):
                                otra_zona_nom = normalizar_zona(otra_z["zona"])
                                se_quedo_final = 0
                                obs_final = f"Pernoctó en {otra_zona_nom} "
                            else:
                                se_quedo_final = 0
                                obs_final = "No pernoctó en ninguna zona"

                    # Si el vehículo ya existía en este reporte (ej. evaluado por otro patio de la misma zona),
                    # se actualiza su registro. Si no existía, se inserta sumándose al reporte único del día.
                    cur.execute("""
                        SELECT id, se_quedo, observacion
                        FROM parqueos
                        WHERE id_reporte = %s AND vehiculo = %s
                        LIMIT 1
                    """, (id_reporte, placa))
                    p_existente_rep = cur.fetchone()

                    if p_existente_rep:
                        # Si en este nuevo formulario pernoctó físicamente, prevalece la pernocta
                        se_quedo_actualizar = se_quedo_final
                        obs_actualizar = obs_final
                        if p_existente_rep.get("se_quedo") == 1 and se_quedo_final == 0:
                            se_quedo_actualizar = 1
                            obs_actualizar = p_existente_rep.get("observacion") or obs_final

                        cur.execute("""
                            UPDATE parqueos
                            SET id_vehiculo = COALESCE(%s, id_vehiculo),
                                zona_asignada = %s,
                                se_quedo = %s,
                                observacion = %s
                            WHERE id = %s
                        """, (id_vehiculo, zona_asignada, se_quedo_actualizar, obs_actualizar, p_existente_rep["id"]))
                    else:
                        cur.execute("""
                            INSERT INTO parqueos (id_reporte, id_vehiculo, vehiculo, zona_asignada, se_quedo, observacion)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (id_reporte, id_vehiculo, placa, zona_asignada, se_quedo_final, obs_final))

                conn.commit()

                cur.execute("SELECT COUNT(id) AS total FROM parqueos WHERE id_reporte = %s", (id_reporte,))
                cnt_row = cur.fetchone()
                total_en_reporte = cnt_row["total"] if cnt_row else len(vehiculos)

                accion_txt = "complementado" if rep_existente else "registrado"
                return {
                    "exito": True,
                    "mensaje": f"Reporte de parqueo para '{zona}' {accion_txt} exitosamente (Total acumulado: {total_en_reporte} vehículos).",
                    "id_reporte": id_reporte,
                    "total_vehiculos": total_en_reporte,
                    "fue_complementado": bool(rep_existente)
                }
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al guardar reporte de zona: {str(e)}"}


def CONSOLIDAR_REPORTES_DUPLICADOS_DB() -> None:
    """
    Consolida cualquier reporte duplicado existente que comparta la misma zona y fecha:
    - Mantiene el reporte principal (priorizando reportes diligenciados por personas).
    - Traspasa todos los vehículos de los reportes secundarios al principal (evitando duplicar placas).
    - Unifica los nombres de reportadores (ej. 'Guardia Patio 1 / Guardia Patio 2') y observaciones.
    - Elimina los reportes secundarios redundantes para que cada zona tenga exactamente 1 reporte por día.
    """
    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                # Purgar cualquier reporte ficticio automático previo de la base de datos
                cur.execute("""
                    DELETE FROM parqueos 
                    WHERE id_reporte IN (
                        SELECT id FROM reportes_parqueo WHERE reportador LIKE '%Cierre Automático%'
                    )
                """)
                cur.execute("DELETE FROM reportes_parqueo WHERE reportador LIKE '%Cierre Automático%'")
                conn.commit()
                cur.execute("""
                    SELECT 
                        DATE(created_at) AS fecha,
                        UPPER(zona) AS zona,
                        COUNT(id) AS cant
                    FROM reportes_parqueo
                    GROUP BY DATE(created_at), UPPER(zona)
                    HAVING COUNT(id) > 1
                """)
                grupos = cur.fetchall() or []
                for g in grupos:
                    f_grp = str(g["fecha"])
                    z_grp = g["zona"]
                    cur.execute("""
                        SELECT id, reportador, observaciones
                        FROM reportes_parqueo
                        WHERE DATE(created_at) = %s AND UPPER(zona) = %s
                        ORDER BY id ASC
                    """, (f_grp, z_grp))
                    reps = cur.fetchall() or []
                    if len(reps) <= 1:
                        continue

                    # Priorizar un reporte que NO sea 'Cierre Automático' como principal si existe
                    rep_manuales = [r for r in reps if "Cierre Automático" not in (r.get("reportador") or "")]
                    rep_principal = rep_manuales[0] if rep_manuales else reps[0]
                    reps_secundarios = [r for r in reps if r["id"] != rep_principal["id"]]

                    id_principal = rep_principal["id"]
                    reps_nombres = []
                    for nom in (rep_principal.get("reportador") or "").split("/"):
                        nom = nom.strip()
                        if nom and "Cierre Automático" not in nom and nom not in reps_nombres:
                            reps_nombres.append(nom)

                    obs_lista = []
                    for o in (rep_principal.get("observaciones") or "").split("|"):
                        o = o.strip()
                        if o and "Cierre Automático" not in o and o not in obs_lista:
                            obs_lista.append(o)

                    for r_sec in reps_secundarios:
                        id_sec = r_sec["id"]
                        sec_nom = r_sec.get("reportador") or ""
                        if "Cierre Automático" not in sec_nom:
                            for n in sec_nom.split("/"):
                                n = n.strip()
                                if n and n not in reps_nombres:
                                    reps_nombres.append(n)

                        sec_obs = r_sec.get("observaciones") or ""
                        if "Cierre Automático" not in sec_obs:
                            for o in sec_obs.split("|"):
                                o = o.strip()
                                if o and o not in obs_lista:
                                    obs_lista.append(o)

                        cur.execute("SELECT * FROM parqueos WHERE id_reporte = %s", (id_sec,))
                        v_secundarios = cur.fetchall() or []
                        for vs in v_secundarios:
                            placa_s = vs["vehiculo"]
                            cur.execute("""
                                SELECT id, se_quedo, observacion FROM parqueos
                                WHERE id_reporte = %s AND vehiculo = %s
                                LIMIT 1
                            """, (id_principal, placa_s))
                            v_exist = cur.fetchone()
                            if v_exist:
                                if vs.get("se_quedo") == 1 and v_exist.get("se_quedo") == 0:
                                    cur.execute("""
                                        UPDATE parqueos
                                        SET se_quedo = 1, observacion = %s
                                        WHERE id = %s
                                    """, (vs.get("observacion"), v_exist["id"]))
                                cur.execute("DELETE FROM parqueos WHERE id = %s", (vs["id"],))
                            else:
                                cur.execute("UPDATE parqueos SET id_reporte = %s WHERE id = %s", (id_principal, vs["id"]))

                        cur.execute("DELETE FROM reportes_parqueo WHERE id = %s", (id_sec,))

                    nom_final = " / ".join(reps_nombres)[:250] if reps_nombres else (rep_principal.get("reportador") or "Personal de turno")
                    obs_final = " | ".join(obs_lista) if obs_lista else (rep_principal.get("observaciones") or None)

                    cur.execute("""
                        UPDATE reportes_parqueo
                        SET reportador = %s, observaciones = %s
                        WHERE id = %s
                    """, (nom_final, obs_final, id_principal))

                conn.commit()
    except Exception as e:
        print(f"Aviso al consolidar reportes duplicados: {e}")


def GET_REPORTES_PARQUEO_DB(
    fecha: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    mes: Optional[str] = None,
    zona: Optional[str] = None,
    busqueda: Optional[str] = None,
    limit: int = 200
) -> Dict[str, Any]:
    """
    Enlista la tabla principal de reportes:
    - Fecha
    - Zona
    - Reportador
    - Conteo de vehículos que se quedaron y no se quedaron
    Soporta filtro por fecha específica, rango (fecha_inicio, fecha_fin) o mes (YYYY-MM).
    """
    try:
        # Si se especifica un mes (YYYY-MM), calcular rango de fechas correspondiente
        if mes and not fecha and not (fecha_inicio and fecha_fin):
            try:
                import calendar
                y, m = [int(x) for x in mes.strip().split("-")]
                _, last_day = calendar.monthrange(y, m)
                fecha_inicio = f"{y:04d}-{m:02d}-01"
                fecha_fin = f"{y:04d}-{m:02d}-{last_day:02d}"
            except Exception as e:
                print(f"Aviso parseando mes '{mes}': {e}")



        # Consolidar reportes duplicados en la misma zona y día en un solo reporte
        CONSOLIDAR_REPORTES_DUPLICADOS_DB()

        with GET_conexion() as conn:
            with conn.cursor() as cur:
                where_clauses = ["1=1"]
                params = []

                if fecha:
                    where_clauses.append("DATE(r.created_at) = %s")
                    params.append(fecha)
                elif fecha_inicio and fecha_fin:
                    where_clauses.append("DATE(r.created_at) BETWEEN %s AND %s")
                    params.extend([fecha_inicio, fecha_fin])
                elif fecha_inicio:
                    where_clauses.append("DATE(r.created_at) >= %s")
                    params.append(fecha_inicio)
                elif fecha_fin:
                    where_clauses.append("DATE(r.created_at) <= %s")
                    params.append(fecha_fin)

                if zona and zona.upper() != "TODAS":
                    where_clauses.append("r.zona = %s")
                    params.append(zona.strip().upper())

                if busqueda and busqueda.strip():
                    term = f"%{busqueda.strip()}%"
                    where_clauses.append("(r.reportador LIKE %s OR r.zona LIKE %s OR r.observaciones LIKE %s)")
                    params.extend([term, term, term])

                sql = f"""
                    SELECT 
                        r.id,
                        DATE_FORMAT(r.created_at, '%%Y-%%m-%%d') AS fecha,
                        r.zona,
                        r.reportador,
                        r.observaciones,
                        r.created_at,
                        COALESCE(SUM(CASE WHEN p.se_quedo = 1 THEN 1 ELSE 0 END), 0) AS total_quedados,
                        COALESCE(SUM(CASE WHEN p.se_quedo = 0 THEN 1 ELSE 0 END), 0) AS total_no_quedados,
                        COUNT(p.id) AS total_evaluados
                    FROM reportes_parqueo r
                    LEFT JOIN parqueos p ON r.id = p.id_reporte
                    WHERE {' AND '.join(where_clauses)}
                    GROUP BY r.id, r.created_at, r.zona, r.reportador, r.observaciones
                    ORDER BY r.created_at DESC, r.id DESC
                    LIMIT %s
                """
                params.append(limit)
                cur.execute(sql, tuple(params))
                filas = cur.fetchall() or []

                if filas:
                    # 1. Catálogo oficial de vehículos por zona
                    cur.execute("SELECT placa, zona FROM vehiculo_int")
                    catalogo_filas = cur.fetchall() or []
                    flota_por_zona = {}
                    catalogo_dict = {}
                    for cv in catalogo_filas:
                        z_norm = normalizar_zona(cv.get("zona", ""))
                        p_norm = str(cv.get("placa", "")).strip().upper()
                        if z_norm and p_norm:
                            flota_por_zona.setdefault(z_norm, set()).add(p_norm)
                            catalogo_dict[p_norm] = z_norm

                    # 2. Consultar todas las pernoctas físicas (se_quedo = 1) en las fechas de estos reportes
                    fechas_reportes = list({r["fecha"] for r in filas if r.get("fecha")})
                    if fechas_reportes:
                        format_fechas = ', '.join(['%s'] * len(fechas_reportes))
                        cur.execute(f"""
                            SELECT 
                                p.vehiculo,
                                DATE_FORMAT(r.created_at, '%%Y-%%m-%%d') AS fecha,
                                UPPER(r.zona) AS zona_quedo,
                                p.id_reporte,
                                COALESCE(p.zona_asignada, '') AS zona_asignada
                            FROM parqueos p
                            JOIN reportes_parqueo r ON p.id_reporte = r.id
                            WHERE p.se_quedo = 1 AND DATE(r.created_at) IN ({format_fechas})
                        """, tuple(fechas_reportes))
                        pernoctas_rows = cur.fetchall() or []
                    else:
                        pernoctas_rows = []

                    pernocta_map = {}
                    for pr in pernoctas_rows:
                        f_k = pr["fecha"]
                        v_k = str(pr["vehiculo"] or "").strip().upper()
                        z_k = normalizar_zona(pr["zona_quedo"])
                        pernocta_map[(f_k, v_k)] = z_k

                    foraneos_por_rep = {}
                    for pr in pernoctas_rows:
                        rep_id = pr["id_reporte"]
                        v_k = str(pr["vehiculo"] or "").strip().upper()
                        z_quedo = normalizar_zona(pr["zona_quedo"])
                        z_asig = normalizar_zona(pr.get("zona_asignada") or catalogo_dict.get(v_k, ""))
                        if z_asig and z_asig != z_quedo:
                            foraneos_por_rep[rep_id] = foraneos_por_rep.get(rep_id, 0) + 1

                    # 3. Calcular balance real y consistente con la modal de detalle
                    for r in filas:
                        z_rep = normalizar_zona(r.get("zona", ""))
                        f_rep = r.get("fecha", "")
                        flota_zona = flota_por_zona.get(z_rep, set())

                        pernoctaron_en_su_sede = 0
                        en_otra_sede = 0
                        ausentes_sin_reporte = 0

                        for placa_v in flota_zona:
                            zona_donde_pernocto = pernocta_map.get((f_rep, placa_v))
                            if zona_donde_pernocto:
                                if zona_donde_pernocto == z_rep:
                                    pernoctaron_en_su_sede += 1
                                else:
                                    en_otra_sede += 1
                            else:
                                ausentes_sin_reporte += 1

                        foraneos_en_patio = foraneos_por_rep.get(r["id"], 0)
                        total_quedados_patio = pernoctaron_en_su_sede + foraneos_en_patio

                        r["total_quedados"] = pernoctaron_en_su_sede
                        r["total_no_quedados"] = ausentes_sin_reporte
                        r["total_otra_zona"] = en_otra_sede
                        r["total_foraneos"] = foraneos_en_patio
                        r["total_quedados_patio"] = total_quedados_patio
                        r["total_flota_zona"] = len(flota_zona)
                        r["total_evaluados"] = pernoctaron_en_su_sede + en_otra_sede + ausentes_sin_reporte + foraneos_en_patio

                total_reportes = len(filas)
                total_quedados_gen = sum(int(r.get("total_quedados", 0)) for r in filas)
                total_no_quedados_gen = sum(int(r.get("total_no_quedados", 0)) for r in filas)

                return {
                    "exito": True,
                    "datos": filas,
                    "metricas": {
                        "total_reportes": total_reportes,
                        "total_quedados": total_quedados_gen,
                        "total_no_quedados": total_no_quedados_gen
                    }
                }
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al consultar listado de reportes: {str(e)}"}


def GET_DETALLE_REPORTE_ZONA_DB(id_reporte: int) -> Dict[str, Any]:
    """
    Detalle que se abre en 'Acciones -> Ver carros de la zona':
    Estructura requerida:
    1. TABLA DE ARRIBA (vehiculos_zona):
       - Aparecen TODOS los vehículos asignados a esta zona.
       - A partir de esta tabla se muestra cuáles pernoctaron en su patio, cuáles no pernoctaron
         en ninguna zona y cuáles pernoctaron en otra zona.
    2. TABLA DE ABAJO (vehiculos_foraneos):
       - Muestra qué carros de OTRA zona pernoctaron en esta zona.
    """
    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                # 1. Obtener la cabecera del reporte
                cur.execute("""
                    SELECT 
                        id, 
                        DATE_FORMAT(created_at, '%%Y-%%m-%%d') AS fecha,
                        zona, 
                        reportador, 
                        observaciones, 
                        created_at
                    FROM reportes_parqueo
                    WHERE id = %s
                """, (id_reporte,))
                reporte = cur.fetchone()

                if not reporte:
                    return {"exito": False, "mensaje": "Reporte de parqueo no encontrado."}

                fecha_rep = reporte["fecha"]
                zona_rep = normalizar_zona(reporte["zona"])

                # 2. Vehículos reportados en este reporte específico
                cur.execute("""
                    SELECT 
                        p.id,
                        p.id_vehiculo,
                        p.vehiculo,
                        p.zona_asignada,
                        p.se_quedo,
                        p.observacion,
                        v.descripcion,
                        v.zona AS zona_catalogo
                    FROM parqueos p
                    LEFT JOIN vehiculo_int v ON p.id_vehiculo = v.id OR p.vehiculo = v.placa
                    WHERE p.id_reporte = %s
                    ORDER BY p.vehiculo ASC
                """, (id_reporte,))
                detalles = cur.fetchall() or []
                detalles_map = {d["vehiculo"].strip().upper(): d for d in detalles}

                # 3. Consultar todos los vehículos oficiales de la base de datos
                cur.execute("""
                    SELECT id, placa, zona, descripcion
                    FROM vehiculo_int
                    ORDER BY placa ASC
                """)
                todos_vehiculos = cur.fetchall() or []
                
                # Vehículos pertenecientes oficialmente a esta zona
                vehiculos_de_esta_zona = [v for v in todos_vehiculos if normalizar_zona(v.get("zona", "")) == zona_rep]
                placas_zona_set = {v["placa"].strip().upper() for v in vehiculos_de_esta_zona}

                # Si en el reporte hay algún vehículo registrado como asignado a esta zona, incluirlo también
                for d in detalles:
                    placa_d = d["vehiculo"].strip().upper()
                    zona_asig_d = normalizar_zona(d.get("zona_asignada") or d.get("zona_catalogo") or "")
                    if zona_asig_d == zona_rep and placa_d not in placas_zona_set:
                        vehiculos_de_esta_zona.append({
                            "id": d.get("id_vehiculo"),
                            "placa": placa_d,
                            "zona": zona_rep,
                            "descripcion": d.get("descripcion")
                        })
                        placas_zona_set.add(placa_d)

                # Ordenar por placa
                vehiculos_de_esta_zona.sort(key=lambda x: x["placa"])

                # 4. Consultar si vehículos de esta zona pernoctaron en OTRAS zonas en esa fecha
                cur.execute("""
                    SELECT 
                        p.vehiculo,
                        r.zona AS zona_reportada,
                        p.observacion,
                        p.se_quedo
                    FROM parqueos p
                    JOIN reportes_parqueo r ON p.id_reporte = r.id
                    WHERE DATE(r.created_at) = %s 
                      AND UPPER(r.zona) != %s
                      AND (
                          p.se_quedo = 1 
                          OR p.observacion LIKE 'Pernoctó en %%' 
                      )
                    ORDER BY r.id DESC
                """, (fecha_rep, zona_rep))
                estancias_otras_zonas = cur.fetchall() or []
                pernoctas_otra_zona = {}
                for est in estancias_otras_zonas:
                    plc = est["vehiculo"].strip().upper()
                    z_otra = normalizar_zona(est["zona_reportada"])
                    obs_e = est.get("observacion") or ""
                    if "Pernoctó en " in obs_e:
                        try:
                            z_otra = normalizar_zona(obs_e.split("Pernoctó en ")[1].split("(")[0].strip())
                        except Exception:
                            pass
                    pernoctas_otra_zona[plc] = {
                        "zona": z_otra,
                        "observacion": obs_e
                    }

                # ------------------------------------------------------------------
                # TABLA 1 (Arriba): TODOS los vehículos de la zona y su balance
                # ------------------------------------------------------------------
                vehiculos_zona = []
                for v in vehiculos_de_esta_zona:
                    placa = v["placa"].strip().upper()
                    d = detalles_map.get(placa)
                    obs_reportada = (d.get("observacion") or "").strip() if d else ""
                    otra_info = pernoctas_otra_zona.get(placa)
                    pernocto_otra_en_obs = "Pernoctó en " in obs_reportada and ("No es su zona" in obs_reportada or "otra zona" in obs_reportada)

                    if otra_info or pernocto_otra_en_obs:
                        # Pernoctó en otra zona
                        z_dest = otra_info["zona"] if otra_info else ""
                        if not z_dest and "Pernoctó en " in obs_reportada:
                            try:
                                z_dest = normalizar_zona(obs_reportada.split("Pernoctó en ")[1].split("(")[0].strip())
                            except Exception:
                                z_dest = "otra zona"
                        
                        vehiculos_zona.append({
                            "id": d["id"] if d else None,
                            "vehiculo": placa,
                            "zona_asignada": zona_rep,
                            "se_quedo": True,
                            "estado": "OTRA_ZONA",
                            "estado_label": "Pernoctó en otra zona",
                            "color_estado": "amarillo",
                            "observacion": f"Pernoctó en {z_dest} ",
                            "color_observacion": "amarillo"
                        })
                    elif d and d.get("se_quedo") == 1:
                        # Pernoctó en su zona
                        obs_final = obs_reportada if obs_reportada else "- Sin novedad (En su zona) -"
                        vehiculos_zona.append({
                            "id": d["id"],
                            "vehiculo": placa,
                            "zona_asignada": zona_rep,
                            "se_quedo": True,
                            "estado": "EN_SU_ZONA",
                            "estado_label": "Pernoctó aquí",
                            "color_estado": "verde",
                            "observacion": obs_final,
                            "color_observacion": "ninguno"
                        })
                    else:
                        # No pernoctó en ninguna zona
                        vehiculos_zona.append({
                            "id": d["id"] if d else None,
                            "vehiculo": placa,
                            "zona_asignada": zona_rep,
                            "se_quedo": False,
                            "estado": "NO_PERNOCTO",
                            "estado_label": "No pernoctó",
                            "color_estado": "rojo",
                            "observacion": "No pernoctó en ninguna zona",
                            "color_observacion": "rojo"
                        })

                # ------------------------------------------------------------------
                # TABLA 2 (Abajo): Carros de OTRA zona que pernoctaron en esta zona
                # ------------------------------------------------------------------
                vehiculos_foraneos = []
                for d in detalles:
                    placa = d["vehiculo"].strip().upper()
                    zona_asig = normalizar_zona(d.get("zona_asignada") or d.get("zona_catalogo") or "")
                    if not zona_asig or zona_asig == zona_rep:
                        continue

                    obs_raw = (d.get("observacion") or "").strip()
                    # Verificar si pernoctó físicamente aquí
                    se_quedo_aqui = (
                        d.get("se_quedo") == 1
                        or f"Pernoctó en {zona_rep}" in obs_raw
                        or ("pernoctó" in obs_raw.lower() and "no pernoctó" not in obs_raw.lower())
                    )

                    if se_quedo_aqui:
                        obs_foraneo = f"Asignado a {zona_asig}" if zona_asig else "Vehículo foráneo"
                        if obs_raw:
                            obs_limpia = obs_raw
                            for pref in [
                                f"Pernoctó en {zona_rep}",
                                f"(Asignado a: {zona_asig})",
                                f"Asignado a: {zona_asig}",
                                f"Asignado a {zona_asig}",
                            ]:
                                obs_limpia = obs_limpia.replace(pref, "")
                            obs_limpia = obs_limpia.strip(" -():")
                            if obs_limpia:
                                obs_foraneo = f"{obs_limpia} (Asignado a {zona_asig})"

                        vehiculos_foraneos.append({
                            "id": d["id"],
                            "vehiculo": placa,
                            "zona_asignada": zona_asig,
                            "zona_origen": zona_asig,
                            "zona_reportada": zona_rep,
                            "se_quedo": True,
                            "estado": "FORANEO_PERNOCTO",
                            "estado_label": "Pernoctó aquí",
                            "color_estado": "amarillo",
                            "observacion": obs_foraneo,
                            "color_observacion": "amarillo"
                        })

                # Listas de compatibilidad histórica
                se_quedaron_aqui = [v for v in vehiculos_zona if v["estado"] == "EN_SU_ZONA"] + vehiculos_foraneos
                no_se_quedaron_aqui = [v for v in vehiculos_zona if v["estado"] != "EN_SU_ZONA"]

                return {
                    "exito": True,
                    "reporte": reporte,
                    "vehiculos_zona": vehiculos_zona,
                    "vehiculos_foraneos": vehiculos_foraneos,
                    "se_quedaron_aqui": se_quedaron_aqui,
                    "no_se_quedaron_aqui": no_se_quedaron_aqui,
                    "resumen": {
                        "total_carros_zona": len(vehiculos_zona),
                        "total_pernoctaron_aqui": sum(1 for v in vehiculos_zona if v["estado"] == "EN_SU_ZONA"),
                        "total_otra_zona": sum(1 for v in vehiculos_zona if v["estado"] == "OTRA_ZONA"),
                        "total_no_pernoctaron": sum(1 for v in vehiculos_zona if v["estado"] == "NO_PERNOCTO"),
                        "total_foraneos_aqui": len(vehiculos_foraneos),
                        "total_quedados_aqui": len(se_quedaron_aqui),
                        "total_no_quedados_aqui": len(no_se_quedaron_aqui)
                    }
                }
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al consultar detalle de zona: {str(e)}"}


def DELETE_REPORTE_PARQUEO_DB(id_reporte: int) -> Dict[str, Any]:
    """
    Elimina un reporte y en cascada sus registros de parqueo.
    """
    try:
        with GET_conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, zona, DATE_FORMAT(created_at, '%%Y-%%m-%%d') AS fecha FROM reportes_parqueo WHERE id = %s", (id_reporte,))
                r = cur.fetchone()
                if not r:
                    return {"exito": False, "mensaje": "Reporte no encontrado."}

                cur.execute("DELETE FROM reportes_parqueo WHERE id = %s", (id_reporte,))
                conn.commit()
                return {"exito": True, "mensaje": f"Reporte de '{r['zona']}' del día {r['fecha']} eliminado con éxito."}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al eliminar reporte: {str(e)}"}


def GENERAR_EXCEL_AUDITORIA_PARQUEO_DB(
    fecha: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    mes: Optional[str] = None,
    zona: Optional[str] = None,
    busqueda: Optional[str] = None
) -> io.BytesIO:
    """
    Genera un libro de Excel (.xlsx) con el consolidado y auditoría completa de los reportes
    de parqueo nocturno según los filtros activos:
    - Hoja 1: 'Resumen de Reportes' (Cabeceras, totales de permanencia y ausencias por zona).
    - Hoja 2: 'Auditoría Detallada' (Revisión vehículo por vehículo: condición, estado de auditoría con colores y novedades).
    Soporta selección por mes (YYYY-MM), periodo personalizado (fecha_inicio, fecha_fin) o fecha fija.
    """
    res = GET_REPORTES_PARQUEO_DB(
        fecha=fecha,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        mes=mes,
        zona=zona,
        busqueda=busqueda,
        limit=2000
    )
    reportes = res.get("datos", [])

    wb = openpyxl.Workbook()

    # Fuentes
    font_title = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    font_sub = Font(name="Calibri", size=9, italic=True, color="FFFFFF")
    font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_cell = Font(name="Calibri", size=10, color="0F172A")
    font_cell_bold = Font(name="Calibri", size=10, bold=True, color="0F172A")

    # Rellenos
    fill_title = PatternFill(start_color="797a7a", end_color="797a7a", fill_type="solid")      # Teal oscuro
    fill_sub = PatternFill(start_color="383d3d", end_color="383d3d", fill_type="solid")        # Teal profundo
    fill_header = PatternFill(start_color="383d3d", end_color="383d3d", fill_type="solid")     # Slate oscuro
    fill_even = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    fill_odd = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    fill_total = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

    # Colores de Estado Auditoría
    fill_verde = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    font_verde = Font(name="Calibri", size=10, bold=True, color="166534")
    fill_amarillo = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    font_amarillo = Font(name="Calibri", size=10, bold=True, color="92400E")
    fill_rojo = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    font_rojo = Font(name="Calibri", size=10, bold=True, color="991B1B")

    # Bordes y Alineaciones
    border_thin = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # Construir descripción de filtros
    MESES_NOMBRES = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    filtros_txt = []
    if mes:
        try:
            y, m = [int(x) for x in mes.strip().split("-")]
            mes_nom = MESES_NOMBRES[m - 1] if 1 <= m <= 12 else str(m)
            filtros_txt.append(f"Mes: {mes_nom} {y}")
        except Exception:
            filtros_txt.append(f"Mes: {mes}")
    elif fecha:
        filtros_txt.append(f"Fecha: {fecha}")
    elif fecha_inicio and fecha_fin:
        filtros_txt.append(f"Periodo: {fecha_inicio} al {fecha_fin}")
    elif fecha_inicio:
        filtros_txt.append(f"Desde: {fecha_inicio}")
    elif fecha_fin:
        filtros_txt.append(f"Hasta: {fecha_fin}")
    else:
        filtros_txt.append("Periodo: Histórico completo")

    if zona and zona.upper() != "TODAS":
        filtros_txt.append(f"Zona: {zona.upper()}")
    else:
        filtros_txt.append("Zonas: Todas")

    if busqueda and busqueda.strip():
        filtros_txt.append(f"Búsqueda: '{busqueda.strip()}'")

    filtros_str = " | ".join(filtros_txt)

    # Ruta del logo de MILPA
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logo_milpa_path = os.path.join(base_dir, "static", "img", "logo-milpa.jpg")
    has_logo = os.path.exists(logo_milpa_path)

    # Función para centrar el logo de MILPA dentro del bloque combinado A1:B2 (1A, 1B, 2A, 2B)
    def aplicar_logo_centrado(ws):
        if not has_logo:
            return
        ws.merge_cells("A1:B2")
        for r_i in range(1, 3):
            for c_i in range(1, 3):
                ws.cell(row=r_i, column=c_i).fill = fill_even
        try:
            img = OpenPyXlImage(logo_milpa_path)
            # Altura deseada y ancho proporcional (aspect ratio 1024x428 ≈ 2.39)
            logo_h = 48
            logo_w = round(logo_h * (1024 / 428))  # 115 px

            # Casilla A1:B2:
            # Altura combinada: fila 1 (28pt) + fila 2 (24pt) = 52pt ≈ 70px
            # Ancho combinado: col A (13 car ≈ 98px) + col B (11 car ≈ 83px) ≈ 181px
            box_w = 181
            box_h = 70

            col_off_px = max(0, (box_w - logo_w) // 2)  # ≈ 33px de margen horizontal
            row_off_px = max(0, (box_h - logo_h) // 2)  # ≈ 11px de margen vertical

            img.width = logo_w
            img.height = logo_h

            marker = AnchorMarker(
                col=0,
                colOff=pixels_to_EMU(col_off_px),
                row=0,
                rowOff=pixels_to_EMU(row_off_px)
            )
            size = XDRPositiveSize2D(pixels_to_EMU(logo_w), pixels_to_EMU(logo_h))
            img.anchor = OneCellAnchor(_from=marker, ext=size)
            ws.add_image(img)
        except Exception as e:
            print(f"Aviso agregando logo centrado a {ws.title}: {e}")

    # ==========================================================================
    # HOJA 1: RESUMEN DE REPORTES
    # ==========================================================================
    ws_resumen = wb.active
    ws_resumen.title = "Resumen de Reportes"
    ws_resumen.views.sheetView[0].showGridLines = True

    # Banner Superior y Logo centrado en esquina superior izquierda (A1:B2)
    if has_logo:
        aplicar_logo_centrado(ws_resumen)

        ws_resumen.merge_cells("C1:J1")
        ws_resumen["C1"] = "MILPA - REPORTE Y AUDITORÍA DE PARQUEOS NOCTURNOS"
        ws_resumen["C1"].font = font_title
        ws_resumen["C1"].fill = fill_title
        ws_resumen["C1"].alignment = align_center

        ws_resumen.merge_cells("C2:J2")
        ws_resumen["C2"] = "Consolidado de Patios, Novedades y Balance de Vehículos"
        ws_resumen["C2"].font = font_sub
        ws_resumen["C2"].fill = fill_sub
        ws_resumen["C2"].alignment = align_center
    else:
        ws_resumen.merge_cells("A1:J1")
        ws_resumen["A1"] = "MILPA - REPORTE Y AUDITORÍA DE PARQUEOS NOCTURNOS"
        ws_resumen["A1"].font = font_title
        ws_resumen["A1"].fill = fill_title
        ws_resumen["A1"].alignment = align_center

        ws_resumen.merge_cells("A2:J2")
        ws_resumen["A2"] = "Consolidado de Patios, Novedades y Balance de Vehículos"
        ws_resumen["A2"].font = font_sub
        ws_resumen["A2"].fill = fill_sub
        ws_resumen["A2"].alignment = align_center

    ws_resumen.row_dimensions[1].height = 28
    ws_resumen.row_dimensions[2].height = 24
    ws_resumen.row_dimensions[3].height = 8

    # Metadatos de Generación
    ws_resumen["A4"] = "Fecha de emisión:"
    ws_resumen["A4"].font = font_cell_bold
    ws_resumen["B4"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws_resumen["B4"].font = font_cell

    ws_resumen["D4"] = "Filtros aplicados:"
    ws_resumen["D4"].font = font_cell_bold
    ws_resumen["E4"] = filtros_str
    ws_resumen["E4"].font = font_cell
    ws_resumen.merge_cells("E4:J4")

    ws_resumen.row_dimensions[4].height = 20
    ws_resumen.row_dimensions[5].height = 6
    ws_resumen.row_dimensions[6].height = 24

    headers_resumen = [
        "Fecha", "Hora", "Zona", "Diligenciado por",
        "Pernoctaron", "En otra zona", "Ausentes", "Ajenos", "Total evaluados", "Observaciones"
    ]
    for col_idx, h in enumerate(headers_resumen, 1):
        cell = ws_resumen.cell(row=6, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = border_thin

    row_idx = 7
    tot_quedados = 0
    tot_otra_zona = 0
    tot_ausentes = 0
    tot_foraneos = 0
    tot_eval = 0

    if not reportes:
        ws_resumen.merge_cells(f"A{row_idx}:J{row_idx}")
        c_vacio = ws_resumen.cell(row=row_idx, column=1, value="No se encontraron reportes con los filtros seleccionados.")
        c_vacio.font = font_cell
        c_vacio.alignment = align_center
        row_idx += 1
    else:
        for rep in reportes:
            c_fill = fill_even if row_idx % 2 == 0 else fill_odd
            hora_str = rep["created_at"].strftime("%H:%M:%S") if isinstance(rep.get("created_at"), datetime) else ""
            q = int(rep.get("total_quedados") or 0)
            oz = int(rep.get("total_otra_zona") or 0)
            a = int(rep.get("total_no_quedados") or 0)
            f = int(rep.get("total_foraneos") or 0)
            # Total evaluados real: balance integral de vehículos evaluados para esta zona/patio
            e = q + oz + a + f
            tot_quedados += q
            tot_otra_zona += oz
            tot_ausentes += a
            tot_foraneos += f
            tot_eval += e

            vals = [
                (str(rep.get("fecha") or ""), align_center),
                (hora_str, align_center),
                (str(rep.get("zona") or ""), align_center),
                (str(rep.get("reportador") or ""), align_left),
                (q, align_right),
                (oz, align_right),
                (a, align_right),
                (f, align_right),
                (e, align_right),
                (str(rep.get("observaciones") or "-"), align_left)
            ]
            for c_idx, (v, al) in enumerate(vals, 1):
                c = ws_resumen.cell(row=row_idx, column=c_idx, value=v)
                c.font = font_cell
                c.fill = c_fill
                c.alignment = al
                c.border = border_thin
            ws_resumen.row_dimensions[row_idx].height = 20
            row_idx += 1

        # Fila de Totales Consolidados
        ws_resumen.merge_cells(f"A{row_idx}:D{row_idx}")
        cell_tot_lbl = ws_resumen.cell(row=row_idx, column=1, value="TOTALES CONSOLIDADOS:")
        cell_tot_lbl.font = font_cell_bold
        cell_tot_lbl.fill = fill_total
        cell_tot_lbl.alignment = Alignment(horizontal="right", vertical="center")

        for col_i in range(1, 5):
            ws_resumen.cell(row=row_idx, column=col_i).border = border_thin
            ws_resumen.cell(row=row_idx, column=col_i).fill = fill_total

        for c_i, t_val in [
            (5, tot_quedados),
            (6, tot_otra_zona),
            (7, tot_ausentes),
            (8, tot_foraneos),
            (9, tot_eval)
        ]:
            c = ws_resumen.cell(row=row_idx, column=c_i, value=t_val)
            c.font = font_cell_bold
            c.fill = fill_total
            c.alignment = align_right
            c.border = border_thin

        c_end = ws_resumen.cell(row=row_idx, column=10, value="")
        c_end.fill = fill_total
        c_end.border = border_thin
        ws_resumen.row_dimensions[row_idx].height = 22

    # ==========================================================================
    # HOJA 2: AUDITORÍA DETALLADA
    # ==========================================================================
    ws_auditoria = wb.create_sheet(title="Auditoría Detallada")
    ws_auditoria.views.sheetView[0].showGridLines = True

    # Banner Hoja 2 y Logo centrado en esquina superior izquierda (A1:B2)
    if has_logo:
        aplicar_logo_centrado(ws_auditoria)

        ws_auditoria.merge_cells("C1:J1")
        ws_auditoria["C1"] = "AUDITORÍA DETALLADA DE VEHÍCULOS POR PATIO Y FECHA"
        ws_auditoria["C1"].font = font_title
        ws_auditoria["C1"].fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        ws_auditoria["C1"].alignment = align_center

        ws_auditoria.merge_cells("C2:J2")
        ws_auditoria["C2"] = "Control individual de pernocta por placa, zona oficial de asignación y verificación física"
        ws_auditoria["C2"].font = font_sub
        ws_auditoria["C2"].fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        ws_auditoria["C2"].alignment = align_center
    else:
        ws_auditoria.merge_cells("A1:J1")
        ws_auditoria["A1"] = "AUDITORÍA DETALLADA DE VEHÍCULOS POR PATIO Y FECHA"
        ws_auditoria["A1"].font = font_title
        ws_auditoria["A1"].fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        ws_auditoria["A1"].alignment = align_center

        ws_auditoria.merge_cells("A2:J2")
        ws_auditoria["A2"] = "Control individual de pernocta por placa, zona oficial de asignación y verificación física"
        ws_auditoria["A2"].font = font_sub
        ws_auditoria["A2"].fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        ws_auditoria["A2"].alignment = align_center

    ws_auditoria.row_dimensions[1].height = 28
    ws_auditoria.row_dimensions[2].height = 24
    ws_auditoria.row_dimensions[3].height = 8

    headers_audit = [
        "Fecha", "Hora", "Zona del Reporte", "Diligenciado por",
        "Placa", "Zona Asignada", "Condición", "¿Pernoctó Físicamente?",
        "Estado Auditoría", "Observación / Novedad"
    ]
    for col_idx, h in enumerate(headers_audit, 1):
        cell = ws_auditoria.cell(row=4, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_title
        cell.alignment = align_center
        cell.border = border_thin
    ws_auditoria.row_dimensions[4].height = 24

    row_a = 5
    if not reportes:
        ws_auditoria.merge_cells(f"A{row_a}:J{row_a}")
        c_vacio_a = ws_auditoria.cell(row=row_a, column=1, value="No se encontraron registros de vehículos con los filtros seleccionados.")
        c_vacio_a.font = font_cell
        c_vacio_a.alignment = align_center
        row_a += 1
    else:
        for rep in reportes:
            det = GET_DETALLE_REPORTE_ZONA_DB(rep["id"])
            hora_str = rep["created_at"].strftime("%H:%M:%S") if isinstance(rep.get("created_at"), datetime) else ""

            # 1. Carros asignados a la zona del reporte
            for v in det.get("vehiculos_zona", []):
                c_fill = fill_even if row_a % 2 == 0 else fill_odd
                estado = v.get("estado")
                if estado == "EN_SU_ZONA":
                    est_fill, est_font = fill_verde, font_verde
                    pernocto_fisico = "SÍ"
                elif estado == "OTRA_ZONA":
                    est_fill, est_font = fill_amarillo, font_amarillo
                    pernocto_fisico = "SÍ (Otra zona)"
                else:
                    est_fill, est_font = fill_rojo, font_rojo
                    pernocto_fisico = "NO"

                vals = [
                    (str(rep.get("fecha") or ""), align_center, font_cell, c_fill),
                    (hora_str, align_center, font_cell, c_fill),
                    (str(rep.get("zona") or ""), align_center, font_cell, c_fill),
                    (str(rep.get("reportador") or ""), align_left, font_cell, c_fill),
                    (v.get("vehiculo", ""), align_center, font_cell_bold, c_fill),
                    (v.get("zona_asignada", ""), align_center, font_cell, c_fill),
                    ("De la zona", align_center, font_cell, c_fill),
                    (pernocto_fisico, align_center, font_cell_bold, c_fill),
                    (v.get("estado_label", ""), align_center, est_font, est_fill),
                    (v.get("observacion", "") or "-", align_left, font_cell, c_fill)
                ]
                for c_idx, (val, al, fnt, fil) in enumerate(vals, 1):
                    c = ws_auditoria.cell(row=row_a, column=c_idx, value=val)
                    c.font = fnt
                    c.fill = fil
                    c.alignment = al
                    c.border = border_thin
                ws_auditoria.row_dimensions[row_a].height = 20
                row_a += 1

            # 2. Carros foráneos que pernoctaron en esta zona
            for v in det.get("vehiculos_foraneos", []):
                c_fill = fill_even if row_a % 2 == 0 else fill_odd
                vals = [
                    (str(rep.get("fecha") or ""), align_center, font_cell, c_fill),
                    (hora_str, align_center, font_cell, c_fill),
                    (str(rep.get("zona") or ""), align_center, font_cell, c_fill),
                    (str(rep.get("reportador") or ""), align_left, font_cell, c_fill),
                    (v.get("vehiculo", ""), align_center, font_cell_bold, c_fill),
                    (v.get("zona_asignada", ""), align_center, font_cell, c_fill),
                    ("Foráneo", align_center, font_cell, c_fill),
                    ("SÍ", align_center, font_cell_bold, c_fill),
                    ("Pernoctó aquí (Foráneo)", align_center, font_amarillo, fill_amarillo),
                    (v.get("observacion", "") or "-", align_left, font_cell, c_fill)
                ]
                for c_idx, (val, al, fnt, fil) in enumerate(vals, 1):
                    c = ws_auditoria.cell(row=row_a, column=c_idx, value=val)
                    c.font = fnt
                    c.fill = fil
                    c.alignment = al
                    c.border = border_thin
                ws_auditoria.row_dimensions[row_a].height = 20
                row_a += 1

    # Filtros automáticos y fijación de encabezados
    ws_resumen.freeze_panes = "A7"
    ws_auditoria.freeze_panes = "A5"
    if row_a > 5:
        ws_auditoria.auto_filter.ref = f"A4:J{row_a-1}"
    if row_idx > 7:
        ws_resumen.auto_filter.ref = f"A6:J{row_idx-1}"

    # Autoajuste inteligente de anchos de columnas
    min_widths_resumen = {
        "A": 13,  # Fecha
        "B": 11,  # Hora
        "C": 15,  # Zona
        "D": 22,  # Diligenciado por
        "E": 14,  # Pernoctaron
        "F": 15,  # En otra zona
        "G": 12,  # Ausentes
        "H": 12,  # Foráneos
        "I": 16,  # Total Evaluados
        "J": 25   # Observaciones
    }
    for col in ws_resumen.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = min_widths_resumen.get(col_letter, 12)
        for cell in col:
            if cell.row < 6 or cell.row >= row_idx:
                continue
            v_str = str(cell.value or "")
            if "\n" in v_str:
                v_str = max(v_str.split("\n"), key=len)
            if len(v_str) > max_len:
                max_len = len(v_str)
        ws_resumen.column_dimensions[col_letter].width = max(max_len + 3, min_widths_resumen.get(col_letter, 12))

    min_widths_audit = {
        "A": 13,  # Fecha
        "B": 11,  # Hora
        "C": 15,  # Zona del Reporte
        "D": 22,  # Diligenciado por
        "E": 12,  # Placa
        "F": 15,  # Zona Asignada
        "G": 13,  # Condición
        "H": 18,  # ¿Pernoctó Físicamente?
        "I": 24,  # Estado Auditoría
        "J": 25   # Observación / Novedad
    }
    for col in ws_auditoria.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = min_widths_audit.get(col_letter, 12)
        for cell in col:
            if cell.row < 4:
                continue
            v_str = str(cell.value or "")
            if "\n" in v_str:
                v_str = max(v_str.split("\n"), key=len)
            if len(v_str) > max_len:
                max_len = len(v_str)
        ws_auditoria.column_dimensions[col_letter].width = max(max_len + 3, min_widths_audit.get(col_letter, 12))

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
