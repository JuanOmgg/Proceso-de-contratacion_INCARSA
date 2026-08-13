import json
import sys
import os
import random

# Forzar salida utf-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Asegurar que Python encuentre el módulo raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.schemas.personas_schema import PersonInput
from src.services.personas import CREATE_person
from database import GET_conexion


# ─────────────────────────────────────────────
# Helpers de limpieza (solo para el test)
# ─────────────────────────────────────────────

def _delete_person_db(persona_id: int):
    """Elimina una persona de prueba (y sus documentos por CASCADE)."""
    with GET_conexion() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM personas WHERE id = %s", (persona_id,))
            conn.commit()


def _get_person_db(persona_id: int) -> dict:
    """Consulta directa a BD para verificar que la persona existe."""
    with GET_conexion() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, nombre, apellido, tipo_doc, identificacion, cargo, observacion FROM personas WHERE id = %s",
                (persona_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else {}


def _get_documentos_db(persona_id: int) -> list:
    """Consulta directa a BD para verificar que los documentos se guardaron."""
    with GET_conexion() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, tipo_doc, nombre_archivo FROM documentos_persona WHERE persona_id = %s",
                (persona_id,)
            )
            return [dict(r) for r in cursor.fetchall()]


# ─────────────────────────────────────────────
# Test principal
# ─────────────────────────────────────────────

def probar_crud_personas():
    print("============================================================")
    print("  BATERIA DE PRUEBAS - PERSONAS (SCHEMA + SERVICE + DB)")
    print("============================================================")

    num_unico = random.randint(10000000, 99999999)

    peticion_json = f"""
    {{
        "nombre": "Carlos",
        "apellido": "Ramirez",
        "tipo_doc": "CC",
        "identificacion": "{num_unico}",
        "cargo": "Electricista",
        "observacion": "Persona de prueba automatica",
        "documentos_ids": [
            {{"tipo_doc": "ARL", "nombre_archivo": "arl_carlos_{num_unico}.pdf"}},
            {{"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_{num_unico}.pdf"}}
        ]
    }}
    """

    # 1. Parsear JSON
    print("\n1. Simulando payload JSON (como llegaria desde Swagger/Frontend)...")
    data_dict = json.loads(peticion_json)
    print(json.dumps(data_dict, indent=4, ensure_ascii=False))

    # 2. Validar con Pydantic
    print("\n2. Validando con Pydantic (PersonInput)...")
    try:
        payload = PersonInput(**data_dict)
        print("   OK - Pydantic: datos validos.")
    except Exception as e:
        print(f"   ERROR - Pydantic rechazo los datos: {e}")
        return

    # 3. Crear persona via servicio (schema -> transformer -> loader)
    print("\n3. Creando persona en Base de Datos (CREATE_person)...")
    res_crear = CREATE_person(payload)
    print(f"   Respuesta: {res_crear}")

    if not res_crear.get("exito"):
        print(f"   ERROR - Fallo la creacion: {res_crear.get('mensaje')}")
        return

    persona_id = res_crear.get("persona")
    print(f"   OK - Persona registrada con ID: #{persona_id}")

    # 4. Verificar que la persona existe en BD
    print(f"\n4. Verificando persona ID #{persona_id} en Base de Datos...")
    persona_db = _get_person_db(persona_id)
    if persona_db:
        print(f"   OK - Encontrada en BD:")
        print(f"        Nombre      : {persona_db.get('nombre')} {persona_db.get('apellido')}")
        print(f"        Documento   : {persona_db.get('tipo_doc')} {persona_db.get('identificacion')}")
        print(f"        Cargo       : {persona_db.get('cargo')}")
        print(f"        Observacion : {persona_db.get('observacion')}")
    else:
        print(f"   ERROR - Persona ID #{persona_id} no encontrada en BD.")
        return

    # 5. Verificar que los documentos se guardaron correctamente
    print(f"\n5. Verificando documentos asociados a Persona ID #{persona_id}...")
    documentos_db = _get_documentos_db(persona_id)
    if documentos_db:
        print(f"   OK - {len(documentos_db)} documento(s) registrado(s):")
        for doc in documentos_db:
            print(f"        [{doc.get('tipo_doc')}] -> {doc.get('nombre_archivo')}")
    else:
        print("   ERROR - No se encontraron documentos asociados a la persona.")

    # 6. Limpieza
    print(f"\n6. Limpiando persona de prueba ID #{persona_id}...")
    _delete_person_db(persona_id)
    verificacion = _get_person_db(persona_id)
    if not verificacion:
        print(f"   OK - Persona ID #{persona_id} eliminada correctamente (documentos eliminados por CASCADE).")
    else:
        print(f"   ERROR - La persona sigue existiendo en BD despues del DELETE.")

    print("\n  TEST DE PERSONAS COMPLETADO")
    print("============================================================\n")


if __name__ == "__main__":
    probar_crud_personas()
