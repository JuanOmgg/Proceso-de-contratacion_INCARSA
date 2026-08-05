import sys
import os
import random

# Forzar salida utf-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Asegurar que Python encuentre el módulo src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.loaders.planta_loader import (
    CREATE_planta_db,
    GET_planta_db,
    UPDATE_planta_db,
    DELETE_planta_db,
)


def probar_gestion_plantas_4_empresas():
    print("============================================================")
    print("🧪 BATERÍA DE PRUEBAS DE PLANTAS (PARA 4 EMPRESAS DISTINTAS)")
    print("============================================================")

    empresas = [
        {"id": 1, "nombre": "INCARSA S.A.S."},
        {"id": 2, "nombre": "MILPA S.A.S."},
        {"id": 3, "nombre": "CARBOINSA S.A.S."},
        {"id": 4, "nombre": "UNIMINAS S.A.S."},
    ]

    plantas_creadas = []

    print("\n🚀 1. Registrando plantas para cada una de las 4 empresas...")
    for emp in empresas:
        rand_num = random.randint(100, 999)
        nombre_planta = f"Planta {emp['nombre'].split()[0]} - ZONA {rand_num}"
        
        datos_planta = {
            "nombre": nombre_planta,
            "id_empresa": emp["id"]
        }

        res_crear = CREATE_planta_db(datos_planta)
        
        if res_crear.get("exito"):
            planta_id = res_crear.get("id")
            plantas_creadas.append({"id": planta_id, "empresa_id": emp["id"], "nombre": nombre_planta})
            print(f"   ✅ Empresa #{emp['id']} ({emp['nombre']}) ➔ Planta '{nombre_planta}' creada con ID #{planta_id}")
        else:
            print(f"   ❌ Error al crear planta para Empresa #{emp['id']}: {res_crear.get('mensaje')}")

    print("\n🔍 2. Verificando lectura de plantas en Base de Datos (GET_planta_db)...")
    for p in plantas_creadas:
        res_get = GET_planta_db(p["id"])
        if res_get.get("exito"):
            data_db = res_get.get("planta", {})
            print(f"   • Planta ID #{data_db.get('id')}: Nombre = '{data_db.get('nombre')}' | Empresa ID = {data_db.get('id_empresa')}")
        else:
            print(f"   ❌ Error al consultar Planta ID #{p['id']}: {res_get.get('mensaje')}")

    if plantas_creadas:
        planta_test = plantas_creadas[0]
        print(f"\n📝 3. Probando actualización (PATCH) en Planta ID #{planta_test['id']}...")
        nuevo_nombre = f"{planta_test['nombre']} (ACTUALIZADA)"
        res_update = UPDATE_planta_db(planta_test["id"], {"nombre": nuevo_nombre})
        print(f"   - Resultado: {res_update.get('mensaje')}")

        print(f"\n🗑️ 4. Limpiando planta de prueba ID #{planta_test['id']}...")
        res_del = DELETE_planta_db(planta_test["id"])
        print(f"   - Resultado: {res_del.get('mensaje')}")

    print("\n🏁 PRUEBA DE PLANTAS PARA 4 EMPRESAS FINALIZADA CON ÉXITO")


if __name__ == "__main__":
    probar_gestion_plantas_4_empresas()
