def TRANSFORM_PLANTA(planta:dict) -> dict:

     data_clean = {}

     if "nombre" in planta and planta["nombre"] is not None:
        data_clean["nombre"] = str(planta["nombre"]).strip().upper()

     if "id_empresa" in planta and planta["id_empresa"] is not None:
        data_clean["id_empresa"] = int(planta["id_empresa"])


     return data_clean
