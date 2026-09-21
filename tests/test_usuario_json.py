import sys
import os

# Forzar salida utf-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Asegurar que Python encuentre el modulo src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.schemas.usuario_schema import UsuarioInput
from src.services.usuario import CREATE_user
from src.loaders.usuario_loader import UPDATE_user_db
from database import GET_conexion

# ─────────────────────────────────────────────────────────────────────
# Roles disponibles en el sistema (MySQL: tabla `roles`):
#   1 = ADMINISTRADOR
#   2 = SUPERADMIN
#   3 = VIGILANTE
#   4 = EQUIPO SCR - RADICADOS
#   5 = GESTION DOCUMENTAL
#   6 = SST (Seguridad y Salud en el Trabajo)
#   7 = GESCO (Gestión del conocimiento)
#   8 = SCR (Seguridad corporativa y riesgo)
# ─────────────────────────────────────────────────────────────────────

ROLES_NOMBRE = {
    1: "ADMINISTRADOR",
    2: "SUPERADMIN",
    3: "VIGILANTE",
    4: "EQUIPO SCR - RADICADOS",
    5: "GESTION DOCUMENTAL",
    6: "SST",
    7: "GESCO",
    8: "SCR",
}

USUARIOS_SEED = [
    # ─── ROL 1: ADMINISTRADOR ─────────────────────────────────────────
    {"nombres": "Laura",     "apellidos": "Ramirez Perez",    "tipo_documento": "CC", "num_documento": "20000001", "num_telefono": "3100000001", "correo": "laura.ramirez@incarsa.com",    "contrasena": "Password123*", "id_rol": 1},
    {"nombres": "Sergio",    "apellidos": "Guerrero Navas",   "tipo_documento": "CC", "num_documento": "20000012", "num_telefono": "3100000012", "correo": "sergio.guerrero@incarsa.com",  "contrasena": "Password123*", "id_rol": 1},

    # ─── ROL 2: SUPERADMIN ────────────────────────────────────────────
    {"nombres": "Carlos",    "apellidos": "Sanchez Mora",     "tipo_documento": "CC", "num_documento": "20000006", "num_telefono": "3100000006", "correo": "carlos.sanchez@incarsa.com",   "contrasena": "Password123*", "id_rol": 2},

    # ─── ROL 3: VIGILANTE ─────────────────────────────────────────────
    {"nombres": "Daniela",   "apellidos": "Vargas Rios",      "tipo_documento": "CC", "num_documento": "20000007", "num_telefono": "3100000007", "correo": "daniela.vargas@incarsa.com",   "contrasena": "Password123*", "id_rol": 3},
    {"nombres": "Mateo",     "apellidos": "Cano Bermudez",    "tipo_documento": "CC", "num_documento": "20000020", "num_telefono": "3100000020", "correo": "mateo.cano@incarsa.com",       "contrasena": "Password123*", "id_rol": 3},

    # ─── ROL 4: EQUIPO SCR - RADICADOS ────────────────────────────────
    {"nombres": "Miguel",    "apellidos": "Hernandez Vega",   "tipo_documento": "CC", "num_documento": "20000004", "num_telefono": "3100000004", "correo": "miguel.hernandez@incarsa.com", "contrasena": "Password123*", "id_rol": 4},
    {"nombres": "Paola",     "apellidos": "Medina Acosta",    "tipo_documento": "CC", "num_documento": "20000013", "num_telefono": "3100000013", "correo": "paola.medina@incarsa.com",     "contrasena": "Password123*", "id_rol": 4},

    # ─── ROL 5: GESTION DOCUMENTAL ────────────────────────────────────
    {"nombres": "Andres",    "apellidos": "Torres Gomez",     "tipo_documento": "CC", "num_documento": "20000002", "num_telefono": "3100000002", "correo": "andres.torres@incarsa.com",    "contrasena": "Password123*", "id_rol": 5},
    {"nombres": "Valentina", "apellidos": "Lopez Castillo",   "tipo_documento": "CC", "num_documento": "20000005", "num_telefono": "3100000005", "correo": "valentina.lopez@incarsa.com",  "contrasena": "Password123*", "id_rol": 5},
    {"nombres": "Juan",      "apellidos": "Moreno Salcedo",   "tipo_documento": "CC", "num_documento": "20000010", "num_telefono": "3100000010", "correo": "juan.moreno@incarsa.com",      "contrasena": "Password123*", "id_rol": 5},
    {"nombres": "Luisa",     "apellidos": "Suarez Valencia",  "tipo_documento": "CC", "num_documento": "20000019", "num_telefono": "3100000019", "correo": "luisa.suarez@incarsa.com",     "contrasena": "Password123*", "id_rol": 5},

    # ─── ROL 6: SST (Seguridad y Salud en el Trabajo) ─────────────────
    {"nombres": "Sofia",     "apellidos": "Martinez Cruz",    "tipo_documento": "CC", "num_documento": "20000003", "num_telefono": "3100000003", "correo": "sofia.martinez@incarsa.com",   "contrasena": "Password123*", "id_rol": 6, "plantas_ids": [1, 2]},
    {"nombres": "Camila",    "apellidos": "Reyes Fuentes",    "tipo_documento": "CC", "num_documento": "20000011", "num_telefono": "3100000011", "correo": "camila.reyes@incarsa.com",     "contrasena": "Password123*", "id_rol": 6, "plantas_ids": [1]},
    {"nombres": "Pablo",     "apellidos": "Rojas Quintero",   "tipo_documento": "CC", "num_documento": "20000016", "num_telefono": "3100000016", "correo": "pablo.rojas@incarsa.com",      "contrasena": "Password123*", "id_rol": 6, "plantas_ids": [2]},

    # ─── ROL 7: GESCO (Gestión del Conocimiento) ──────────────────────
    {"nombres": "Felipe",    "apellidos": "Jimenez Rueda",    "tipo_documento": "CC", "num_documento": "20000008", "num_telefono": "3100000008", "correo": "felipe.jimenez@incarsa.com",   "contrasena": "Password123*", "id_rol": 7, "plantas_ids": [1]},
    {"nombres": "Alejandra", "apellidos": "Florez Montoya",   "tipo_documento": "CC", "num_documento": "20000017", "num_telefono": "3100000017", "correo": "alejandra.florez@incarsa.com", "contrasena": "Password123*", "id_rol": 7, "plantas_ids": [2]},

    # ─── ROL 8: SCR (Seguridad Corporativa y Riesgo) ──────────────────
    {"nombres": "Natalia",   "apellidos": "Castro Benitez",   "tipo_documento": "CC", "num_documento": "20000009", "num_telefono": "3100000009", "correo": "natalia.castro@incarsa.com",   "contrasena": "Password123*", "id_rol": 8},
    {"nombres": "Ricardo",   "apellidos": "Perez Cardenas",   "tipo_documento": "CC", "num_documento": "20000014", "num_telefono": "3100000014", "correo": "ricardo.perez@incarsa.com",    "contrasena": "Password123*", "id_rol": 8},
    {"nombres": "Mariana",   "apellidos": "Diaz Ospina",      "tipo_documento": "CC", "num_documento": "20000015", "num_telefono": "3100000015", "correo": "mariana.diaz@incarsa.com",     "contrasena": "Password123*", "id_rol": 8},
    {"nombres": "Esteban",   "apellidos": "Aguilar Pinto",    "tipo_documento": "CC", "num_documento": "20000018", "num_telefono": "3100000018", "correo": "esteban.aguilar@incarsa.com",  "contrasena": "Password123*", "id_rol": 8},
]


def buscar_usuario_existente(cursor, num_documento: str, correo: str):
    """Verifica si el usuario ya existe por cédula o correo electrónico."""
    cursor.execute(
        "SELECT id, id_rol, nombres, apellidos FROM usuarios WHERE num_documento = %s OR correo = %s LIMIT 1",
        (num_documento, correo)
    )
    return cursor.fetchone()


def crear_20_usuarios():
    print("============================================================")
    print("  SEED - GESTIÓN Y CARGA DE 20 USUARIOS CON NUEVOS ROLES")
    print("============================================================")
    print("  Roles en sistema: 8 roles (ADMIN, SUPERADMIN, VIGILANTE,")
    print("  EQUIPO SCR - RADICADOS, GESTION DOC, SST, GESCO, SCR).")
    print("============================================================\n")

    ids_procesados = []
    creados = 0
    actualizados = 0
    errores = []
    conteo_por_rol = {nombre: 0 for nombre in ROLES_NOMBRE.values()}

    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                for i, u_data in enumerate(USUARIOS_SEED, start=1):
                    rol_id = u_data["id_rol"]
                    rol_nombre = ROLES_NOMBRE.get(rol_id, f"Rol {rol_id}")

                    try:
                        existente = buscar_usuario_existente(cursor, u_data["num_documento"], u_data["correo"])

                        if existente:
                            user_id = existente["id"]
                            # Si ya existe, actualizamos su rol y datos para asegurar concordancia con los nuevos roles
                            update_payload = {
                                "nombres": u_data["nombres"],
                                "apellidos": u_data["apellidos"],
                                "tipo_documento": u_data["tipo_documento"],
                                "num_telefono": u_data["num_telefono"],
                                "id_rol": rol_id,
                                "is_active": True,
                            }
                            if "plantas_ids" in u_data:
                                update_payload["plantas_ids"] = u_data["plantas_ids"]

                            res_update = UPDATE_user_db(user_id, update_payload)
                            if res_update.get("exito"):
                                ids_procesados.append(user_id)
                                actualizados += 1
                                conteo_por_rol[rol_nombre] += 1
                                print(f"  [{i:02d}/20] ACTUALIZADO ID #{user_id:>3} - {u_data['nombres']} {u_data['apellidos']}"
                                      f" | Rol: {rol_nombre}")
                            else:
                                msg = res_update.get("mensaje", "Error al actualizar")
                                errores.append((i, u_data["nombres"], msg))
                                print(f"  [{i:02d}/20] ERROR ACT - {u_data['nombres']}: {msg}")

                        else:
                            # Usuario nuevo: registrarlo
                            payload = UsuarioInput(**u_data)
                            resultado = CREATE_user(payload)

                            if resultado.get("exito"):
                                user_id = resultado.get("id_generado")
                                ids_procesados.append(user_id)
                                creados += 1
                                conteo_por_rol[rol_nombre] += 1
                                print(f"  [{i:02d}/20] CREADO      ID #{user_id:>3} - {u_data['nombres']} {u_data['apellidos']}"
                                      f" | Rol: {rol_nombre}")
                            else:
                                msg = resultado.get("mensaje", "Error desconocido")
                                errores.append((i, u_data["nombres"], msg))
                                print(f"  [{i:02d}/20] ERROR - {u_data['nombres']} {u_data['apellidos']}: {msg}")

                    except Exception as item_err:
                        errores.append((i, u_data.get("nombres", "?"), str(item_err)))
                        print(f"  [{i:02d}/20] EXCEPCION - {u_data.get('nombres', '?')}: {item_err}")

    except Exception as db_err:
        print(f"\n❌ Error general de conexión o base de datos: {db_err}")
        return []

    print("\n" + "=" * 60)
    print(f"  Usuarios procesados con éxito : {len(ids_procesados)} / 20")
    print(f"    - Nuevos creados            : {creados}")
    print(f"    - Actualizados al nuevo rol : {actualizados}")
    print(f"  Errores                       : {len(errores)}")
    print("=" * 60)
    print("  Distribución por rol:")
    for rol, cant in conteo_por_rol.items():
        print(f"    • {rol:<24}: {cant} usuario(s)")
    print("=" * 60)
    print(f"  IDs listos para usar en tests : {ids_procesados}")
    print("============================================================\n")

    return ids_procesados


if __name__ == "__main__":
    crear_20_usuarios()
