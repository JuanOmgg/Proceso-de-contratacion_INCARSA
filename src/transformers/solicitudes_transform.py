# src/transformers/solicitudes_transform.py
from datetime import datetime

def transformar_solicitud(datos_raw: dict) -> dict:
    """
    Recibe los datos en sucio de la solicitud, los limpia,
    los valida y entrega un diccionario listo para el loader.
    """
    
    # Limpieza 
    solicitud_limpia = {
        "empresa_origen": datos_raw.get("empresa_origen", "").strip().upper(),
        "diligenciado_por": datos_raw.get("diligenciado_por", "").strip().title(), #title() - Para nombres propios, si escriben juan pasa a Juan
        "nivel_de_riesgo": datos_raw.get("nivel_de_riesgo", "BAJO").strip().upper(),
        "tipo_de_persona": datos_raw.get("tipo_de_persona", "").strip(),
        "empresa_contratista": datos_raw.get("empresa_contratista", "").strip().upper(),
        "planta_a_visitar": datos_raw.get("planta_a_visitar", "").strip(),
        "actividad": datos_raw.get("actividad", "").strip(),
        "estado": datos_raw.get("estado", "PENDIENTE").strip().upper(), #strip elimina espacios vacios al inicio o al final
    }

    # Convertir fechas a formato MySQL (YYYY-MM-DD)
    for campo_fecha in ["fecha_inicio", "fecha_fin"]:
        val_fecha = datos_raw.get(campo_fecha)
        if isinstance(val_fecha, str) and "/" in val_fecha:
            # Ejemplo: Transforma '28/07/2026' -> '2026-07-28'
            solicitud_limpia[campo_fecha] = datetime.strptime(val_fecha, "%d/%m/%Y").strftime("%Y-%m-%d")
        else:
            solicitud_limpia[campo_fecha] = val_fecha

    # Limpieza de vehículo
    vehiculo_raw = datos_raw.get("vehiculo", {})
    solicitud_limpia["vehiculo"] = {
        "tipo": vehiculo_raw.get("tipo", "").strip().upper(),
        "placa": vehiculo_raw.get("placa", "").strip().upper().replace("-", "").replace(" ", "")
    }

    # 4. Limpieza de la lista de personas
    personas_limpias = []
    for p in datos_raw.get("personas", []):
        personas_limpias.append({
            "ap_nombre": p.get("ap_nombre", "").strip().upper(),
            "tipo_doc": p.get("tipo_doc", "").strip().upper(),
            # Quita puntos de la identificación: '1.020.333' -> '1020333'
            "identificacion": str(p.get("identificacion", "")).replace(".", "").strip(),
            "cargo": p.get("cargo", "").strip().title()
        })
    solicitud_limpia["personas"] = personas_limpias

    # 5. Limpieza de equipos
    equipos_limpios = []
    for eq in datos_raw.get("eq_computo", []):
        equipos_limpios.append({
            "marca": eq.get("marca", "").strip().upper(),
            "modelo": eq.get("modelo", "").strip().upper(),
            "serie": eq.get("serie", "").strip().upper()
        })
    solicitud_limpia["eq_computo"] = equipos_limpios

    return solicitud_limpia