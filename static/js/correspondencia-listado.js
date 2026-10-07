function correspondenciaTable() {
    const checkEsSuperAdmin = () => {
        try {
            const ses = (typeof getAuthSession === 'function') 
                ? getAuthSession() 
                : JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || 'null');
            const r = String(ses?.rol || ses?.nombre_rol || ses?.rol_nombre || '').toUpperCase().trim();
            const u = String(ses?.tipo_usuario || ses?.usuario || '').toUpperCase().trim();
            return r === 'SUPERADMIN' 
                || u === 'SUPERADMIN' 
                || ses?.id_rol === 1 
                || ses?.id_rol === 6
                || document.documentElement.getAttribute('data-role') === 'SUPERADMIN'
                || document.documentElement.classList.contains('role-superadmin');
        } catch (e) {
            return false;
        }
    };

    return {
        esSuperAdmin: checkEsSuperAdmin(),
        correspondencias: [],
        cargando: false,
        error: null,

        // ---------------------------------------------------
        // Filtros y búsqueda
        // ---------------------------------------------------
        search: "",
        filtroTipo: "",
        filtroAnio: "",
        filtroFechas: "",

        // ---------------------------------------------------
        // Paginación
        // ---------------------------------------------------
        currentPage: 1,
        pageSize: 10,

        // ---------------------------------------------------
        // Inicialización
        // ---------------------------------------------------
        async init() {
            await this.getCorrespondencia();

            if (this.$watch) {
                this.$watch("search", () => (this.currentPage = 1));
                this.$watch("filtroTipo", () => (this.currentPage = 1));
                this.$watch("filtroAnio", () => (this.currentPage = 1));
                this.$watch("pageSize", () => (this.currentPage = 1));
            }
        },

        // ---------------------------------------------------
        // Carga de Datos
        // ---------------------------------------------------
        async getCorrespondencia() {
            this.cargando = true;
            this.error = null;
            try {
                const response = await fetch(`${API.correspondencia}/getall`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    const errData = await response.json().catch(() => ({}));
                    throw new Error(errData.detail || errData.mensaje || `HTTP ${response.status}`);
                }

                const res = await response.json();
                const raw = Array.isArray(res) ? res : (res.data || res.datos || []);
                this.correspondencias = raw;
            } catch (error) {
                console.error("Error al obtener correspondencia:", error);
                this.error = error.message || "Error al cargar la correspondencia.";
                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "error",
                        title: "Error al cargar",
                        text: "No se pudo obtener el listado de correspondencia.",
                        confirmButtonText: "Aceptar"
                    });
                }
            } finally {
                this.cargando = false;
            }
        },

        // ---------------------------------------------------
        // Métricas / Contadores
        // ---------------------------------------------------
        get anioActual() {
            return new Date().getFullYear();
        },

        get anioAnterior() {
            return this.anioActual - 1;
        },

        get totalCorrespondencias() {
            return this.correspondencias.length;
        },

        get totalAnioActual() {
            const y = String(this.anioActual);
            return this.correspondencias.filter(c => c.fecha_envio && String(c.fecha_envio).startsWith(y)).length;
        },

        get totalAnioAnterior() {
            const y = String(this.anioAnterior);
            return this.correspondencias.filter(c => c.fecha_envio && String(c.fecha_envio).startsWith(y)).length;
        },

        get aniosDisponibles() {
            const anios = new Set();
            const anioActual = new Date().getFullYear();
            anios.add(anioActual);

            (this.correspondencias || []).forEach(c => {
                if (c.fecha_envio) {
                    const y = String(c.fecha_envio).substring(0, 4);
                    if (y && !isNaN(y)) anios.add(Number(y));
                }
            });

            return Array.from(anios).sort((a, b) => b - a);
        },

        // ---------------------------------------------------
        // Filtrado Reactivo
        // ---------------------------------------------------
        get correspondenciasFiltradas() {
            const texto = (this.search || "").trim().toLowerCase();
            const anioFiltro = String(this.filtroAnio || this.filtroRol || "").trim();

            return this.correspondencias.filter(item => {
                if (!item) return false;

                const radicado = String(item.radicado || "").toLowerCase();
                const tipo = String(item.tipo_correspondencia || "").toLowerCase();
                const asunto = String(item.asunto || "").toLowerCase();
                const procedencia = String(item.procedencia || "").toLowerCase();
                const destino = String(item.destino || "").toLowerCase();
                const fecha = String(item.fecha_envio || "").toLowerCase();

                const matchTexto =
                    !texto ||
                    radicado.includes(texto) ||
                    tipo.includes(texto) ||
                    asunto.includes(texto) ||
                    procedencia.includes(texto) ||
                    destino.includes(texto) ||
                    fecha.includes(texto);

                const matchTipo =
                    !this.filtroTipo ||
                    tipo === this.filtroTipo.toLowerCase();

                const matchAnio =
                    !anioFiltro ||
                    fecha.startsWith(anioFiltro);

                return matchTexto && matchTipo && matchAnio;
            });
        },

        // ---------------------------------------------------
        // Paginación y Rangos
        // ---------------------------------------------------
        get totalPaginas() {
            return Math.max(1, Math.ceil(this.correspondenciasFiltradas.length / this.pageSize));
        },

        get correspondenciasPagina() {
            const start = (this.currentPage - 1) * this.pageSize;
            return this.correspondenciasFiltradas.slice(start, start + this.pageSize);
        },

        get rangoMostrado() {
            if (this.correspondenciasFiltradas.length === 0) return "0 de 0";
            const start = (this.currentPage - 1) * this.pageSize + 1;
            const end = Math.min(this.currentPage * this.pageSize, this.correspondenciasFiltradas.length);
            return `${start}–${end} de ${this.correspondenciasFiltradas.length}`;
        },

        get paginasVisibles() {
            const total = this.totalPaginas;
            let startP = Math.max(1, this.currentPage - 2);
            let endP = Math.min(total, startP + 4);
            startP = Math.max(1, endP - 4);
            const pages = [];
            for (let i = startP; i <= endP; i++) pages.push(i);
            return pages;
        },

        // ---------------------------------------------------
        // Controles de Paginación
        // ---------------------------------------------------
        resetPage() {
            this.currentPage = 1;
        },

        goToPage(n) {
            if (n >= 1 && n <= this.totalPaginas) {
                this.currentPage = n;
            }
        },

        prevPage() {
            this.goToPage(this.currentPage - 1);
        },

        nextPage() {
            this.goToPage(this.currentPage + 1);
        },

        // ---------------------------------------------------
        // Limpieza de Filtros
        // ---------------------------------------------------
        limpiarFiltros() {
            this.search = "";
            this.filtroTipo = "";
            this.filtroAnio = "";
            this.filtroFechas = "";
            this.currentPage = 1;
        },

        // ---------------------------------------------------
        // Formato y Helpers
        // ---------------------------------------------------
        formatearFecha(fechaStr) {
            if (!fechaStr) return "—";
            try {
                const raw = String(fechaStr).trim().split("T")[0].split(" ")[0];
                const partes = raw.split("-");
                if (partes.length === 3) {
                    const [anio, mes, dia] = partes;
                    const meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
                    const mesIndex = parseInt(mes, 10) - 1;
                    const mesTexto = meses[mesIndex] || mes;
                    return `${dia} ${mesTexto}, ${anio}`;
                }
                return fechaStr;
            } catch {
                return fechaStr;
            }
        },

        // ---------------------------------------------------
        // Eliminación
        // ---------------------------------------------------
        showDeleteModal: false,
        deleteModalOpen: false,
        itemAEliminar: null,
        eliminando: false,

        confirmarEliminar(item) {
            this.itemAEliminar = item;
            this.showDeleteModal = true;
            this.deleteModalOpen = true;
        },

        confirmDelete(item) {
            this.confirmarEliminar(item);
        },

        cancelarEliminar() {
            this.itemAEliminar = null;
            this.showDeleteModal = false;
            this.deleteModalOpen = false;
        },

        cancelDelete() {
            this.cancelarEliminar();
        },

        executeDelete() {
            return this.eliminarCorrespondencia();
        },

        async eliminarCorrespondencia() {
            if (!this.itemAEliminar) return;
            const id = this.itemAEliminar.id;
            const radicado = this.itemAEliminar.radicado || ('#' + id);

            this.eliminando = true;
            try {
                const res = await fetch(`${API.correspondencia}/${id}`, {
                    method: "DELETE"
                });
                const data = await res.json().catch(() => ({}));

                if (!res.ok || data.exito === false) {
                    throw new Error(data.detail || data.mensaje || "Error al eliminar correspondencia.");
                }

                // Cerrar modal inmediatamente reseteando todas las banderas
                this.cancelarEliminar();

                // Eliminación optimista
                this.correspondencias = this.correspondencias.filter(c => c.id !== id);

                if (this.currentPage > this.totalPaginas) {
                    this.currentPage = Math.max(1, this.totalPaginas);
                }

                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "success",
                        title: "¡Eliminado!",
                        text: `El radicado ${radicado} fue eliminado correctamente.`,
                        timer: 2500,
                        showConfirmButton: false,
                        customClass: { popup: "swal-login-card" }
                    });
                }
            } catch (err) {
                console.error("Error al eliminar correspondencia:", err);
                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "error",
                        title: "Error",
                        text: err.message || "No se pudo eliminar la correspondencia.",
                        customClass: { popup: "swal-login-card" }
                    });
                } else {
                    alert(err.message || "No se pudo eliminar la correspondencia.");
                }
            } finally {
                this.eliminando = false;
            }
        },

        // ---------------------------------------------------
        // Modal Detalle (Ticket)
        // ---------------------------------------------------
        showDetalleModal: false,
        correspondenciaDetalle: null,

        verCorrespondencia(item) {
            this.correspondenciaDetalle = item;
            this.showDetalleModal = true;
        },

        cerrarDetalle() {
            this.correspondenciaDetalle = null;
            this.showDetalleModal = false;
        },

        // ---------------------------------------------------
        // Edición
        // ---------------------------------------------------
        showEditModal: false,
        guardandoEdicion: false,
        formEdit: {
            id: null,
            radicado: "",
            tipo_correspondencia: "",
            asunto: "",
            procedencia: "",
            destino: "",
            fecha_envio: ""
        },

        abrirModalEditar(item) {
            this.esSuperAdmin = checkEsSuperAdmin();
            this.formEdit = {
                id: item.id,
                radicado: item.radicado || "",
                tipo_correspondencia: item.tipo_correspondencia || "",
                asunto: item.asunto || "",
                procedencia: item.procedencia || "",
                destino: item.destino || "",
                fecha_envio: item.fecha_envio ? String(item.fecha_envio).split("T")[0] : ""
            };
            this.showEditModal = true;
        },

        cerrarModalEditar() {
            this.showEditModal = false;
            this.formEdit = {
                id: null,
                radicado: "",
                tipo_correspondencia: "",
                asunto: "",
                procedencia: "",
                destino: "",
                fecha_envio: ""
            };
        },

        async guardarEdicion() {
            if (!this.formEdit.id) return;
            if (!this.formEdit.tipo_correspondencia || !this.formEdit.asunto || !this.formEdit.procedencia || !this.formEdit.destino) {
                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "warning",
                        title: "Campos requeridos",
                        text: "Por favor completa todos los campos del formulario.",
                        customClass: { popup: "swal-login-card" }
                    });
                }
                return;
            }

            this.guardandoEdicion = true;
            try {
                const payload = {
                    tipo_correspondencia: this.formEdit.tipo_correspondencia,
                    asunto: this.formEdit.asunto.trim(),
                    procedencia: this.formEdit.procedencia.trim(),
                    destino: this.formEdit.destino.trim(),
                    radicado: this.formEdit.radicado ? this.formEdit.radicado.trim() : undefined,
                    fecha_envio: this.formEdit.fecha_envio || undefined
                };

                const res = await fetch(`${API.correspondencia}/${this.formEdit.id}`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json().catch(() => ({}));

                if (!res.ok || data.exito === false) {
                    throw new Error(data.detail || data.mensaje || "Error al actualizar la correspondencia.");
                }

                // Actualizar item en memoria
                const idx = this.correspondencias.findIndex(c => c.id === this.formEdit.id);
                if (idx !== -1) {
                    this.correspondencias[idx] = {
                        ...this.correspondencias[idx],
                        ...payload
                    };
                }

                this.showEditModal = false;

                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "success",
                        title: "¡Actualizado!",
                        text: "Correspondencia actualizada exitosamente.",
                        timer: 2200,
                        showConfirmButton: false,
                        customClass: { popup: "swal-login-card" }
                    });
                }
            } catch (err) {
                console.error("Error al actualizar correspondencia:", err);
                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "error",
                        title: "Error",
                        text: err.message || "No se pudo actualizar la correspondencia.",
                        customClass: { popup: "swal-login-card" }
                    });
                } else {
                    alert(err.message || "No se pudo actualizar.");
                }
            } finally {
                this.guardandoEdicion = false;
            }
        }
    };
}

// Alias de compatibilidad por si se llama corespondenciaTable o correspondenciaTable
window.corespondenciaTable = correspondenciaTable;
window.correspondenciaTable = correspondenciaTable;