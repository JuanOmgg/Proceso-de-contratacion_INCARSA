import os
import uvicorn
from fastapi import FastAPI
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

app = FastAPI(
    title="API - Proceso de Contratos",
    description="Servicio web para procesar, agilizar y ordenar solicitudes de ingreso de personas externas.",
    version="1.0.0",
)

origins = [
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
]

# Crear y pre-generar las subcarpetas estáticas de documentos
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DOCUMENTOS_DIR = os.path.join(UPLOAD_DIR, "documentos")

subcategorias = ["cedulas", "arl", "examenes_medicos", "otros", "general", "vehiculos"]
for sub in subcategorias:
    os.makedirs(os.path.join(DOCUMENTOS_DIR, sub), exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
