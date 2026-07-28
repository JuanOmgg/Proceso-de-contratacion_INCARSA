import json
import os

def extraer_solicitud_desde_json(ruta_archivo: str) -> dict:

    """
    Lee un archivo JSON desde el disco duro y lo convierte 
    en un diccionario de Python (dict).
    """

    if not os.path.exists(ruta_archivo):
        print(f"❌ Error: El archivo '{ruta_archivo}' no existe.")
        return {}

    try:
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            
            # json.load() toma el texto del archivo y lo convierte a un dict de Python
            datos_raw = json.load(archivo)
            print(f"📦 Datos extraídos con éxito desde: {ruta_archivo}")
            return datos_raw
            
    except json.JSONDecodeError as e:
        print(f"❌ Error: El archivo JSON está mal formado: {e}")
        return {}
    except Exception as e:
        print(f"❌ Error inesperado al leer el archivo: {e}")
        return {}