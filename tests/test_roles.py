# tests/test_roles.py
import sys
import os

# Agrega la carpeta raíz del proyecto al PATH de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ahora sí realizas la importación de tu loader
from src.loaders.roles_loader import GETALL_roles


def probar_conexion_roles():
    print("🔄 Conectando a MySQL para consultar roles...")
    roles = GETALL_roles()

    if not roles:
        print("⚠️ No se encontraron roles o la conexión a la base de datos falló.")
        return

    print("\n📋 Roles registrados en la Base de Datos:")
    print("=" * 70)
    for r in roles:
        print(f"  - ID: {r['id_rol']:<2} | Rol: {r['nombre_rol']:<22} | {r['descripcion']}")
    print("=" * 70)
    print(f"✅ ¡Prueba exitosa! Se consultaron {len(roles)} roles correctamente.")


if __name__ == "__main__":
    probar_conexion_roles()