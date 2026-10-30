from fastapi import Response
from typing import Optional
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
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
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
from src.routes.inducciones_route import router as inducciones_router
from src.routes.formulario_gesco_route import router as formulario_gesco_router
from src.routes.pregunta_route import router as pregunta_router
from src.routes.seguridad_social_route import router as seguridad_social_router
from src.routes.auth_router import router as auth_router
from src.routes.notificacion_route import router as notificacion_router
from src.routes.superadmin_router import router as superadmin_router
from src.routes.correspondencia_route import router as correspondencia_router
from src.routes.dispositivo_router import router as dispositivo_router
from src.routes.estadisticas_route import router as estadisticas_router
from src.routes.parqueo_route import router as parqueo_router
from src.loaders.superadmin_loader import GET_mantenimiento_status
from src.loaders.formulario_gesco_loader import GET_formulario_gesco_por_id_db, GET_formularios_gesco_db
from src.utils.security import decode_access_token
from urllib.parse import unquote

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    from src.utils.broadcaster import notification_broadcaster
    from database import verificar_conexion
    try:
        loop = asyncio.get_running_loop()
        notification_broadcaster.set_loop(loop)
        print("🚀 [STARTUP] NotificationBroadcaster conectado al loop asíncrono para SSE en tiempo real.")
    except Exception as e:
        print(f"⚠️ Aviso inicializando loop para notificaciones: {e}")

    try:
        if verificar_conexion(max_reintentos=2, espera=1.0):
            print("🚀 [STARTUP] Conexión a la base de datos MySQL verificada y lista.")
        else:
            print("⚠️ [STARTUP] La base de datos aún no responde; las peticiones reintentarán la conexión automáticamente.")
    except Exception as e:
        print(f"⚠️ [STARTUP] Aviso verificando base de datos: {e}")
    yield

app = FastAPI(
    title="API - Proceso de Contratos",
    description="Servicio web para procesar, agilizar y ordenar solicitudes de ingreso de personas externas.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuración y preparación de carpetas de subida
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.abspath(os.path.join(BASE_DIR, "uploads"))
DOCUMENTOS_DIR = os.path.join(UPLOAD_DIR, "documentos")

subcategorias = ["cedulas", "arl", "examenes_medicos", "otros", "general", "vehiculos", "notificaciones"]
for sub in subcategorias:
    os.makedirs(os.path.join(DOCUMENTOS_DIR, sub), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "gesco"), exist_ok=True)

# Cabeceras estándar de caché y seguridad para archivos adjuntos
CACHE_HEADERS_UPLOADS = {
    "Cache-Control": "public, max-age=86400",  # Cache de 24 horas en cliente
    "X-Content-Type-Options": "nosniff",
}

# Subcarpetas frecuentes de almacenamiento para búsqueda directa O(1)
SUBCARPETAS_UPLOADS_DIRECTAS = [
    DOCUMENTOS_DIR,
    os.path.join(DOCUMENTOS_DIR, "cedulas"),
    os.path.join(DOCUMENTOS_DIR, "arl"),
    os.path.join(DOCUMENTOS_DIR, "eps"),
    os.path.join(DOCUMENTOS_DIR, "gesco_sst"),
    os.path.join(DOCUMENTOS_DIR, "examenes_medicos"),
    os.path.join(DOCUMENTOS_DIR, "vehiculos"),
    os.path.join(DOCUMENTOS_DIR, "notificaciones"),
    os.path.join(DOCUMENTOS_DIR, "general"),
    os.path.join(DOCUMENTOS_DIR, "otros"),
    os.path.join(UPLOAD_DIR, "gesco"),
    os.path.join(UPLOAD_DIR, "gesco", "evidencias"),
    os.path.join(UPLOAD_DIR, "vehiculos"),
    os.path.join(UPLOAD_DIR, "sistema"),
    os.path.join(UPLOAD_DIR, "sistemas"),
    UPLOAD_DIR,
]

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
        return FileResponse(ruta_candidata, headers=CACHE_HEADERS_UPLOADS)

    # 3. Comprobación directa O(1) en subcarpetas frecuentes antes de fallback
    nombre_archivo = os.path.basename(archivo_path)
    for carpeta in SUBCARPETAS_UPLOADS_DIRECTAS:
        candidato = os.path.join(carpeta, nombre_archivo)
        if os.path.isfile(candidato):
            return FileResponse(candidato, headers=CACHE_HEADERS_UPLOADS)

    # 4. Fallback secundario de tolerancia a fallos si se encuentra en otra subcarpeta
    for root, _, files in os.walk(UPLOAD_DIR):
        if nombre_archivo in files:
            ruta_encontrada = os.path.join(root, nombre_archivo)
            return FileResponse(ruta_encontrada, headers=CACHE_HEADERS_UPLOADS)

    raise HTTPException(status_code=404, detail="El documento solicitado no fue encontrado en el servidor.")


@app.get("/api/sistema/formato-herramientas", tags=["Archivos"])
async def descargar_formato_herramientas():
    """Descarga el formato oficial de relación de herramientas, materiales y equipos (FR-SCR-042) para control en portería."""
    carpetas = [
        os.path.join(UPLOAD_DIR, "sistema"),
        os.path.join(UPLOAD_DIR, "sistemas")
    ]
    for carpeta in carpetas:
        if os.path.isdir(carpeta):
            archivos = [f for f in os.listdir(carpeta) if not f.startswith(".")]
            if archivos:
                herramientas = [f for f in archivos if "HERRAMIENTA" in f.upper() or "FR_SCR" in f.upper()]
                elegido = herramientas[0] if herramientas else archivos[0]
                ruta = os.path.join(carpeta, elegido)
                return FileResponse(
                    path=ruta,
                    filename=elegido,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{elegido}"'}
                )
    raise HTTPException(status_code=404, detail="El formato de herramientas no fue encontrado en el servidor.")

# ==============================================================================
# CONFIGURACIÓN SEGURA DE CORS (Restricción de Orígenes y Credenciales)
# ==============================================================================
raw_origins = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]

# Orígenes estándar para entorno local y desarrollo
default_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
for orig in default_origins:
    if orig not in allowed_origins:
        allowed_origins.append(orig)

frontend_url = os.getenv("FRONTEND_URL", "").strip()
if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # Permite únicamente localhost, 127.0.0.1 y redes de área local privadas (192.168.x.x, 10.x.x.x)
    # Bloquea orígenes externos maliciosos o no autorizados con credenciales
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compresión Gzip para transferir CSS, JS, HTML y JSON con hasta un 80% menos de peso
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Cabeceras de Seguridad HTTP Globales (Protección OWASP)
@app.middleware("http")
async def agregar_cabeceras_seguridad(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response

MODULO_NOMBRES = {
    "dashboard": "Dashboard y Estadísticas",
    "solicitudes": "Listado de Solicitudes",
    "nueva_solicitud": "Nueva Solicitud",
    "usuarios": "Listado de Usuarios",
    "nuevo_usuario": "Formulario de Usuarios",
    "plantas": "Gestión de Plantas y Zonas",
    "contratistas": "Empresas Contratistas",
    "vehiculos": "Vehículos y Maquinaria",
    "personas": "Directorio de Personas",
    "procesamiento": "Procesamiento de Solicitudes",
    "antecedentes": "Verificación de Antecedentes",
    "seguridad_social": "Seguridad Social",
    "inducciones": "Gestión de Inducciones",
    "estadisticas": "Estadísticas y Reportes",
    "formulario_temporal": "Solicitudes para Terceros",
    "revision_solicitud": "Revisión y Aprobación de Solicitudes",
    "dispositivos": "Consulta de Dispositivos",
    "formularios_gesco": "Formularios GESCO",
    "parqueos": "Control de Parqueos Nocturnos"
}

def obtener_modulo_de_ruta(path: str) -> Optional[str]:
    """Determina a qué módulo del sistema pertenece una ruta de URL."""
    p = path.rstrip("/")
    if not p:
        return None
    if p == "/dashboard":
        return "dashboard"
    if p in ("/solicitudes/nueva", "/formulario-solicitudes"):
        return "nueva_solicitud"
    if p.startswith("/solicitudes/revision") or p == "/revision-solicitud":
        return "revision_solicitud"
    if p == "/solicitudes" or p.startswith("/api/v1/solicitudes") or p.startswith("/api/solicitudes"):
        return "solicitudes"
    if p in ("/usuarios/nuevo", "/usuarios/nueva", "/formulario-usuarios", "/usuario-formulario.html"):
        return "nuevo_usuario"
    if p == "/usuarios" or p.startswith("/api/v1/usuarios"):
        return "usuarios"
    if p.startswith("/planta") or p.startswith("/api/plantas") or p.startswith("/api/v1/plantas"):
        return "plantas"
    if p.startswith("/emp_contratista") or p.startswith("/api/contratistas") or p.startswith("/api/v1/contratistas"):
        return "contratistas"
    if p.startswith("/vehiculo") or p.startswith("/api/vehiculos") or p.startswith("/api/v1/vehiculos"):
        return "vehiculos"
    if p.startswith("/api/v1/dispositivos") or p.startswith("/api/dispositivos") or p == "/dispositivos":
        return "dispositivos"
    if p.startswith("/personas") or p.startswith("/api/v1/personas"):
        return "personas"
    if p.startswith("/procesamiento") or p.startswith("/api/v1/procesamiento"):
        return "procesamiento"
    if p.startswith("/antecedentes") or p.startswith("/api/v1/antecedentes"):
        return "antecedentes"
    if p.startswith("/seguridad-social") or p.startswith("/seguridadsocial") or p.startswith("/api/v1/seguridad-social"):
        return "seguridad_social"
    if p.startswith("/inducciones") or p.startswith("/api/v1/inducciones"):
        return "inducciones"
    if p.startswith("/estadisticas") or p.startswith("/api/v1/estadisticas"):
        return "estadisticas"
    if p.startswith("/formulario-temporal") or p.startswith("/api/v1/tokens-formulario") or p.startswith("/api/tokens"):
        return "formulario_temporal"
    if p.startswith("/formularios-gesco") or p.startswith("/api/v1/formularios-gesco") or p.startswith("/api/v1/preguntas") or p.startswith("/preguntas"):
        return "formularios_gesco"
    if p.startswith("/parqueos") or p.startswith("/api/v1/parqueos") or p.startswith("/api/parqueos"):
        return "parqueos"
    return None

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
            "/api/v1/sistema/mantenimiento",
            "/api/v1/notificaciones/stream",
            "/docs",
            "/openapi.json",
            "/formulario-parqueo",
            "/reporte-parqueo"
        ]
        
        # Permitir rutas estáticas, login, estado de mantenimiento y panel administrativo de SuperAdmin
        if any(path == r or path.startswith(r + "/") or path.startswith(r + "?") for r in rutas_permitidas):
            return await call_next(request)

        # Si el usuario es SUPERADMIN mediante token Bearer o cookie, permitir acceso irrestricto
        auth_header = request.headers.get("Authorization") or ""
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        elif "token" in request.cookies:
            token = request.cookies.get("token")
        elif "incarsa_token" in request.cookies:
            token = request.cookies.get("incarsa_token")
        elif "access_token" in request.cookies:
            token = request.cookies.get("access_token")

        if token:
            import urllib.parse
            token_clean = urllib.parse.unquote(str(token)).strip().strip('"').strip("'")
            if token_clean.startswith("Bearer "):
                token_clean = token_clean.split(" ")[1]
            payload = decode_access_token(token_clean)
            if payload:
                user_rol = str(payload.get("rol", "")).strip().upper()
                if user_rol in ("SUPERADMIN", "SUPER ADMIN", "SUPER_ADMIN") or payload.get("id_rol") == 1:
                    return await call_next(request)

        tipo = mantenimiento.get("tipo", "general")
        modulos_mantenimiento = mantenimiento.get("modulos") or []
        modulo_afectado = None
        nombre_modulo_afectado = None

        if tipo == "modulos":
            modulo_solicitado = obtener_modulo_de_ruta(path)
            # Si la ruta pertenece a un módulo y dicho módulo está en mantenimiento, bloquear
            if modulo_solicitado and modulo_solicitado in modulos_mantenimiento:
                modulo_afectado = modulo_solicitado
                nombre_modulo_afectado = MODULO_NOMBRES.get(modulo_solicitado, modulo_solicitado.replace("_", " ").title())
            else:
                # El módulo solicitado no está en mantenimiento; continuar normalmente
                return await call_next(request)

        # Retornar vista 503 o JSON 503
        mensaje = mantenimiento.get("mensaje")
        tiempo = mantenimiento.get("tiempo")
        temporizador_fin = mantenimiento.get("temporizador_fin")
        temporizador_minutos = mantenimiento.get("temporizador_minutos")

        if "text/html" in request.headers.get("Accept", ""):
            return templates.TemplateResponse(
                name="errors/error-503.html",
                request=request,
                status_code=503,
                context={
                    "mensaje": mensaje,
                    "tiempo": tiempo,
                    "tipo_mantenimiento": tipo,
                    "modulo_afectado": modulo_afectado,
                    "nombre_modulo_afectado": nombre_modulo_afectado,
                    "temporizador_fin": temporizador_fin,
                    "temporizador_minutos": temporizador_minutos
                }
            )
        return JSONResponse(
            status_code=503,
            content={
                "detail": f"Módulo en mantenimiento: {nombre_modulo_afectado}" if modulo_afectado else "Sistema en mantenimiento",
                "tipo_mantenimiento": tipo,
                "modulo_afectado": modulo_afectado,
                "nombre_modulo_afectado": nombre_modulo_afectado,
                "mensaje": mensaje,
                "tiempo": tiempo,
                "temporizador_fin": temporizador_fin,
                "status_code": 503
            }
        )

    return await call_next(request)

# ============================================================================
# MIDDLEWARE DE SEGURIDAD HTTP (OWASP Best Practices)
# ============================================================================
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """
    Inyecta cabeceras HTTP de seguridad recomendadas por OWASP en todas las respuestas
    del servidor para mitigar vectores de ataque web comunes.
    """
    response = await call_next(request)
    
    # 1. Protección contra ataques de confusión de tipo MIME (MIME-Sniffing).
    # Impide que los navegadores intenten "adivinar" e interpretar archivos subidos (ej. en /uploads)
    # como scripts ejecutables (.js o .html) si el servidor los declaró como imágenes o binarios.
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # 2. Protección contra Clickjacking (Secuestro de clic).
    # Evita que sitios de terceros incrusten esta aplicación dentro de un <iframe> invisible
    # para engañar a los usuarios y robar clics o credenciales. 'SAMEORIGIN' permite que 
    # la propia aplicación incruste vistas internas (como previsualizadores de documentos propios).
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    
    # 3. Filtro XSS reflejado para navegadores heredados.
    # Fuerza al navegador a bloquear completamente la renderización de la página si detecta
    # un ataque de Cross-Site Scripting (XSS) reflejado en la solicitud.
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # 4. Control de privacidad de Referrer (fuga de URLs internas).
    # Al navegar hacia sitios externos, no envía rutas completas ni parámetros de consulta
    # (protegiendo tokens, IDs o datos privados en la URL), enviando únicamente el dominio de origen.
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # 5. Restricción de permisos y APIs sensibles del dispositivo (Permissions-Policy).
    # Deshabilita explícitamente el acceso por defecto a cámara, micrófono y geolocalización,
    # impidiendo que librerías de terceros o scripts maliciosos puedan acceder al hardware del cliente.
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    
    return response

# ============================================================================
# MIDDLEWARE DE POLÍTICAS DE CACHÉ HTTP (Cache-Control)
# ============================================================================
@app.middleware("http")
async def cache_control_middleware(request: Request, call_next):
    """
    Gestiona las directivas Cache-Control para optimizar la velocidad de navegación.
    - Los recursos estáticos (CSS, JS, iconos) se guardan en la memoria local del navegador.
    - Los datos dinámicos de la API y las vistas HTML no se cachean para garantizar datos en vivo.
    """
    response = await call_next(request)
    
    # Si la ruta ya definió una política específica (ej. SSE 'no-cache, no-transform'), respetarla
    if "Cache-Control" in response.headers:
        return response

    path = request.url.path

    # 1. Archivos estáticos versionados (/static: css, js, fuentes, imágenes de interfaz)
    # Cacheo público de 24 horas (86,400s) con stale-while-revalidate para respuesta inmediata.
    # Al cambiar el parámetro de versión en HTML (?v=3.4), el navegador descarga el nuevo automáticamente.
    if path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=3600"

    # 2. Ícono de la pestaña del navegador (favicon.ico)
    # Cacheo de 7 días (604,800s) ya que rara vez cambia.
    elif path == "/favicon.ico":
        response.headers["Cache-Control"] = "public, max-age=604800"

    # 3. Documentos y adjuntos subidos por usuarios (/uploads)
    # Cacheo 'private' de 1 hora para que los proxys públicos no almacenen documentos sensibles.
    elif path.startswith("/uploads/"):
        response.headers["Cache-Control"] = "private, max-age=3600, must-revalidate"

    # 4. Endpoints dinámicos de la API (/api/...)
    # Nunca se cachean en disco o proxies para asegurar que el usuario vea cambios en tiempo real.
    elif path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"

    # 5. Páginas HTML dinámicas servidas por Jinja2
    # Deben revalidarse para verificar autenticación y estado de sesión.
    elif "text/html" in response.headers.get("content-type", ""):
        response.headers["Cache-Control"] = "no-cache, private, must-revalidate"

    return response

app.include_router(solicitud_router)
app.include_router(usuario_router, prefix="/api/v1")
app.include_router(emp_contratista_router)
app.include_router(planta_router)
app.include_router(roles_router)
app.include_router(personas_router, prefix="/api/v1")
app.include_router(vehiculo_router)
app.include_router(empresa_router)
app.include_router(antecedentes_router, prefix="/api/v1")
app.include_router(inducciones_router, prefix="/api/v1")
app.include_router(formulario_gesco_router, prefix="/api/v1")
app.include_router(pregunta_router, prefix="/api/v1")
app.include_router(seguridad_social_router, prefix="/api/v1")
app.include_router(seguridad_social_router)
app.include_router(auth_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(notificacion_router, prefix="/api/v1")
app.include_router(superadmin_router)
app.include_router(correspondencia_router, prefix="/api/v1")
app.include_router(correspondencia_router)
app.include_router(dispositivo_router, prefix="/api/v1")
app.include_router(dispositivo_router)
app.include_router(estadisticas_router, prefix="/api/v1")
app.include_router(estadisticas_router)
app.include_router(parqueo_router, prefix="/api/v1")
app.include_router(parqueo_router)

@app.get("/", tags=["Verificador de servidor"])

def verificacion_servidor():
    return {
        "estado": "OK",
        "mensaje": "Servidor de Proceso de Contratos operativo.",
        "docs": "/docs",
        "uploads": "/uploads",
    }

class CachedStaticFiles(StaticFiles):
    def file_response(self, *args, **kwargs):
        resp = super().file_response(*args, **kwargs)
        # Cache de 1 día para assets estáticos con versión (?v=...)
        resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp

app.mount("/static", CachedStaticFiles(directory="static"), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    icon_path = os.path.join(BASE_DIR, "static", "img", "icono.png")
    if os.path.exists(icon_path):
        return FileResponse(icon_path, media_type="image/png", headers={"Cache-Control": "public, max-age=604800"})
    return Response(status_code=204)

templates = Jinja2Templates(directory="templates")



@app.get("/dashboard")
async def get_dashboard(request: Request):
    return templates.TemplateResponse(name="dashboard.html", request=request)

@app.get("/login")
async def get_login(request: Request):
    response = templates.TemplateResponse(name="login.html", request=request)
    if request.query_params.get("logout") or request.query_params.get("expired"):
        response.delete_cookie(key="token", path="/")
        response.delete_cookie(key="incarsa_token", path="/")
        response.delete_cookie(key="access_token", path="/")
    return response

@app.get("/splash-loading")
@app.get("/cargando")
async def get_splash_loading(request: Request):
    return templates.TemplateResponse(name="splash-loading.html", request=request)

@app.get("/antecedentes")
async def get_antecedentes(request: Request):
    return templates.TemplateResponse(name="antecedentes.html", request=request)

@app.get("/seguridad-social")
@app.get("/seguridadsocial")
async def get_seguridad_social(request: Request):
    return templates.TemplateResponse(name="seguridadsocial.html", request=request)

@app.get("/inducciones")
async def get_inducciones(request: Request):
    return templates.TemplateResponse(name="inducciones.html", request=request)

@app.get("/estadisticas")
async def get_estadisticas(request: Request):
    return templates.TemplateResponse(name="Estadisticas.html", request=request)


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

@app.get("/formularios-gesco")
@app.get("/gesco/formularios")
@app.get("/formulariosGESCO.html")
async def get_formularios_gesco(request: Request):
    return templates.TemplateResponse(name="formulariosGESCO.html", request=request)

@app.get("/formularios-gesco/nuevo")
@app.get("/formulario-gesco/nuevo")
async def get_nuevo_formulario_gesco(request: Request):
    return templates.TemplateResponse(name="formulario-gesco.html", request=request)

@app.get("/formularios-gesco/editar/{id_form}")
async def get_editar_formulario_gesco(request: Request, id_form: int):
    return templates.TemplateResponse(
        name="formulario-gesco.html",
        request=request,
        context={"formulario_id": id_form}
    )

@app.get("/evaluacion-induccion")
@app.get("/evaluacion-induccion/")
async def get_evaluacion_induccion_default(request: Request):
    """
    Ruta raíz de inducción: redirige al formulario activo por defecto utilizando su nombre/slug.
    """
    res = GET_formularios_gesco_db(solo_activos=True)
    if res.get("exito") and res.get("datos"):
        primer = res["datos"][0]
        slug = primer.get("slug") or str(primer.get("id"))
        query_str = f"?{request.url.query}" if request.url.query else ""
        return RedirectResponse(
            url=f"/evaluacion-induccion/{slug}{query_str}",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
    return RedirectResponse(url="/formularios-gesco", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

@app.get("/induccion/evaluacion/{identificador:path}")
@app.get("/evaluacion-induccion/{identificador:path}")
@app.get("/evaluacion/{identificador:path}")
async def get_evaluacion_induccion_page(request: Request, identificador: str):
    """
    Entrega la vista del cuestionario público de inducción GESCO.
    Si se accede con ID numérico (ej: /evaluacion-induccion/3), redirige con 307
    al slug amigable con el nombre del formulario (ej: /evaluacion-induccion/formulario-test-preguntas-back).
    Permite acceso por ID, nombre exacto o slug.
    """
    ident_clean = unquote(str(identificador or "").strip())

    res = GET_formulario_gesco_por_id_db(ident_clean)
    if res.get("exito") and res.get("datos"):
        form_data = res["datos"]
        form_id = form_data.get("id")
        form_nombre = form_data.get("nombre") or ""
        form_slug = form_data.get("slug") or str(form_id)

        # Si el usuario o enlace ingresó con ID numérico pero el formulario tiene slug/nombre,
        # redirigir para que en la barra del navegador aparezca el nombre en vez del número
        if ident_clean.isdigit() and form_slug and ident_clean != form_slug:
            query_str = f"?{request.url.query}" if request.url.query else ""
            return RedirectResponse(
                url=f"/evaluacion-induccion/{form_slug}{query_str}",
                status_code=status.HTTP_307_TEMPORARY_REDIRECT
            )

        return templates.TemplateResponse(
            name="evaluacion-induccion.html",
            request=request,
            context={
                "formulario_id": form_id,
                "formulario_nombre": form_nombre,
                "formulario_slug": form_slug
            }
        )

    # Si es numérico pero no existe registro en BD, renderizar fallback
    if ident_clean.isdigit():
        return templates.TemplateResponse(
            name="evaluacion-induccion.html",
            request=request,
            context={
                "formulario_id": int(ident_clean),
                "formulario_nombre": f"Formulario #{ident_clean}",
                "formulario_slug": ident_clean
            }
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Formulario de inducción '{ident_clean}' no encontrado."
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


@app.get("/verificar/{codigo}")
@app.get("/verificar")
@app.get("/porteria/verificar/{codigo}")
@app.get("/porteria/verificar")
async def get_verificar_solicitud(request: Request, codigo: str = ""):
    return templates.TemplateResponse(
        name="verificar-solicitud.html",
        request=request,
        context={"codigo_solicitud": codigo.strip().upper()}
    )


@app.get("/autorizacion-datos/{token}")
@app.get("/autorizacion-datos")
async def get_autorizacion_datos_page(request: Request, token: str = ""):
    from src.loaders.empresa_loader import GET_empresas_con_plantas_bd
    res_emp = GET_empresas_con_plantas_bd()
    empresas = res_emp.get("datos", []) if res_emp.get("exito") else []
    return templates.TemplateResponse(
        name="autorizacion-datos.html",
        request=request,
        context={
            "token": token.strip(),
            "empresas_db": empresas
        }
    )


@app.get("/autorizacion-datos/{token}/certificado-pdf")
async def get_autorizacion_datos_certificado_redirect(token: str):
    tok = token.strip() if token else "preview"
    return RedirectResponse(
        url=f"/api/v1/solicitudes/publico/autorizacion-datos/{tok}/certificado-pdf",
        status_code=302
    )


@app.get("/formulario-temporal/{token}")
@app.get("/formulario-temporal")
async def get_formulario_temporal_page(request: Request, token: str = ""):
    tok = token.strip()
    if not tok:
        try:
            from database import GET_conexion
            with GET_conexion() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT token FROM tokens_formulario_temporal 
                        WHERE usado = 0 AND revocado = 0 AND fecha_expiracion > NOW() 
                        ORDER BY id DESC LIMIT 1
                    """)
                    row = cur.fetchone()
                    if row and row.get("token"):
                        tok = row["token"]
        except Exception as e:
            print(f"⚠️ [FORMULARIO TEMPORAL] Error buscando token activo por defecto: {e}")

    return templates.TemplateResponse(
        name="formulario-temporal.html",
        request=request,
        context={"token": tok}
    )

@app.get("/formulario-correspondencia")
async def get_formulario_correspondencia_publico(request: Request):
    return templates.TemplateResponse(name="correspondencia-form.html", request=request)

@app.get("/correspondencias")
async def get_correspondencia(request: Request):
    return templates.TemplateResponse(name="correspondencia-listado.html", request=request)

@app.get("/parqueos")
async def get_parqueos(request: Request):
    return templates.TemplateResponse(name="parqueos.html", request=request)

@app.get("/formulario-parqueo")
@app.get("/reporte-parqueo")
async def get_formulario_parqueo_publico(request: Request):
    return templates.TemplateResponse(name="parqueo-form.html", request=request)

@app.get("/403")
@app.get("/error-403")
async def get_error_403(request: Request):
    return templates.TemplateResponse(
        name="errors/error-403.html",
        request=request,
        status_code=403
    )

@app.get("/500")
@app.get("/error-500")
async def get_error_500(request: Request):
    return templates.TemplateResponse(
        name="errors/error-500.html",
        request=request,
        status_code=500
    )

# Manejo centralizado de excepciones HTTP de Starlette / FastAPI
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if "text/html" in request.headers.get("Accept", ""):
        if exc.status_code == 403:
            try:
                return templates.TemplateResponse(
                    name="errors/error-403.html",
                    request=request,
                    status_code=403,
                    context={"mensaje": exc.detail if exc.detail else "Tu rol actual no tiene permisos para ver esta sección."}
                )
            except Exception:
                pass
        elif exc.status_code == 404:
            try:
                return templates.TemplateResponse(
                    name="errors/error-404.html",
                    request=request,
                    status_code=404
                )
            except Exception:
                pass
        elif exc.status_code == 500:
            try:
                return templates.TemplateResponse(
                    name="errors/error-500.html",
                    request=request,
                    status_code=500
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

# Manejo centralizado de excepciones no controladas de Python (Error 500 inesperado)
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"🔥 [ERROR 500 INTERNO] en {request.method} {request.url.path}: {exc}")
    traceback.print_exc()

    if "text/html" in request.headers.get("Accept", ""):
        try:
            return templates.TemplateResponse(
                name="errors/error-500.html",
                request=request,
                status_code=500
            )
        except Exception:
            pass

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Ocurrió un error interno en el servidor. El equipo técnico ha sido notificado.",
            "status_code": 500
        },
    )

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload_env = os.getenv("RELOAD", "True").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host=host, port=port, reload=reload_env)
