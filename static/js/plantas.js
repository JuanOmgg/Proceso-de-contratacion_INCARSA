function plantasManager() {
    return {
        isOpen: false,
        cargando: false,
        guardando: false,
        mensajeExito: "",
        mensajeError: "",

        isModuloMantenimiento(mod) {
            return window.isModuloMantenimiento ? window.isModuloMantenimiento(mod || 'plantas') : false;
        },
        get estadoMantenimiento() {
            return (typeof Alpine !== 'undefined' && Alpine.store && Alpine.store('mantenimiento'))
                ? Alpine.store('mantenimiento')
                : (window.estadoMantenimiento || {});
        },

        // Modo edición
        editandoId: null,

        // Datos
        empresas: [],
        plantas: [],

        // Contadores
        incarsa: 0,
        uniminas: 0,
        carboinsa: 0,
        milpa: 0,

        // Filtros y búsqueda
        search: "",
        busqueda: "",
        filtroEmpresa: "",

        // Paginación
        pageSize: 5,
        currentPage: 1,

        // Formulario (registro o edición)
        form: {
            empresa: "",
            nombre: ""
        },
        nuevaPlanta: {
            id_empresa: "",
            nombre: ""
        },

        async init() {
            // Escuchar evento global para abrir el modal desde cualquier sidebar o botón
            window.addEventListener("open-plantas-modal", () => {
                this.abrirModal();
            });

            this.$watch("search", () => (this.currentPage = 1));
            this.$watch("busqueda", () => (this.currentPage = 1));
            this.$watch("filtroEmpresa", () => (this.currentPage = 1));
        },

        async abrirModal() {
            this.isOpen = true;
            this.limpiarMensajes();
            this.cancelarEdicion();
            await this.cargarTodo();
        },

        cerrarModal() {
            this.isOpen = false;
            this.cancelarEdicion();
            this.limpiarMensajes();
        },

        async cargarTodo() {
            this.cargando = true;
            try {
                await Promise.allSettled([
                    this.cargarEmpresas(),
                    this.cargarPlantas()
                ]);
                this.actualizarContadores();
            } finally {
                this.cargando = false;
            }
        },

        getNombreEmpresa(id) {
            if (!id) return "";
            const emp = this.empresas.find(e => String(e.id) === String(id));
            return emp ? (emp.nombre || emp.nombre_empresa || "") : "";
        },

        getColorBadgeEmpresa(emp) {
            const nom = (typeof emp === "object" ? (emp.N_empresa || emp.nombre || "") : String(emp || "")).toLowerCase();
            if (nom.includes("incarsa") || nom === "1") return "bg-cyan-400";
            if (nom.includes("uniminas") || nom === "4") return "bg-emerald-400";
            if (nom.includes("carboinsa") || nom === "3") return "bg-amber-400";
            if (nom.includes("milpa") || nom === "2") return "bg-purple-400";
            return "bg-blue-400";
        },

        async cargarEmpresas() {
            try {
                const res = await fetch(`${API.empresas}/getall`);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                this.empresas = Array.isArray(data) ? data : (data.datos || []);
            } catch (err) {
                console.error("Error al cargar empresas:", err);
                this.empresas = [];
            }
        },

        async cargarPlantas() {
            try {
                const res = await fetch(`${API.plantas}/getall`);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                const lista = Array.isArray(data) ? data : (data.datos || []);
                this.plantas = lista.map(p => {
                    const empNom = p.N_empresa || p.empresa_nombre || this.getNombreEmpresa(p.id_empresa) || "";
                    return {
                        ...p,
                        N_empresa: empNom,
                        empresa_nombre: empNom,
                        nombre: p.nombre || ""
                    };
                });
            } catch (err) {
                console.error("Error al cargar plantas:", err);
                this.plantas = [];
            }
        },

        actualizarContadores() {
            const getCount = (id, nombre) => {
                return this.plantas.filter(p =>
                    p.id_empresa === id ||
                    (p.N_empresa && p.N_empresa.toLowerCase().includes(nombre.toLowerCase()))
                ).length;
            };

            this.incarsa = getCount(1, "incarsa");
            this.milpa = getCount(2, "milpa");
            this.carboinsa = getCount(3, "carboinsa");
            this.uniminas = getCount(4, "uniminas");
        },

        get totalPlantas() {
            return this.plantas.length || (this.incarsa + this.milpa + this.carboinsa + this.uniminas);
        },

        // ---------------------------------------------------
        // Filtros y Tabla
        // ---------------------------------------------------
        get plantasFiltradas() {
            const text = (this.search || this.busqueda || "").trim().toLowerCase();
            return this.plantas.filter(p => {
                const empNom = p.N_empresa || p.empresa_nombre || this.getNombreEmpresa(p.id_empresa) || "";
                const matchTexto = !text ||
                    (p.nombre || "").toLowerCase().includes(text) ||
                    empNom.toLowerCase().includes(text) ||
                    String(p.id).includes(text);

                const matchEmpresa = !this.filtroEmpresa ||
                    empNom.toLowerCase() === this.filtroEmpresa.toLowerCase() ||
                    String(p.id_empresa) === String(this.filtroEmpresa) ||
                    (this.empresas.find(e => String(e.id) === String(this.filtroEmpresa))?.nombre?.toLowerCase() === empNom.toLowerCase());

                return matchTexto && matchEmpresa;
            });
        },

        get totalPaginas() {
            return Math.max(1, Math.ceil(this.plantasFiltradas.length / this.pageSize));
        },

        get plantasPagina() {
            const start = (this.currentPage - 1) * this.pageSize;
            return this.plantasFiltradas.slice(start, start + this.pageSize);
        },

        get rangoMostrado() {
            if (this.plantasFiltradas.length === 0) return "0 de 0";
            const start = (this.currentPage - 1) * this.pageSize + 1;
            const end = Math.min(this.currentPage * this.pageSize, this.plantasFiltradas.length);
            return `${start}–${end} de ${this.plantasFiltradas.length}`;
        },

        // ---------------------------------------------------
        // Registro y Edición de Planta
        // ---------------------------------------------------
        iniciarEdicion(planta) {
            this.limpiarMensajes();
            this.editandoId = planta.id;

            // Determinar ID y nombre de empresa
            let empId = planta.id_empresa;
            let empNombre = planta.N_empresa || "";
            if (!empId && empNombre) {
                const match = this.empresas.find(e => e.nombre.toLowerCase() === empNombre.toLowerCase());
                if (match) empId = match.id;
            } else if (empId && !empNombre) {
                const match = this.empresas.find(e => e.id === empId);
                if (match) empNombre = match.nombre;
            }

            this.form = {
                empresa: empNombre || String(empId || ""),
                nombre: planta.nombre || ""
            };

            this.nuevaPlanta = {
                id_empresa: empId || "",
                nombre: planta.nombre || ""
            };

            // Enfocar input
            const input = document.getElementById("inputNombrePlanta");
            if (input) input.focus();
        },

        cancelarEdicion() {
            this.editandoId = null;
            this.limpiarFormulario();
        },

        async guardarPlanta() {
            this.limpiarMensajes();

            const empVal = (this.form.empresa || this.nuevaPlanta.id_empresa || "").toString().trim();
            const nomVal = (this.form.nombre || this.nuevaPlanta.nombre || "").toString().trim();

            if (!empVal) {
                this.mensajeError = "Por favor selecciona una empresa.";
                return;
            }

            if (!nomVal) {
                this.mensajeError = "El nombre de la planta o zona es requerido.";
                return;
            }

            // Resolver ID numérico de empresa
            let empId = empVal;
            if (isNaN(Number(empVal))) {
                const match = this.empresas.find(e => e.nombre.toLowerCase() === empVal.toLowerCase());
                if (match) empId = match.id;
            }

            this.guardando = true;
            try {
                const payload = {
                    id_empresa: Number(empId),
                    nombre: nomVal
                };

                if (this.editandoId) {
                    // Modo actualización (PATCH)
                    const res = await fetch(`${API.plantas}/${this.editandoId}`, {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });

                    const data = await res.json();
                    if (!res.ok) {
                        throw new Error(data.detail || data.mensaje || "Error al actualizar la planta.");
                    }

                    this.mensajeExito = "¡Planta actualizada exitosamente!";
                    this.cancelarEdicion();
                } else {
                    // Modo creación (POST)
                    const res = await fetch(`${API.plantas}/`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });

                    const data = await res.json();
                    if (!res.ok || !data.exito) {
                        throw new Error(data.detail || data.mensaje || "Error al crear la planta.");
                    }

                    this.mensajeExito = "¡Planta registrada exitosamente!";
                    this.limpiarFormulario();
                }

                await this.cargarTodo();

                setTimeout(() => {
                    this.mensajeExito = "";
                }, 4000);

            } catch (err) {
                console.error("Error al guardar planta:", err);
                this.mensajeError = err.message || "Error al conectar con el servidor.";
            } finally {
                this.guardando = false;
            }
        },

        // ---------------------------------------------------
        // Eliminación de planta
        // ---------------------------------------------------
        async eliminarPlanta(id, nombre) {
            if (!confirm(`¿Estás seguro de eliminar la planta "${nombre || id}"?`)) return;

            try {
                const res = await fetch(`${API.plantas}/${id}`, {
                    method: "DELETE"
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || data.mensaje || "Error al eliminar.");
                }
                this.mensajeExito = "Planta eliminada con éxito.";
                if (this.editandoId === id) this.cancelarEdicion();
                await this.cargarTodo();
                if (this.currentPage > this.totalPaginas) this.currentPage = this.totalPaginas;

                setTimeout(() => {
                    this.mensajeExito = "";
                }, 3000);
            } catch (err) {
                console.error("Error al eliminar planta:", err);
                this.mensajeError = err.message || "No se pudo eliminar la planta.";
            }
        },

        // ---------------------------------------------------
        // Helpers
        // ---------------------------------------------------
        limpiarFormulario() {
            this.form = {
                empresa: "",
                nombre: ""
            };
            this.nuevaPlanta = {
                id_empresa: "",
                nombre: ""
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

// Alias compatible para plantillas que usan plantaManager() en singular
window.plantaManager = plantasManager;