import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.routes.solicitud_route import router as solicitud_router
from src.routes.usuario_route import router as usuario_router
from src.routes.emContr_route import router as emp_contratista_router
from src.routes.planta_route import router as planta_router
from src.routes.roles_route import router as roles_router
from src.routes.personas_route import router as personas_router
from src.routes.vehiculo_router import router as vehiculo_router
from src.routes.empresa_route import router as empresa_router
from src.routes.antecedentes_route import router as antecedentes_router

app = FastAPI(
    title="API - Proceso de Contratos",
    description="Servicio web para procesar, agilizar y ordenar solicitudes de ingreso de personas externas.",
    version="1.0.0",
)

origins = [
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
]

# Configuración y preparación de carpetas de subida
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.abspath(os.path.join(BASE_DIR, "uploads"))
DOCUMENTOS_DIR = os.path.join(UPLOAD_DIR, "documentos")

subcategorias = ["cedulas", "arl", "examenes_medicos", "otros", "general", "vehiculos"]
for sub in subcategorias:
    os.makedirs(os.path.join(DOCUMENTOS_DIR, sub), exist_ok=True)

# Servidor inteligente de archivos para /uploads
# Resuelve tanto rutas directas (/uploads/documentos/general/xxx.jpg)
# como búsquedas directas por nombre (/uploads/xxx.jpg)
@app.get("/uploads/{archivo_path:path}", tags=["Archivos"])
async def servir_archivo_upload(archivo_path: str):
    # 1. Protección contra Directory Traversal
    ruta_candidata = os.path.abspath(os.path.join(UPLOAD_DIR, archivo_path))
    if not ruta_candidata.startswith(UPLOAD_DIR):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    # 2. Si la ruta existe de forma exacta
    if os.path.isfile(ruta_candidata):
        return FileResponse(ruta_candidata)

    # 3. Si solo se envió el nombre del archivo, buscarlo en las subcarpetas
    nombre_archivo = os.path.basename(archivo_path)
    for root, _, files in os.walk(UPLOAD_DIR):
        if nombre_archivo in files:
            ruta_encontrada = os.path.join(root, nombre_archivo)
            return FileResponse(ruta_encontrada)

    raise HTTPException(status_code=404, detail="El documento solicitado no fue encontrado en el servidor.")

# Conectamos los routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(solicitud_router)
app.include_router(usuario_router)
app.include_router(emp_contratista_router)
app.include_router(planta_router)
app.include_router(roles_router)
app.include_router(personas_router)
app.include_router(vehiculo_router)
app.include_router(empresa_router)
app.include_router(antecedentes_router)

@app.get("/", tags=["Verificador de servidor"])
def verificacion_servidor():
    return {
        "estado": "OK",
        "mensaje": "Servidor de Proceso de Contratos operativo.",
        "docs": "/docs",
        "uploads": "/uploads",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
