from typing import TypedDict, List
from config import settings
from src.loaders import guardar_solicitud_bd

LISTA_SOLICITUDES = []
#========================================================

class equipoComputo(TypedDict):
    marca:str
    modelo:str
    serie:str

class personaIngreso(TypedDict):
    item:str
    ap_nombre: str
    tipo_doc: str
    identificacion:int
    cargo: str

#========================================================

def crear_solicitud(
    
    empresa_orig:str, #Para que empresa va
    contratista: str, #nombre del solicitante
    nivel_de_riesgo: str, 
    
    tipo_de_persona: str,
    
    empresa: str,
    planta_a_visitar:str,
    fechaInicio:str,
    fechaFin: str,
    actividad:str,
    tipo_vehiculo:str,
    placa:str,

    eq_computo:List[equipoComputo],

    personas:List[personaIngreso],

    doc_adjuntos:List[str],


    ) -> dict:
    
    nuevo_id = len(LISTA_SOLICITUDES) + 1

#=====================================================

    nueva_solicitud = {
        "id": nuevo_id,
        "empresa_origen": empresa_orig,
        "diligenciado_por": contratista,
        "nivel_de_riesgo": nivel_de_riesgo,
        "tipo_de_persona": tipo_de_persona,
        "empresa_contratista": empresa,
        "planta_a_visitar": planta_a_visitar,
        "fecha_inicio": fechaInicio,
        "fecha_fin" : fechaFin,
        "actividad": actividad,

        "vehiculo": {
            "tipo": tipo_vehiculo,
            "placa": placa.upper() if placa else "" #upper() para pasar el texto a mayuscula independientemente si se escribe en minuscula
        },

        "eq_computo": eq_computo,
        "personas": personas,
        "doc_adjuntos": doc_adjuntos,
        
        # Estado Inicial del Flujo
        "estado": settings.ESTADO_EN_REVISION,
        
        "aprobaciones": {
            "SST": {"evaluado": False, "aprobado": False, "comentario": ""},
            "GESCO": {"evaluado": False, "aprobado": False, "comentario": ""},
            "SEGURIDAD_CORP": {"evaluado": False, "aprobado": False, "comentario": ""}
        }
    }

    LISTA_SOLICITUDES.append(nueva_solicitud) #El .append() asegura que la información permanezca guardada en la aplicación.
    
    print(f"==================================================")
    print(f"✅ [ÉXITO] Solicitud #{nuevo_id} creada correctamente.")
    print(f"   Destino: {planta_a_visitar} | Contratista: {empresa}")
    print(f"   Personas registradas: {len(personas)} | Equipos: {len(eq_computo)}")
    print(f"==================================================")

    respuesta_bd = guardar_solicitud_bd(nueva_solicitud)    
    
    return respuesta_bd