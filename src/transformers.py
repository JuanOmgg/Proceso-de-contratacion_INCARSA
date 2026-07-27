import pandas as pd
from pathlib import Path

def extraer_desde_excel(ruta_relativa: str) -> pd.DataFrame:

    """Lee un archivo Excel local comprobando su existencia."""
    
    ruta = Path("data/raw") / ruta_relativa
    
    if not ruta.exists():
        raise FileNotFoundError(f"El archivo no se encuentra en: {ruta}")
        
    print(f"📥 Leyendo datos desde Excel: {ruta.name}")
    return pd.read_excel(ruta)

def extraer_desde_sql(consulta_query: str, conexion_db) -> pd.DataFrame:

    """Extrae datos directamente ejecutando una consulta SQL."""
    
    print("📥 Consultando base de datos...")
    return pd.read_sql(consulta_query, conexion_db)