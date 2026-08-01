import pymysql

# 1. Leer el archivo SQL
with open("schema.sql", "r", encoding="utf-8") as archivo:
    sql_script = archivo.read()

try:
    # 2. Conectar a MySQL (cambia 'root' por tu contraseña si es diferente)
    conexion = pymysql.connect(
        host="localhost", user="root", password="root", autocommit=True
    )

    with conexion.cursor() as cursor:
        # Separar y ejecutar cada sentencia SQL por punto y coma
        sentencias = sql_script.split(";")
        for sentencia in sentencias:
            sentencia_limpia = sentencia.strip()
            if sentencia_limpia:
                cursor.execute(sentencia_limpia)

    print(
        "✅ Base de datos 'incarsa_ingresos' y tablas creadas / actualizadas con éxito."
    )
    conexion.close()

except Exception as e:
    print(f"❌ Error al ejecutar el script SQL: {e}")