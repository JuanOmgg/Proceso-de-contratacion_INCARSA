import sys
import os
import random

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.transformers.solicitudes_transformer import transformar_solicitud
from src.loaders.solicitudes_loaders import CREATE_solicitud_bd, GET_solicitud_bd

# IDs de referencia según la BD[cite: 2]
USUARIOS_VALIDOS     = list(range(1, 22))      # IDs del 1 al 21[cite: 2]
CONTRATISTAS_VALIDOS = [1, 2, 3, 4, 5, 6]      # IDs del 1 al 6[cite: 2]
PLANTAS_VALIDAS      = [1, 2, 3, 4, 5, 6]

# Rango completo de IDs de personas creadas con seed_personas.py[cite: 1, 2]
PERSONAS_VALIDAS     = list(range(1, 26))      # IDs del 1 al 25[cite: 1]


SOLICITUDES_SEED = [
    # 1. Individual (1 persona)
    {
        "titulo": "1. Inspección puntual de caldera (1 persona)",
        "payload": {
            "fecha_inicio": "2026-09-01", "fecha_fin": "2026-09-02",
            "empresa_origen": 1, "diligenciado_por": 1, "nivel_de_riesgo": "BAJO",
            "tipo_personal": "Contratista", "empresa_contratista": 1,
            "plantas_ids": [1], "personas_ids": [1],
            "actividad": "Verificación y lectura de sensores de presión",
            "estado": "ENVIADO", "is_active": True,
            "vehiculo": [], "eq_computo": [{"marca": "Dell", "modelo": "Latitude", "serie": "SN-001"}]
        }
    },
    # 2. Pareja (2 personas)
    {
        "titulo": "2. Mantenimiento eléctrico de paneles (2 personas)",
        "payload": {
            "fecha_inicio": "2026-09-03", "fecha_fin": "2026-09-07",
            "empresa_origen": 1, "diligenciado_por": 2, "nivel_de_riesgo": "BAJO",
            "tipo_personal": "Contratista", "empresa_contratista": 2,
            "plantas_ids": [1, 2], "personas_ids": [2, 3],
            "actividad": "Mantenimiento preventivo de tableros eléctricos",
            "estado": "ENVIADO", "is_active": True,
            "vehiculo": [{"placa": "ABC-123", "tipo": "Camioneta"}], "eq_computo": []
        }
    },
    # 3. Equipo pequeño (3 personas)
    {
        "titulo": "3. Reparación de tubería hidráulica (3 personas)",
        "payload": {
            "fecha_inicio": "2026-09-05", "fecha_fin": "2026-09-10",
            "empresa_origen": 2, "diligenciado_por": 5, "nivel_de_riesgo": "MEDIO",
            "tipo_personal": "Contratista", "empresa_contratista": 3,
            "plantas_ids": [2], "personas_ids": [4, 5, 6],
            "actividad": "Sustitución de tramo dañado en tubería principal",
            "estado": "POR APROBAR", "is_active": True,
            "vehiculo": [{"placa": "TUB-888", "tipo": "Camión"}], "eq_computo": []
        }
    },
    # 4. Grupo mediano (5 personas)
    {
        "titulo": "4. Auditoría general HSEQ (5 personas)",
        "payload": {
            "fecha_inicio": "2026-09-10", "fecha_fin": "2026-09-12",
            "empresa_origen": 1, "diligenciado_por": 7, "nivel_de_riesgo": "ALTO",
            "tipo_personal": "Visitante", "empresa_contratista": 4,
            "plantas_ids": [1, 3, 5], "personas_ids": [7, 8, 9, 10, 11],
            "actividad": "Auditoría de cumplimiento de normas SST y del sistema contraincendios",
            "estado": "APROBADO", "is_active": True,
            "vehiculo": [{"placa": "AUD-001", "tipo": "Sedán"}],
            "eq_computo": [{"marca": "Lenovo", "modelo": "ThinkPad", "serie": "SN-AUD1"}]
        }
    },
    # 5. Individual (1 persona)
    {
        "titulo": "5. Configuración de PLC y automatización (1 persona)",
        "payload": {
            "fecha_inicio": "2026-09-11", "fecha_fin": "2026-09-11",
            "empresa_origen": 3, "diligenciado_por": 4, "nivel_de_riesgo": "BAJO",
            "tipo_personal": "Contratista", "empresa_contratista": 2,
            "plantas_ids": [3], "personas_ids": [21],
            "actividad": "Actualización de firmware en controladores lógicos",
            "estado": "APROBADO", "is_active": True,
            "vehiculo": [], "eq_computo": [{"marca": "HP", "modelo": "ProBook", "serie": "SN-PLC-99"}]
        }
    },
    # 6. Cuadrilla grande (8 personas)
    {
        "titulo": "6. Obra civil y nivelación de terrenos (8 personas)",
        "payload": {
            "fecha_inicio": "2026-09-15", "fecha_fin": "2026-10-15",
            "empresa_origen": 2, "diligenciado_por": 10, "nivel_de_riesgo": "ALTO",
            "tipo_personal": "Contratista", "empresa_contratista": 1,
            "plantas_ids": [2, 4], "personas_ids": [12, 13, 14, 15, 16, 17, 18, 19],
            "actividad": "Adecuación de calzada interna y cimentación de parqueaderos",
            "estado": "EN REVISION", "is_active": True,
            "vehiculo": [
                {"placa": "EXC-101", "tipo": "Excavadora"},
                {"placa": "VOL-202", "tipo": "Volqueta"}
            ],
            "eq_computo": []
        }
    },
    # 7. Pareja (2 personas)
    {
        "titulo": "7. Levantamiento topográfico con dron (2 personas)",
        "payload": {
            "fecha_inicio": "2026-09-18", "fecha_fin": "2026-09-19",
            "empresa_origen": 3, "diligenciado_por": 12, "nivel_de_riesgo": "BAJO",
            "tipo_personal": "Contratista", "empresa_contratista": 5,
            "plantas_ids": [3, 6], "personas_ids": [11, 15],
            "actividad": "Mapeo fotogramétrico de terrenos adyacentes",
            "estado": "ENVIADO", "is_active": True,
            "vehiculo": [{"placa": "TOP-555", "tipo": "Camioneta"}],
            "eq_computo": [{"marca": "Asus", "modelo": "ROG", "serie": "SN-DRON-01"}]
        }
    },
    # 8. Grupo mediano (4 personas)
    {
        "titulo": "8. Limpieza técnica de tanques de combustible (4 personas)",
        "payload": {
            "fecha_inicio": "2026-09-20", "fecha_fin": "2026-09-23",
            "empresa_origen": 1, "diligenciado_por": 14, "nivel_de_riesgo": "ALTO",
            "tipo_personal": "Contratista", "empresa_contratista": 6,
            "plantas_ids": [1], "personas_ids": [7, 22, 23, 24],
            "actividad": "Drenaje, lavado industrial y neutralización de tanques de almacenamiento",
            "estado": "POR APROBAR", "is_active": True,
            "vehiculo": [{"placa": "CIST-99", "tipo": "Camión Cisterna"}], "eq_computo": []
        }
    },
    # 9. Individual (1 persona)
    {
        "titulo": "9. Capacitación de primeros auxilios (1 persona)",
        "payload": {
            "fecha_inicio": "2026-09-25", "fecha_fin": "2026-09-25",
            "empresa_origen": 4, "diligenciado_por": 15, "nivel_de_riesgo": "BAJO",
            "tipo_personal": "Visitante", "empresa_contratista": 3,
            "plantas_ids": [4], "personas_ids": [13],
            "actividad": "Taller teórico-práctico de atención básica a emergencias",
            "estado": "APROBADO", "is_active": True,
            "vehiculo": [], "eq_computo": [{"marca": "Apple", "modelo": "MacBook Air", "serie": "SN-MAC-12"}]
        }
    },
    # 10. Grupo grande (6 personas)
    {
        "titulo": "10. Montaje estructural de cubierta (6 personas)",
        "payload": {
            "fecha_inicio": "2026-10-01", "fecha_fin": "2026-10-10",
            "empresa_origen": 2, "diligenciado_por": 8, "nivel_de_riesgo": "ALTO",
            "tipo_personal": "Contratista", "empresa_contratista": 1,
            "plantas_ids": [2, 5], "personas_ids": [1, 4, 7, 9, 16, 17],
            "actividad": "Izaje y fijación de vigas principales en bodega central",
            "estado": "ENVIADO", "is_active": True,
            "vehiculo": [{"placa": "GRU-777", "tipo": "Grúa Telescópica"}], "eq_computo": []
        }
    },
    # 11. Trío (3 personas)
    {
        "titulo": "11. Fumigación y control de plagas (3 personas)",
        "payload": {
            "fecha_inicio": "2026-10-05", "fecha_fin": "2026-10-06",
            "empresa_origen": 3, "diligenciado_por": 3, "nivel_de_riesgo": "MEDIO",
            "tipo_personal": "Contratista", "empresa_contratista": 4,
            "plantas_ids": [1, 2, 3], "personas_ids": [18, 19, 20],
            "actividad": "Fumigación general de archivos y zonas de depósito",
            "estado": "RECHAZADO", "is_active": False,
            "vehiculo": [{"placa": "FUM-001", "tipo": "Van"}], "eq_computo": []
        }
    },
    # 12. Grupo mediano (5 personas)
    {
        "titulo": "12. Instalación de sistema de refrigeración (5 personas)",
        "payload": {
            "fecha_inicio": "2026-10-10", "fecha_fin": "2026-10-18",
            "empresa_origen": 1, "diligenciado_por": 18, "nivel_de_riesgo": "MEDIO",
            "tipo_personal": "Contratista", "empresa_contratista": 2,
            "plantas_ids": [1, 4], "personas_ids": [2, 6, 10, 14, 25],
            "actividad": "Montaje de chillers y ductos de aire acondicionado industrial",
            "estado": "ENVIADO", "is_active": True,
            "vehiculo": [{"placa": "REF-303", "tipo": "Camión"}], "eq_computo": []
        }
    },
    # 13. Individual (1 persona)
    {
        "titulo": "13. Revisión contable y financiera de obra (1 persona)",
        "payload": {
            "fecha_inicio": "2026-10-12", "fecha_fin": "2026-10-14",
            "empresa_origen": 4, "diligenciado_por": 21, "nivel_de_riesgo": "BAJO",
            "tipo_personal": "Visitante", "empresa_contratista": 5,
            "plantas_ids": [4], "personas_ids": [25],
            "actividad": "Verificación física de presupuestos e inventario de activos",
            "estado": "APROBADO", "is_active": True,
            "vehiculo": [], "eq_computo": [{"marca": "Dell", "modelo": "Vostro", "serie": "SN-CNT-88"}]
        }
    },
    # 14. Equipo masivo (7 personas)
    {
        "titulo": "14. Parada de planta por mantenimiento anual (7 personas)",
        "payload": {
            "fecha_inicio": "2026-11-01", "fecha_fin": "2026-11-15",
            "empresa_origen": 1, "diligenciado_por": 19, "nivel_de_riesgo": "ALTO",
            "tipo_personal": "Contratista", "empresa_contratista": 1,
            "plantas_ids": [1, 2, 3, 4, 5, 6], "personas_ids": [1, 2, 6, 7, 12, 20, 22],
            "actividad": "Mantenimiento general preventivo y correctivo multiespecialidad",
            "estado": "POR APROBAR", "is_active": True,
            "vehiculo": [
                {"placa": "MNT-001", "tipo": "Camioneta"},
                {"placa": "MNT-002", "tipo": "Camión de herramientas"}
            ],
            "eq_computo": [{"marca": "HP", "modelo": "ZBook", "serie": "SN-MNT-01"}]
        }
    },
    # 15. Pareja (2 personas)
    {
        "titulo": "15. Reemplazo de iluminación LED en altura (2 personas)",
        "payload": {
            "fecha_inicio": "2026-11-16", "fecha_fin": "2026-11-18",
            "empresa_origen": 2, "diligenciado_por": 6, "nivel_de_riesgo": "MEDIO",
            "tipo_personal": "Contratista", "empresa_contratista": 6,
            "plantas_ids": [2, 3], "personas_ids": [3, 18],
            "actividad": "Cambio de luminarias de vapor de sodio por campanas LED",
            "estado": "ENVIADO", "is_active": True,
            "vehiculo": [{"placa": "LUZ-909", "tipo": "Grúa de canastilla"}], "eq_computo": []
        }
    }
]


def seed_solicitudes():
    print("=" * 75)
    print("  SEED - CREANDO 15 SOLICITUDES CON DIFERENTE CANTIDAD DE PERSONAS")
    print("=" * 75)

    creadas = 0
    errores = 0

    for i, item in enumerate(SOLICITUDES_SEED, start=1):
        titulo = item["titulo"]
        payload = item["payload"]

        datos_limpios = transformar_solicitud(payload)
        resultado = CREATE_solicitud_bd(datos_limpios)

        if resultado.get("exito"):
            ids = resultado.get("ids_generados", [])
            num_personas = len(payload.get("personas_ids", []))
            num_plantas = len(payload.get("plantas_ids", []))
            creadas += len(ids)
            print(f"  [{i:02d}/15] OK  Solicitudes IDs: {ids} | {num_personas} persona(s) | {num_plantas} planta(s) -> {titulo}")
        else:
            errores += 1
            print(f"  [{i:02d}/15] ERROR - {titulo}: {resultado.get('mensaje')}")

    print("\n" + "=" * 75)
    print(f"  Solicitudes creadas exitosamente: {creadas}")
    print(f"  Errores al insertar             : {errores}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    seed_solicitudes()