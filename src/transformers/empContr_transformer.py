def TRANSFORM_EMPCONTRATISTA(data_raw: dict) -> dict:

    data_clean = {}

    if "nombre" in data_raw and data_raw["nombre"] is not None:
        data_clean["nombre"] = str(data_raw["nombre"]).strip().upper()

    if "observacion" in data_raw and data_raw["observacion"] is not None:
        data_clean["observacion"] = str(data_raw["observacion"]).strip()

    return data_clean   