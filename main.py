import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.solicitud_route import router as solicitud_router
from src.routes.usuario_route import router as usuario_router

app = FastAPI(
    title="API - Proceso de Contratos",
    description="Servicio web para procesar, agilizar y ordenar solicitudes de ingreso de personas externas.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectamos el router
app.include_router(solicitud_router)
app.include_router(usuario_router)

@app.get("/", tags=["Healthcheck"])
def verificacion_servidor():
    return {
        "estado": "OK",
        "mensaje": "Servidor de Proceso de Contratos operativo.",
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)