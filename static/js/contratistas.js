function contratistaManager() {
    return {
        isOpen: false,
        cargando: false,
        guardando: false,
        mensajeExito: "",
        mensajeError: "",

        isModuloMantenimiento(mod) {
            return window.isModuloMantenimiento ? window.isModuloMantenimiento(mod || 'contratistas') : false;
        },
        get estadoMantenimiento() {
            return (typeof Alpine !== 'undefined' && Alpine.store && Alpine.store('mantenimiento'))
                ? Alpine.store('mantenimiento')
                : (window.estadoMantenimiento || {});
        },

        // Modo edición
        editandoId: null,

        // Datos
        contratistas: [],

        // Filtros y búsqueda
        search: "",

        // Paginación
        pageSize: 5,
        currentPage: 1,

        // Formulario (registro o edición)
        form: {
            nombre: "",
            nit: "",
            observacion: ""
        },

        async init() {
            // Escuchar evento global para abrir el modal desde el sidebar o cualquier botón
            window.addEventListener("open-contratistas-modal", () => {
                this.abrirModal();
            });

            this.$watch("search", () => (this.currentPage = 1));
        },

        async abrirModal() {
            this.isOpen = true;
            this.limpiarMensajes();
            this.cancelarEdicion();
            await this.cargarContratistas();
        },

        cerrarModal() {
            this.isOpen = false;
            this.cancelarEdicion();
            this.limpiarMensajes();
        },

        async cargarContratistas() {
            this.cargando = true;
            try {
                const res = await fetch(`${API.contratistas}/`);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                this.contratistas = Array.isArray(data) ? data : (data.data || data.datos || []);
            } catch (err) {
                console.error("Error al cargar empresas contratistas:", err);
                this.contratistas = [];
            } finally {
                this.cargando = false;
            }
        },

        get totalContratistas() {
            return this.contratistas.length;
        },

        // ---------------------------------------------------
        // Filtros y Tabla
        // ---------------------------------------------------
        get contratistasFiltrados() {
            const text = this.search.trim().toLowerCase();
            return this.contratistas.filter(c => {
                if (!text) return true;
                return (
                    (c.nombre || "").toLowerCase().includes(text) ||
                    (c.nit || "").toLowerCase().includes(text) ||
                    (c.observacion || "").toLowerCase().includes(text) ||
                    String(c.id).includes(text)
                );
            });
        },

        get totalPaginas() {
            return Math.max(1, Math.ceil(this.contratistasFiltrados.length / this.pageSize));
        },

        get contratistasPagina() {
            const start = (this.currentPage - 1) * this.pageSize;
            return this.contratistasFiltrados.slice(start, start + this.pageSize);
        },

        get rangoMostrado() {
            if (this.contratistasFiltrados.length === 0) return "0 de 0";
            const start = (this.currentPage - 1) * this.pageSize + 1;
            const end = Math.min(this.currentPage * this.pageSize, this.contratistasFiltrados.length);
            return `${start}–${end} de ${this.contratistasFiltrados.length}`;
        },

        // ---------------------------------------------------
        // Registro y Edición de Contratista
        // ---------------------------------------------------
        iniciarEdicion(contratista) {
            this.limpiarMensajes();
            this.editandoId = contratista.id;
            this.form = {
                nombre: contratista.nombre || "",
                nit: contratista.nit || "",
                observacion: contratista.observacion || ""
            };

            const input = document.getElementById("inputNombreContratista");
            if (input) input.focus();
        },

        cancelarEdicion() {
            this.editandoId = null;
            this.limpiarFormulario();
        },

        async guardarContratista() {
            this.limpiarMensajes();

            const nombre = this.form.nombre.trim();
            const nit = this.form.nit.trim();

            if (!nombre) {
                this.mensajeError = "El nombre de la empresa contratista es obligatorio.";
                return;
            }

            if (!nit) {
                this.mensajeError = "El NIT de la empresa contratista es obligatorio.";
                return;
            }

            if (!/^\d+$/.test(nit)) {
                this.mensajeError = "El NIT debe contener únicamente números.";
                return;
            }

            // Validar nombre único
            const existeNombre = this.contratistas.find(c =>
                String(c.nombre || "").trim().toLowerCase() === nombre.toLowerCase() &&
                c.id !== this.editandoId
            );
            if (existeNombre) {
                this.mensajeError = `Ya existe otra empresa contratista con el nombre "${nombre}".`;
                return;
            }

            // Validar NIT único
            const existeNit = this.contratistas.find(c =>
                String(c.nit || "").trim() === nit &&
                c.id !== this.editandoId
            );
            if (existeNit) {
                this.mensajeError = `El NIT ${nit} ya está registrado para la empresa "${existeNit.nombre}".`;
                return;
            }

            this.guardando = true;
            try {
                const payload = {
                    nombre: this.form.nombre.trim(),
                    nit: this.form.nit.trim(),
                    observacion: (this.form.observacion || "").trim()
                };

                if (this.editandoId) {
                    // Modo actualización (PATCH)
                    const res = await fetch(`${API.contratistas}/${this.editandoId}`, {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });

                    const data = await res.json();
                    if (!res.ok) {
                        throw new Error(data.detail || data.mensaje || "Error al actualizar.");
                    }

                    this.mensajeExito = "¡Empresa contratista actualizada exitosamente!";
                    this.cancelarEdicion();
                } else {
                    // Modo creación (POST)
                    const res = await fetch(API.contratistas, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });

                    const data = await res.json();
                    if (!res.ok) {
                        throw new Error(data.detail || data.mensaje || "Error al crear.");
                    }

                    this.mensajeExito = "¡Empresa contratista registrada exitosamente!";
                    this.limpiarFormulario();
                }

                await this.cargarContratistas();

                setTimeout(() => {
                    this.mensajeExito = "";
                }, 4000);

            } catch (err) {
                console.error("Error al guardar empresa contratista:", err);
                this.mensajeError = err.message || "Error al conectar con el servidor.";
            } finally {
                this.guardando = false;
            }
        },

        // ---------------------------------------------------
        // Eliminación de Contratista
        // ---------------------------------------------------
        async eliminarContratista(id, nombre) {
            if (!confirm(`¿Estás seguro de eliminar la empresa contratista "${nombre || id}"?`)) return;

            try {
                const res = await fetch(`${API.contratistas}/${id}`, {
                    method: "DELETE"
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || data.mensaje || "Error al eliminar.");
                }

                this.mensajeExito = "Empresa contratista eliminada con éxito.";
                if (this.editandoId === id) this.cancelarEdicion();
                await this.cargarContratistas();
                if (this.currentPage > this.totalPaginas) this.currentPage = this.totalPaginas;

                setTimeout(() => {
                    this.mensajeExito = "";
                }, 3000);
            } catch (err) {
                console.error("Error al eliminar empresa contratista:", err);
                this.mensajeError = err.message || "No se pudo eliminar la empresa contratista.";
            }
        },

        // ---------------------------------------------------
        // Helpers
        // ---------------------------------------------------
        limpiarFormulario() {
            this.form = {
                nombre: "",
                nit: "",
                observacion: ""
            };
        },

        limpiarMensajes() {
            this.mensajeExito = "";
            this.mensajeError = "";
        },

        goToPage(n) {
            if (n >= 1 && n <= this.totalPaginas) this.currentPage = n;
        },

        resetPage() {
            this.currentPage = 1;
        }
    };
}