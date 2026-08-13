import sys
import os

# Forzar salida utf-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Asegurar que Python encuentre el modulo src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.schemas.usuario_schema import UsuarioInput
from src.services.usuario import CREATE_user

# ─────────────────────────────────────────────────────────────────────
# Roles disponibles en la BD:
#   1 = Administrador
#   2 = Gestion documental
#   3 = SST
#   4 = GESCO
#   5 = Seguridad corporativa & riesgo
# ─────────────────────────────────────────────────────────────────────

USUARIOS_SEED = [
    {"nombres": "Laura",    "apellidos": "Ramirez Perez",    "tipo_documento": "CC", "num_documento": "20000001", "num_telefono": "3100000001", "correo": "laura.ramirez@incarsa.com",    "contrasena": "Password123*", "id_rol": 1},
    {"nombres": "Andres",   "apellidos": "Torres Gomez",     "tipo_documento": "CC", "num_documento": "20000002", "num_telefono": "3100000002", "correo": "andres.torres@incarsa.com",    "contrasena": "Password123*", "id_rol": 2},
    {"nombres": "Sofia",    "apellidos": "Martinez Cruz",    "tipo_documento": "CC", "num_documento": "20000003", "num_telefono": "3100000003", "correo": "sofia.martinez@incarsa.com",   "contrasena": "Password123*", "id_rol": 3},
    {"nombres": "Miguel",   "apellidos": "Hernandez Vega",   "tipo_documento": "CC", "num_documento": "20000004", "num_telefono": "3100000004", "correo": "miguel.hernandez@incarsa.com", "contrasena": "Password123*", "id_rol": 4},
    {"nombres": "Valentina","apellidos": "Lopez Castillo",   "tipo_documento": "CC", "num_documento": "20000005", "num_telefono": "3100000005", "correo": "valentina.lopez@incarsa.com",  "contrasena": "Password123*", "id_rol": 5},
    {"nombres": "Carlos",   "apellidos": "Sanchez Mora",     "tipo_documento": "CC", "num_documento": "20000006", "num_telefono": "3100000006", "correo": "carlos.sanchez@incarsa.com",   "contrasena": "Password123*", "id_rol": 2},
    {"nombres": "Daniela",  "apellidos": "Vargas Rios",      "tipo_documento": "CC", "num_documento": "20000007", "num_telefono": "3100000007", "correo": "daniela.vargas@incarsa.com",   "contrasena": "Password123*", "id_rol": 3},
    {"nombres": "Felipe",   "apellidos": "Jimenez Rueda",    "tipo_documento": "CC", "num_documento": "20000008", "num_telefono": "3100000008", "correo": "felipe.jimenez@incarsa.com",   "contrasena": "Password123*", "id_rol": 4},
    {"nombres": "Natalia",  "apellidos": "Castro Benitez",   "tipo_documento": "CC", "num_documento": "20000009", "num_telefono": "3100000009", "correo": "natalia.castro@incarsa.com",   "contrasena": "Password123*", "id_rol": 5},
    {"nombres": "Juan",     "apellidos": "Moreno Salcedo",   "tipo_documento": "CC", "num_documento": "20000010", "num_telefono": "3100000010", "correo": "juan.moreno@incarsa.com",      "contrasena": "Password123*", "id_rol": 2},
    {"nombres": "Camila",   "apellidos": "Reyes Fuentes",    "tipo_documento": "CC", "num_documento": "20000011", "num_telefono": "3100000011", "correo": "camila.reyes@incarsa.com",     "contrasena": "Password123*", "id_rol": 3},
    {"nombres": "Sergio",   "apellidos": "Guerrero Navas",   "tipo_documento": "CC", "num_documento": "20000012", "num_telefono": "3100000012", "correo": "sergio.guerrero@incarsa.com",  "contrasena": "Password123*", "id_rol": 1},
    {"nombres": "Paola",    "apellidos": "Medina Acosta",    "tipo_documento": "CC", "num_documento": "20000013", "num_telefono": "3100000013", "correo": "paola.medina@incarsa.com",     "contrasena": "Password123*", "id_rol": 4},
    {"nombres": "Ricardo",  "apellidos": "Perez Cardenas",   "tipo_documento": "CC", "num_documento": "20000014", "num_telefono": "3100000014", "correo": "ricardo.perez@incarsa.com",    "contrasena": "Password123*", "id_rol": 5},
    {"nombres": "Mariana",  "apellidos": "Diaz Ospina",      "tipo_documento": "CC", "num_documento": "20000015", "num_telefono": "3100000015", "correo": "mariana.diaz@incarsa.com",     "contrasena": "Password123*", "id_rol": 2},
    {"nombres": "Pablo",    "apellidos": "Rojas Quintero",   "tipo_documento": "CC", "num_documento": "20000016", "num_telefono": "3100000016", "correo": "pablo.rojas@incarsa.com",      "contrasena": "Password123*", "id_rol": 3},
    {"nombres": "Alejandra","apellidos": "Florez Montoya",   "tipo_documento": "CC", "num_documento": "20000017", "num_telefono": "3100000017", "correo": "alejandra.florez@incarsa.com", "contrasena": "Password123*", "id_rol": 4},
    {"nombres": "Esteban",  "apellidos": "Aguilar Pinto",    "tipo_documento": "CC", "num_documento": "20000018", "num_telefono": "3100000018", "correo": "esteban.aguilar@incarsa.com",  "contrasena": "Password123*", "id_rol": 5},
    {"nombres": "Luisa",    "apellidos": "Suarez Valencia",  "tipo_documento": "CC", "num_documento": "20000019", "num_telefono": "3100000019", "correo": "luisa.suarez@incarsa.com",     "contrasena": "Password123*", "id_rol": 2},
    {"nombres": "Mateo",    "apellidos": "Cano Bermudez",    "tipo_documento": "CC", "num_documento": "20000020", "num_telefono": "3100000020", "correo": "mateo.cano@incarsa.com",       "contrasena": "Password123*", "id_rol": 3},
]

ROLES_NOMBRE = {
    1: "Administrador",
    2: "Gestion documental",
    3: "SST",
    4: "GESCO",
    5: "Seguridad corporativa & riesgo",
}


def crear_20_usuarios():
    print("============================================================")
    print("  SEED - CREANDO 20 USUARIOS EN LA BASE DE DATOS")
    print("============================================================")
    print("  NOTA: Estos registros SE QUEDAN en la BD.")
    print("============================================================\n")

    ids_creados = []
    errores = []

    for i, u_data in enumerate(USUARIOS_SEED, start=1):
        try:
            payload = UsuarioInput(**u_data)
            resultado = CREATE_user(payload)

            if resultado.get("exito"):
                user_id = resultado.get("id_generado")
                ids_creados.append(user_id)
                rol_nombre = ROLES_NOMBRE.get(u_data["id_rol"], "?")
                print(f"  [{i:02d}/20] OK  ID #{user_id:>3} - {u_data['nombres']} {u_data['apellidos']}"
                      f" | Rol: {rol_nombre}")
            else:
                msg = resultado.get("mensaje", "Error desconocido")
                errores.append((i, u_data["nombres"], msg))
                print(f"  [{i:02d}/20] ERROR - {u_data['nombres']} {u_data['apellidos']}: {msg}")

        except Exception as e:
            errores.append((i, u_data.get("nombres", "?"), str(e)))
            print(f"  [{i:02d}/20] EXCEPCION - {u_data.get('nombres', '?')}: {e}")

    print(f"\n  Usuarios creados : {len(ids_creados)} / 20")
    print(f"  Errores          : {len(errores)}")
    print(f"  IDs generados    : {ids_creados}")
    print("\n  Puedes usar estos IDs en USUARIOS_VALIDOS del test_multi_solicitud.py")
    print("============================================================\n")

    return ids_creados


if __name__ == "__main__":
    crear_20_usuarios()
