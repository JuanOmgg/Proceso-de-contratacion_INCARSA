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
    vehiculos: `${API_BASE_URL}/api/v1/vehiculos`,
    contratistas: `${API_BASE_URL}/emp_contratista`,
    auth: `${API_BASE_URL}/api/v1/auth`,
    notificaciones: `${API_BASE_URL}/api/v1/notificaciones`
};

// ============================================================================
// GESTIÓN CENTRALIZADA DE AUTENTICACIÓN Y TOKEN JWT
// ============================================================================
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
    return token;
}

function getAuthSession() {
    try {
        return JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
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
    } catch (e) {}
}

function cerrarSesionUsuario() {
    clearAuthSession();
    window.location.replace("/login?logout=1");
}

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

// Utilidad para formatear tiempos relativos amigables
function formatearTiempoRelativo(fechaStr) {
    if (!fechaStr) return "";
    try {
        const fecha = new Date(String(fechaStr).replace(" ", "T"));
        const ahora = new Date();
        const diffSegundos = Math.floor((ahora - fecha) / 1000);
        if (diffSegundos < 60) return "Hace un momento";
        const diffMinutos = Math.floor(diffSegundos / 60);
        if (diffMinutos < 60) return `Hace ${diffMinutos} min`;
        const diffHoras = Math.floor(diffMinutos / 60);
        if (diffHoras < 24) return `Hace ${diffHoras} h`;
        const diffDias = Math.floor(diffHoras / 24);
        if (diffDias === 1) return "Ayer";
        if (diffDias < 7) return `Hace ${diffDias} d`;
        return fecha.toLocaleDateString("es-CO", { day: "numeric", month: "short" });
    } catch (e) {
        return fechaStr;
    }
}

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
// SERVICIO DE NOTIFICACIONES EN TIEMPO REAL ('EN CALIENTE') - SSE & WEB AUDIO
// ============================================================================
function reproducirSonidoNotificacion() {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        if (ctx.state === 'suspended') {
            ctx.resume();
        }

        const ahora = ctx.currentTime;

        // Oscilador 1: Tono base suave (F5 -> A5)
        const osc1 = ctx.createOscillator();
        const gain1 = ctx.createGain();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(698.46, ahora);
        osc1.frequency.exponentialRampToValueAtTime(880, ahora + 0.12);

        gain1.gain.setValueAtTime(0, ahora);
        gain1.gain.linearRampToValueAtTime(0.18, ahora + 0.03);
        gain1.gain.exponentialRampToValueAtTime(0.001, ahora + 0.55);

        osc1.connect(gain1);
        gain1.connect(ctx.destination);

        // Oscilador 2: Armónico brillante (A5 -> C#6)
        const osc2 = ctx.createOscillator();
        const gain2 = ctx.createGain();
        osc2.type = 'sine';
        osc2.frequency.setValueAtTime(880, ahora + 0.09);
        osc2.frequency.exponentialRampToValueAtTime(1108.73, ahora + 0.22);

        gain2.gain.setValueAtTime(0, ahora);
        gain2.gain.setValueAtTime(0, ahora + 0.09);
        gain2.gain.linearRampToValueAtTime(0.14, ahora + 0.12);
        gain2.gain.exponentialRampToValueAtTime(0.001, ahora + 0.7);

        osc2.connect(gain2);
        gain2.connect(ctx.destination);

        osc1.start(ahora);
        osc1.stop(ahora + 0.6);
        osc2.start(ahora + 0.09);
        osc2.stop(ahora + 0.75);
    } catch (e) {
        // En navegadores con políticas estrictas de autoplay antes del primer clic
    }
}
window.reproducirSonidoNotificacion = reproducirSonidoNotificacion;

function animarCampanaNotificaciones() {
    try {
        const campanas = document.querySelectorAll('.topbar .fa-bell, button[title="Notificaciones"] i');
        campanas.forEach(el => {
            el.classList.remove('bell-ring-active');
            void el.offsetWidth; // Reflow para reiniciar animación
            el.classList.add('bell-ring-active');
            setTimeout(() => el.classList.remove('bell-ring-active'), 3200);
        });

        const badges = document.querySelectorAll('.badge-count');
        badges.forEach(b => {
            b.classList.remove('badge-pulse-active');
            void b.offsetWidth;
            b.classList.add('badge-pulse-active');
            setTimeout(() => b.classList.remove('badge-pulse-active'), 1800);
        });
    } catch (e) {}
}
window.animarCampanaNotificaciones = animarCampanaNotificaciones;

function mostrarToastNotificacion(n) {
    if (!n) return;
    const tipo = (n.tipo || 'info').toLowerCase();
    let titulo = n.titulo || 'Nueva Notificación';
    // Limpiar emojis al inicio del título si ya los trae para evitar duplicación visual
    titulo = titulo.replace(/^[⚠️ℹ️✅❌🔔]+\s*/, '');
    const mensaje = n.mensaje || '';
    const enlace = n.enlace || '';
    const archivoUrl = n.archivo_url || '';
    const archivoNombre = n.archivo_nombre || '';

    if (typeof Swal !== 'undefined') {
        const isDark = document.documentElement.classList.contains('dark');

        let iconHtml = '';
        let accentColor = '#0C767D';

        if (tipo === 'danger' || tipo === 'error') {
            accentColor = isDark ? '#f87171' : '#ef4444';
            iconHtml = `<div class="shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[11px] bg-rose-500/10 text-rose-500 dark:text-rose-400 border border-rose-500/20"><i class="fa-solid fa-circle-xmark"></i></div>`;
        } else if (tipo === 'warning') {
            accentColor = isDark ? '#fbbf24' : '#d97706';
            iconHtml = `<div class="shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[11px] bg-amber-500/10 text-amber-500 dark:text-amber-400 border border-amber-500/20"><i class="fa-solid fa-triangle-exclamation"></i></div>`;
        } else if (tipo === 'success') {
            accentColor = isDark ? '#34d399' : '#059669';
            iconHtml = `<div class="shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[11px] bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 border border-emerald-500/20"><i class="fa-solid fa-circle-check"></i></div>`;
        } else {
            accentColor = isDark ? '#38bdf8' : '#0284c7';
            iconHtml = `<div class="shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[11px] bg-sky-500/10 text-sky-500 dark:text-sky-400 border border-sky-500/20"><i class="fa-solid fa-bell"></i></div>`;
        }

        const htmlContent = `
            <div class="flex items-start gap-2.5 text-left w-full py-0.5">
                ${iconHtml}
                <div class="flex-1 min-w-0">
                    <div class="text-[12.5px] font-semibold text-slate-800 dark:text-slate-100 tracking-tight leading-snug truncate pr-3">
                        ${titulo}
                    </div>
                    <div class="mt-0.5 text-[11.5px] leading-relaxed text-slate-500 dark:text-slate-400 font-normal line-clamp-3 select-none">
                        ${mensaje}
                    </div>
                    ${archivoUrl ? `
                        <div class="mt-2">
                            <a href="${archivoUrl}" target="_blank" download class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                                <i class="fa-solid fa-file-arrow-down text-emerald-500"></i> ${archivoNombre || 'Adjunto'}
                            </a>
                        </div>
                    ` : ''}
                    ${enlace ? `
                        <div class="mt-2 pt-0.5 flex items-center gap-2">
                            <a href="${enlace}" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium bg-slate-100 hover:bg-slate-200 dark:bg-slate-800/90 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700/80 transition-colors shadow-xs">
                                <span>Abrir</span>
                                <i class="fa-solid fa-arrow-up-right-from-square text-[9px] opacity-70"></i>
                            </a>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            showCloseButton: true,
            timer: 7500,
            timerProgressBar: true,
            background: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.98)',
            color: isDark ? '#f8fafc' : '#0f172a',
            customClass: {
                popup: 'incarsa-toast-subtle shadow-xl'
            },
            didOpen: (toast) => {
                toast.style.borderLeft = `3px solid ${accentColor}`;
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
                if (enlace) {
                    toast.style.cursor = 'pointer';
                    toast.addEventListener('click', (e) => {
                        if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A' && !e.target.closest('a') && !e.target.closest('button')) {
                            window.location.href = enlace;
                        }
                    });
                }
            }
        });

        Toast.fire({
            html: htmlContent
        });
    }
}
window.mostrarToastNotificacion = mostrarToastNotificacion;

// Canal BroadcastChannel para sincronizar entre pestañas del mismo navegador
const notifChannel = (typeof window.BroadcastChannel !== 'undefined')
    ? new BroadcastChannel('incarsa_notificaciones_stream')
    : null;

window.NotificacionesRealtime = (function() {
    let eventSource = null;
    let reconectarTimer = null;
    let activo = false;
    let intentosReconexion = 0;

    function conectar() {
        const token = getAuthToken();
        if (!token) return;
        if (eventSource) {
            try { eventSource.close(); } catch(e) {}
        }

        const streamUrl = `${API_BASE_URL}/api/v1/notificaciones/stream?token=${encodeURIComponent(token)}`;

        try {
            eventSource = new EventSource(streamUrl);

            eventSource.addEventListener("connected", (e) => {
                activo = true;
                intentosReconexion = 0;
                console.log("⚡ [NOTIFICACIONES EN CALIENTE] Canal SSE conectado exitosamente:", e.data);
            });

            eventSource.addEventListener("nueva_notificacion", (e) => {
                try {
                    const parsed = JSON.parse(e.data);
                    const notif = parsed.data || parsed;
                    console.log("🔔 [NOTIFICACIONES EN CALIENTE] Recibida en vivo:", notif);

                    // 1. Chime auditivo suave
                    reproducirSonidoNotificacion();

                    // 2. Toast interactivo flotante
                    mostrarToastNotificacion(notif);

                    // 3. Vibración/pulso visual en la campana
                    animarCampanaNotificaciones();

                    // 4. Despachar a Alpine y vistas
                    window.dispatchEvent(new CustomEvent("notificacion-en-caliente", { detail: notif }));
                    window.dispatchEvent(new CustomEvent("notificaciones-actualizadas", { detail: notif }));

                    // 5. Notificar a otras pestañas
                    if (notifChannel) {
                        notifChannel.postMessage({ type: 'NUEVA_NOTIFICACION', notif });
                    }
                    localStorage.setItem("incarsa_notif_reload", String(Date.now()));
                } catch (err) {
                    console.error("Error al procesar notificación en vivo:", err);
                }
            });

            eventSource.addEventListener("notificaciones_leidas", (e) => {
                try {
                    const parsed = JSON.parse(e.data);
                    window.dispatchEvent(new CustomEvent("notificaciones-leidas-sync", { detail: parsed.data || parsed }));
                } catch(err) {}
            });

            eventSource.addEventListener("solicitud_actualizada", (e) => {
                try {
                    const parsed = JSON.parse(e.data);
                    console.log("⚡ [NOTIFICACIONES EN CALIENTE] Solicitud actualizada:", parsed.data);
                    window.dispatchEvent(new CustomEvent("solicitud-actualizada-en-caliente", { detail: parsed.data }));
                    window.dispatchEvent(new CustomEvent("solicitudes-recargar"));
                } catch(err) {}
            });

            eventSource.onerror = function() {
                activo = false;
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
                intentosReconexion++;
                const delay = Math.min(1000 * Math.pow(1.5, intentosReconexion), 15000);
                clearTimeout(reconectarTimer);
                reconectarTimer = setTimeout(() => {
                    if (getAuthToken()) {
                        conectar();
                    }
                }, delay);
            };
        } catch (err) {
            console.error("Error conectando a EventSource:", err);
        }
    }

    // Escuchar mensajes de sincronización de otras pestañas
    if (notifChannel) {
        notifChannel.onmessage = function(ev) {
            if (ev.data && ev.data.type === 'NUEVA_NOTIFICACION') {
                animarCampanaNotificaciones();
                window.dispatchEvent(new CustomEvent("notificacion-en-caliente-remota", { detail: ev.data.notif }));
                window.dispatchEvent(new CustomEvent("notificaciones-actualizadas"));
            }
        };
    }

    // Iniciar conexión inmediatamente si el usuario ya está autenticado
    if (getAuthToken()) {
        conectar();
    }

    // Reconectar si la pestaña vuelve de estar en segundo plano
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden && !activo && getAuthToken()) {
            conectar();
        }
    });

    return {
        conectar,
        desconectar() {
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
            activo = false;
        },
        get estaConectado() {
            return activo;
        }
    };
})();

// ============================================================================
// Función global de validación de roles para Alpine y cualquier script
// ============================================================================
function tieneRol(...roles) {
    let sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
    if (!sesion) {
        try {
            sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
        } catch (e) {}
    }
    const miRol = (sesion?.rol || "ADMINISTRADOR").trim().toUpperCase();

    // Solo SuperAdmin tiene acceso total automático
    if (miRol === "SUPERADMIN") {
        return true;
    }

    const listaRoles = roles.flat().filter(Boolean).map(r => String(r).trim().toUpperCase());
    return listaRoles.includes(miRol);
}
window.tieneRol = tieneRol;

// ============================================================================
// GESTIÓN DINÁMICA DE PERMISOS RBAC (Módulos y Acciones)
// ============================================================================
window.permisosActivos = (function() {
    try {
        return JSON.parse(sessionStorage.getItem("incarsa_permisos") || localStorage.getItem("incarsa_permisos") || "null");
    } catch(e) {
        return null;
    }
})();

async function recargarMisPermisos() {
    try {
        const token = getAuthToken();
        if (!token) return {};
        const res = await fetch("/api/v1/roles/mis-permisos");
        if (res.ok) {
            const data = await res.json();
            if (data && data.permisos) {
                sessionStorage.setItem("incarsa_permisos", JSON.stringify(data.permisos));
                localStorage.setItem("incarsa_permisos", JSON.stringify(data.permisos));
                window.permisosActivos = data.permisos;
                window.dispatchEvent(new CustomEvent("permisos-actualizados", { detail: data.permisos }));
                return data.permisos;
            }
        }
    } catch (e) {
        console.warn("Aviso cargando permisos dinámicos:", e);
    }
    return {};
}
window.recargarMisPermisos = recargarMisPermisos;

function puedeModulo(modulo) {
    let sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
    const miRol = (sesion?.rol || "").trim().toUpperCase();
    if (miRol === "SUPERADMIN") return true;

    try {
        const permisos = window.permisosActivos || JSON.parse(sessionStorage.getItem("incarsa_permisos") || localStorage.getItem("incarsa_permisos") || "null");
        if (permisos && permisos[modulo] && permisos[modulo].ver !== undefined) {
            return !!permisos[modulo].ver;
        }
    } catch (e) {}

    // Fallbacks de compatibilidad por rol si no se ha cargado la matriz
    const fallbacks = {
        "dashboard": true,
        "solicitudes": true,
        "nueva_solicitud": ["ADMINISTRADOR", "GESTION DOCUMENTAL", "SST", "GESCO", "SCR"].includes(miRol),
        "usuarios": ["ADMINISTRADOR"].includes(miRol),
        "nuevo_usuario": ["ADMINISTRADOR"].includes(miRol),
        "plantas": ["ADMINISTRADOR", "SCR"].includes(miRol),
        "contratistas": ["ADMINISTRADOR", "SCR", "GESTION DOCUMENTAL"].includes(miRol),
        "vehiculos": ["ADMINISTRADOR", "SCR", "GESTION DOCUMENTAL"].includes(miRol),
        "personas": true,
        "procesamiento": ["ADMINISTRADOR", "SST", "GESCO", "SCR"].includes(miRol),
        "antecedentes": ["ADMINISTRADOR", "SCR"].includes(miRol),
        "superadmin": miRol === "SUPERADMIN"
    };

    return fallbacks[modulo] !== undefined ? fallbacks[modulo] : true;
}
window.puedeModulo = puedeModulo;

function puedeAccion(modulo, accion) {
    let sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
    const miRol = (sesion?.rol || "").trim().toUpperCase();
    if (miRol === "SUPERADMIN") return true;

    try {
        const permisos = window.permisosActivos || JSON.parse(sessionStorage.getItem("incarsa_permisos") || localStorage.getItem("incarsa_permisos") || "null");
        if (permisos && permisos[modulo] && permisos[modulo][accion] !== undefined) {
            return !!permisos[modulo][accion];
        }
    } catch (e) {}

    // Por defecto administrador tiene permiso de acción si no hay regla específica
    if (miRol === "ADMINISTRADOR") return true;
    return false;
}
window.puedeAccion = puedeAccion;

function puedeEditarSolicitud(solicitud) {
    if (!solicitud) return false;
    let sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
    const miRol = (sesion?.rol || "").trim().toUpperCase();

    // SUPERADMIN puede editar sin importar en qué estado esté la solicitud
    if (miRol === "SUPERADMIN") return true;

    // Los demás usuarios solo pueden editar si tienen permiso Y la solicitud está en estado ENVIADO
    if (!puedeAccion("solicitudes", "editar") && !puedeAccion("dashboard", "editar")) {
        return false;
    }

    const est = String(solicitud.estado || "").trim().toUpperCase();
    return est === "ENVIADO";
}
window.puedeEditarSolicitud = puedeEditarSolicitud;

// ============================================================================
// ESTADO GLOBAL REACTIVO DE MANTENIMIENTO (SISTEMA Y MÓDULOS)
// ============================================================================
window.estadoMantenimiento = {
    activo: false,
    tipo: 'general',
    modulos: [],
    mensaje: '',
    tiempo: '',
    temporizador_minutos: 30,
    temporizador_fin: null
};

window.isModuloMantenimiento = function(mod) {
    let sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
    if (!sesion) {
        try {
            sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
        } catch(e) {}
    }
    const miRol = (sesion?.rol || "").trim().toUpperCase();
    if (miRol === "SUPERADMIN") return false;

    const est = (typeof Alpine !== "undefined" && Alpine.store && Alpine.store("mantenimiento"))
        ? Alpine.store("mantenimiento")
        : window.estadoMantenimiento;

    if (!est || !est.activo) return false;
    if (est.tipo === "general") return true;
    if (est.tipo === "modulos") {
        return (est.modulos || []).includes(mod);
    }
    return false;
};

async function cargarEstadoMantenimientoGlobal() {
    try {
        const res = await fetch("/api/v1/sistema/mantenimiento");
        if (res.ok) {
            const data = await res.json();
            const nuevoEstado = {
                activo: !!data.activo,
                tipo: data.tipo || "general",
                modulos: Array.isArray(data.modulos) ? data.modulos : [],
                mensaje: data.mensaje || "",
                tiempo: data.tiempo || "",
                temporizador_minutos: data.temporizador_minutos || 30,
                temporizador_fin: data.temporizador_fin || null
            };
            Object.assign(window.estadoMantenimiento, nuevoEstado);

            if (typeof Alpine !== "undefined" && Alpine.store && Alpine.store("mantenimiento")) {
                const store = Alpine.store("mantenimiento");
                store.activo = nuevoEstado.activo;
                store.tipo = nuevoEstado.tipo;
                store.modulos = nuevoEstado.modulos;
                store.mensaje = nuevoEstado.mensaje;
                store.tiempo = nuevoEstado.tiempo;
                store.temporizador_minutos = nuevoEstado.temporizador_minutos;
                store.temporizador_fin = nuevoEstado.temporizador_fin;
            }

            window.dispatchEvent(new CustomEvent("mantenimiento-actualizado", { detail: nuevoEstado }));
        }
    } catch (e) {
        console.warn("Aviso cargando estado de mantenimiento global:", e);
    }
}
window.cargarEstadoMantenimientoGlobal = cargarEstadoMantenimientoGlobal;

// Registrar Alpine store tan pronto Alpine se inicialice
document.addEventListener("alpine:init", () => {
    Alpine.store("mantenimiento", {
        activo: window.estadoMantenimiento.activo,
        tipo: window.estadoMantenimiento.tipo,
        modulos: window.estadoMantenimiento.modulos,
        mensaje: window.estadoMantenimiento.mensaje,
        tiempo: window.estadoMantenimiento.tiempo,
        temporizador_minutos: window.estadoMantenimiento.temporizador_minutos,
        temporizador_fin: window.estadoMantenimiento.temporizador_fin,

        isModuloMantenimiento(mod) {
            return window.isModuloMantenimiento(mod);
        },

        async cargar() {
            await window.cargarEstadoMantenimientoGlobal();
        }
    });

    window.cargarEstadoMantenimientoGlobal();
});

// Cargar de inmediato
cargarEstadoMantenimientoGlobal();

// Polling periódico cada 25 segundos
setInterval(() => {
    cargarEstadoMantenimientoGlobal();
}, 25000);

// ============================================================================
// Shell global de navegación y sesión de usuario para todas las vistas
// ============================================================================
function appShellStub() {
    let sesion = getAuthSession();

    const nombreUsuario = sesion ? (sesion.nombre || sesion.nombres || `${sesion.nombres || ''} ${sesion.apellidos || ''}`.trim() || "Usuario") : "Administrador Sistema";
    const iniciales = nombreUsuario.split(" ").filter(Boolean).map(p => p[0]).join("").substring(0, 2).toUpperCase() || "AD";
    const userId = sesion?.id || 1;
    const roleId = sesion?.id_rol || 2;

    return {
        sidebarCollapsed: false,
        sidebarOpenMobile: false,
        notificationsOpen: false,
        modalTodasNotificacionesOpen: false,
        filtroNotifTab: 'todas',
        busquedaNotif: '',
        notifPage: 1,
        notifPageSize: 8,
        userId: userId,
        roleId: roleId,
        activeRole: sesion?.rol || "ADMINISTRADOR",
        openModules: { formularios: false, tablas: true, procesamiento: false },
        notifications: [],
        unreadNotificationsCount: 0,
        userDisplayName: nombreUsuario,
        userInitials: iniciales,
        darkMode: localStorage.getItem('darkMode') === 'true',
        get estadoMantenimiento() {
            return (typeof Alpine !== 'undefined' && Alpine.store && Alpine.store('mantenimiento'))
                ? Alpine.store('mantenimiento')
                : window.estadoMantenimiento;
        },
        permisos: (function() {
            try {
                return window.permisosActivos || JSON.parse(sessionStorage.getItem("incarsa_permisos") || localStorage.getItem("incarsa_permisos") || "{}");
            } catch(e) {
                return {};
            }
        })(),

        tieneRol(...roles) {
            return window.tieneRol(...roles);
        },

        isModuloMantenimiento(mod) {
            return window.isModuloMantenimiento(mod);
        },

        advertirModuloMantenimiento(nombreModulo) {
            if (typeof Swal !== 'undefined') {
                const mensaje = this.estadoMantenimiento?.mensaje || 'Estamos realizando labores de optimización y mantenimiento programado.';
                const tiempo = this.estadoMantenimiento?.tiempo || 'Disponible en breve';
                Swal.fire({
                    icon: 'warning',
                    title: 'Módulo en Mantenimiento',
                    html: `<div class="text-left space-y-2">
                        <p class="font-bold text-amber-400 text-sm">${nombreModulo}</p>
                        <p class="text-xs sm:text-sm text-slate-300 leading-relaxed">${mensaje}</p>
                        <div class="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 mt-2 flex items-center gap-2">
                            <i class="fa-regular fa-clock"></i>
                            <span><strong>Tiempo estimado:</strong> ${tiempo}</span>
                        </div>
                    </div>`,
                    confirmButtonText: 'Entendido',
                    confirmButtonColor: '#f59e0b',
                    background: '#0f172a',
                    color: '#f8fafc'
                });
            } else {
                alert(`El módulo ${nombreModulo} se encuentra en mantenimiento.`);
            }
        },

        puedeModulo(mod) {
            if (this.activeRole === "SUPERADMIN") return true;
            if (this.permisos && this.permisos[mod] && this.permisos[mod].ver !== undefined) {
                return !!this.permisos[mod].ver;
            }
            return window.puedeModulo(mod);
        },

        puedeAccion(mod, acc) {
            if (this.activeRole === "SUPERADMIN") return true;
            if (this.permisos && this.permisos[mod] && this.permisos[mod][acc] !== undefined) {
                return !!this.permisos[mod][acc];
            }
            return window.puedeAccion(mod, acc);
        },

        formatearTiempoRelativo: formatearTiempoRelativo,
        formatearTextoEnlace: formatearTextoEnlace,

        get notificacionesFiltradas() {
            let lista = this.notifications || [];
            if (this.filtroNotifTab === 'no_leidas') {
                lista = lista.filter(n => !n.leido);
            } else if (this.filtroNotifTab === 'info') {
                lista = lista.filter(n => !n.tipo || n.tipo === 'info');
            } else if (this.filtroNotifTab === 'alertas') {
                lista = lista.filter(n => ['warning', 'error', 'danger'].includes(n.tipo));
            }

            if (this.busquedaNotif && this.busquedaNotif.trim()) {
                const q = this.busquedaNotif.toLowerCase().trim();
                lista = lista.filter(n => 
                    (n.titulo && n.titulo.toLowerCase().includes(q)) ||
                    (n.mensaje && n.mensaje.toLowerCase().includes(q))
                );
            }
            return lista;
        },

        get notificacionesModalPagina() {
            const filtradas = this.notificacionesFiltradas;
            const start = (this.notifPage - 1) * this.notifPageSize;
            return filtradas.slice(start, start + this.notifPageSize);
        },

        get notifTotalPaginas() {
            return Math.ceil(this.notificacionesFiltradas.length / this.notifPageSize) || 1;
        },

        abrirModalTodasNotificaciones() {
            this.modalTodasNotificacionesOpen = true;
            this.notificationsOpen = false;
            this.sidebarOpenMobile = false;
            this.filtroNotifTab = 'todas';
            this.busquedaNotif = '';
            this.notifPage = 1;
            this.cargarNotificaciones(100);
        },

        cerrarModalTodasNotificaciones() {
            this.modalTodasNotificacionesOpen = false;
        },

        async cargarEstadoMantenimientoGlobal() {
            try {
                const res = await fetch('/api/v1/sistema/mantenimiento');
                if (res.ok) {
                    const data = await res.json();
                    this.estadoMantenimiento = {
                        activo: !!data.activo,
                        tipo: data.tipo || 'general',
                        modulos: Array.isArray(data.modulos) ? data.modulos : [],
                        mensaje: data.mensaje || '',
                        tiempo: data.tiempo || '',
                        temporizador_minutos: data.temporizador_minutos,
                        temporizador_fin: data.temporizador_fin
                    };
                }
            } catch (e) {
                console.warn('Aviso consultando estado de mantenimiento:', e);
            }
        },

        init() {
            // Aplicar el modo oscuro guardado al cargar la página
            document.documentElement.classList.toggle('dark', this.darkMode);
            this.cargarNotificaciones();
            this.cargarEstadoMantenimientoGlobal();
            // Polling periódico cada 35 segundos
            setInterval(() => {
                this.cargarNotificaciones();
                this.cargarEstadoMantenimientoGlobal();
            }, 35000);

            // Escuchar apertura remota de modal de notificaciones
            window.addEventListener("open-notificaciones-modal", () => {
                this.abrirModalTodasNotificaciones();
            });

            // Escuchar notificaciones en caliente vía SSE
            window.addEventListener("notificacion-en-caliente", (e) => {
                const notif = e.detail;
                if (notif) {
                    const existe = (this.notifications || []).some(n => n.id && notif.id && String(n.id) === String(notif.id));
                    if (!existe) {
                        this.notifications.unshift(notif);
                        this.unreadNotificationsCount = (this.unreadNotificationsCount || 0) + 1;
                    }
                }
            });

            window.addEventListener("notificacion-en-caliente-remota", (e) => {
                const notif = e.detail;
                if (notif) {
                    const existe = (this.notifications || []).some(n => n.id && notif.id && String(n.id) === String(notif.id));
                    if (!existe) {
                        this.notifications.unshift(notif);
                        this.unreadNotificationsCount = (this.unreadNotificationsCount || 0) + 1;
                    }
                }
            });

            window.addEventListener("notificaciones-leidas-sync", (e) => {
                const data = e.detail || {};
                if (data.todas) {
                    (this.notifications || []).forEach(n => n.leido = true);
                    this.unreadNotificationsCount = 0;
                } else if (data.id_notificacion) {
                    const target = (this.notifications || []).find(n => String(n.id) === String(data.id_notificacion));
                    if (target && !target.leido) {
                        target.leido = true;
                        if (this.unreadNotificationsCount > 0) this.unreadNotificationsCount--;
                    }
                }
            });

            // Escuchar actualizaciones de notificaciones al revisar solicitudes
            window.addEventListener("notificaciones-actualizadas", () => {
                this.cargarNotificaciones();
            });
            window.addEventListener("storage", (e) => {
                if (e.key === "incarsa_notificaciones_reload" || e.key === "incarsa_notif_reload") {
                    this.cargarNotificaciones();
                }
            });

            // Escuchar actualizaciones de permisos en vivo
            window.addEventListener("permisos-actualizados", (e) => {
                this.permisos = e.detail || {};
            });

            // Sincronizar permisos frescos con backend
            if (getAuthToken()) {
                window.recargarMisPermisos().then(p => {
                    if (p && Object.keys(p).length > 0) {
                        this.permisos = p;
                    }
                });
            }
        },

        async cargarNotificaciones(limit = 50) {
            try {
                const params = new URLSearchParams();
                if (this.userId) params.append("id_usuario", this.userId);
                if (this.roleId) params.append("id_rol", this.roleId);
                if (limit) params.append("limit", limit);
                const res = await fetch(`${API.notificaciones}?${params.toString()}`);
                if (res.ok) {
                    const data = await res.json();
                    this.notifications = data.notificaciones || [];
                    this.unreadNotificationsCount = data.no_leidas || 0;
                }
            } catch (err) {
                console.warn("Aviso al cargar notificaciones:", err);
            }
        },

        async marcarNotificacionLeida(n) {
            if (!n.leido) {
                try {
                    await fetch(`${API.notificaciones}/${n.id}/leer`, { method: "PATCH" });
                    n.leido = true;
                    if (this.unreadNotificationsCount > 0) {
                        this.unreadNotificationsCount--;
                    }
                } catch (e) {
                    console.warn("Aviso al marcar notificación como leída:", e);
                }
            }
            if (n.enlace) {
                window.location.href = n.enlace;
            }
        },

        esNotifPreaprobada(n) {
            if (!n) return false;
            const enlace = String(n.enlace || "");
            const titulo = String(n.titulo || "");
            return enlace.includes("confirmar=true") || (titulo.toLowerCase().includes("preaprobada") && enlace.includes("/solicitudes/revision/"));
        },

        obtenerCodigoSolicitudDeNotif(n) {
            if (!n || !n.enlace) return null;
            const match = n.enlace.match(/\/solicitudes\/revision\/([^\/?#]+)/);
            if (match && match[1]) return match[1];
            return null;
        },

        async revisarSolicitudNotif(n) {
            if (!n.leido) {
                try {
                    await fetch(`${API.notificaciones}/${n.id}/leer`, { method: "PATCH" });
                    n.leido = true;
                    if (this.unreadNotificationsCount > 0) this.unreadNotificationsCount--;
                } catch (e) {}
            }
            const cod = this.obtenerCodigoSolicitudDeNotif(n);
            if (cod) {
                window.location.href = `/solicitudes/revision/${cod}`;
            } else if (n.enlace) {
                window.location.href = n.enlace;
            }
        },

        async confirmarAprobacionDirectaNotif(n) {
            const cod = this.obtenerCodigoSolicitudDeNotif(n);
            if (!cod) {
                if (n.enlace) window.location.href = n.enlace;
                return;
            }

            const sesion = (typeof getSesionActual === "function") ? getSesionActual() : null;
            const nombreUsuario = sesion?.nombres 
                ? `${sesion.nombres} ${sesion.apellidos || ''}`.trim() 
                : (this.userDisplayName || "Auditor SCR");

            const accionConfirmar = async () => {
                n.aprobando = true;
                try {
                    const payload = {
                        id_planta: null,
                        rol: "SCR",
                        decision: "APROBADO",
                        observacion: "Aprobación definitiva confirmada directamente desde el panel de notificaciones.",
                        id_usuario: this.userId || sesion?.id || null,
                        nombre_revisor: nombreUsuario
                    };
                    const res = await fetch(`${API.solicitudes}/${cod}/dictamen`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });
                    if (res.ok) {
                        n.aprobadoExitoso = true;
                        n.leido = true;
                        fetch(`${API.notificaciones}/${n.id}/leer`, { method: "PATCH" }).catch(() => {});
                        if (this.unreadNotificationsCount > 0) this.unreadNotificationsCount--;

                        if (typeof Swal !== 'undefined') {
                            Swal.fire({
                                icon: 'success',
                                title: '¡Solicitud Aprobada!',
                                text: `La solicitud #${cod} ha sido aprobada definitivamente con éxito.`,
                                timer: 3000,
                                showConfirmButton: false
                            });
                        } else if (typeof Alerta !== 'undefined') {
                            Alerta.fire({
                                type: 'success',
                                title: '¡Solicitud Aprobada!',
                                text: `La solicitud #${cod} ha sido aprobada definitivamente.`
                            });
                        }
                    } else {
                        const err = await res.json().catch(() => ({}));
                        const msg = err.detail || err.mensaje || "Error al aprobar la solicitud.";
                        if (typeof Swal !== 'undefined') {
                            Swal.fire({ icon: 'error', title: 'Error', text: msg });
                        } else {
                            alert(`Error al aprobar: ${msg}`);
                        }
                    }
                } catch (e) {
                    console.error("Error al aprobar desde notificación:", e);
                    alert("Error de conexión al aprobar la solicitud: " + e.message);
                } finally {
                    n.aprobando = false;
                }
            };

            if (typeof Swal !== 'undefined') {
                const result = await Swal.fire({
                    title: '¿Confirmar Aprobación Final?',
                    html: `<p class="text-sm text-slate-300">¿Deseas dar la <strong>aprobación definitiva</strong> a la solicitud <strong>#${cod}</strong> sin ingresar a la ventana de revisión?</p>`,
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonColor: '#10b981',
                    cancelButtonColor: '#64748b',
                    confirmButtonText: '<i class="fa-solid fa-check-double mr-1.5"></i> Sí, Confirmar y Aprobar',
                    cancelButtonText: 'Cancelar',
                    background: '#0f172a',
                    color: '#f8fafc'
                });
                if (result.isConfirmed) {
                    await accionConfirmar();
                }
            } else if (typeof Alerta !== 'undefined') {
                const res = await Alerta.fire({
                    type: 'question',
                    title: '¿Confirmar Aprobación?',
                    text: `¿Deseas aprobar definitivamente la solicitud #${cod} sin ingresar a la ventana de revisión?`,
                    confirmText: 'Sí, Aprobar',
                    cancelText: 'Cancelar',
                    showCancel: true
                });
                if (res.isConfirmed) {
                    await accionConfirmar();
                }
            } else {
                if (confirm(`¿Deseas confirmar la aprobación definitiva de la solicitud #${cod}?`)) {
                    await accionConfirmar();
                }
            }
        },

        async marcarTodasNotificacionesLeidas() {
            try {
                await fetch(`${API.notificaciones}/marcar-todas-leidas`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id_usuario: this.userId, id_rol: this.roleId })
                });
                this.notifications.forEach(n => n.leido = true);
                this.unreadNotificationsCount = 0;
            } catch (e) {
                console.warn("Aviso al marcar todas las notificaciones:", e);
            }
        },

        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            document.documentElement.classList.toggle('dark', this.darkMode);
            localStorage.setItem('darkMode', this.darkMode);
        },

        toggleSidebar() {
            this.sidebarCollapsed = !this.sidebarCollapsed;
        },

        toggleMobileSidebar() {
            this.sidebarOpenMobile = !this.sidebarOpenMobile;
        },

        closeMobileSidebar() {
            this.sidebarOpenMobile = false;
        },

        cerrarSesion() {
            cerrarSesionUsuario();
        }
    };
}

/* =========================================================
   Alerta — mini librería de alertas propia (sin dependencias)
   API: Alerta.fire({ type, title, text, confirmText, cancelText, showCancel })
   Devuelve una Promise<{ isConfirmed: boolean }>
   ========================================================= */
const Alerta = (() => {

  const ICONS = {
    success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>',
    error:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"/></svg>',
    warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4M12 17h.01M10.3 3.9L1.8 18a1 1 0 0 0 .9 1.5h18.6a1 1 0 0 0 .9-1.5L13.7 3.9a1 1 0 0 0-1.7 0Z"/></svg>',
    info:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16v-4M12 8h.01"/><circle cx="12" cy="12" r="9.5"/></svg>'
  };

  function fire({
    type = 'info',
    title = '',
    text = '',
    confirmText = 'Aceptar',
    cancelText = 'Cancelar',
    showCancel = false
  } = {}) {
    return new Promise((resolve) => {
      const overlay = document.createElement('div');
      overlay.className = 'al-overlay';

      overlay.innerHTML = `
        <div class="al-card ${type}">
          <div class="al-stamp">${ICONS[type] || ICONS.info}</div>
          <h2 class="al-title"></h2>
          <p class="al-text"></p>
          <div class="al-actions">
            ${showCancel ? `<button class="al-btn al-btn-cancel">${cancelText}</button>` : ''}
            <button class="al-btn al-btn-confirm">${confirmText}</button>
          </div>
          <div class="al-serrated"></div>
        </div>
      `;

      // set text content safely (avoids HTML injection from dynamic strings)
      overlay.querySelector('.al-title').textContent = title;
      overlay.querySelector('.al-text').textContent = text;

      document.body.appendChild(overlay);
      requestAnimationFrame(() => overlay.classList.add('show'));

      function close(result) {
        overlay.classList.remove('show');
        setTimeout(() => overlay.remove(), 180);
        resolve(result);
      }

      overlay.querySelector('.al-btn-confirm').addEventListener('click', () => close({ isConfirmed: true }));
      const cancelBtn = overlay.querySelector('.al-btn-cancel');
      if (cancelBtn) cancelBtn.addEventListener('click', () => close({ isConfirmed: false }));

      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close({ isConfirmed: false });
      });
      document.addEventListener('keydown', function esc(e) {
        if (e.key === 'Escape') { close({ isConfirmed: false }); document.removeEventListener('keydown', esc); }
      });
    });
  }

  return { fire };
})();

async function confirmDemo() {
  const { isConfirmed } = await Alerta.fire({
    type: 'warning',
    title: '¿Eliminar el archivo?',
    text: 'Esta acción es permanente y no se puede deshacer.',
    showCancel: true,
    confirmText: 'Sí, eliminar',
    cancelText: 'Cancelar'
  });
  Alerta.fire({
    type: isConfirmed ? 'success' : 'info',
    title: isConfirmed ? 'Eliminado' : 'Cancelado',
    text: isConfirmed ? 'El archivo fue eliminado.' : 'No se realizó ningún cambio.'
  });
}

window.showToast = function(message, icon = 'info', duration = 3000) {
  if (typeof Swal !== 'undefined') {
    Swal.fire({
      toast: true,
      position: 'top-end',
      icon: icon,
      title: message,
      showConfirmButton: false,
      timer: duration,
      timerProgressBar: true
    });
  } else {
    console.log(`[TOAST ${String(icon).toUpperCase()}] ${message}`);
  }
};

// ============================================================================
// COMPONENTE ALPINE: Temporizador Visual para Modales en Mantenimiento (503)
// ============================================================================
function modalTimerCountdown() {
  return {
    hours: '00',
    minutes: '00',
    seconds: '00',
    timerId: null,
    init() {
      this.tick();
      this.timerId = setInterval(() => this.tick(), 1000);
    },
    destroy() {
      if (this.timerId) clearInterval(this.timerId);
    },
    tick() {
      let target = null;
      const est = (typeof Alpine !== 'undefined' && Alpine.store && Alpine.store('mantenimiento'))
        ? Alpine.store('mantenimiento')
        : window.estadoMantenimiento;

      if (est && est.temporizador_fin) {
        target = Number(est.temporizador_fin);
      }

      if (!target || isNaN(target)) {
        try {
          const saved = JSON.parse(sessionStorage.getItem('incarsa_503_active_timer') || 'null');
          if (saved && saved.target) {
            target = Number(saved.target);
          }
        } catch (e) {}
      }

      if (!target || isNaN(target)) {
        const mins = (est && est.temporizador_minutos) ? Number(est.temporizador_minutos) : 30;
        target = Date.now() + (mins * 60 * 1000);
      }

      const diff = target - Date.now();
      if (diff <= 0) {
        this.hours = '00';
        this.minutes = '00';
        this.seconds = '00';
        return;
      }

      const h = Math.floor(diff / (1000 * 60 * 60));
      const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const s = Math.floor((diff % (1000 * 60)) / 1000);

      this.hours = String(h).padStart(2, '0');
      this.minutes = String(m).padStart(2, '0');
      this.seconds = String(s).padStart(2, '0');
    }
  };
}
window.modalTimerCountdown = modalTimerCountdown;

// ============================================================================
// SISTEMA UNIVERSAL DE TOOLTIPS MODERNOS (Reemplaza y estiliza [title] y [data-tooltip])
// ============================================================================
(function initModernTooltips() {
  let tooltipEl = null;
  let activeTarget = null;

  function getTooltipEl() {
    if (!tooltipEl) {
      tooltipEl = document.createElement('div');
      tooltipEl.id = 'incarsa-global-tooltip';
      tooltipEl.className = 'incarsa-global-tooltip';
      document.body.appendChild(tooltipEl);
    }
    return tooltipEl;
  }

  function showTooltip(target, text) {
    if (!text || !text.trim()) return;
    const tip = getTooltipEl();
    tip.textContent = text.trim();
    tip.classList.remove('is-active', 'pos-bottom');
    tip.style.display = 'block';

    const rect = target.getBoundingClientRect();
    const tipRect = tip.getBoundingClientRect();

    let top = rect.top - tipRect.height - 8;
    let posClass = 'pos-top';

    // Si se sale por arriba de la pantalla visible, colocar abajo
    if (top < 8) {
      top = rect.bottom + 8;
      posClass = 'pos-bottom';
    }

    let left = rect.left + (rect.width / 2) - (tipRect.width / 2);
    // Limitar dentro de los bordes izquierdo y derecho
    const maxLeft = window.innerWidth - tipRect.width - 12;
    left = Math.max(12, Math.min(left, maxLeft));

    tip.style.top = `${top + window.scrollY}px`;
    tip.style.left = `${left + window.scrollX}px`;
    tip.classList.add(posClass, 'is-active');
    activeTarget = target;
  }

  function hideTooltip() {
    if (tooltipEl) {
      tooltipEl.classList.remove('is-active');
    }
    activeTarget = null;
  }

  // Interceptar al pasar el cursor sobre elementos con title o data-tooltip
  document.addEventListener('mouseover', function (e) {
    const target = e.target.closest ? e.target.closest('[title], [data-tooltip], [data-title]') : null;
    if (!target) return;

    let text = target.getAttribute('data-tooltip') || target.getAttribute('data-title');

    // Si tiene atributo title nativo, transferir su contenido y suprimir title para evitar el tooltip nativo
    if (target.hasAttribute('title')) {
      const nativeTitle = target.getAttribute('title');
      if (nativeTitle && nativeTitle.trim()) {
        text = nativeTitle.trim();
        target.setAttribute('data-tooltip', text);
      }
      target.removeAttribute('title'); // Elimina la caja negra nativa del navegador
    }

    if (text && text.trim()) {
      showTooltip(target, text);
    }
  }, true);

  // Ocultar al retirar el cursor
  document.addEventListener('mouseout', function (e) {
    if (activeTarget && (!e.relatedTarget || !activeTarget.contains(e.relatedTarget))) {
      hideTooltip();
    }
  }, true);

  window.addEventListener('scroll', hideTooltip, { passive: true });
  document.addEventListener('click', hideTooltip, true);
})();