import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.schemas.personas_schema import PersonInput
from src.services.personas import CREATE_person

PERSONAS_SEED = [
    # ── Bloque 1: perfil técnico/operativo ──────────────────────────────
    {
        "nombre": "Juan",        "apellido": "Perez Torres",
        "tipo_doc": "CC",        "identificacion": "10000001",
        "cargo": "Ingeniero Residente",  "observacion": "Lider de cuadrilla",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_juan_perez.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_juan_perez.pdf"},
            {"tipo_doc": "CEDULA",        "nombre_archivo": "cedula_juan_perez.pdf"},
        ],
    },
    {
        "nombre": "Maria",       "apellido": "Lopez Salcedo",
        "tipo_doc": "CC",        "identificacion": "10000002",
        "cargo": "Tecnica Electrica",    "observacion": "",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_maria_lopez.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_maria_lopez.pdf"},
        ],
    },
    {
        "nombre": "Carlos",      "apellido": "Gomez Rios",
        "tipo_doc": "CC",        "identificacion": "10000003",
        "cargo": "Auxiliar Operativo",   "observacion": "Maneja equipos pesados",
        "documentos_ids": [
            {"tipo_doc": "ARL",     "nombre_archivo": "arl_carlos_gomez.pdf"},
            {"tipo_doc": "LICENCIA","nombre_archivo": "licencia_carlos_gomez.pdf"},
        ],
    },
    {
        "nombre": "Luisa",       "apellido": "Martinez Vega",
        "tipo_doc": "CC",        "identificacion": "10000004",
        "cargo": "SST",                  "observacion": "Responsable de seguridad en obra",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_luisa_martinez.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_luisa_martinez.pdf"},
            {"tipo_doc": "CERTIFICADO",   "nombre_archivo": "cert_alturas_luisa.pdf"},
        ],
    },
    {
        "nombre": "Andres",      "apellido": "Torres Benitez",
        "tipo_doc": "CC",        "identificacion": "10000005",
        "cargo": "Supervisor",           "observacion": "",
        "documentos_ids": [
            {"tipo_doc": "ARL", "nombre_archivo": "arl_andres_torres.pdf"},
        ],
    },
    # ── Bloque 2: 20 personas adicionales ────────────────────────────────
    {
        "nombre": "Sofia",       "apellido": "Ramirez Cruz",
        "tipo_doc": "CC",        "identificacion": "10000006",
        "cargo": "Electromecánica",      "observacion": "Especialista en motores trifásicos",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_sofia_ramirez.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_sofia_ramirez.pdf"},
        ],
    },
    {
        "nombre": "Miguel",      "apellido": "Hernandez Mora",
        "tipo_doc": "CC",        "identificacion": "10000007",
        "cargo": "Soldador Certificado", "observacion": "Certificado en soldadura 6G",
        "documentos_ids": [
            {"tipo_doc": "ARL",         "nombre_archivo": "arl_miguel_hernandez.pdf"},
            {"tipo_doc": "CERTIFICADO", "nombre_archivo": "cert_soldadura_miguel.pdf"},
            {"tipo_doc": "LICENCIA",    "nombre_archivo": "licencia_trabajos_caliente.pdf"},
        ],
    },
    {
        "nombre": "Valentina",   "apellido": "Lopez Castillo",
        "tipo_doc": "CC",        "identificacion": "10000008",
        "cargo": "Coordinadora HSE",     "observacion": "Auditora HSEQ nivel 2",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_valentina_lopez.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_valentina_lopez.pdf"},
            {"tipo_doc": "CERTIFICADO",   "nombre_archivo": "cert_hse_valentina.pdf"},
        ],
    },
    {
        "nombre": "Felipe",      "apellido": "Jimenez Rueda",
        "tipo_doc": "CC",        "identificacion": "10000009",
        "cargo": "Operador de Grúa",     "observacion": "Licencia de conduccion cat E",
        "documentos_ids": [
            {"tipo_doc": "ARL",     "nombre_archivo": "arl_felipe_jimenez.pdf"},
            {"tipo_doc": "LICENCIA","nombre_archivo": "licencia_grua_felipe.pdf"},
        ],
    },
    {
        "nombre": "Natalia",     "apellido": "Castro Fuentes",
        "tipo_doc": "CC",        "identificacion": "10000010",
        "cargo": "Instrumentista",       "observacion": "",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_natalia_castro.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_natalia_castro.pdf"},
        ],
    },
    {
        "nombre": "Camila",      "apellido": "Reyes Ospina",
        "tipo_doc": "CC",        "identificacion": "10000011",
        "cargo": "Arquitecta de Proyectos", "observacion": "Especialista en FEED y EPCM",
        "documentos_ids": [
            {"tipo_doc": "ARL",         "nombre_archivo": "arl_camila_reyes.pdf"},
            {"tipo_doc": "CERTIFICADO", "nombre_archivo": "cert_pmp_camila.pdf"},
        ],
    },
    {
        "nombre": "Sergio",      "apellido": "Guerrero Navas",
        "tipo_doc": "CC",        "identificacion": "10000012",
        "cargo": "Plomero Industrial",   "observacion": "Trabaja con tuberias de alta presion",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_sergio_guerrero.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_sergio_guerrero.pdf"},
        ],
    },
    {
        "nombre": "Paola",       "apellido": "Medina Acosta",
        "tipo_doc": "CC",        "identificacion": "10000013",
        "cargo": "Enfermera Ocupacional","observacion": "Atiende primeros auxilios en campo",
        "documentos_ids": [
            {"tipo_doc": "ARL",         "nombre_archivo": "arl_paola_medina.pdf"},
            {"tipo_doc": "CERTIFICADO", "nombre_archivo": "cert_primeros_auxilios_paola.pdf"},
        ],
    },
    {
        "nombre": "Ricardo",     "apellido": "Perez Cardenas",
        "tipo_doc": "CC",        "identificacion": "10000014",
        "cargo": "Tecnico en Refrigeración", "observacion": "",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_ricardo_perez.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_ricardo_perez.pdf"},
        ],
    },
    {
        "nombre": "Mariana",     "apellido": "Diaz Quintero",
        "tipo_doc": "CC",        "identificacion": "10000015",
        "cargo": "Topógrafa",            "observacion": "Levantamientos con dron y GPS",
        "documentos_ids": [
            {"tipo_doc": "ARL",         "nombre_archivo": "arl_mariana_diaz.pdf"},
            {"tipo_doc": "CERTIFICADO", "nombre_archivo": "cert_topografia_mariana.pdf"},
        ],
    },
    {
        "nombre": "Pablo",       "apellido": "Rojas Montoya",
        "tipo_doc": "CC",        "identificacion": "10000016",
        "cargo": "Albañil Especializado","observacion": "",
        "documentos_ids": [
            {"tipo_doc": "ARL", "nombre_archivo": "arl_pablo_rojas.pdf"},
        ],
    },
    {
        "nombre": "Alejandra",   "apellido": "Florez Valencia",
        "tipo_doc": "CC",        "identificacion": "10000017",
        "cargo": "Coordinadora de Obra", "observacion": "Residente de obra etapa civil",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_alejandra_florez.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_alejandra_florez.pdf"},
            {"tipo_doc": "CERTIFICADO",   "nombre_archivo": "cert_alturas_alejandra.pdf"},
        ],
    },
    {
        "nombre": "Esteban",     "apellido": "Aguilar Bermudez",
        "tipo_doc": "CC",        "identificacion": "10000018",
        "cargo": "Electricista de Baja Tension", "observacion": "",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_esteban_aguilar.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_esteban_aguilar.pdf"},
        ],
    },
    {
        "nombre": "Luisa",       "apellido": "Suarez Pinto",
        "tipo_doc": "CC",        "identificacion": "10000019",
        "cargo": "Operaria de Planta",   "observacion": "Turno nocturno",
        "documentos_ids": [
            {"tipo_doc": "ARL", "nombre_archivo": "arl_luisa_suarez.pdf"},
        ],
    },
    {
        "nombre": "Mateo",       "apellido": "Cano Vargas",
        "tipo_doc": "CC",        "identificacion": "10000020",
        "cargo": "Mecanico de Turbo",    "observacion": "Soporte en turbinas de gas",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_mateo_cano.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_mateo_cano.pdf"},
            {"tipo_doc": "CERTIFICADO",   "nombre_archivo": "cert_turbinas_mateo.pdf"},
        ],
    },
    {
        "nombre": "Daniela",     "apellido": "Vargas Ibañez",
        "tipo_doc": "CC",        "identificacion": "10000021",
        "cargo": "Tecnica en Automatización", "observacion": "PLC Siemens y Allen Bradley",
        "documentos_ids": [
            {"tipo_doc": "ARL",         "nombre_archivo": "arl_daniela_vargas.pdf"},
            {"tipo_doc": "CERTIFICADO", "nombre_archivo": "cert_plc_daniela.pdf"},
        ],
    },
    {
        "nombre": "Hector",      "apellido": "Mora Salinas",
        "tipo_doc": "CC",        "identificacion": "10000022",
        "cargo": "Conductor Pesado",     "observacion": "Licencia C3 vigente",
        "documentos_ids": [
            {"tipo_doc": "ARL",     "nombre_archivo": "arl_hector_mora.pdf"},
            {"tipo_doc": "LICENCIA","nombre_archivo": "licencia_c3_hector.pdf"},
        ],
    },
    {
        "nombre": "Isabela",     "apellido": "Gutierrez Ossa",
        "tipo_doc": "CC",        "identificacion": "10000023",
        "cargo": "Química Industrial",   "observacion": "Manejo de reactivos peligrosos",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_isabela_gutierrez.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_isabela_gutierrez.pdf"},
            {"tipo_doc": "CERTIFICADO",   "nombre_archivo": "cert_quimica_isabela.pdf"},
        ],
    },
    {
        "nombre": "Tomas",       "apellido": "Escobar Hurtado",
        "tipo_doc": "CC",        "identificacion": "10000024",
        "cargo": "Pintor Industrial",    "observacion": "Aplicacion de recubrimientos epoxicos",
        "documentos_ids": [
            {"tipo_doc": "ARL",           "nombre_archivo": "arl_tomas_escobar.pdf"},
            {"tipo_doc": "EXAMEN_MEDICO", "nombre_archivo": "examen_tomas_escobar.pdf"},
        ],
    },
    {
        "nombre": "Gabriela",    "apellido": "Soto Palacios",
        "tipo_doc": "CC",        "identificacion": "10000025",
        "cargo": "Contadora de Costos",  "observacion": "Seguimiento de presupuesto de obra",
        "documentos_ids": [
            {"tipo_doc": "ARL",         "nombre_archivo": "arl_gabriela_soto.pdf"},
            {"tipo_doc": "CERTIFICADO", "nombre_archivo": "cert_contadora_gabriela.pdf"},
        ],
    },
]


def seed_personas():
    print("=" * 70)
    print("  SEED - CREANDO 25 PERSONAS EN LA BASE DE DATOS")
    print("=" * 70)
    print("  NOTA: Estos registros SE QUEDAN en la BD.")
    print(f"  Total a insertar : {len(PERSONAS_SEED)} personas")
    print("=" * 70 + "\n")

    ids_creados = []
    errores = []

    for i, p in enumerate(PERSONAS_SEED, start=1):
        try:
            payload = PersonInput(**p)
            resultado = CREATE_person(payload)

            if resultado.get("exito"):
                persona_id = resultado.get("persona")
                ids_creados.append(persona_id)
                num_docs = len(p.get("documentos_ids", []))
                print(f"  [{i:02d}/{len(PERSONAS_SEED)}] OK  ID #{persona_id:>3} - {p['nombre']} {p['apellido']}"
                      f" ({p['cargo']}) - {num_docs} doc(s)")
            else:
                msg = resultado.get("mensaje", "Error desconocido")
                errores.append((i, p["nombre"], msg))
                print(f"  [{i:02d}/{len(PERSONAS_SEED)}] ERROR - {p['nombre']} {p['apellido']}: {msg}")

        except Exception as e:
            errores.append((i, p.get("nombre", "?"), str(e)))
            print(f"  [{i:02d}/{len(PERSONAS_SEED)}] EXCEPCION - {p.get('nombre', '?')}: {e}")

    print(f"\n  Personas creadas : {len(ids_creados)} / {len(PERSONAS_SEED)}")
    print(f"  Errores          : {len(errores)}")
    print(f"  IDs generados    : {ids_creados}")
    print("\n  Usa estos IDs en PERSONAS_VALIDAS del test_multi_solicitud.py")
    print("=" * 70 + "\n")

    return ids_creados


if __name__ == "__main__":
    seed_personas()
