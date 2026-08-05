import sys
import os

# Forzar salida utf-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Agregar la raíz del proyecto al PATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.transformers.solicitudes_transformer import transformar_solicitud
from src.loaders.solicitudes_loaders import CREATE_solicitud_bd, GET_solicitud_bd


def ejecutar_caso_prueba(titulo: str, plantas_ids: list):
    payload = {
        "fecha_inicio": "2026-08-10",
        "fecha_fin": "2026-08-15",
        "empresa_origen": 1,
        "diligenciado_por": 1,
        "nivel_de_riesgo": "BAJO",
        "tipo_personal": "Contratista",
        "empresa_contratista": 1,
        "plantas_ids": plantas_ids,
        "actividad": f"Mantenimiento programado - {titulo}",
        "vehiculo": [{"placa": "XYZ-999", "tipo": "Camión"}],
        "personas": [
            {
                "ap_nombre": "Juan Pérez",
                "cargo": "Ingeniero Residente",
                "identificacion": "987654321",
                "tipo_doc": "CC",
                "documentos": [
                    {"tipo_doc": "cedula", "nombre_archivo": "test_cedula.pdf"},
                    {"tipo_doc": "arl", "nombre_archivo": "test_arl.pdf"},
                    {"tipo_doc": "examenes_medicos", "nombre_archivo": "test_med.pdf"},
                    {"tipo_doc": "otros", "nombre_archivo": "test_otros.pdf"}
                ]
            }
        ],
        "eq_computo": [
            {"marca": "Dell", "modelo": "Latitude 5420", "serie": "DELL-12345"}
        ],
    }

    print("\n" + "=" * 70)
    print(f"🧪 {titulo.upper()}")
    print("=" * 70)
    print(f"📥 Plantas Solicitadas: {plantas_ids}")

    datos_limpios = transformar_solicitud(payload)
    resultado = CREATE_solicitud_bd(datos_limpios)

    if resultado.get("exito"):
        ids = resultado.get("ids_generados", [])
        print(f"✅ Resultado: {resultado.get('mensaje')}")
        print(f"📋 Solicitudes Generadas en BD: IDs {ids}")

        for sol_id in ids:
            detalle = GET_solicitud_bd(sol_id)
            if detalle.get("exito"):
                datos = detalle.get("datos", {})
                plantas_visita = datos.get("plantas", [])
                nombres_plantas = [p["nombre"] for p in plantas_visita]
                print(f"\n   📌 Solicitud ID #{sol_id}:")
                print(f"      • Empresa Origen ID: {datos.get('empresa_origen')}")
                print(f"      • Cantidad de Plantas: {len(plantas_visita)}")
                print(f"      • Nombres de Plantas: {nombres_plantas}")
                print(f"      • Personas: {len(datos.get('personas', []))}")
                print(f"      • Vehículos: {len(datos.get('vehiculo', []))}")
    else:
        print(f"❌ Error: {resultado.get('mensaje')}")


def correr_todas_las_pruebas():
    print("\n🚀 INICIANDO BATERÍA DE PRUEBAS DE CREACIÓN DE SOLICITUDES")

    # CASO 1: 3 plantas de la MISMA empresa (Empresa 1: Plantas 1, 2, 5)
    ejecutar_caso_prueba(
        titulo="Caso 1: 3 plantas de la MISMA empresa (INCARSA S.A.S.)",
        plantas_ids=[1, 2, 5]
    )

    # CASO 2: Mezcla de empresas (3 plantas de Empresa 1 + 2 plantas de Empresa 2)
    ejecutar_caso_prueba(
        titulo="Caso 2: Agrupación Mixta (3 plantas de Empresa 1 + 2 plantas de Empresa 2)",
        plantas_ids=[1, 2, 5, 3, 6]
    )

    # CASO 3: 3 plantas de 3 empresas DIFERENTES (Empresa 1: 1, Empresa 2: 3, Empresa 3: 4)
    ejecutar_caso_prueba(
        titulo="Caso 3: 3 plantas de 3 empresas DIFERENTES",
        plantas_ids=[1, 3, 4]
    )

    print("\n🏁 BATERÍA DE PRUEBAS FINALIZADA CON ÉXITO")


if __name__ == "__main__":
    correr_todas_las_pruebas()
