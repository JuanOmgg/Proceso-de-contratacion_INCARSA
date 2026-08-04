import os
from contextlib import contextmanager
from dbutils.pooled_db import PooledDB
import pymysql
from dotenv import load_dotenv

# Cargar variables desde un archivo .env
load_dotenv()

# Crear el POOL de conexiones al arrancar la app
POOL = PooledDB(
    creator=pymysql,
    maxconnections=15,
    mincached=2, 
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=False,
    blocking=True,  # Si el pool se llena, las nuevas peticiones esperan un instante en vez de fallar
    ping=7,  # Verifica que la conexión esté viva antes de usarla
)

@contextmanager
def GET_conexion():

    conexion = POOL.connection()
    try:
        yield conexion
    except Exception as e:
        conexion.rollback()
        print(f"❌❌ Error en la conexión a la base de datos desde database: {e} ❌❌")
        raise e
    finally:
        conexion.close() #devuelve conecion al pool sin destruirla