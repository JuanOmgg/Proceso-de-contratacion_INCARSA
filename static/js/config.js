const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API_BASE_URL = window.location.origin;

const API = {
    base: API_BASE_URL,
    solicitudes: `${API_BASE_URL}/api/v1/solicitudes`,
    empresas: `${API_BASE_URL}/api/v1/empresas`,
    usuarios: `${API_BASE_URL}/api/v1/usuarios`,
    plantas: `${API_BASE_URL}/planta`,
    roles: `${API_BASE_URL}/roles`,
    personas: `${API_BASE_URL}/api/v1/personas`,
    antecedentes: `${API_BASE_URL}/api/v1/antecedentes`,
    seguridad_social: `${API_BASE_URL}/api/v1/seguridad-social`,
    inducciones: `${API_BASE_URL}/api/v1/inducciones`,
    vehiculos: `${API_BASE_URL}/api/v1/vehiculos`,
    dispositivos: `${API_BASE_URL}/api/v1/dispositivos`,
    contratistas: `${API_BASE_URL}/emp_contratista`,
    auth: `${API_BASE_URL}/api/v1/auth`,
    notificaciones: `${API_BASE_URL}/api/v1/notificaciones`,
    correspondencia: `${API_BASE_URL}/api/v1/correspondencia`
};

// ============================================================================
// GESTIÓN CENTRALIZADA DE AUTENTICACIÓN Y TOKEN JWT
// ============================================================================
function syncAuthCookie(token) {
    if (token) {
        document.cookie = "token=" + encodeURIComponent(token) + "; path=/; max-age=604800; SameSite=Lax";
        document.cookie = "incarsa_token=" + encodeURIComponent(token) + "; path=/; max-age=604800; SameSite=Lax";
    }
}

function getAuthToken() {
    let token = sessionStorage.getItem("incarsa_token") || localStorage.getItem("incarsa_token") || null;
    if (!token) {
        try {
            const sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
            if (sesion && sesion.token) {
                token = sesion.token;
            }
        } catch (e) {}
    }
    if (token) {
        syncAuthCookie(token);
    }
    return token;
}

function getAuthSession() {
    try {
        const sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
        if (sesion && sesion.token) {
            syncAuthCookie(sesion.token);
        }
        return sesion;
    } catch (e) {
        return null;
    }
}

function clearAuthSession() {
    try {
        sessionStorage.removeItem("incarsa_token");
        sessionStorage.removeItem("incarsa_session");
        sessionStorage.clear();
        localStorage.removeItem("incarsa_token");
        localStorage.removeItem("incarsa_session");
        document.cookie = "token=; path=/; max-age=0; SameSite=Lax";
        document.cookie = "incarsa_token=; path=/; max-age=0; SameSite=Lax";
        document.cookie = "access_token=; path=/; max-age=0; SameSite=Lax";
    } catch (e) {}
}

function cerrarSesionUsuario() {
    clearAuthSession();
    window.location.replace("/login?logout=1");
}

// Sincronización proactiva al cargar config.js
try {
    const _t = getAuthToken();
    if (_t) syncAuthCookie(_t);
} catch (e) {}

// ============================================================================
// INTERCEPTOR GLOBAL DE FETCH: Inyecta Authorization: Bearer <token>
// ============================================================================
(function () {
    const _fetch = window.fetch;
    window.fetch = async function (resource, init = {}) {
        const token = getAuthToken();
        const urlStr = typeof resource === "string" ? resource : (resource?.url || "");

        // Verificar si es una petición a nuestros endpoints de API
        // Es importante porque evita enviarle el JWT a servicios externos
        const esApiInterna = urlStr.includes("/api/") || 
                             urlStr.includes("/planta") || 
                             urlStr.includes("/roles") || 
                             urlStr.includes("/emp_contratista") || 
                             urlStr.includes("/auth/");

        if (token && esApiInterna) {
            if (resource instanceof Request) {
                const newHeaders = new Headers(resource.headers);
                if (!newHeaders.has("Authorization")) {
                    newHeaders.set("Authorization", `Bearer ${token}`);
                }
                resource = new Request(resource, { headers: newHeaders });
            } else {
                if (!init.headers) {
                    init.headers = {};
                }
                if (init.headers instanceof Headers) {
                    if (!init.headers.has("Authorization")) {
                        init.headers.set("Authorization", `Bearer ${token}`);
                    }
                } else if (Array.isArray(init.headers)) {
                    const hasAuth = init.headers.some(([k]) => k.toLowerCase() === "authorization");
                    if (!hasAuth) {
                        init.headers.push(["Authorization", `Bearer ${token}`]);
                    }
                } else {
                    const hasAuth = Object.keys(init.headers).some(k => k.toLowerCase() === "authorization");
                    if (!hasAuth) {
                        init.headers["Authorization"] = `Bearer ${token}`;
                    }
                }
            }
        }

        const response = await _fetch.apply(this, [resource, init]);

        // Si el backend responde 401 Unauthorized en peticiones autenticadas
        if (response.status === 401 && esApiInterna && !window.location.pathname.includes("/login")) {
            console.warn("🔒 [AUTH] Token inválido o sesión caducada. Redirigiendo a /login...");
            clearAuthSession();
            window.location.replace("/login?expired=1");
        }

        // Si el backend responde 403 Forbidden en peticiones autenticadas
        if (response.status === 403 && esApiInterna) {
            console.warn("⛔ [AUTH] Petición no autorizada o recurso denegado (403):", resource);
        }

        return response;
    };
})();

function formatearFechaHoraEspanol(fechaStr) {
    if (window.Fechas && typeof window.Fechas.formatearFechaHora === 'function') {
        return window.Fechas.formatearFechaHora(fechaStr);
    }
    return fechaStr || '—';
}
window.formatearFechaHoraEspanol = formatearFechaHoraEspanol;
window.formatearFechaHora = formatearFechaHoraEspanol;

// Utilidad para formatear tiempos relativos amigables
function formatearTiempoRelativo(fechaStr) {
    if (window.Fechas && typeof window.Fechas.tiempoRelativo === 'function') {
        return window.Fechas.tiempoRelativo(fechaStr);
    }
    return fechaStr || '';
}
window.formatearTiempoRelativo = formatearTiempoRelativo;

function formatearTextoEnlace(url) {
    if (!url) return '';
    const u = String(url).trim();
    try {
        if (u.startsWith('http://') || u.startsWith('https://')) {
            const parsed = new URL(u);
            const domain = parsed.hostname.replace(/^www\./, '');
            const path = parsed.pathname !== '/' ? parsed.pathname : '';
            return domain + (path.length > 25 ? path.substring(0, 20) + '…' : path);
        }
    } catch (e) {}
    return u;
}
window.formatearTextoEnlace = formatearTextoEnlace;


