from src.loaders.emp_contratista_loader import CREATE_empCont_db
from src.transformers.empContr_transformer import TRANSFORM_EMPCONTRATISTA
from src.schemas.emp_contratista_schema import EmpContratistaInput, UpdateEmpContratistainput


def CREATE_emp_contratista(payload: EmpContratistaInput):

    data_raw = payload.model_dump() 

    data_clean = TRANSFORM_EMPCONTRATISTA(data_raw)

    return CREATE_empCont_db(data_clean)
