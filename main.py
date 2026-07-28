from src.flujo_estado import crear_solicitud

if __name__ == "__main__":
    
    # 1. Creamos personas de prueba (usando ap_nombre en minúscula)
    personas_prueba = [
        {
            "item": "1",
            "ap_nombre": "Carlos Mendoza",
            "tipo_doc": "CC",
            "identificacion": 1012345678,
            "cargo": "Supervisora de Obra"
        },
        {
            "item": "2",
            "ap_nombre": "Ana María Gómez",
            "tipo_doc": "CC",
            "identificacion": 1098765432,
            "cargo": "Técnico Electricista"
        }
    ]
    
    # 2. Creamos equipos de prueba
    equipos_prueba = [
        {
            "marca": "Lenovo",
            "modelo": "ThinkPad E14",
            "serie": "SN-987654321"
        }
    ]

    print("🚀 [INICIO] Ejecutando prueba de inserción en MySQL...\n")
    
    # 3. Llamamos a la función principal
    resultado = crear_solicitud(
        empresa_orig="INCARSA",
        contratista="Juan Pérez",
        nivel_de_riesgo="Alto",
        tipo_de_persona="Contratista",
        empresa="Soluciones Industriales SAS",
        planta_a_visitar="Planta Central",
        fechaInicio="2026-08-01",
        fechaFin="26-08-24",
        actividad="Mantenimiento preventivo en caldera principal",
        tipo_vehiculo="Camioneta",
        placa="ABC-123",
        eq_computo=equipos_prueba,
        personas=personas_prueba,
        doc_adjuntos=["arl.pdf", "pasado_judicial.pdf"]
    )

    print("\n📩 [RESPUESTA FINAL DEL SISTEMA]:")
    print(resultado)