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
    correspondencia: `${API_BASE_URL}/api/v1/correspondencia`,
    formularios_gesco: `${API_BASE_URL}/api/v1/formularios-gesco`,
    preguntas: `${API_BASE_URL}/api/v1/preguntas`
};
window.API = API;

// ============================================================================
// GESTIÓN CENTRALIZADA DE AUTENTICACIÓN Y TOKEN JWT (OPTIMIZADO CON CACHÉ EN MEMORIA)
// ============================================================================
let _cachedAuthSession = null;
let _cachedAuthToken = null;
let _lastSyncedToken = null;

function syncAuthCookie(token) {
    // Las cookies de autenticación HttpOnly son gestionadas exclusivamente por el backend para prevenir XSS
    return;
}

function getAuthToken() {
    if (_cachedAuthToken) return _cachedAuthToken;
    let token = sessionStorage.getItem("incarsa_token") || localStorage.getItem("incarsa_token") || null;
    if (!token) {
        try {
            const sesion = getAuthSession();
            if (sesion && sesion.token) {
                token = sesion.token;
            }
        } catch (e) {}
    }
    if (token) {
        _cachedAuthToken = token;
        syncAuthCookie(token);
    }
    return token;
}

function getAuthSession() {
    if (_cachedAuthSession !== null) {
        return _cachedAuthSession;
    }
    try {
        const sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
        _cachedAuthSession = sesion;
        if (sesion && sesion.token) {
            _cachedAuthToken = sesion.token;
            syncAuthCookie(sesion.token);
        }
        return sesion;
    } catch (e) {
        _cachedAuthSession = null;
        return null;
    }
}

function invalidateAuthCache() {
    _cachedAuthSession = null;
    _cachedAuthToken = null;
    _lastSyncedToken = null;
}
window.invalidateAuthCache = invalidateAuthCache;

function clearAuthSession() {
    invalidateAuthCache();
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

async function cerrarSesionUsuario() {
    try {
        await window.fetch("/api/v1/auth/logout", { method: "POST" });
    } catch (e) {}
    clearAuthSession();
    window.location.replace("/login?logout=1");
}

async function syncAuthSessionWithServer() {
    try {
        const token = getAuthToken();
        if (!token) return null;
        const res = await window.fetch("/api/v1/auth/me", {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
            const data = await res.json();
            const u = data.usuario || data;
            if (u && u.id) {
                let sesionActual = null;
                try {
                    sesionActual = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
                } catch(e) {}
                if (!sesionActual) sesionActual = {};

                let cambio = false;

                const nuevasPlantasIds = Array.isArray(u.plantas_ids) ? u.plantas_ids.map(Number) : [];
                const viejasPlantasIds = (sesionActual.plantas_ids || []).map(Number);
                const a1 = [...nuevasPlantasIds].sort().join(",");
                const a2 = [...viejasPlantasIds].sort().join(",");
                if (a1 !== a2) {
                    sesionActual.plantas_ids = nuevasPlantasIds;
                    cambio = true;
                }

                if (Array.isArray(u.plantas)) {
                    sesionActual.plantas = u.plantas;
                    cambio = true;
                }

                if (u.id_rol && Number(sesionActual.id_rol) !== Number(u.id_rol)) {
                    sesionActual.id_rol = u.id_rol;
                    sesionActual.rol = u.nombre_rol || sesionActual.rol;
                    cambio = true;
                }

                if (cambio) {
                    sessionStorage.setItem("incarsa_session", JSON.stringify(sesionActual));
                    if (localStorage.getItem("incarsa_session")) {
                        localStorage.setItem("incarsa_session", JSON.stringify(sesionActual));
                    }
                    invalidateAuthCache();
                    window.dispatchEvent(new CustomEvent("sesion-actualizada-en-caliente", { detail: sesionActual }));
                }
                return sesionActual;
            }
        }
    } catch (e) {
        console.warn("Aviso al sincronizar sesión con servidor:", e);
    }
    return getAuthSession();
}
window.syncAuthSessionWithServer = syncAuthSessionWithServer;

// Sincronización proactiva al cargar config.js
try {
    const _t = getAuthToken();
    if (_t) {
        syncAuthCookie(_t);
        // Sincronizar permisos y plantas en segundo plano sin bloquear renderizado
        setTimeout(() => syncAuthSessionWithServer(), 150);
    }
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

// ============================================================================
// HELPERS Y NORMALIZACIÓN GLOBAL DE SOLICITUDES (CENTRALIZADO)
// ============================================================================
function estadoClass(estado) {
    const map = {
        "ENVIADO": "status-enviado",
        "PRE-ENVIADO": "status-revision",
        "PREENVIADO": "status-revision",
        "EN REVISIÓN": "status-revision",
        "EN REVISION": "status-revision",
        "DEVUELTO PARA CORRECCIÓN": "status-devuelto",
        "DEVUELTO PARA CORRECCION": "status-devuelto",
        "DEVUELTO": "status-devuelto",
        "POR APROBAR": "status-aprobar",
        "APROBADO": "status-aprobado",
        "PRE-APROBADO": "status-aprobado",
        "PREAPROBADO": "status-aprobado",
        "RECHAZADO": "status-rechazado"
    };
    return map[(estado || "").toUpperCase()] || "status-enviado";
}
window.estadoClass = estadoClass;

function formatearFechaCorta(fechaStr) {
    if (!fechaStr || fechaStr === "—" || fechaStr === "-") return "—";
    if (window.Fechas && typeof window.Fechas.formatearSoloFecha === 'function') {
        return window.Fechas.formatearSoloFecha(fechaStr);
    }
    return fechaStr;
}
window.formatearFechaCorta = formatearFechaCorta;

function generarCodigoAlfanumerico(id) {
    if (!id) return "INC-X9B1";
    if (typeof id === 'string' && id.startsWith("SOL-") && id.length > 10) {
        return id;
    }
    const str = String(id);
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash |= 0;
    }
    const chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ";
    let code = "";
    let n = Math.abs(hash);
    for (let i = 0; i < 4; i++) {
        code += chars[n % chars.length];
        n = Math.floor(n / chars.length) + (i + 1) * 11;
    }
    return `RAD-${code}${String(id).padStart(2, '0')}`;
}
window.generarCodigoAlfanumerico = generarCodigoAlfanumerico;

function esSolicitudActiva(s) {
    if (!s) return false;
    if (s.is_active === 0 || s.is_active === false || s.is_active === "0" || s.is_active === "false") {
        return false;
    }
    return true;
}
window.esSolicitudActiva = esSolicitudActiva;

let _hoyCacheTimestamp = 0;
let _hoyCacheValue = 0;

function getHoyTimestamp() {
    const now = Date.now();
    if (_hoyCacheValue && (now - _hoyCacheTimestamp < 60000)) {
        return _hoyCacheValue;
    }
    const h = new Date();
    h.setHours(0, 0, 0, 0);
    _hoyCacheTimestamp = now;
    _hoyCacheValue = h.getTime();
    return _hoyCacheValue;
}

function esInactivaVencida(s) {
    if (!s) return false;
    const esInactiva = (s.is_active === 0 || s.is_active === false || s.is_active === "0");
    if (!esInactiva) return false;

    const fFinRaw = s.fecha_salida || s.fecha_fin || s.fechaSalida;
    if (!fFinRaw) return false;

    let fechaFinDate = null;
    if (fFinRaw instanceof Date) {
        fechaFinDate = new Date(fFinRaw.getTime());
    } else if (typeof fFinRaw === "string" && fFinRaw.trim()) {
        const limpia = fFinRaw.trim().split("T")[0].split(" ")[0].replace(/\//g, "-");
        const partes = limpia.split("-");
        if (partes.length === 3) {
            if (partes[0].length === 4) {
                fechaFinDate = new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
            } else if (partes[2].length === 4) {
                fechaFinDate = new Date(Number(partes[2]), Number(partes[1]) - 1, Number(partes[0]));
            }
        }
    }

    if (!fechaFinDate || isNaN(fechaFinDate.getTime())) return false;

    fechaFinDate.setHours(0, 0, 0, 0);
    return fechaFinDate.getTime() < getHoyTimestamp();
}
window.esInactivaVencida = esInactivaVencida;

function normalizarSolicitud(s) {
    if (!s) return {};

    let cadenaPlanta = "—";
    if (Array.isArray(s.plantas) && s.plantas.length > 0) {
        cadenaPlanta = s.plantas.map(p => (typeof p === "object" ? (p.nombre || p.nombre_planta || p.planta) : p)).filter(Boolean).join(", ");
    } else if (typeof s.planta === "string" && s.planta.trim() !== "") {
        cadenaPlanta = s.planta;
    } else if (typeof s.plantas === "string" && s.plantas.trim() !== "") {
        cadenaPlanta = s.plantas;
    }

    let observacionesGuardadas = {};
    if (window._cachedObservacionesLocal !== undefined && window._cachedObservacionesLocal !== null) {
        observacionesGuardadas = window._cachedObservacionesLocal;
    } else {
        try {
            observacionesGuardadas = JSON.parse(localStorage.getItem("incarsa_observaciones_solicitudes") || "{}");
            window._cachedObservacionesLocal = observacionesGuardadas;
        } catch (e) {
            observacionesGuardadas = {};
        }
    }

    const observacionVal = s.observacion || s.observaciones || observacionesGuardadas[s.id] || "";
    const codigoVal = s.codigo || s.codigo_radicado || generarCodigoAlfanumerico(s.id);

    let listaComputos = [];
    if (typeof s.computos === 'string' && s.computos.trim() !== '') {
        listaComputos = s.computos.split('###').map(c => {
            const [id, marca, modelo, serie] = c.split('|||');
            return { id, marca, modelo, serie };
        });
    } else if (Array.isArray(s.computos)) {
        listaComputos = s.computos;
    }

    let listaVehiculos = [];
    if (typeof s.vehiculos === 'string' && s.vehiculos.trim() !== '') {
        listaVehiculos = s.vehiculos.split('###').map(v => {
            const partes = v.split('|||');
            const id = partes[0];
            const tipo = partes[1] || "Vehículo";
            const placa = partes[2] || "—";
            const licencia_doc = partes[3] || "";
            const aut = partes[4];
            const mot = partes[5] || "";
            return {
                id,
                tipo,
                placa,
                conductor: partes[6] || "",
                licencia_doc,
                licencia: licencia_doc,
                autorizado: aut !== '0' && aut !== 0 && aut !== false && aut !== 'false',
                motivo: mot
            };
        });
    } else if (Array.isArray(s.vehiculos) || Array.isArray(s.vehiculo)) {
        const rawV = Array.isArray(s.vehiculos) ? s.vehiculos : s.vehiculo;
        listaVehiculos = rawV.map(v => ({
            id: v.id || v.id_vehiculo,
            tipo: v.tipo || "Vehículo",
            placa: v.placa || "—",
            conductor: v.conductor || "",
            licencia_doc: v.licencia_doc || v.licencia || "",
            licencia: v.licencia_doc || v.licencia || "",
            autorizado: v.autorizado !== '0' && v.autorizado !== 0 && v.autorizado !== false && v.autorizado !== 'false',
            motivo: v.motivo || v.motivo_rechazo || ""
        }));
    }

    try {
        const storageKeyVeh = `incarsa_solicitud_${s.id}_vehiculos`;
        const localVeh = JSON.parse(localStorage.getItem(storageKeyVeh) || "null");
        if (Array.isArray(localVeh) && localVeh.length > 0) {
            listaVehiculos = listaVehiculos.map(lv => {
                const match = localVeh.find(v => String(v.id) === String(lv.id) || (v.placa && v.placa === lv.placa));
                if (match) {
                    return {
                        ...lv,
                        autorizado: match.autorizado !== '0' && match.autorizado !== 0 && match.autorizado !== false && match.autorizado !== 'false',
                        motivo: match.motivo_rechazo || match.motivo || lv.motivo || ""
                    };
                }
                return lv;
            });
        }
    } catch (e) {}

    let listaRevisiones = [];
    if (Array.isArray(s.revisiones)) {
        listaRevisiones = s.revisiones;
    } else {
        try {
            const storageKeyRev = `incarsa_revisiones_${s.id}`;
            const guardado = JSON.parse(localStorage.getItem(storageKeyRev) || "null");
            if (guardado) {
                if (Array.isArray(guardado.historial)) {
                    listaRevisiones = guardado.historial;
                } else if (Array.isArray(guardado)) {
                    listaRevisiones = guardado;
                }
            }
        } catch (e) {}
    }

    let listaPersonas = [];
    if (typeof s.personas === 'string' && s.personas.trim() !== '') {
        if (s.personas.includes('|||') || s.personas.includes('###')) {
            listaPersonas = s.personas.split('###').map(p => {
                const parts = p.split('|||');
                const id = parts[0];
                const ap_nombre = parts[1];
                const tipo_doc = parts[2];
                const identificacion = parts[3];
                const cargo = parts[4];
                const autorizado = parts[5];
                const motivo = parts[6] || "";
                const estado_datos = parts[7] || "PENDIENTE";
                return {
                    id,
                    ap_nombre,
                    nombre: ap_nombre,
                    tipo_doc,
                    identificacion,
                    cargo,
                    autorizado: autorizado !== '0' && autorizado !== 0 && autorizado !== false && autorizado !== 'false',
                    motivo: motivo || "",
                    estado_datos: String(estado_datos || "PENDIENTE").trim().toUpperCase()
                };
            });
        } else {
            try {
                listaPersonas = JSON.parse(s.personas);
            } catch (e) {
                listaPersonas = [];
            }
        }
    } else if (Array.isArray(s.personas) || Array.isArray(s.ingresantes)) {
        const rawP = Array.isArray(s.personas) ? s.personas : s.ingresantes;
        listaPersonas = rawP.map(p => ({
            id: p.id,
            ap_nombre: p.ap_nombre || `${p.nombre || ''} ${p.apellido || ''}`.trim() || p.nombre || "Contratista",
            nombre: p.nombre || p.ap_nombre || "Contratista",
            tipo_doc: p.tipo_doc || "CC",
            identificacion: p.identificacion || "—",
            cargo: p.cargo || "Operario",
            autorizado: p.autorizado !== '0' && p.autorizado !== 0 && p.autorizado !== false && p.autorizado !== 'false',
            motivo: p.motivo || p.motivo_rechazo || "",
            estado_datos: String(p.estado_datos || "PENDIENTE").trim().toUpperCase()
        }));
    }

    try {
        const storageKey = `incarsa_solicitud_${s.id}_personas`;
        const localPersonas = JSON.parse(localStorage.getItem(storageKey) || "null");
        if (Array.isArray(localPersonas) && localPersonas.length > 0) {
            listaPersonas = listaPersonas.map(lp => {
                const match = localPersonas.find(p => String(p.id) === String(lp.id) || (p.identificacion && p.identificacion === lp.identificacion));
                if (match) {
                    return {
                        ...lp,
                        autorizado: match.autorizado !== '0' && match.autorizado !== 0 && match.autorizado !== false && match.autorizado !== 'false',
                        motivo: match.motivo_rechazo || match.motivo || lp.motivo || ""
                    };
                }
                return lp;
            });
        }
    } catch (e) {}

    const nombreEmpresaOrigen = s.nombre_empresa || s.empresa_origen || s.empresaOrigen || "INCARSA";
    const nombreContratista = s.nombre_emContratista || s.empresa_contratista || s.contratista || "—";
    const diligenciadorNombre = s.diligenciador || (typeof s.diligenciado_por === "string" ? s.diligenciado_por : null) || s.diligenciadoPor || "Administrador";

    return {
        id: s.id,
        codigo: codigoVal,
        codigo_radicado: codigoVal,
        observaciones: observacionVal,
        observacion: observacionVal,
        nombre_empresa: nombreEmpresaOrigen,
        nombre_emContratista: nombreContratista,
        empresaOrigen: nombreEmpresaOrigen,
        empresa_origen: nombreEmpresaOrigen,
        contratista: nombreContratista,
        empresa_contratista: nombreContratista,
        planta: cadenaPlanta,
        plantas: cadenaPlanta,
        plantas_ids: Array.isArray(s.plantas) ? s.plantas.map(p => typeof p === 'object' ? Number(p.id) : Number(p)).filter(Boolean) : (s.plantas_ids ? String(s.plantas_ids).replace(/[\[\]]/g, "").split(",").map(x => parseInt(x.trim(), 10)).filter(n => !isNaN(n)) : []),
        fecha_ingreso: formatearFechaCorta(s.fecha_ingreso || s.fecha_inicio || s.fechaIngreso),
        fecha_salida: formatearFechaCorta(s.fecha_salida || s.fecha_fin || s.fechaSalida),
        fechaIngreso: formatearFechaCorta(s.fecha_ingreso || s.fecha_inicio || s.fechaIngreso),
        fechaSalida: formatearFechaCorta(s.fecha_salida || s.fecha_fin || s.fechaSalida),
        fecha_creacion_raw: s.fecha_creacion_raw || s.fecha_creacion,
        fecha_creacion: formatearFechaHoraEspanol(s.fecha_creacion_raw || s.fecha_creacion),
        fecha_creacion_corta: formatearFechaCorta(s.fecha_creacion_raw || s.fecha_creacion),
        fecha_registro: formatearFechaCorta(s.fecha_registro || s.fecha_creacion_raw || s.fecha_creacion || s.created_at || s.fecha_ingreso || s.fecha_inicio),
        estado: (s.estado || "ENVIADO").toUpperCase(),
        riesgo: s.nivel_de_riesgo || s.nivelRiesgo || s.riesgo || "—",
        actividad: s.actividad || "—",
        diligenciador: diligenciadorNombre,
        diligenciado_por: (s.diligenciado_por !== undefined && s.diligenciado_por !== null && !isNaN(Number(s.diligenciado_por))) ? Number(s.diligenciado_por) : (s.id_diligenciador ? Number(s.id_diligenciador) : null),
        is_active: s.is_active,
        esVencida: esInactivaVencida(s),
        es_vencida: esInactivaVencida(s),
        vehiculos: listaVehiculos,
        computos: listaComputos,
        personas: listaPersonas,
        revisiones: listaRevisiones
    };
}
window.normalizarSolicitud = normalizarSolicitud;



