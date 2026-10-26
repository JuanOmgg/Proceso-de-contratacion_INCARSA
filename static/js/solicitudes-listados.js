// Helpers centralizados: normalizarSolicitud, generarCodigoAlfanumerico, esInactivaVencida y formatearFechaCorta
// se encuentran definidos y expuestos globalmente en /static/js/config.js

function solicitudesCards() {
    return {
        solActivas: 0,
        solInactivas: 0,
        totalRegistros: 0,
        cargando: true,
        _tieneMetricasServidor: false,

        init() {
            window.addEventListener("solicitudes-updated", (e) => {
                const list = e.detail || [];
                if (!this._tieneMetricasServidor) {
                    this.actualizarConteo(list);
                }
            });

            window.addEventListener("solicitudes-metrics-updated", (e) => {
                const m = e.detail;
                if (m) {
                    this._tieneMetricasServidor = true;
                    this.solActivas = Number(m.activas || 0);
                    this.solInactivas = Number(m.inactivas || 0);
                    this.totalRegistros = Number(m.total || (this.solActivas + this.solInactivas));
                    this.cargando = false;
                }
            });
        },

        get esAdmin() {
            const sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
            const rolTexto = String((sesion && (sesion.rol || sesion.nombre_rol)) || "").toUpperCase();
            const rolId = Number(sesion ? (sesion.id_rol || sesion.rol_id) : 0);
            return rolId === 1 || rolId === 2 || rolTexto.includes("ADMIN");
        },

        actualizarConteo(lista) {
            let filtrada = lista;
            const sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
            const rolTexto = String((sesion && (sesion.rol || sesion.nombre_rol)) || "").toUpperCase();
            const rolId = Number(sesion ? (sesion.id_rol || sesion.rol_id) : 0);
            const esAdminUser = rolId === 1 || rolId === 2 || rolTexto.includes("ADMIN");

            // Si el usuario no es admin ni superadmin, omitir solicitudes inactivas por vencimiento
            if (!esAdminUser) {
                filtrada = filtrada.filter(s => !(s.esVencida !== undefined ? s.esVencida : esInactivaVencida(s)));
            }

            const esSstGesco = rolTexto.includes("SST") || rolTexto.includes("GESCO") || rolId === 6 || rolId === 7;
            if (esSstGesco) {
                const misPlantas = (sesion && sesion.plantas_ids ? sesion.plantas_ids : []).map(Number);
                if (!misPlantas || misPlantas.length === 0) {
                    filtrada = [];
                } else {
                    filtrada = filtrada.filter(s => {
                        const pIds = Array.isArray(s.plantas_ids) ? s.plantas_ids.map(Number) : (s.plantas_ids ? String(s.plantas_ids).split(",").map(Number).filter(Boolean) : []);
                        return pIds.some(pid => misPlantas.includes(pid));
                    });
                }
            }
            this.solActivas = filtrada.filter(s => s.is_active === 1 || s.is_active === true || s.is_active === "1").length;
            this.solInactivas = filtrada.filter(s => s.is_active === 0 || s.is_active === false || s.is_active === "0").length;
            this.totalRegistros = this.solActivas + this.solInactivas;
            this.cargando = false;
        },

        get totalSolicitudes() {
            if (this.totalRegistros > 0) return this.totalRegistros;
            return this.solActivas + this.solInactivas;
        }
    };
}

function solicitudesTable() {
    return {
        // Datos
        solicitudes: [],
        empresas: [],

        search: "",
        filtroEmpresa: "",
        filtroEstado: "todos",

        pageSize: 10,
        currentPage: 1,
        totalRegistros: 0,
        totalPaginasServidor: 1,
        cargando: true,

        // Modal Detalle
        viewModalOpen: false,
        selected: null,

        // Modal QR de Acceso
        qrModalOpen: false,
        selectedQr: null,

        // Modal Observaciones
        observacionesModalOpen: false,
        solicitudObservacion: null,
        textoObservacion: "",
        guardandoObservacion: false,

        // Toast de copiado
        copiadoToast: false,

        // Catálogos
        contratistas: [],

        // Modal Selector de Tipo de Formulario (Directo vs Externo)
        modalTipoSolicitudOpen: false,

        // Modal Formulario Temporal para Terceros (Estilo Ticket)
        modalTokenOpen: false,
        modalTokenTab: "crear",
        tokenModoTiempo: "rapido", // 'rapido' o 'exacto'
        tokenDuracion: "24",
        tokenFechaPersonalizada: "",
        tokenContratistaId: "",
        tokenContratistaSearch: "",
        tokenBuscadorAbierto: false,
        tokenGeneradoUrl: "",
        tokenInfoGenerado: null,
        tokenCopiado: false,
        tokensHistorial: [],
        cargandoTokens: false,

        // Modal eliminación
        showDeleteModal: false,
        deleteModalOpen: false,
        solicitudAEliminar: null,
        pendingDeleteId: null,

        // Reactividad de permisos RBAC
        permisosVersion: 0,
        puedeAccion(mod, acc) {
            const _v = this.permisosVersion;
            return window.puedeAccion(mod, acc);
        },
        puedeModulo(mod) {
            const _v = this.permisosVersion;
            return window.puedeModulo(mod);
        },
        puedeEditarSolicitud(s) {
            const _v = this.permisosVersion;
            if (typeof window.puedeEditarSolicitud === "function") {
                return window.puedeEditarSolicitud(s);
            }
            if (!s) return false;
            const sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
            const miRol = (sesion?.rol || this.activeRole || "").trim().toUpperCase();
            if (miRol === "SUPERADMIN") return true;

            if (!this.puedeAccion("solicitudes", "editar")) return false;
            const est = String(s.estado || "").trim().toUpperCase();
            return est === "ENVIADO" || est === "PRE-ENVIADO";
        },

        async init() {
            window.addEventListener("permisos-actualizados", () => {
                this.permisosVersion++;
            });

            // Recarga automática en caliente ante dictámenes o radicaciones
            window.addEventListener("solicitudes-recargar", () => this.getSolicitudes());
            window.addEventListener("solicitud-actualizada-en-caliente", () => this.getSolicitudes());

            // Abrir modal de token si es disparado por un evento personalizado (ej: sidebar)
            window.addEventListener("abrir-modal-token-formulario", () => {
                this.abrirModalToken();
            });

            // Abrir modal selector o token si viene en los query params de URL (?modal=token-terceros o ?modal=selector)
            try {
                const params = new URLSearchParams(window.location.search);
                if (params.get("modal") === "token-terceros") {
                    this.abrirModalToken();
                    window.history.replaceState({}, document.title, window.location.pathname);
                } else if (params.get("modal") === "selector") {
                    this.modalTipoSolicitudOpen = true;
                    window.history.replaceState({}, document.title, window.location.pathname);
                }

                // Filtrar automáticamente si viene desde una notificación de solicitud PRE-ENVIADA
                const estParam = params.get("estado") || params.get("filtro");
                if (estParam && (estParam.toLowerCase() === "pre-enviado" || estParam.toLowerCase() === "pre_enviado")) {
                    this.filtroEstado = "pre-enviado";
                }
                const codParam = params.get("codigo") || params.get("search");
                if (codParam) {
                    this.search = codParam.trim();
                }
            } catch (e) {}

            await Promise.allSettled([
                this.getEmpresas(),
                this.getContratistas(),
                this.getSolicitudes()
            ]);

            // Escuchar sincronización de sesión y recarga de solicitudes en caliente vía SSE
            window.addEventListener("sesion-actualizada-en-caliente", () => {
                this.currentPage = 1;
                this.getSolicitudes();
            });

            window.addEventListener("solicitudes-recargar", () => {
                this.getSolicitudes();
            });

            // Búsqueda con debounce en servidor (300ms)
            let searchTimeout = null;
            this.$watch("search", () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.currentPage = 1;
                    this.getSolicitudes();
                }, 300);
            });
            this.$watch("filtroEmpresa", () => {
                this.currentPage = 1;
                this.getSolicitudes();
            });
            this.$watch("filtroEstado", () => {
                this.currentPage = 1;
                this.getSolicitudes();
            });
            this.$watch("pageSize", () => {
                this.currentPage = 1;
                this.getSolicitudes();
            });
        },

        notificarCambio() {
            window.dispatchEvent(new CustomEvent("solicitudes-updated", { detail: this.solicitudes }));
        },

        async getSolicitudes() {
            this.cargando = true;
            try {
                let sesion = null;
                try {
                    sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
                } catch (e) {}

                let url = `${API.solicitudes}/getall?page=${this.currentPage}&limit=${this.pageSize}`;
                if (this.search && this.search.trim()) {
                    url += `&search=${encodeURIComponent(this.search.trim())}`;
                }
                if (this.filtroEstado && this.filtroEstado !== "todos") {
                    url += `&estado=${encodeURIComponent(this.filtroEstado)}`;
                }
                if (this.filtroEmpresa && this.filtroEmpresa.trim()) {
                    url += `&empresa=${encodeURIComponent(this.filtroEmpresa.trim())}`;
                }

                const rolTexto = String((sesion && (sesion.rol || sesion.nombre_rol)) || "").toUpperCase();
                const rolId = Number(sesion ? (sesion.id_rol || sesion.rol_id) : 0);
                const esSstGesco = rolTexto.includes("SST") || rolTexto.includes("GESCO") || rolId === 6 || rolId === 7;
                if (sesion && sesion.id && esSstGesco) {
                    url += `&id_usuario=${sesion.id}`;
                }
                const esGestionDoc = rolTexto.includes("SOLICITANTE") || rolId === 5;
                if (sesion && sesion.id && esGestionDoc) {
                    url += `&diligenciado_por=${sesion.id}`;
                }

                const response = await fetch(url);
                if (!response.ok) throw new Error(`Error ${response.status}`);
                const data = await response.json();

                if (data && data.datos && Array.isArray(data.datos)) {
                    this.solicitudes = data.datos.map(s => normalizarSolicitud(s));
                    this.totalRegistros = Number(data.total || this.solicitudes.length);
                    this.totalPaginasServidor = Number(data.total_paginas || Math.max(1, Math.ceil(this.totalRegistros / this.pageSize)));
                    if (data.metricas) {
                        window.dispatchEvent(new CustomEvent("solicitudes-metrics-updated", { detail: data.metricas }));
                    }
                } else {
                    const lista = Array.isArray(data) ? data : (data.datos || []);
                    this.solicitudes = lista.map(s => normalizarSolicitud(s));
                    this.totalRegistros = this.solicitudes.length;
                    this.totalPaginasServidor = Math.max(1, Math.ceil(this.totalRegistros / this.pageSize));
                }
                this.notificarCambio();
            } catch (error) {
                console.error("Error al cargar solicitudes:", error);
                this.solicitudes = [];
                this.totalRegistros = 0;
                this.totalPaginasServidor = 1;
            } finally {
                this.cargando = false;
            }
        },

        async getEmpresas() {
            try {
                const response = await fetch(`${API.empresas}/getall`);
                if (!response.ok) throw new Error(`Error ${response.status}`);
                const data = await response.json();
                this.empresas = Array.isArray(data) ? data : (data.datos || []);
            } catch (error) {
                console.error("Error al cargar empresas:", error);
                this.empresas = [];
            }
        },

        async getContratistas() {
            try {
                const token = (typeof getAuthToken === "function") ? getAuthToken() : null;
                const headers = token ? { "Authorization": `Bearer ${token}` } : {};
                let response = await fetch(`${API.contratistas}/getall`, { headers });
                if (!response.ok) {
                    response = await fetch(`${API.contratistas}/`, { headers });
                }
                if (response.ok) {
                    const data = await response.json();
                    this.contratistas = Array.isArray(data) ? data : (data.data || data.datos || []);
                }
            } catch (error) {
                console.warn("Error al cargar empresas contratistas:", error);
                this.contratistas = [];
            }
        },

        get esAdmin() {
            const u = this.sesionUsuario;
            if (!u) return false;
            const idRol = parseInt(u.id_rol || u.rol_id, 10);
            const rolNom = String(u.rol || u.nombre_rol || "").toUpperCase();
            return idRol === 1 || idRol === 2 || rolNom.includes("ADMIN");
        },

        get solicitudFiltrados() {
            return this.solicitudes;
        },

        get puedeGenerarFormularioTemporal() {
            const u = this.sesionUsuario;
            if (!u) return true;
            const idRol = parseInt(u.id_rol || u.rol_id, 10);
            const rolNom = String(u.rol || u.nombre_rol || "").toUpperCase();
            return idRol === 5 || idRol === 1 || idRol === 2 ||
                   rolNom.includes("SOLICITANTE") ||
                   rolNom.includes("SOLICITANTE") ||
                   rolNom.includes("ADMIN");
        },

        puedeAprobarPreEnvio(s) {
            if (!s || (s.estado || "").toUpperCase() !== "PRE-ENVIADO") return false;
            const u = this.sesionUsuario;
            if (!u) return true;
            const idRol = parseInt(u.id_rol || u.rol_id, 10);
            const rolNom = String(u.rol || u.nombre_rol || "").toUpperCase();
            if (idRol === 1 || idRol === 2 || rolNom.includes("ADMIN")) return true;
            return (idRol === 5 || rolNom.includes("SOLICITANTE"));
        },

        get sesionUsuario() {
            try {
                return (typeof getAuthSession === "function")
                    ? getAuthSession()
                    : JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
            } catch (e) {
                return null;
            }
        },

        get esRolConPlantas() {
            const sesion = this.sesionUsuario;
            if (!sesion) return false;
            const rolTexto = String(sesion.rol || sesion.nombre_rol || "").trim().toUpperCase();
            if (rolTexto === "SST" || rolTexto === "GESCO") return true;
            const rolId = Number(sesion.id_rol);
            // ÚNICAMENTE SST (ID 6) y GESCO (ID 7) filtran por plantas
            return rolId === 6 || rolId === 7;
        },

        get plantasUsuario() {
            const sesion = this.sesionUsuario;
            if (!sesion) return [];
            return (sesion.plantas_ids || []).map(Number);
        },

        get plantasUsuarioNombres() {
            const sesion = this.sesionUsuario;
            if (!sesion || !sesion.plantas || sesion.plantas.length === 0) return "";
            return sesion.plantas.map(p => typeof p === 'object' ? p.nombre : p).join(", ");
        },

        get totalPaginas() {
            return this.totalPaginasServidor || 1;
        },

        get solicitudesPagina() {
            return this.solicitudes;
        },

        get rangoMostrado() {
            if (!this.totalRegistros || this.totalRegistros === 0) return "0 de 0";
            const start = (this.currentPage - 1) * this.pageSize + 1;
            const end = Math.min(this.currentPage * this.pageSize, this.totalRegistros);
            return `${start}–${end} de ${this.totalRegistros}`;
        },

        // ---------------------------------------------------
        // Acciones sobre registros
        // ---------------------------------------------------
        async toggleActivo(solicitud) {
            const nuevoEstado = !(solicitud.is_active === 1 || solicitud.is_active === true || solicitud.is_active === "1");
            solicitud.is_active = nuevoEstado;
            const idx = this.solicitudes.findIndex(s => s.id === solicitud.id);
            if (idx > -1) this.solicitudes[idx].is_active = nuevoEstado;

            this.notificarCambio();

            try {
                const res = await fetch(`${API.solicitudes}/${solicitud.id}`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ is_active: nuevoEstado })
                });
                if (!res.ok) {
                    console.warn(`Error al actualizar estado de solicitud en backend (HTTP ${res.status})`);
                }
            } catch (err) {
                console.error("Error en PATCH de solicitud:", err);
            }
        },

        // ---------------------------------------------------
        // Gestión de Observaciones
        // ---------------------------------------------------
        openObservacionModal(solicitud) {
            this.solicitudObservacion = solicitud;
            this.textoObservacion = solicitud.observaciones || solicitud.observacion || "";
            this.observacionesModalOpen = true;
        },

        closeObservacionModal() {
            this.observacionesModalOpen = false;
            this.solicitudObservacion = null;
            this.textoObservacion = "";
        },

        async guardarObservacion() {
            if (!this.solicitudObservacion) return;
            this.guardandoObservacion = true;

            const nuevaObs = this.textoObservacion.trim();
            const solId = this.solicitudObservacion.id;

            // 1. Actualizar en el objeto de la lista en memoria
            this.solicitudObservacion.observaciones = nuevaObs;
            this.solicitudObservacion.observacion = nuevaObs;

            const idx = this.solicitudes.findIndex(s => String(s.id) === String(solId));
            if (idx > -1) {
                this.solicitudes[idx].observaciones = nuevaObs;
                this.solicitudes[idx].observacion = nuevaObs;
            }

            // 2. Persistir en localStorage e invalidar caché
            try {
                const guardadas = JSON.parse(localStorage.getItem("incarsa_observaciones_solicitudes") || "{}");
                guardadas[solId] = nuevaObs;
                window._cachedObservacionesLocal = guardadas;
                localStorage.setItem("incarsa_observaciones_solicitudes", JSON.stringify(guardadas));
            } catch (e) {}

            // 3. Intentar persistir en FastAPI Backend
            try {
                await fetch(`${API.solicitudes}/${solId}`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ observacion: nuevaObs, observaciones: nuevaObs })
                });
            } catch (e) {
                console.warn("No se pudo guardar observación en backend, guardada localmente:", e);
            } finally {
                this.guardandoObservacion = false;
                this.closeObservacionModal();
            }
        },

        copiarTexto(texto) {
            if (!texto) return;
            navigator.clipboard.writeText(texto).then(() => {
                this.copiadoToast = true;
                setTimeout(() => { this.copiadoToast = false; }, 2000);
            }).catch(() => {});
        },

        async openView(solicitud) {
            this.selected = normalizarSolicitud(solicitud);
            this.viewModalOpen = true;

            try {
                const res = await fetch(`${API.solicitudes}/${solicitud.id}`);
                if (res.ok) {
                    const dataLive = await res.json();
                    if (dataLive && (dataLive.id || dataLive.codigo)) {
                        this.selected = normalizarSolicitud({
                            ...solicitud,
                            ...dataLive
                        });
                        const idx = this.solicitudes.findIndex(s => String(s.id) === String(solicitud.id));
                        if (idx > -1) {
                            this.solicitudes[idx] = this.selected;
                            this.notificarCambio();
                        }
                        window.dispatchEvent(new CustomEvent("notificaciones-actualizadas"));
                        localStorage.setItem("incarsa_notificaciones_reload", Date.now().toString());
                    }
                }
            } catch (err) {
                console.warn("Aviso al refrescar detalle de solicitud:", err);
            }
        },

        closeView() {
            this.viewModalOpen = false;
            this.selected = null;
        },

        openQrModal(solicitud) {
            if (!solicitud) return;
            this.selectedQr = solicitud;
            this.qrModalOpen = true;
        },

        cerrarQrModal() {
            this.qrModalOpen = false;
            this.selectedQr = null;
        },

        descargarQr() {
            if (!this.selectedQr) return;
            const codigo = this.selectedQr.codigo || ('RAD-' + this.selectedQr.id);
            const a = document.createElement('a');
            a.href = `/api/v1/solicitudes/${encodeURIComponent(codigo)}/qr`;
            a.download = `QR-${codigo}.png`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        },

        async copiarEnlaceQr() {
            if (!this.selectedQr) return;
            const codigo = this.selectedQr.codigo || ('RAD-' + this.selectedQr.id);
            const url = `${window.location.origin}/verificar/${encodeURIComponent(codigo)}`;
            try {
                await navigator.clipboard.writeText(url);
                this.copiadoToast = true;
                setTimeout(() => (this.copiadoToast = false), 2500);
            } catch (e) {
                const ta = document.createElement('textarea');
                ta.value = url;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
                this.copiadoToast = true;
                setTimeout(() => (this.copiadoToast = false), 2500);
            }
        },

        // ============================================================
        // MÉTODOS PARA FORMULARIOS TEMPORALES CON TOKEN (DELEGA A MODAL GLOBAL)
        // ============================================================
        abrirModalToken(tab = "crear") {
            window.dispatchEvent(new CustomEvent("open-token-formulario-modal", { detail: { tab } }));
        },

        async aprobarPreEnvio(solicitud) {
            const cod = solicitud.codigo || ("RAD-" + solicitud.id);
            let confirmacion = false;
            if (typeof Swal !== "undefined") {
                const res = await Swal.fire({
                    title: "¿Aprobar y Enviar solicitud?",
                    html: `La solicitud <strong>${cod}</strong> pasará de <span class="text-purple-400 font-bold">PRE-ENVIADO</span> a <span class="text-emerald-400 font-bold">ENVIADO</span> y se notificará a los evaluadores (SST, GESCO, SCR) para iniciar la revisión.`,
                    icon: "question",
                    showCancelButton: true,
                    confirmButtonColor: "#10b981",
                    cancelButtonColor: "#64748b",
                    confirmButtonText: "Sí, Aprobar y Enviar",
                    cancelButtonText: "Cancelar"
                });
                confirmacion = res.isConfirmed;
            } else {
                confirmacion = confirm(`¿Deseas autorizar y enviar la solicitud ${cod} para su revisión oficial?`);
            }

            if (!confirmacion) return;

            try {
                const res = await fetch(`${API.solicitudes}/${solicitud.id}/aprobar-envio`, {
                    method: "POST"
                });
                const data = await res.json();
                if (!res.ok || !data.exito) {
                    throw new Error(data.detail || data.mensaje || "Error al aprobar el envío");
                }

                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "success",
                        title: "¡Solicitud Enviada!",
                        text: `La solicitud ${cod} ha sido aprobada y enviada exitosamente al proceso de revisión.`,
                        timer: 2500,
                        showConfirmButton: false
                    });
                } else {
                    alert(`¡Solicitud ${cod} enviada exitosamente!`);
                }

                await this.getSolicitudes();
            } catch (e) {
                if (typeof Swal !== "undefined") {
                    Swal.fire({ icon: "error", title: "Error al aprobar", text: e.message });
                } else {
                    alert("Error: " + e.message);
                }
            }
        },

        estadoClass(estado) {
            return (typeof window.estadoClass === 'function') ? window.estadoClass(estado) : 'status-enviado';
        },

        confirmarEliminar(solicitud) {
            this.solicitudAEliminar = solicitud;
            this.pendingDeleteId = solicitud?.id || null;
            this.showDeleteModal = true;
            this.deleteModalOpen = true;
        },

        confirmDelete(solicitud) {
            this.confirmarEliminar(solicitud);
        },

        cancelarEliminar() {
            this.solicitudAEliminar = null;
            this.pendingDeleteId = null;
            this.showDeleteModal = false;
            this.deleteModalOpen = false;
        },

        cancelDelete() {
            this.cancelarEliminar();
        },

        async eliminarSolicitud() {
            if (!this.solicitudAEliminar && !this.pendingDeleteId) return;
            const id = this.solicitudAEliminar?.id || this.pendingDeleteId;
            try {
                await fetch(`${API.solicitudes}/${id}`, { method: "DELETE" });
            } catch (e) {
                console.warn("No se pudo eliminar en backend:", e);
            }
            this.cancelarEliminar();
            await this.getSolicitudes();
        },

        executeDelete() {
            return this.eliminarSolicitud();
        },

        // ---------------------------------------------------
        // Paginación y Filtros
        // ---------------------------------------------------
        resetPage() {
            this.currentPage = 1;
            this.getSolicitudes();
        },
        goToPage(n) {
            if (n >= 1 && n <= this.totalPaginas) {
                this.currentPage = n;
                this.getSolicitudes();
            }
        },
        prevPage() {
            if (this.currentPage > 1) {
                this.goToPage(this.currentPage - 1);
            }
        },
        nextPage() {
            if (this.currentPage < this.totalPaginas) {
                this.goToPage(this.currentPage + 1);
            }
        },

        limpiarFiltros() {
            this.filtroEmpresa = "";
            this.filtroEstado = "todos";
            this.search = "";
            this.currentPage = 1;
            this.getSolicitudes();
        }
    };
}