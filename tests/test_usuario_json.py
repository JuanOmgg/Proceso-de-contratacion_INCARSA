import json
import sys
import os
import random

# Forzar salida utf-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Asegurar que Python encuentre el módulo src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.schemas.usuario_schema import UsuarioInput
from src.services.usuario import CREATE_user, READ_user, DELETE_user
from src.loaders.usuario_loader import UPDATE_user_db


def probar_crud_usuario_json():
    print("============================================================")
    print("🧪 BATERÍA DE PRUEBAS PARA USUARIOS (SCHEMA + SERVICE + DB)")
    print("============================================================")

    # 1. Generar datos dinámicos con documento y correo único para evitar colisiones
    num_unico = random.randint(1000000, 9999999)
    doc_prueba = f"10{num_unico}"
    correo_prueba = f"usuario.{num_unico}@incarsa.com"

    peticion_json_swagger = f"""
    {{
        "nombres": "Carlos Esteban",
        "apellidos": "Mendoza Lopez",
        "tipo_documento": "CC",
        "num_documento": "{doc_prueba}",
        "num_telefono": "3109876543",
        "correo": "{correo_prueba}",
        "contrasena": "PasswordSegura123*",
        "id_rol": 1
    }}
    """

    print("📩 1. Simulando Petición HTTP/Swagger (JSON Payload)...")
    data_dict = json.loads(peticion_json_swagger)
    print(json.dumps(data_dict, indent=4, ensure_ascii=False))

    # 2. Validación con Schema Pydantic
    print("\n🧹 2. Validando Payload con Pydantic (UsuarioInput)...")
    payload = UsuarioInput(**data_dict)
    print("   ✅ Pydantic: Datos válidos.")

    # 3. Creación de Usuario vía Servicio (incluye hashing bcrypt)
    print("\n🚀 3. Creando Usuario en Base de Datos (CREATE_user)...")
    res_crear = CREATE_user(payload)
    print(f"   - Respuesta: {res_crear}")

    if not res_crear.get("exito"):
        print(f"   ❌ Falló la creación: {res_crear.get('mensaje')}")
        return

    user_id = res_crear.get("id_generado")
    print(f"   ✅ Usuario registrado con ID: #{user_id}")

    # 4. Lectura / Consulta de Usuario
    print(f"\n🔍 4. Consultando Usuario ID #{user_id} (READ_user)...")
    res_lectura = READ_user(user_id)
    if res_lectura.get("exito"):
        user_data = res_lectura.get("data", {})
        print(f"   • Nombre completo: {user_data.get('nombres')} {user_data.get('apellidos')}")
        print(f"   • Documento: {user_data.get('tipo_documento')} {user_data.get('num_documento')}")
        print(f"   • Correo: {user_data.get('correo')}")
        print(f"   • Rol Asignado: {user_data.get('nombre_rol')} ({user_data.get('descripcion_rol')})")
    else:
        print(f"   ❌ Error al leer: {res_lectura.get('mensaje')}")

    # 5. Actualización parcial (PATCH)
    print(f"\n📝 5. Actualizando campos del Usuario ID #{user_id} (UPDATE_user_db)...")
    cambios = {"num_telefono": "3150009988", "apellidos": "Mendoza Gómez"}
    res_update = UPDATE_user_db(user_id, cambios)
    print(f"   - Resultado: {res_update.get('mensaje')}")

    # 6. Limpieza / Eliminación de Usuario de prueba
    print(f"\n🗑️ 6. Eliminando Usuario ID #{user_id} (DELETE_user)...")
    res_delete = DELETE_user(user_id)
    print(f"   - Resultado: {res_delete.get('mensaje')}")

    print("\n🏁 PRUEBA DE USUARIOS COMPLETADA CON ÉXITO")


if __name__ == "__main__":
    probar_crud_usuario_json()
