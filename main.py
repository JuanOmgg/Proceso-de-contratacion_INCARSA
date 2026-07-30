# main.py
import os
from src.extractors import extraer_solicitud_desde_json
from src.transformers import transformar_solicitud
from src.loaders import guardar_solicitud_bd


def ejecutar_flujo(ruta_json: str = None):
    # -------------------------------------------------------------
    # 1. EXTRACTOR (O MOCK DATA SI AÚN NO HAY ARCHIVO JSON)
    # -------------------------------------------------------------
    if ruta_json and os.path.exists(ruta_json):
        print(f"📂 Extrayendo datos desde archivo: {ruta_json}")
        datos_raw = extraer_solicitud_desde_json(ruta_json)
    else:
        print(
            "⚠️ No se proporcionó un archivo JSON válido. Usando datos de prueba (Mock Data)..."
        )
        # Diccionario de prueba con datos 'sucios' para probar el transformer
        datos_raw = {
            "empresa_origen": "INCARSA",
            "diligenciado_por": "Juan Pérez",
            "nivel_de_riesgo": "Alto",
            "tipo_de_persona": "Contratista",
            "empresa_contratista": "Soluciones Industriales SAS",
            "planta_a_visitar": "Planta Central",
            "fecha_inicio": "01/08/2026",
            "fecha_fin": "24/08/2026",
            "actividad": "Mantenimiento preventivo en caldera principal",
            "vehiculo": {"tipo": "Camioneta", "placa": "ABC-123"},
            "personas": [
                {
                    "item": "1",
                    "ap_nombre": "Carlos Mendoza",
                    "tipo_doc": "CC",
                    "identificacion": 1012345678,
                    "cargo": "Supervisora de Obra",
                },
                {
                    "item": "2",
                    "ap_nombre": "Ana María Gómez",
                    "tipo_doc": "CC",
                    "identificacion": "1.098.765.432",
                    "cargo": "Técnico Electricista",
                },
            ],
            "eq_computo": [
                {"marca": "Lenovo", "modelo": "ThinkPad E14", "serie": "SN-987654321"}
            ],
        }

    if not datos_raw:
        print("⛔ No se pudieron obtener datos para procesar.")
        return

    # -------------------------------------------------------------
    # 2. TRANSFORMER: Limpia el diccionario
    # -------------------------------------------------------------
    print("🧹 [TRANSFORMER] Limpiando y normalizando datos...")
    datos_limpios = transformar_solicitud(datos_raw)

    # -------------------------------------------------------------
    # 3. LOADER: Guarda en la base de datos MySQL
    # -------------------------------------------------------------
    print("🚀 [LOADER] Insertando solicitud en MySQL...")
    resultado = guardar_solicitud_bd(datos_limpios)

    print("\n📩 [RESPUESTA FINAL]:")
    print(resultado)


if __name__ == "__main__":
    # Puedes pasarle la ruta de un JSON si existe, o dejarlo vacío para probar los datos locales
    ejecutar_flujo(ruta_json="data/raw/solicitud_ejemplo.json")
