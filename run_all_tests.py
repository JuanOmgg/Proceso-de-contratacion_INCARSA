import sys
import os

# Forzar salida utf-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Asegurar que Python encuentre el módulo src y tests
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from tests.test_roles import probar_conexion_roles
from tests.test_usuario_json import probar_crud_usuario_json
from tests.test_plantas import probar_gestion_plantas_4_empresas
from tests.test_multi_solicitud import correr_todas_las_pruebas

def ejecutar_suite_completa():
    print("============================================================")
    print("🚀 EJECUTANDO BATERÍA COMPLETA DE PRUEBAS - PROCESO CONTRATOS")
    print("============================================================\n")

    print("------------------------------------------------------------")
    print("📋 1. PRUEBA DE ROLES")
    print("------------------------------------------------------------")
    probar_conexion_roles()

    print("\n------------------------------------------------------------")
    print("👤 2. PRUEBA DE USUARIOS (CRUD + SCHEMA + HASHING)")
    print("------------------------------------------------------------")
    probar_crud_usuario_json()

    print("\n------------------------------------------------------------")
    print("🏭 3. PRUEBA DE PLANTAS (4 EMPRESAS DISTINTAS)")
    print("------------------------------------------------------------")
    probar_gestion_plantas_4_empresas()

    print("\n------------------------------------------------------------")
    print("📄 4. PRUEBA DE SOLICITUDES Y MULTI-CREACIÓN POR EMPRESA")
    print("------------------------------------------------------------")
    correr_todas_las_pruebas()

    print("\n============================================================")
    print("🎉 ¡TODAS LAS PRUEBAS SE EJECUTARON EXITOSAMENTE!")
    print("============================================================")

if __name__ == "__main__":
    ejecutar_suite_completa()
