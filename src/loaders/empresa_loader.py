from database import GET_conexion
from typing import Dict, Any

def GET_empresas_con_plantas_bd() -> Dict[str, Any]:
    """
    Obtiene todas las empresas con sus plantas anidadas.
    Estructura: [{ id, nombre_empresa, plantas: [{ id, nombre }, ...] }, ...]
    """
    try:
        with GET_conexion() as conexion:
            with conexion.cursor() as cursor:
                # Query que joinea empresa con planta
                cursor.execute("""
                    SELECT 
                        e.id AS empresa_id,
                        e.nombre_empresa,
                        e.nit,
                        e.correo,
                        p.id AS planta_id,
                        p.nombre AS planta_nombre
                    FROM empresa e
                    LEFT JOIN planta p ON p.id_empresa = e.id
                    ORDER BY e.id, p.id
                """)
                
                rows = cursor.fetchall()
                
                # Transformar en estructura anidada
                empresas_dict = {}
                
                for row in rows:
                    emp_id = row['empresa_id']
                    
                    # Si no existe la empresa, crearla
                    if emp_id not in empresas_dict:
                        empresas_dict[emp_id] = {
                            'id': emp_id,
                            'nombre': row['nombre_empresa'],
                            'nit': row.get('nit') or '',
                            'correo': row.get('correo') or '',
                            'plantas': []
                        }
                    
                    # Agregar planta si existe
                    if row['planta_id']:
                        empresas_dict[emp_id]['plantas'].append({
                            'id': row['planta_id'],
                            'nombre': row['planta_nombre']
                        })
                
                # Convertir dict a lista
                empresas = list(empresas_dict.values())
                
                print(f"📦 [LOADER] Se recuperaron {len(empresas)} empresas con sus plantas.")
                
                return {
                    "exito": True,
                    "datos": empresas,
                    "mensaje": "Empresas y plantas recuperadas exitosamente."
                }
    
    except Exception as e:
        print(f"❌ [LOADER Error] Error consultando empresas: {e}")
        return {
            "exito": False,
            "datos": [],
            "mensaje": f"Error al consultar la base de datos: {str(e)}"
        }
