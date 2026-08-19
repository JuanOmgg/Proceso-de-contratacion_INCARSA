import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.schemas.vehiculo_schema import VehiculoInput
from src.services.vehiculo import CREATE_vehiculo

VEHICULOS_SEED = [
    # ── 1. Camionetas y Vehículos Operativos 4x4 ─────────────────────────────
    {
        "tipo": "Camioneta",
        "placa": "HIL-101",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_hil101.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_hil101.pdf"},
            {"tipo_doc": "tarjeta_propiedad", "nom_documento": "tarjeta_hil101.pdf"},
        ],
    },
    {
        "tipo": "Camioneta",
        "placa": "DIM-202",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_dim202.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_dim202.pdf"},
        ],
    },
    {
        "tipo": "Camioneta",
        "placa": "FRN-303",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_frn303.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_frn303.pdf"},
            {"tipo_doc": "poliza_contractual", "nom_documento": "poliza_frn303.pdf"},
        ],
    },
    {
        "tipo": "Camioneta",
        "placa": "AMR-404",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_amr404.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_amr404.pdf"},
        ],
    },
    # ── 2. Camiones de Carga y Furgones ─────────────────────────────────────
    {
        "tipo": "Camión",
        "placa": "NPR-505",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_npr505.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_npr505.pdf"},
            {"tipo_doc": "tarjeta_propiedad", "nom_documento": "tarjeta_npr505.pdf"},
        ],
    },
    {
        "tipo": "Camión",
        "placa": "FVR-606",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_fvr606.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_fvr606.pdf"},
        ],
    },
    {
        "tipo": "Furgón",
        "placa": "FUR-707",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_fur707.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_fur707.pdf"},
        ],
    },
    {
        "tipo": "Volqueta",
        "placa": "VOL-808",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_vol808.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_vol808.pdf"},
            {"tipo_doc": "inspeccion_preoperacional", "nom_documento": "preop_vol808.pdf"},
        ],
    },
    # ── 3. Maquinaria y Equipos Especiales ──────────────────────────────────
    {
        "tipo": "Grúa",
        "placa": "GRU-909",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_gru909.pdf"},
            {"tipo_doc": "certificacion_brazo", "nom_documento": "cert_gru909.pdf"},
        ],
    },
    {
        "tipo": "Tractocamión",
        "placa": "TRA-111",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_tra111.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_tra111.pdf"},
        ],
    },
    # ── 4. Motocicletas (Formato Colombiano Actual 3L-2N-1L) ────────────────
    {
        "tipo": "Motocicleta",
        "placa": "XTZ-12A",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_xtz12a.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_xtz12a.pdf"},
        ],
    },
    {
        "tipo": "Motocicleta",
        "placa": "PUL-34B",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_pul34b.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_pul34b.pdf"},
        ],
    },
    {
        "tipo": "Motocicleta",
        "placa": "BWS-56C",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_bws56c.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_bws56c.pdf"},
        ],
    },
    {
        "tipo": "Motocicleta",
        "placa": "GIX-78D",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_gix78d.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_gix78d.pdf"},
        ],
    },
    # ── 5. Remolques y Semirremolques (R/S + 5 dígitos) ──────────────────────
    {
        "tipo": "Remolque",
        "placa": "R-10203",
        "documentos": [
            {"tipo_doc": "tarjeta_registro", "nom_documento": "registro_r10203.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_r10203.pdf"},
        ],
    },
    {
        "tipo": "Semirremolque",
        "placa": "S-40506",
        "documentos": [
            {"tipo_doc": "tarjeta_registro", "nom_documento": "registro_s40506.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_s40506.pdf"},
        ],
    },
    # ── 6. Automóviles y Sedanes ─────────────────────────────────────────────
    {
        "tipo": "Automóvil",
        "placa": "LOG-212",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_log212.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_log212.pdf"},
        ],
    },
    {
        "tipo": "Automóvil",
        "placa": "ONX-313",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_onx313.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_onx313.pdf"},
        ],
    },
    {
        "tipo": "Van / Microbús",
        "placa": "VAN-414",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_van414.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_van414.pdf"},
            {"tipo_doc": "poliza_extracontractual", "nom_documento": "poliza_van414.pdf"},
        ],
    },
    {
        "tipo": "Camioneta",
        "placa": "COL-515",
        "documentos": [
            {"tipo_doc": "soat", "nom_documento": "soat_col515.pdf"},
            {"tipo_doc": "tecnomecanica", "nom_documento": "tecno_col515.pdf"},
            {"tipo_doc": "tarjeta_propiedad", "nom_documento": "tarjeta_col515.pdf"},
        ],
    },
]


def ejecutar_seed_vehiculos():
    print("=" * 65)
    print("🚛 INICIANDO SEED DE 20 VEHÍCULOS CON DOCUMENTOS ANIDADOS")
    print("=" * 65)

    creados = 0
    existentes = 0
    errores = 0

    for i, v_data in enumerate(VEHICULOS_SEED, start=1):
        try:
            payload = VehiculoInput(**v_data)
            resultado = CREATE_vehiculo(payload)

            if resultado.get("exito"):
                datos = resultado.get("data", {})
                v_id = datos.get("id")
                placa = datos.get("placa")
                tipo = datos.get("tipo")
                num_docs = len(datos.get("documentos", []))
                print(f"  [{i:02d}/20] ✅ Vehículo #{v_id} [{tipo}] Placa: {placa} | Documentos: {num_docs}")
                creados += 1
            elif resultado.get("duplicado") or "ya se encuentra registrado" in resultado.get("mensaje", ""):
                datos = resultado.get("data", {})
                v_id = datos.get("id")
                placa = v_data.get("placa")
                tipo = v_data.get("tipo")
                print(f"  [{i:02d}/20] ℹ️ Vehículo ya registrado en BD [ID #{v_id}] Placa: {placa} [{tipo}]")
                existentes += 1
            else:
                print(f"  [{i:02d}/20] ⚠️ No creado: {resultado.get('mensaje')}")
                errores += 1

        except Exception as e:
            print(f"  [{i:02d}/20] ❌ Error inesperado: {e}")
            errores += 1

    print("\n" + "=" * 65)
    print(f"🎉 SEED FINALIZADO: {creados} creados | {existentes} ya en BD | {errores} errores")
    print("=" * 65)


if __name__ == "__main__":
    ejecutar_seed_vehiculos()
