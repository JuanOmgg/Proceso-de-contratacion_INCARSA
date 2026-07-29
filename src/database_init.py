# src/database_init.py
import os
from src.database import obtener_conexion

def inicializar_base_de_datos():
    """
    Lee el archivo schema.sql y lo ejecuta completo en MySQL.
    Ideal para el primer despliegue en producción.
    """
    ruta_schema = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    
    if not os.path.exists(ruta_schema):
        print(f"❌ No se encontró el archivo de esquema en: {ruta_schema}")
        return

    # Leer el contenido del script SQL
    with open(ruta_schema, "r", encoding="utf-8") as f:
        sql_script = f.read()

    conexion = obtener_conexion()
    if not conexion:
        print("❌ Error de conexión al inicializar BD")
        return

    try:
        cursor = conexion.cursor()
        # multi=True permite ejecutar múltiples sentencias SQL separadas por ';'
        for resultado in cursor.execute(sql_script, multi=True):
            pass  # Procesa cada sentencia del script
            
        conexion.commit()
        print("🚀 ¡Base de datos e infraestructuras inicializadas con éxito desde schema.sql!")
    except Exception as e:
        conexion.rollback()
        print(f"❌ Error durante la inicialización de la BD: {e}")
    finally:
        conexion.close()

if __name__ == "__main__":
    inicializar_base_de_datos()