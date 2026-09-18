/**
 * ============================================================================
 * dispositivos.js — Consulta y Auditoría de Dispositivos Registrados (Modal Global)
 * ============================================================================
 */

function dispositivoManager() {
    return {
        isOpen: false,
        cargando: false,
        mensajeError: "",

        isModuloMantenimiento(mod) {
            return window.isModuloMantenimiento ? window.isModuloMantenimiento(mod || 'dispositivos') : false;
        },
        get estadoMantenimiento() {
            return (typeof Alpine !== 'undefined' && Alpine.store && Alpine.store('mantenimiento'))
                ? Alpine.store('mantenimiento')
                : (window.estadoMantenimiento || {});
        },

        // Datos
        dispositivos: [],

        // Filtros y búsqueda
        search: "",
        filtroEstado: "",
        copiadoSerie: null,

        // Paginación
        pageSize: 6,
        currentPage: 1,

        async init() {
            // Escuchar evento global para abrir el modal desde el sidebar o cualquier botón
            window.addEventListener("open-dispositivos-modal", () => {
                this.abrirModal();
            });

            this.$watch("search", () => (this.currentPage = 1));
            this.$watch("filtroEstado", () => (this.currentPage = 1));
        },

        async abrirModal() {
            this.isOpen = true;
            this.mensajeError = "";
            this.search = "";
            this.filtroEstado = "";
            this.currentPage = 1;
            await this.cargarDispositivos();
        },

        cerrarModal() {
            this.isOpen = false;
            this.search = "";
            this.copiadoSerie = null;
        },

        async cargarDispositivos() {
            this.cargando = true;
            this.mensajeError = "";
            try {
                const token = typeof getAuthToken === "function" ? getAuthToken() : null;
                const headers = {};
                if (token) headers["Authorization"] = `Bearer ${token}`;

                const res = await fetch(`${API.dispositivos}/getAll`, { headers });
                if (!res.ok) {
                    if (res.status === 403) {
                        throw new Error("No tienes permisos asignados para consultar dispositivos.");
                    }
                    throw new Error(`HTTP ${res.status}`);
                }
                const data = await res.json();
                this.dispositivos = Array.isArray(data) ? data : (data.datos || data.data || []);
            } catch (err) {
                console.error("Error al cargar dispositivos:", err);
                this.mensajeError = err.message || "Error de conexión al consultar los dispositivos.";
                this.dispositivos = [];
            } finally {
                this.cargando = false;
            }
        },

        async copiarSerie(serie) {
            if (!serie || serie === "—" || serie === "S/N") return;
            try {
                await navigator.clipboard.writeText(serie);
                this.copiadoSerie = serie;
                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        toast: true,
                        position: "top-end",
                        icon: "success",
                        title: "Serie copiada",
                        showConfirmButton: false,
                        timer: 1500
                    });
                }
                setTimeout(() => {
                    if (this.copiadoSerie === serie) {
                        this.copiadoSerie = null;
                    }
                }, 2000);
            } catch (e) {
                console.warn("No se pudo copiar al portapapeles:", e);
            }
        },

        // Métricas calculadas
        get totalDispositivos() {
            return this.dispositivos.length;
        },

        get totalMarcasUnicas() {
            const set = new Set();
            this.dispositivos.forEach(d => {
                if (d.marca && d.marca.trim()) set.add(d.marca.trim().toUpperCase());
            });
            return set.size;
        },

        get totalSolicitudesConDispositivos() {
            const set = new Set();
            this.dispositivos.forEach(d => {
                if (d.solicitud_id) set.add(d.solicitud_id);
            });
            return set.size;
        },

        // Lista filtrada
        get dispositivosFiltrados() {
            let list = this.dispositivos;
            const q = (this.search || "").trim().toLowerCase();
            const est = (this.filtroEstado || "").trim().toUpperCase();

            if (q) {
                list = list.filter(d => 
                    (d.marca || "").toLowerCase().includes(q) ||
                    (d.modelo || "").toLowerCase().includes(q) ||
                    (d.serie || "").toLowerCase().includes(q) ||
                    (d.codigo_radicado || "").toLowerCase().includes(q) ||
                    (d.contratista || "").toLowerCase().includes(q)
                );
            }

            if (est) {
                list = list.filter(d => (d.estado_solicitud || "").toUpperCase() === est);
            }

            return list;
        },

        // Paginación
        get totalPages() {
            const len = this.dispositivosFiltrados.length;
            return Math.max(1, Math.ceil(len / this.pageSize));
        },

        get dispositivosPaginados() {
            const start = (this.currentPage - 1) * this.pageSize;
            return this.dispositivosFiltrados.slice(start, start + this.pageSize);
        },

        prevPage() {
            if (this.currentPage > 1) this.currentPage--;
        },

        nextPage() {
            if (this.currentPage < this.totalPages) this.currentPage++;
        },

        irAPagina(p) {
            if (p >= 1 && p <= this.totalPages) this.currentPage = p;
        },

        formatearFecha(f) {
            if (!f) return "—";
            try {
                const date = new Date(f);
                if (isNaN(date.getTime())) return f;
                return date.toLocaleDateString("es-CO", {
                    day: "2-digit",
                    month: "short",
                    year: "numeric"
                });
            } catch (e) {
                return f;
            }
        }
    };
}
