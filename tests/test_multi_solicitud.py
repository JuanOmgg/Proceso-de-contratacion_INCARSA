import sys
import os
import random

# Forzar salida utf-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Agregar la raiz del proyecto al PATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.transformers.solicitudes_transformer import transformar_solicitud
from src.loaders.solicitudes_loaders import CREATE_solicitud_bd, GET_solicitud_bd

# ─── IDs reales en la BD ─────────────────────────────────────────────────────
USUARIOS_VALIDOS     = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
CONTRATISTAS_VALIDOS = [1, 2, 3, 4, 5, 6]   # 1=General 2=Electricos 3=Andes 4=Omega 5=Rio 6=Alpha
PERSONAS_VALIDAS     = [2, 3, 4, 5, 6]       # Creadas con seed_personas.py


def ejecutar_caso_prueba(titulo: str, payload: dict):
    print("\n" + "=" * 70)
    print(f"  {titulo.upper()}")
    print("=" * 70)
    print(f"  Actividad        : {payload.get('actividad')}")
    print(f"  Nivel riesgo     : {payload.get('nivel_de_riesgo')}")
    print(f"  Tipo personal    : {payload.get('tipo_personal')}")
    print(f"  Estado           : {payload.get('estado')}")
    print(f"  Fechas           : {payload.get('fecha_inicio')} -> {payload.get('fecha_fin')}")
    print(f"  Contratista ID   : {payload.get('empresa_contratista')}")
    print(f"  Diligenciado por : {payload.get('diligenciado_por')}")
    print(f"  Plantas          : {payload.get('plantas_ids')}")
    print(f"  Personas         : {payload.get('personas_ids')}")
    print(f"  Vehiculos        : {len(payload.get('vehiculo', []))} unidad(es)")
    print(f"  Equipos computo  : {len(payload.get('eq_computo', []))} equipo(s)")
    print(f"  is_active        : {payload.get('is_active')}")

    datos_limpios = transformar_solicitud(payload)
    resultado = CREATE_solicitud_bd(datos_limpios)

    if resultado.get("exito"):
        ids = resultado.get("ids_generados", [])
        print(f"  OK  Solicitudes creadas: {ids}")
        for sol_id in ids:
            detalle = GET_solicitud_bd(sol_id)
            if detalle.get("exito"):
                datos = detalle.get("datos", {})
                plantas_visita = datos.get("plantas", [])
                ingresantes    = datos.get("ingresantes", [])
                print(f"    -> ID #{sol_id} | Empresa origen: {datos.get('empresa_origen')}"
                      f" | Plantas: {len(plantas_visita)}"
                      f" | Ingresantes: {len(ingresantes)}"
                      f" | Vehiculos: {len(datos.get('vehiculo', []))}")
    else:
        print(f"  ERROR: {resultado.get('mensaje')}")


def correr_todas_las_pruebas():
    print("\n  INICIANDO BATERIA DE PRUEBAS DE CREACION DE SOLICITUDES")

    # ── CASO 1: Mantenimiento electrico ───────────────────────────────
    ejecutar_caso_prueba(
        titulo="Caso 1: Mantenimiento electrico - ENVIADO - Riesgo BAJO",
        payload={
            "fecha_inicio":       "2026-08-01",
            "fecha_fin":          "2026-08-05",
            "empresa_origen":     1,
            "diligenciado_por":   1,
            "nivel_de_riesgo":    "BAJO",
            "tipo_personal":      "Contratista",
            "empresa_contratista": 1,
            "plantas_ids":        [1, 2, 5],
            "personas_ids":       [2, 3],
            "actividad":          "Mantenimiento preventivo de tableros electricos en planta principal",
            "estado":             "ENVIADO",
            "is_active":          True,
            "vehiculo":           [{"placa": "ABC-123", "tipo": "Camioneta"}],
            "eq_computo":         [{"marca": "Dell", "modelo": "Latitude 5420", "serie": "SN-001"}],
        },
    )

    # ── CASO 2: Obra civil ────────────────────────────────────────────
    ejecutar_caso_prueba(
        titulo="Caso 2: Obra civil - POR APROBAR - Riesgo MEDIO",
        payload={
            "fecha_inicio":       "2026-08-12",
            "fecha_fin":          "2026-08-25",
            "empresa_origen":     1,
            "diligenciado_por":   3,
            "nivel_de_riesgo":    "MEDIO",
            "tipo_personal":      "Contratista",
            "empresa_contratista": 2,
            "plantas_ids":        [1, 2, 5, 3, 6],
            "personas_ids":       [2, 4, 6],
            "actividad":          "Construccion de cerramiento perimetral y adecuacion de vias internas",
            "estado":             "POR APROBAR",
            "is_active":          True,
            "vehiculo": [
                {"placa": "TRK-456", "tipo": "Camion"},
                {"placa": "EXC-789", "tipo": "Excavadora"},
            ],
            "eq_computo": [],
        },
    )

    # ── CASO 3: Inspeccion SST ────────────────────────────────────────
    ejecutar_caso_prueba(
        titulo="Caso 3: Inspeccion SST - APROBADO - Riesgo ALTO",
        payload={
            "fecha_inicio":       "2026-07-20",
            "fecha_fin":          "2026-07-22",
            "empresa_origen":     2,
            "diligenciado_por":   7,
            "nivel_de_riesgo":    "ALTO",
            "tipo_personal":      "Visitante",
            "empresa_contratista": 3,
            "plantas_ids":        [1, 3, 4],
            "personas_ids":       [2, 3, 4, 5],
            "actividad":          "Inspeccion de condiciones de seguridad y salud - auditoria externa",
            "estado":             "APROBADO",
            "is_active":          False,
            "vehiculo":           [{"placa": "VIS-321", "tipo": "Sedan"}],
            "eq_computo": [
                {"marca": "Lenovo", "modelo": "ThinkPad X1",    "serie": "SN-002"},
                {"marca": "HP",     "modelo": "EliteBook 840",  "serie": "SN-003"},
            ],
        },
    )

    # ── CASO 4: Transporte de carga ───────────────────────────────────
    ejecutar_caso_prueba(
        titulo="Caso 4: Transporte de carga - EN REVISION - Riesgo MEDIO",
        payload={
            "fecha_inicio":       "2026-09-01",
            "fecha_fin":          "2026-09-30",
            "empresa_origen":     3,
            "diligenciado_por":   11,
            "nivel_de_riesgo":    "MEDIO",
            "tipo_personal":      "Contratista",
            "empresa_contratista": 4,
            "plantas_ids":        [1, 2, 3, 4],
            "personas_ids":       [2, 3, 4, 5, 6],
            "actividad":          "Transporte y despacho de materiales pesados entre plantas - contrato mensual",
            "estado":             "EN REVISION",
            "is_active":          True,
            "vehiculo": [
                {"placa": "MUL-111", "tipo": "Tracto-camion"},
                {"placa": "MUL-222", "tipo": "Tracto-camion"},
                {"placa": "MUL-333", "tipo": "Camion"},
            ],
            "eq_computo": [],
        },
    )

    # ── CASO 5: Capacitacion ──────────────────────────────────────────
    ejecutar_caso_prueba(
        titulo="Caso 5: Capacitacion - RECHAZADO - Riesgo BAJO",
        payload={
            "fecha_inicio":       "2026-06-10",
            "fecha_fin":          "2026-06-11",
            "empresa_origen":     4,
            "diligenciado_por":   15,
            "nivel_de_riesgo":    "BAJO",
            "tipo_personal":      "Visitante",
            "empresa_contratista": 5,
            "plantas_ids":        [2],
            "personas_ids":       [6],
            "actividad":          "Capacitacion en primeros auxilios y uso de extintores - personal externo",
            "estado":             "RECHAZADO",
            "is_active":          False,
            "vehiculo":           [],
            "eq_computo":         [{"marca": "Apple", "modelo": "MacBook Pro", "serie": "SN-MAC-001"}],
        },
    )

    # ── CASO 6: Totalmente aleatorio ──────────────────────────────────
    actividades = [
        "Revision de calderas y sistemas de vapor",
        "Instalacion de paneles solares en cubierta",
        "Fumigacion y control de plagas en bodegas",
        "Cambio de luminarias LED en areas de produccion",
        "Mantenimiento de sistemas contra incendios",
    ]
    personas_random = sorted(random.sample(PERSONAS_VALIDAS, k=random.randint(1, 3)))

    ejecutar_caso_prueba(
        titulo="Caso 6: Totalmente aleatorio",
        payload={
            "fecha_inicio":       f"2026-{random.randint(7, 9):02d}-{random.randint(1, 15):02d}",
            "fecha_fin":          f"2026-{random.randint(10, 12):02d}-{random.randint(1, 28):02d}",
            "empresa_origen":     random.choice([1, 2, 3, 4]),
            "diligenciado_por":   random.choice(USUARIOS_VALIDOS),
            "nivel_de_riesgo":    random.choice(["BAJO", "MEDIO", "ALTO"]),
            "tipo_personal":      random.choice(["Contratista", "Visitante"]),
            "empresa_contratista": random.choice(CONTRATISTAS_VALIDOS),
            "plantas_ids":        random.sample([1, 2, 3, 4], k=random.randint(1, 3)),
            "personas_ids":       personas_random,
            "actividad":          random.choice(actividades),
            "estado":             random.choice(["ENVIADO", "POR APROBAR", "APROBADO", "EN REVISION", "RECHAZADO"]),
            "is_active":          random.choice([True, False]),
            "vehiculo":           random.choice([
                [],
                [{"placa": "RND-001", "tipo": "Camioneta"}],
                [{"placa": "RND-002", "tipo": "Camion"}, {"placa": "RND-003", "tipo": "Sedan"}],
            ]),
            "eq_computo":         random.choice([
                [],
                [{"marca": "Asus", "modelo": "ZenBook", "serie": "SN-RND-01"}],
            ]),
        },
    )

    print("\n  BATERIA DE PRUEBAS FINALIZADA CON EXITO")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    correr_todas_las_pruebas()
