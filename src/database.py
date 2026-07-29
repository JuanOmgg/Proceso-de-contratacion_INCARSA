import mysql.connector
from mysql.connector import Error

DB_CONFIG = {

    'host' : 'localhost',
    'user' : 'root',
    'password' : 'root',
    'database' : 'incarsa_ingresos',
    'charset' : 'utf8mb4'

}

def GET_conexion():

    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"❌ Error al conectar a MySQL: {e}")
        return None