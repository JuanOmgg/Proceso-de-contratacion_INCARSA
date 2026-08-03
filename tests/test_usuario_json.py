import json
import sys
import os

# Asegurar que Python encuentre el módulo src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.usuario import CREATE_user  # O la ruta donde tengas tu entidad

# 1. Este es el JSON tal cual como te llegaría desde Swagger o Postman
peticion_json_swagger = """
{
    "nombres": "Carlos",
    "apellidos": "Mendoza",
    "tipo_de_documento": "CC",
    "num_documento": 1098765432,
    "numero_de_telefono": 3109876543,
    "correo": "carlos.mendoza@incarsa.com",
    "password": "PasswordSegura123*",
    "id_rol": 1
}
"""


def probar_creacion_desde_json():
    print("📩 Simulando petición HTTP/Swagger con Payload JSON...\n")

    # 2. Parsear el string JSON a un diccionario de Python
    data = json.loads(peticion_json_swagger)

    # 3. Consumir la entidad pasando las claves del JSON
    respuesta = CREATE_user(
        nombre=data["nombres"],
        apellido=data["apellidos"],
        tipo_doc=data["tipo_de_documento"],
        documento=data["num_documento"],
        telefono=data["numero_de_telefono"],
        correo=data["correo"],
        password=data["password"],
        id_rol=data["id_rol"],
    )

    # 4. Imprimir la respuesta formateada como JSON (simulando la respuesta de la API)
    print("📤 Respuesta de la API (JSON):")
    print(json.dumps(respuesta, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    probar_creacion_desde_json()
