import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import GET_conexion

CONTRATISTAS_SEED = [
    {"nombre": "Electricos del Norte S.A.S.",     "observacion": "Especialistas en instalaciones electricas industriales"},
    {"nombre": "Construcciones Andes Ltda.",       "observacion": "Obras civiles y mantenimiento de infraestructura"},
    {"nombre": "Servicios Tecnicos Omega S.A.S.",  "observacion": "Mantenimiento mecanico y servicios tecnicos especializados"},
    {"nombre": "Logistica y Transporte Rio S.A.",  "observacion": "Transporte de carga y logistica operacional"},
    {"nombre": "Seguridad Industrial Alpha Ltda.", "observacion": "Consultoria en SST y seguridad industrial"},
]

def seed_contratistas():
    print("============================================================")
    print("  SEED - CREANDO EMPRESAS CONTRATISTAS EN LA BASE DE DATOS")
    print("============================================================\n")

    ids_creados = []

    with GET_conexion() as conn:
        with conn.cursor() as cursor:
            for c in CONTRATISTAS_SEED:
                try:
                    cursor.execute(
                        "INSERT INTO emp_contratista (nombre, observacion) VALUES (%s, %s)",
                        (c["nombre"], c["observacion"])
                    )
                    new_id = cursor.lastrowid
                    ids_creados.append(new_id)
                    print(f"  OK  ID #{new_id} - {c['nombre']}")
                except Exception as e:
                    if "Duplicate" in str(e):
                        cursor.execute("SELECT id FROM emp_contratista WHERE nombre = %s", (c["nombre"],))
                        row = cursor.fetchone()
                        existing_id = row["id"] if row else "?"
                        ids_creados.append(existing_id)
                        print(f"  YA EXISTE ID #{existing_id} - {c['nombre']}")
                    else:
                        print(f"  ERROR - {c['nombre']}: {e}")

            conn.commit()

    print(f"\n  Contratistas en BD: {len(ids_creados)}")
    print(f"  IDs              : {ids_creados}")
    print("\n  Usa estos IDs en CONTRATISTAS_VALIDOS del test_multi_solicitud.py")
    print("============================================================\n")
    return ids_creados

if __name__ == "__main__":
    seed_contratistas()
