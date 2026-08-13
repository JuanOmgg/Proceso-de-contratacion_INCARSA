import sys
import os
import time

# Forzar salida utf-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Asegurar que Python encuentre el modulo src y tests
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from tests.test_roles          import probar_conexion_roles
from tests.test_plantas        import probar_gestion_plantas_4_empresas
from tests.test_personas       import probar_crud_personas
from tests.test_multi_solicitud import correr_todas_las_pruebas

# Seeds (poblan la BD y se quedan)
from tests.test_usuario_json   import crear_20_usuarios
from tests.seed_personas       import seed_personas
from tests.seed_contratistas   import seed_contratistas


def seccion(numero: int, titulo: str):
    print(f"\n{'=' * 70}")
    print(f"  {numero}. {titulo}")
    print(f"{'=' * 70}")


def ejecutar_suite_completa():
    inicio = time.time()

    print("=" * 70)
    print("  SUITE COMPLETA DE PRUEBAS - PROCESO DE CONTRATOS INCARSA")
    print("=" * 70)
    print("  NOTA: Los seeds (usuarios, personas, contratistas) guardan")
    print("        datos en la BD para ser usados en los tests.")
    print("=" * 70)

    resultados = []

    # ── 1. ROLES ──────────────────────────────────────────────────────
    seccion(1, "CONEXION Y LECTURA DE ROLES")
    try:
        probar_conexion_roles()
        resultados.append(("Roles", "OK"))
    except Exception as e:
        resultados.append(("Roles", f"ERROR: {e}"))

    # ── 2. SEED USUARIOS (crea 20, se quedan en BD) ───────────────────
    seccion(2, "SEED - CREACION DE 20 USUARIOS (quedan en BD)")
    try:
        ids = crear_20_usuarios()
        resultados.append(("Seed Usuarios", f"OK - {len(ids)} creados"))
    except Exception as e:
        resultados.append(("Seed Usuarios", f"ERROR: {e}"))

    # ── 3. SEED CONTRATISTAS ──────────────────────────────────────────
    seccion(3, "SEED - EMPRESAS CONTRATISTAS (quedan en BD)")
    try:
        ids = seed_contratistas()
        resultados.append(("Seed Contratistas", f"OK - {len(ids)} registradas"))
    except Exception as e:
        resultados.append(("Seed Contratistas", f"ERROR: {e}"))

    # ── 4. PLANTAS ────────────────────────────────────────────────────
    seccion(4, "GESTION DE PLANTAS (4 EMPRESAS)")
    try:
        probar_gestion_plantas_4_empresas()
        resultados.append(("Plantas", "OK"))
    except Exception as e:
        resultados.append(("Plantas", f"ERROR: {e}"))

    # ── 5. SEED PERSONAS ──────────────────────────────────────────────
    seccion(5, "SEED - PERSONAS CON DOCUMENTOS (quedan en BD)")
    try:
        ids = seed_personas()
        resultados.append(("Seed Personas", f"OK - {len(ids)} creadas"))
    except Exception as e:
        resultados.append(("Seed Personas", f"ERROR: {e}"))

    # ── 6. TEST PERSONAS (CRUD limpio) ────────────────────────────────
    seccion(6, "TEST PERSONAS - CRUD COMPLETO (crea y borra)")
    try:
        probar_crud_personas()
        resultados.append(("Test Personas", "OK"))
    except Exception as e:
        resultados.append(("Test Personas", f"ERROR: {e}"))

    # ── 7. SOLICITUDES ────────────────────────────────────────────────
    seccion(7, "SOLICITUDES - MULTI-CREACION POR EMPRESA (6 casos)")
    try:
        correr_todas_las_pruebas()
        resultados.append(("Solicitudes", "OK"))
    except Exception as e:
        resultados.append(("Solicitudes", f"ERROR: {e}"))

    # ── RESUMEN FINAL ─────────────────────────────────────────────────
    duracion = time.time() - inicio
    print("\n" + "=" * 70)
    print("  RESUMEN FINAL")
    print("=" * 70)
    for nombre, estado in resultados:
        icono = "OK " if estado.startswith("OK") else "ERR"
        print(f"  [{icono}]  {nombre:<25} {estado}")
    print(f"\n  Tiempo total: {duracion:.1f}s")
    errores = [r for r in resultados if not r[1].startswith("OK")]
    if errores:
        print(f"  Fallaron {len(errores)} modulo(s): {[r[0] for r in errores]}")
    else:
        print("  Todos los modulos pasaron correctamente.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    ejecutar_suite_completa()
