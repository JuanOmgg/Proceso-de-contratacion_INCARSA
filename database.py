import os
import time
import threading
from contextlib import contextmanager
from dbutils.pooled_db import PooledDB
import pymysql
from dotenv import load_dotenv

# Cargar variables desde un archivo .env
load_dotenv()

_pool = None
_pool_lock = threading.Lock()

def _crear_pool(max_reintentos: int = 5, espera_segundos: float = 2.0) -> PooledDB:
    """
    Crea el pool de conexiones de forma tolerante a fallos.
    Si la base de datos tarda en responder al arrancar, reintenta con backoff
    en lugar de crashear la aplicación completa.
    """
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", 3306))
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME")

    ultimo_error = None
    for intento in range(1, max_reintentos + 1):
        try:
            pool = PooledDB(
                creator=pymysql,
                maxconnections=20,
                mincached=0,  # No abre conexiones en frío al importar; las crea bajo demanda
                maxcached=5,
                maxshared=0,
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                blocking=True,  # Si el pool se llena, espera en vez de fallar
                ping=7,  # 7 = reconectar si se pierde conexión + ping activo
            )
            # Prueba de humo: verificar que MySQL responda
            conn = pool.connection()
            conn.close()
            return pool
        except Exception as e:
            ultimo_error = e
            print(f"⚠️ [DATABASE] Intento {intento}/{max_reintentos} de conexión a MySQL ({host}:{port}/{database}) falló: {e}")
            if intento < max_reintentos:
                time.sleep(espera_segundos * intento)

    print(f"❌ [DATABASE] No se pudo establecer conexión con MySQL tras {max_reintentos} intentos: {ultimo_error}")
    # Retorna un pool configurado en modo bajo demanda para que intente conectar cuando la BD levante
    return PooledDB(
        creator=pymysql,
        maxconnections=20,
        mincached=0,
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        blocking=True,
        ping=7,
    )

def obtener_pool() -> PooledDB:
    """Retorna el pool de conexiones existente o lo inicializa de manera perezosa y segura (thread-safe)."""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = _crear_pool()
    return _pool

# Proxy transparente para compatibilidad total con cualquier `POOL.connection()` existente
class _PoolProxy:
    def __getattr__(self, name):
        return getattr(obtener_pool(), name)

POOL = _PoolProxy()

def obtener_conexion(max_reintentos: int = 3, espera: float = 1.0):
    """
    Obtiene una conexión del pool con tolerancia a fallos transitorios.
    """
    ultimo_err = None
    for intento in range(1, max_reintentos + 1):
        try:
            return obtener_pool().connection()
        except Exception as e:
            ultimo_err = e
            print(f"⚠️ [DATABASE] Error al solicitar conexión (intento {intento}/{max_reintentos}): {e}")
            if intento < max_reintentos:
                time.sleep(espera)
    raise ultimo_err

def verificar_conexion(max_reintentos: int = 3, espera: float = 1.0) -> bool:
    """Verifica si la base de datos está disponible sin lanzar excepciones no controladas."""
    try:
        conn = obtener_conexion(max_reintentos=max_reintentos, espera=espera)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        return True
    except Exception as e:
        print(f"⚠️ [DATABASE] Chequeo de conexión falló: {e}")
        return False

@contextmanager
def GET_conexion(max_reintentos: int = 3, espera: float = 1.0):
    """
    Context manager tolerante a fallos para transacciones y consultas.
    Devuelve automáticamente la conexión al pool al finalizar.
    """
    conexion = obtener_conexion(max_reintentos=max_reintentos, espera=espera)
    try:
        yield conexion
    except Exception as e:
        try:
            conexion.rollback()
        except Exception:
            pass
        print(f"[ERROR] Error en la conexion a la base de datos desde database: {e}")
        raise e
    finally:
        try:
            conexion.close()  # Devuelve la conexión al pool sin destruirla
        except Exception:
            pass