/**
 * ============================================================================
 * INCARSA - GESTIÓN Y TIEMPO REAL DE NOTIFICACIONES
 * Archivo: /static/js/notificaciones.js
 * ============================================================================
 */

// ----------------------------------------------------------------------------
// 1. SONIDOS Y EFECTOS VISUALES
// ----------------------------------------------------------------------------
function reproducirSonidoNotificacion() {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        if (ctx.state === "suspended") {
            ctx.resume();
        }

        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        // Sonido tipo chime suave (dos tonos armónicos)
        osc.type = "sine";
        osc.frequency.setValueAtTime(587.33, now); // D5
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.12); // A5

        gain.gain.setValueAtTime(0, now);
        gain.gain.linearRampToValueAtTime(0.08, now + 0.04);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.55);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(now);
        osc.stop(now + 0.55);
    } catch (e) {
        // Silencioso si el navegador bloquea audio antes de interacción
    }
}
window.reproducirSonidoNotificacion = reproducirSonidoNotificacion;

function animarCampanaNotificaciones() {
    const bells = document.querySelectorAll('.notification-btn, #btn-notificaciones, [data-notif-bell]');
    bells.forEach(bell => {
        bell.classList.remove('animate-wiggle', 'ring-2', 'ring-amber-400');
        void bell.offsetWidth; // Trigger reflow
        bell.classList.add('animate-wiggle', 'ring-2', 'ring-amber-400');
        setTimeout(() => {
            bell.classList.remove('animate-wiggle', 'ring-2', 'ring-amber-400');
        }, 1600);
    });
}
window.animarCampanaNotificaciones = animarCampanaNotificaciones;

// ----------------------------------------------------------------------------
// 2. TOAST FLOTANTE INTERACTIVO
// ----------------------------------------------------------------------------
function mostrarToastNotificacion(n) {
    if (!n) return;
    const tipo = (n.tipo || 'info').toLowerCase();
    const titulo = n.titulo || 'Nueva notificación';
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

// ----------------------------------------------------------------------------
// 3. FORMATO Y DETECCIÓN DE SOLICITUDES PREAPROBADAS
// ----------------------------------------------------------------------------
window._solicitudesConfirmadasDirectas = window._solicitudesConfirmadasDirectas || new Set();

function esNotifPreaprobada(n) {
    // Ya no se maneja la confirmación de aprobación mediante notificación.
    // Al alcanzar los avales técnicos, las solicitudes pre-aprobadas pasan automáticamente a APROBADO.
    return false;
}
window.esNotifPreaprobada = esNotifPreaprobada;

function obtenerCodigoSolicitudDeNotif(n) {
    if (!n) return null;
    if (n.codigo_solicitud) return String(n.codigo_solicitud).trim();
    if (n.cod_solicitud) return String(n.cod_solicitud).trim();
    if (n.codigo) return String(n.codigo).trim();
    if (n.id_solicitud && isNaN(Number(n.id_solicitud))) return String(n.id_solicitud).trim();

    if (n.enlace) {
        const match = String(n.enlace).match(/\/solicitudes\/revision\/([^\/?#\s]+)/i);
        if (match && match[1]) return match[1].trim();
        const matchRad = String(n.enlace).match(/(RAD-[A-Za-z0-9]+)/i);
        if (matchRad && matchRad[1]) return matchRad[1].trim();
    }
    if (n.titulo) {
        const match = String(n.titulo).match(/(RAD-[A-Za-z0-9]+)/i);
        if (match && match[1]) return match[1].trim();
    }
    if (n.mensaje) {
        const match = String(n.mensaje).match(/(RAD-[A-Za-z0-9]+)/i);
        if (match && match[1]) return match[1].trim();
    }
    if (n.id_solicitud) return String(n.id_solicitud).trim();
    return null;
}
window.obtenerCodigoSolicitudDeNotif = obtenerCodigoSolicitudDeNotif;

// ----------------------------------------------------------------------------
// 4. ACCIONES SOBRE NOTIFICACIONES
// ----------------------------------------------------------------------------
async function revisarSolicitudNotif(n) {
    if (!n) return;
    if (!n.leido && n.id) {
        try {
            const notifUrl = (typeof API !== "undefined" && API.notificaciones) 
                ? API.notificaciones 
                : `${window.location.origin}/api/v1/notificaciones`;
            const token = (typeof getAuthToken === "function") ? getAuthToken() : null;
            await fetch(`${notifUrl}/${n.id}/leer`, { 
                method: "PATCH",
                headers: token ? { "Authorization": `Bearer ${token}` } : {}
            });
            n.leido = true;
        } catch (e) {}
    }
    const cod = obtenerCodigoSolicitudDeNotif(n);
    if (cod) {
        window.location.href = `/solicitudes/revision/${cod}`;
    } else if (n.enlace) {
        window.location.href = n.enlace;
    }
}
window.revisarSolicitudNotif = revisarSolicitudNotif;

async function confirmarAprobacionDirectaNotif(n) {
    if (!n) return;
    const cod = obtenerCodigoSolicitudDeNotif(n);
    if (!cod) {
        if (n.enlace) window.location.href = n.enlace;
        return;
    }

    const sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
    const token = (typeof getAuthToken === "function") ? getAuthToken() : (sesion?.token || null);
    const nombreUsuario = sesion?.nombre || (sesion?.nombres 
        ? `${sesion.nombres} ${sesion.apellidos || ''}`.trim() 
        : "Auditor SCR");
    const idUsuario = sesion?.id || null;
    const rolUsuario = sesion?.rol || "SCR";

    n.aprobando = true;
    try {
        const payload = {
            id_planta: null,
            rol: rolUsuario,
            decision: "APROBADO",
            observacion: "Aprobación definitiva confirmada directamente desde el panel de notificaciones.",
            id_usuario: idUsuario,
            nombre_revisor: nombreUsuario
        };

        const solicitudesUrl = (typeof API !== "undefined" && API.solicitudes) 
            ? API.solicitudes 
            : `${window.location.origin}/api/v1/solicitudes`;

        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${solicitudesUrl}/${encodeURIComponent(cod)}/dictamen`, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            n.aprobadoExitoso = true;
            n.leido = true;
            if (cod) window._solicitudesConfirmadasDirectas.add(cod);
            if (n.enlace) n.enlace = n.enlace.replace("?confirmar=true", "").replace("&confirmar=true", "");

            const notifUrl = (typeof API !== "undefined" && API.notificaciones) 
                ? API.notificaciones 
                : `${window.location.origin}/api/v1/notificaciones`;
            if (n.id) {
                fetch(`${notifUrl}/${n.id}/leer`, { 
                    method: "PATCH",
                    headers: token ? { "Authorization": `Bearer ${token}` } : {}
                }).catch(() => {});
            }

            // Notificar a las tablas y vistas en caliente
            window.dispatchEvent(new CustomEvent("solicitud-actualizada-en-caliente", { detail: { codigo: cod, estado: "APROBADO" } }));
            
            // Retrasar levemente la recarga de notificaciones para que el usuario aprecie el estado aprobado
            setTimeout(() => {
                window.dispatchEvent(new CustomEvent("notificaciones-actualizadas"));
            }, 1200);

            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    icon: 'success',
                    title: '¡Solicitud Aprobada!',
                    text: `La solicitud #${cod} ha sido aprobada definitivamente con éxito.`,
                    timer: 3500,
                    showConfirmButton: false,
                    background: '#0f172a',
                    color: '#f8fafc'
                });
            } else if (typeof Alerta !== 'undefined') {
                Alerta.fire({
                    type: 'success',
                    title: '¡Solicitud Aprobada!',
                    text: `La solicitud #${cod} ha sido aprobada definitivamente.`
                });
            } else {
                alert(`¡Solicitud #${cod} aprobada con éxito!`);
            }
        } else {
            const err = await res.json().catch(() => ({}));
            const msg = err.detail || err.mensaje || "Error al aprobar la solicitud.";
            if (typeof Swal !== 'undefined') {
                Swal.fire({ icon: 'error', title: 'Error', text: msg, background: '#0f172a', color: '#f8fafc' });
            } else {
                alert(`Error al aprobar: ${msg}`);
            }
        }
    } catch (e) {
        console.error("Error al aprobar desde notificación:", e);
        if (typeof Swal !== 'undefined') {
            Swal.fire({ icon: 'error', title: 'Error de conexión', text: e.message, background: '#0f172a', color: '#f8fafc' });
        } else {
            alert("Error de conexión al aprobar la solicitud: " + e.message);
        }
    } finally {
        n.aprobando = false;
    }
}
window.confirmarAprobacionDirectaNotif = confirmarAprobacionDirectaNotif;

// ----------------------------------------------------------------------------
// 5. CANAL EN TIEMPO REAL SSE & MULTI-PESTAÑA (BROADCAST)
// ----------------------------------------------------------------------------
const notifBroadcastChannel = (typeof window.BroadcastChannel !== 'undefined')
    ? new BroadcastChannel('incarsa_notificaciones_stream')
    : null;

window.NotificacionesRealtime = (function() {
    let eventSource = null;
    let reconectarTimer = null;
    let activo = false;
    let intentosReconexion = 0;

    function conectar() {
        const token = (typeof getAuthToken === "function") ? getAuthToken() : null;
        if (!token) return;
        if (eventSource) {
            try { eventSource.close(); } catch(e) {}
        }

        const baseUrl = (typeof API_BASE_URL !== "undefined") ? API_BASE_URL : window.location.origin;
        const streamUrl = `${baseUrl}/api/v1/notificaciones/stream?token=${encodeURIComponent(token)}`;

        try {
            eventSource = new EventSource(streamUrl);

            eventSource.addEventListener("connected", (e) => {
                activo = true;
                intentosReconexion = 0;
                console.log("⚡ [SSE] Canal de notificaciones conectado exitosamente:", e.data);
            });

            eventSource.addEventListener("nueva_notificacion", (e) => {
                try {
                    const parsed = JSON.parse(e.data);
                    const notif = parsed.data || parsed;
                    console.log("🔔 [SSE] Nueva notificación en vivo:", notif);

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
                    if (notifBroadcastChannel) {
                        notifBroadcastChannel.postMessage({ type: 'NUEVA_NOTIFICACION', notif });
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
                    console.log("⚡ [SSE] Solicitud actualizada:", parsed.data);
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
                    const t = (typeof getAuthToken === "function") ? getAuthToken() : null;
                    if (t) {
                        conectar();
                    }
                }, delay);
            };
        } catch (err) {
            console.error("Error conectando a EventSource:", err);
        }
    }

    // Escuchar mensajes de sincronización de otras pestañas
    if (notifBroadcastChannel) {
        notifBroadcastChannel.onmessage = function(ev) {
            if (ev.data && ev.data.type === 'NUEVA_NOTIFICACION') {
                animarCampanaNotificaciones();
                window.dispatchEvent(new CustomEvent("notificacion-en-caliente-remota", { detail: ev.data.notif }));
                window.dispatchEvent(new CustomEvent("notificaciones-actualizadas"));
            }
        };
    }

    // Iniciar conexión si la pestaña está visible y autenticada
    const tInit = (typeof getAuthToken === "function") ? getAuthToken() : null;
    if (tInit && !document.hidden) {
        conectar();
    }

    // Gestionar conexiones inteligentemente según visibilidad para no agotar los sockets del navegador
    document.addEventListener("visibilitychange", () => {
        if (document.hidden) {
            if (eventSource) {
                try { eventSource.close(); } catch(e) {}
                eventSource = null;
                activo = false;
            }
            clearTimeout(reconectarTimer);
        } else {
            const t = (typeof getAuthToken === "function") ? getAuthToken() : null;
            if (t && !eventSource) {
                conectar();
            }
        }
    });

    // Reconectar inmediatamente en caliente cuando el centinela detecta que regresó la red
    window.addEventListener("red-restablecida", () => {
        const t = (typeof getAuthToken === "function") ? getAuthToken() : null;
        if (t && !document.hidden) {
            intentosReconexion = 0;
            clearTimeout(reconectarTimer);
            if (eventSource) {
                try { eventSource.close(); } catch(e) {}
                eventSource = null;
            }
            console.log("⚡ [SSE] Red restablecida: reconectando canal de notificaciones en vivo...");
            conectar();
        }
    });

    return {
        conectar,
        desconectar: function() {
            if (eventSource) {
                try { eventSource.close(); } catch(e) {}
                eventSource = null;
                activo = false;
            }
            clearTimeout(reconectarTimer);
        },
        estaActivo: function() { return activo; }
    };
})();
