import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from fastapi.responses import JSONResponse
import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.routes.solicitud_route import router as solicitud_router
from src.routes.usuario_route import router as usuario_router
from src.routes.emContr_route import router as emp_contratista_router
from src.routes.planta_route import router as planta_router
from src.routes.roles_route import router as roles_router
from src.routes.personas_route import router as personas_router
from src.routes.vehiculo_router import router as vehiculo_router
from src.routes.empresa_route import router as empresa_router
from src.routes.antecedentes_route import router as antecedentes_router
from src.routes.auth_router import router as auth_router
from src.routes.notificacion_route import router as notificacion_router
from src.routes.superadmin_router import router as superadmin_router
from src.loaders.superadmin_loader import GET_mantenimiento_status
from src.utils.security import decode_access_token

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
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de modo mantenimiento (Error 503)
@app.middleware("http")
async def modo_mantenimiento_middleware(request: Request, call_next):
    mantenimiento = GET_mantenimiento_status()
    if mantenimiento and mantenimiento.get("activo"):
        path = request.url.path
        rutas_permitidas = [
            "/static",
            "/uploads",
            "/favicon.ico",
            "/login",
            "/auth",
            "/api/v1/auth",
            "/superadmin",
            "/api/v1/superadmin",
            "/docs",
            "/openapi.json"
        ]
        
        # Permitir rutas estáticas, login y panel administrativo de SuperAdmin
        if any(path == r or path.startswith(r + "/") or path.startswith(r + "?") for r in rutas_permitidas):
            return await call_next(request)

        # Si el usuario es SUPERADMIN mediante token Bearer o cookie, permitir acceso
        auth_header = request.headers.get("Authorization") or ""
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        elif "token" in request.cookies:
            token = request.cookies.get("token")

        if token:
            payload = decode_access_token(token)
            if payload and payload.get("rol") == "SUPERADMIN":
                return await call_next(request)

        # Retornar vista 503 o JSON 503
        if "text/html" in request.headers.get("Accept", ""):
            return templates.TemplateResponse(
                name="errors/error-503.html",
                request=request,
                status_code=503,
                context={
                    "mensaje": mantenimiento.get("mensaje"),
                    "tiempo": mantenimiento.get("tiempo")
                }
            )
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Sistema en mantenimiento",
                "mensaje": mantenimiento.get("mensaje"),
                "tiempo": mantenimiento.get("tiempo"),
                "status_code": 503
            }
        )

    return await call_next(request)

app.include_router(solicitud_router)
app.include_router(usuario_router, prefix="/api/v1")
app.include_router(emp_contratista_router)
app.include_router(planta_router)
app.include_router(roles_router)
app.include_router(personas_router, prefix="/api/v1")
app.include_router(vehiculo_router)
app.include_router(empresa_router)
app.include_router(antecedentes_router, prefix="/api/v1")
app.include_router(auth_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(notificacion_router, prefix="/api/v1")
app.include_router(superadmin_router)

@app.get("/", tags=["Verificador de servidor"])

def verificacion_servidor():
    return {
        "estado": "OK",
        "mensaje": "Servidor de Proceso de Contratos operativo.",
        "docs": "/docs",
        "uploads": "/uploads",
    }

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(BASE_DIR, "static", "img", "icono.jpg"))

templates = Jinja2Templates(directory="templates")



@app.get("/dashboard")
async def get_dashboard(request: Request):
    return templates.TemplateResponse(name="dashboard.html", request=request)

@app.get("/login")
async def get_login(request: Request):
    return templates.TemplateResponse(name="login.html", request=request)

@app.get("/splash-loading")
@app.get("/cargando")
async def get_splash_loading(request: Request):
    return templates.TemplateResponse(name="splash-loading.html", request=request)

@app.get("/antecedentes")
async def get_antecedentes(request: Request):
    return templates.TemplateResponse(name="antecedentes.html", request=request)

@app.get("/procesamiento")
async def get_procesamiento(request: Request):
    return templates.TemplateResponse(name="procesamiento.html", request=request)

@app.get("/solicitudes")
async def get_solicitudes(request: Request):
    return templates.TemplateResponse(name="solicitudes-listado.html", request=request)

@app.get("/usuarios")
async def get_usuarios(request: Request):
    return templates.TemplateResponse(name="usuarios-listado.html", request=request)

@app.get("/personas")
async def get_personas(request: Request):
    return templates.TemplateResponse(name="personas-listado.html", request=request)

@app.get("/usuarios/nuevo")
@app.get("/usuarios/nueva")
@app.get("/formulario-usuarios")
@app.get("/usuario-formulario.html")
async def get_formulario_usuarios(request: Request):
    return templates.TemplateResponse(name="usuario-formulario.html", request=request)

@app.get("/usuarios/editar/{identificador}")
async def get_editar_usuario(request: Request, identificador: str):
    return templates.TemplateResponse(
        name="usuario-formulario.html",
        request=request,
        context={"usuario_identificador": identificador}
    )

@app.get("/solicitudes/nueva")
@app.get("/formulario-solicitudes")
async def get_formulario_solicitudes(request: Request):
    return templates.TemplateResponse(name="solicitudes-formulario.html", request=request)

@app.get("/solicitudes/editar/{codigo}")
async def get_editar_solicitud(request: Request, codigo: str):
    return templates.TemplateResponse(name="solicitudes-formulario.html", request=request, context={"codigo_solicitud": codigo})

@app.get("/solicitudes/revision/{codigo}")
@app.get("/revision-solicitud")
@app.get("/revision-solicitud.html")
async def get_revision_solicitud(request: Request, codigo: str = ""):
    return templates.TemplateResponse(name="revision-solicitud.html", request=request, context={"codigo_solicitud": codigo})

# Manejo de errores
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if "text/html" in request.headers.get("Accept", ""):
        if exc.status_code == 404:
            try:
                return templates.TemplateResponse(
                    name="errors/error-404.html",
                    request=request,
                    status_code=404
                )
            except Exception:
                pass
        elif exc.status_code == 503:
            try:
                mantenimiento = GET_mantenimiento_status()
                return templates.TemplateResponse(
                    name="errors/error-503.html",
                    request=request,
                    status_code=503,
                    context={
                        "mensaje": mantenimiento.get("mensaje") if mantenimiento else exc.detail,
                        "tiempo": mantenimiento.get("tiempo") if mantenimiento else None
                    }
                )
            except Exception:
                pass
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=False)
