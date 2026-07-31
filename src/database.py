import os
from dbutils.pooled_db import PooledDB
import pymysql
from dotenv import load_dotenv

# Cargar variables desde un archivo .env
load_dotenv()

# Crear el POOL de conexiones al arrancar la app
POOL = PooledDB(
    creator=pymysql,
    maxconnections=10,  # Máximo de conexiones simultáneas en el pool
    mincached=2,  # Conexiones mínimas siempre abiertas y listas
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=False,
    blocking=True,  # Si el pool se llena, las nuevas peticiones esperan un instante en vez de fallar
    ping=7,  # Verifica que la conexión esté viva antes de usarla
)


def GET_conexion():
    
    return POOL.connection()