import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import GET_conexion
from src.transformers.solicitudes_transformer import transformar_solicitud
from src.loaders.solicitudes_loaders import CREATE_solicitud_bd

# 1. Obtener IDs reales existentes en la base de datos
with GET_conexion() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM personas ORDER BY id ASC")
        DB_PERSONAS = [r["id"] for r in cur.fetchall()]

        cur.execute("SELECT id FROM planta ORDER BY id ASC")
        DB_PLANTAS = [r["id"] for r in cur.fetchall()]

        cur.execute("SELECT id FROM usuarios ORDER BY id ASC")
        DB_USUARIOS = [r["id"] for r in cur.fetchall()]

        cur.execute("SELECT id FROM emp_contratista ORDER BY id ASC")
        DB_CONTRATISTAS = [r["id"] for r in cur.fetchall()]

        cur.execute("SELECT id FROM empresa ORDER BY id ASC")
        DB_EMPRESAS = [r["id"] for r in cur.fetchall()]

        cur.execute("SELECT id FROM vehiculos ORDER BY id ASC")
        DB_VEHICULOS = [r["id"] for r in cur.fetchall()]


def get_items(db_list, indices):
    """Devuelve los IDs reales según los índices especificados."""
    if not db_list:
        return [idx + 1 for idx in indices]
    return [db_list[i % len(db_list)] for i in indices]


def get_single(db_list, index):
    """Devuelve un ID real según el índice."""
    if not db_list:
        return index + 1
    return db_list[index % len(db_list)]


SOLICITUDES_SEED = [
    # 1. Individual (1 persona, sin vehículo)
    {
        "titulo": "1. Inspección puntual de caldera (1 persona)",
        "payload": {
            "fecha_inicio": "2026-09-01", "fecha_fin": "2026-09-02",
            "empresa_origen": get_single(DB_EMPRESAS, 0),
            "diligenciado_por": get_single(DB_USUARIOS, 0),
            "nivel_de_riesgo": "BAJO", "tipo_personal": "Contratista",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 0),
            "plantas_ids": get_items(DB_PLANTAS, [0]),
            "personas_ids": get_items(DB_PERSONAS, [0]),
            "vehiculos_ids": [],
            "actividad": "Verificación y lectura de sensores de presión",
            "estado": "ENVIADO", "is_active": True,
            "eq_computo": [{"marca": "Dell", "modelo": "Latitude", "serie": "SN-001"}]
        }
    },
    # 2. Pareja (2 personas, 1 camioneta)
    {
        "titulo": "2. Mantenimiento eléctrico de paneles (2 personas, 1 camioneta)",
        "payload": {
            "fecha_inicio": "2026-09-03", "fecha_fin": "2026-09-07",
            "empresa_origen": get_single(DB_EMPRESAS, 0),
            "diligenciado_por": get_single(DB_USUARIOS, 1),
            "nivel_de_riesgo": "BAJO", "tipo_personal": "Contratista",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 1),
            "plantas_ids": get_items(DB_PLANTAS, [0, 1]),
            "personas_ids": get_items(DB_PERSONAS, [1, 2]),
            "vehiculos_ids": get_items(DB_VEHICULOS, [0]),
            "actividad": "Mantenimiento preventivo de tableros eléctricos",
            "estado": "ENVIADO", "is_active": True,
            "eq_computo": []
        }
    },
    # 3. Equipo pequeño (3 personas, 1 camión)
    {
        "titulo": "3. Reparación de tubería hidráulica (3 personas, 1 camión)",
        "payload": {
            "fecha_inicio": "2026-09-05", "fecha_fin": "2026-09-10",
            "empresa_origen": get_single(DB_EMPRESAS, 1),
            "diligenciado_por": get_single(DB_USUARIOS, 4),
            "nivel_de_riesgo": "MEDIO", "tipo_personal": "Contratista",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 2),
            "plantas_ids": get_items(DB_PLANTAS, [1]),
            "personas_ids": get_items(DB_PERSONAS, [3, 4, 5]),
            "vehiculos_ids": get_items(DB_VEHICULOS, [4]),
            "actividad": "Sustitución de tramo dañado en tubería principal",
            "estado": "POR APROBAR", "is_active": True,
            "eq_computo": []
        }
    },
    # 4. Grupo mediano (5 personas, 1 automóvil)
    {
        "titulo": "4. Auditoría general HSEQ (5 personas, 1 automóvil)",
        "payload": {
            "fecha_inicio": "2026-09-10", "fecha_fin": "2026-09-12",
            "empresa_origen": get_single(DB_EMPRESAS, 0),
            "diligenciado_por": get_single(DB_USUARIOS, 6),
            "nivel_de_riesgo": "ALTO", "tipo_personal": "Visitante",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 3),
            "plantas_ids": get_items(DB_PLANTAS, [0, 2, 4]),
            "personas_ids": get_items(DB_PERSONAS, [6, 7, 8, 9, 10]),
            "vehiculos_ids": get_items(DB_VEHICULOS, [16]),
            "actividad": "Auditoría de cumplimiento de normas SST y del sistema contraincendios",
            "estado": "APROBADO", "is_active": True,
            "eq_computo": [{"marca": "Lenovo", "modelo": "ThinkPad", "serie": "SN-AUD1"}]
        }
    },
    # 5. Individual (1 persona, sin vehículo)
    {
        "titulo": "5. Configuración de PLC y automatización (1 persona)",
        "payload": {
            "fecha_inicio": "2026-09-11", "fecha_fin": "2026-09-11",
            "empresa_origen": get_single(DB_EMPRESAS, 2),
            "diligenciado_por": get_single(DB_USUARIOS, 3),
            "nivel_de_riesgo": "BAJO", "tipo_personal": "Contratista",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 1),
            "plantas_ids": get_items(DB_PLANTAS, [2]),
            "personas_ids": get_items(DB_PERSONAS, [20]),
            "vehiculos_ids": [],
            "actividad": "Actualización de firmware en controladores lógicos",
            "estado": "APROBADO", "is_active": True,
            "eq_computo": [{"marca": "HP", "modelo": "ProBook", "serie": "SN-PLC-99"}]
        }
    },
    # 6. Cuadrilla grande (8 personas, 2 vehículos: Volqueta y Grúa)
    {
        "titulo": "6. Obra civil y nivelación de terrenos (8 personas, 2 vehículos)",
        "payload": {
            "fecha_inicio": "2026-09-15", "fecha_fin": "2026-10-15",
            "empresa_origen": get_single(DB_EMPRESAS, 1),
            "diligenciado_por": get_single(DB_USUARIOS, 9),
            "nivel_de_riesgo": "ALTO", "tipo_personal": "Contratista",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 0),
            "plantas_ids": get_items(DB_PLANTAS, [1, 3]),
            "personas_ids": get_items(DB_PERSONAS, [11, 12, 13, 14, 15, 16, 17, 18]),
            "vehiculos_ids": get_items(DB_VEHICULOS, [7, 8]),
            "actividad": "Adecuación de calzada interna y cimentación de parqueaderos",
            "estado": "EN REVISION", "is_active": True,
            "eq_computo": []
        }
    },
    # 7. Pareja (2 personas, 1 camioneta)
    {
        "titulo": "7. Levantamiento topográfico con dron (2 personas, 1 camioneta)",
        "payload": {
            "fecha_inicio": "2026-09-18", "fecha_fin": "2026-09-19",
            "empresa_origen": get_single(DB_EMPRESAS, 2),
            "diligenciado_por": get_single(DB_USUARIOS, 11),
            "nivel_de_riesgo": "BAJO", "tipo_personal": "Contratista",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 4),
            "plantas_ids": get_items(DB_PLANTAS, [2, 5]),
            "personas_ids": get_items(DB_PERSONAS, [10, 14]),
            "vehiculos_ids": get_items(DB_VEHICULOS, [1]),
            "actividad": "Mapeo fotogramétrico de terrenos adyacentes",
            "estado": "ENVIADO", "is_active": True,
            "eq_computo": [{"marca": "Asus", "modelo": "ROG", "serie": "SN-DRON-01"}]
        }
    },
    # 8. Grupo mediano (4 personas, 1 tractocamión)
    {
        "titulo": "8. Limpieza técnica de tanques (4 personas, 1 tractocamión)",
        "payload": {
            "fecha_inicio": "2026-09-20", "fecha_fin": "2026-09-23",
            "empresa_origen": get_single(DB_EMPRESAS, 0),
            "diligenciado_por": get_single(DB_USUARIOS, 13),
            "nivel_de_riesgo": "ALTO", "tipo_personal": "Contratista",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 5),
            "plantas_ids": get_items(DB_PLANTAS, [0]),
            "personas_ids": get_items(DB_PERSONAS, [6, 21, 22, 23]),
            "vehiculos_ids": get_items(DB_VEHICULOS, [9]),
            "actividad": "Drenaje, lavado industrial y neutralización de tanques",
            "estado": "POR APROBAR", "is_active": True,
            "eq_computo": []
        }
    },
    # 9. Individual (1 persona, sin vehículo)
    {
        "titulo": "9. Capacitación de primeros auxilios (1 persona)",
        "payload": {
            "fecha_inicio": "2026-09-25", "fecha_fin": "2026-09-25",
            "empresa_origen": get_single(DB_EMPRESAS, 3),
            "diligenciado_por": get_single(DB_USUARIOS, 14),
            "nivel_de_riesgo": "BAJO", "tipo_personal": "Visitante",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 2),
            "plantas_ids": get_items(DB_PLANTAS, [3]),
            "personas_ids": get_items(DB_PERSONAS, [12]),
            "vehiculos_ids": [],
            "actividad": "Taller teórico-práctico de atención básica a emergencias",
            "estado": "APROBADO", "is_active": True,
            "eq_computo": [{"marca": "Apple", "modelo": "MacBook Air", "serie": "SN-MAC-12"}]
        }
    },
    # 10. Grupo grande (6 personas, 2 vehículos: Grúa y Camioneta)
    {
        "titulo": "10. Montaje estructural de cubierta (6 personas, 2 vehículos)",
        "payload": {
            "fecha_inicio": "2026-10-01", "fecha_fin": "2026-10-10",
            "empresa_origen": get_single(DB_EMPRESAS, 1),
            "diligenciado_por": get_single(DB_USUARIOS, 7),
            "nivel_de_riesgo": "ALTO", "tipo_personal": "Contratista",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 0),
            "plantas_ids": get_items(DB_PLANTAS, [1, 4]),
            "personas_ids": get_items(DB_PERSONAS, [0, 3, 6, 8, 15, 16]),
            "vehiculos_ids": get_items(DB_VEHICULOS, [8, 2]),
            "actividad": "Izaje y fijación de vigas principales en bodega central",
            "estado": "ENVIADO", "is_active": True,
            "eq_computo": []
        }
    },
    # 11. Trío (3 personas, 2 vehículos: Motocicleta y Furgón)
    {
        "titulo": "11. Fumigación y control de plagas (3 personas, 2 vehículos)",
        "payload": {
            "fecha_inicio": "2026-10-05", "fecha_fin": "2026-10-06",
            "empresa_origen": get_single(DB_EMPRESAS, 2),
            "diligenciado_por": get_single(DB_USUARIOS, 2),
            "nivel_de_riesgo": "MEDIO", "tipo_personal": "Contratista",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 3),
            "plantas_ids": get_items(DB_PLANTAS, [0, 1, 2]),
            "personas_ids": get_items(DB_PERSONAS, [17, 18, 19]),
            "vehiculos_ids": get_items(DB_VEHICULOS, [6, 10]),
            "actividad": "Fumigación general de archivos y zonas de depósito",
            "estado": "RECHAZADO", "is_active": False,
            "eq_computo": []
        }
    },
    # 12. Grupo mediano (5 personas, 1 camión)
    {
        "titulo": "12. Instalación de sistema de refrigeración (5 personas, 1 camión)",
        "payload": {
            "fecha_inicio": "2026-10-10", "fecha_fin": "2026-10-18",
            "empresa_origen": get_single(DB_EMPRESAS, 0),
            "diligenciado_por": get_single(DB_USUARIOS, 17),
            "nivel_de_riesgo": "MEDIO", "tipo_personal": "Contratista",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 1),
            "plantas_ids": get_items(DB_PLANTAS, [0, 3]),
            "personas_ids": get_items(DB_PERSONAS, [1, 5, 9, 13, 24]),
            "vehiculos_ids": get_items(DB_VEHICULOS, [5]),
            "actividad": "Montaje de chillers y ductos de aire acondicionado industrial",
            "estado": "ENVIADO", "is_active": True,
            "eq_computo": []
        }
    },
    # 13. Individual (1 persona, sin vehículo)
    {
        "titulo": "13. Revisión contable y financiera de obra (1 persona)",
        "payload": {
            "fecha_inicio": "2026-10-12", "fecha_fin": "2026-10-14",
            "empresa_origen": get_single(DB_EMPRESAS, 3),
            "diligenciado_por": get_single(DB_USUARIOS, 20),
            "nivel_de_riesgo": "BAJO", "tipo_personal": "Visitante",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 4),
            "plantas_ids": get_items(DB_PLANTAS, [3]),
            "personas_ids": get_items(DB_PERSONAS, [24]),
            "vehiculos_ids": [],
            "actividad": "Verificación física de presupuestos e inventario de activos",
            "estado": "APROBADO", "is_active": True,
            "eq_computo": [{"marca": "Dell", "modelo": "Vostro", "serie": "SN-CNT-88"}]
        }
    },
    # 14. Equipo masivo (7 personas, 2 vehículos)
    {
        "titulo": "14. Parada de planta por mantenimiento anual (7 personas, 2 vehículos)",
        "payload": {
            "fecha_inicio": "2026-11-01", "fecha_fin": "2026-11-15",
            "empresa_origen": get_single(DB_EMPRESAS, 0),
            "diligenciado_por": get_single(DB_USUARIOS, 18),
            "nivel_de_riesgo": "ALTO", "tipo_personal": "Contratista",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 0),
            "plantas_ids": get_items(DB_PLANTAS, [0, 1, 2, 3, 4, 5]),
            "personas_ids": get_items(DB_PERSONAS, [0, 1, 5, 6, 11, 19, 21]),
            "vehiculos_ids": get_items(DB_VEHICULOS, [0, 18]),
            "actividad": "Mantenimiento general preventivo y correctivo multiespecialidad",
            "estado": "POR APROBAR", "is_active": True,
            "eq_computo": [{"marca": "HP", "modelo": "ZBook", "serie": "SN-MNT-01"}]
        }
    },
    # 15. Pareja (2 personas, 1 grúa)
    {
        "titulo": "15. Reemplazo de iluminación LED en altura (2 personas, 1 grúa)",
        "payload": {
            "fecha_inicio": "2026-11-16", "fecha_fin": "2026-11-18",
            "empresa_origen": get_single(DB_EMPRESAS, 1),
            "diligenciado_por": get_single(DB_USUARIOS, 5),
            "nivel_de_riesgo": "MEDIO", "tipo_personal": "Contratista",
            "empresa_contratista": get_single(DB_CONTRATISTAS, 5),
            "plantas_ids": get_items(DB_PLANTAS, [1, 2]),
            "personas_ids": get_items(DB_PERSONAS, [2, 17]),
            "vehiculos_ids": get_items(DB_VEHICULOS, [8]),
            "actividad": "Cambio de luminarias de vapor de sodio por campanas LED",
            "estado": "ENVIADO", "is_active": True,
            "eq_computo": []
        }
    }
]


def seed_solicitudes():
    print("=" * 75)
    print("  SEED - CREANDO 15 SOLICITUDES CON PERSONAS Y VEHÍCULOS (POR IDS)")
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
            num_vehiculos = len(payload.get("vehiculos_ids", []))
            creadas += len(ids)
            print(f"  [{i:02d}/15] OK  Solicitudes IDs: {ids} | {num_personas} pers. | {num_vehiculos} veh. | {num_plantas} plant. -> {titulo}")
        else:
            errores += 1
            print(f"  [{i:02d}/15] ERROR - {titulo}: {resultado.get('mensaje')}")

    print("\n" + "=" * 75)
    print(f"  Solicitudes creadas exitosamente: {creadas}")
    print(f"  Errores al insertar             : {errores}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    seed_solicitudes()