/**
 * ============================================================================
 * vehiculos.js — Gestión y Consulta de Vehículos Registrados (Modal Global)
 * ============================================================================
 */

function vehiculoManager() {
    return {
        isOpen: false,
        cargando: false,
        guardando: false,
        mensajeExito: "",
        mensajeError: "",

        // Modo edición
        editandoId: null,

        // Datos
        vehiculos: [],

        // Filtros y búsqueda
        search: "",

        // Paginación
        pageSize: 5,
        currentPage: 1,

        tiposVehiculo: ["Camioneta", "Camión", "Automóvil", "Motocicleta", "Volqueta", "Maquinaria", "Otro"],
        tiposDocAdjuntoVehiculo: [
            "SOAT",
            "Revisión Tecnomecánica",
            "Tarjeta de Propiedad",
            "Póliza Contractual / Extracontractual",
            "Tarjeta de Operación",
            "Otro documento"
        ],

        // Formulario (registro o edición)
        form: {
            tipo: "Camioneta",
            placa: "",
            conductor: "",
            licencia_doc: "",
            licencia_url: null,
            documentos: [
                { tipo_doc: "SOAT", nombre_archivo: "" }
            ]
        },

        async init() {
            // Escuchar evento global para abrir el modal desde el sidebar o cualquier botón
            window.addEventListener("open-vehiculos-modal", () => {
                this.abrirModal();
            });

            this.$watch("search", () => (this.currentPage = 1));
        },

        async abrirModal() {
            this.isOpen = true;
            this.limpiarMensajes();
            this.cancelarEdicion();
            await this.cargarVehiculos();
        },

        cerrarModal() {
            this.isOpen = false;
            this.cancelarEdicion();
            this.limpiarMensajes();
        },

        async cargarVehiculos() {
            this.cargando = true;
            try {
                const res = await fetch(`${API.vehiculos}/`);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                const lista = Array.isArray(data) ? data : (data.datos || data.data || []);
                this.vehiculos = lista.map(v => {
                    const docs = Array.isArray(v.documentos) && v.documentos.length > 0 
                        ? v.documentos 
                        : (Array.isArray(v.documentos_ids) ? v.documentos_ids : []);

                    let licDoc = v.licencia_doc || v.licencia || "";
                    if (!licDoc && docs.length > 0) {
                        const licEnDocs = docs.find(d => String(d.tipo_doc || d.tipo || '').toLowerCase().includes('licencia'));
                        if (licEnDocs) {
                            licDoc = licEnDocs.nom_documento || licEnDocs.nombre_archivo || "";
                        }
                    }

                    return {
                        id: v.id,
                        tipo: v.tipo || "Camioneta",
                        placa: (v.placa || "").toUpperCase().trim(),
                        conductor: v.conductor || "",
                        licencia_doc: licDoc,
                        documentos: docs
                    };
                });
            } catch (err) {
                console.error("Error al cargar vehículos:", err);
                this.vehiculos = [];
            } finally {
                this.cargando = false;
            }
        },

        abrirDocumento(doc) {
            if (!doc) return;
            let filename = typeof doc === "string" ? doc : (doc.url_acceso || doc.nom_documento || doc.nombre_archivo || "");
            if (!filename) return;
            if (filename.startsWith("http://") || filename.startsWith("https://")) {
                window.open(filename, "_blank");
                return;
            }
            if (filename.startsWith("/uploads/")) {
                window.open(`${API.base}${filename}`, "_blank");
                return;
            }
            window.open(`${API.base}/uploads/documentos/vehiculos/${filename}`, "_blank");
        },

        get totalVehiculos() {
            return this.vehiculos.length;
        },

        // ---------------------------------------------------
        // Filtros y Tabla
        // ---------------------------------------------------
        get vehiculosFiltrados() {
            const text = this.search.trim().toLowerCase();
            return this.vehiculos.filter(v => {
                if (!text) return true;
                return (
                    (v.placa || "").toLowerCase().includes(text) ||
                    (v.tipo || "").toLowerCase().includes(text) ||
                    (v.conductor || "").toLowerCase().includes(text) ||
                    String(v.id).includes(text)
                );
            });
        },

        get totalPaginas() {
            return Math.max(1, Math.ceil(this.vehiculosFiltrados.length / this.pageSize));
        },

        get vehiculosPagina() {
            const start = (this.currentPage - 1) * this.pageSize;
            return this.vehiculosFiltrados.slice(start, start + this.pageSize);
        },

        get rangoMostrado() {
            if (this.vehiculosFiltrados.length === 0) return "0 de 0";
            const start = (this.currentPage - 1) * this.pageSize + 1;
            const end = Math.min(this.currentPage * this.pageSize, this.vehiculosFiltrados.length);
            return `${start}–${end} de ${this.vehiculosFiltrados.length}`;
        },

        resetPage() {
            this.currentPage = 1;
        },

        goToPage(page) {
            if (page >= 1 && page <= this.totalPaginas) {
                this.currentPage = page;
            }
        },

        // ---------------------------------------------------
        // Documentos y archivos
        // ---------------------------------------------------
        addDocumento() {
            this.form.documentos.push({
                tipo_doc: "Revisión Tecnomecánica",
                nombre_archivo: ""
            });
        },

        removeDocumento(idx) {
            if (this.form.documentos.length > 1) {
                this.form.documentos.splice(idx, 1);
            } else {
                this.form.documentos[0].nombre_archivo = "";
            }
        },

        async uploadArchivo(file, tipoDocumento = "general") {
            if (!file) return null;
            const formData = new FormData();
            formData.append("file", file);
            formData.append("tipo_documento", tipoDocumento);

            try {
                const res = await fetch(`${API.solicitudes}/subir-documento/`, {
                    method: "POST",
                    body: formData
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                return {
                    nombre_archivo: data.nombre_archivo,
                    url_documento: data.url_documento,
                    nombre_original: data.nombre_original || file.name
                };
            } catch (error) {
                console.warn("⚠️ No se pudo subir el archivo, usando nombre local:", error.message);
                return {
                    nombre_archivo: file.name,
                    url_documento: null,
                    nombre_original: file.name
                };
            }
        },

        async handleDocumentoFile(event, idx) {
            const file = event.target.files[0];
            if (file && this.form.documentos[idx]) {
                const tipo = this.form.documentos[idx].tipo_doc || "soat";
                const uploaded = await this.uploadArchivo(file, tipo);
                if (uploaded) {
                    this.form.documentos[idx].nombre_archivo = uploaded.nombre_archivo;
                    this.form.documentos[idx].url_documento = uploaded.url_documento;
                }
            }
        },

        async handleLicenciaFile(event) {
            const file = event.target.files[0];
            if (file) {
                const uploaded = await this.uploadArchivo(file, "licencia");
                if (uploaded) {
                    this.form.licencia_doc = uploaded.nombre_archivo;
                    this.form.licencia_url = uploaded.url_documento;
                }
            }
        },

        removeLicencia() {
            this.form.licencia_doc = "";
            this.form.licencia_url = null;
        },

        abrirDocumento(doc) {
            const nombre = typeof doc === 'string' ? doc : (doc.url || doc.nombre_archivo || doc.nom_documento || '');
            if (!nombre) return;
            if (nombre.startsWith('http://') || nombre.startsWith('https://') || nombre.startsWith('blob:') || nombre.startsWith('data:')) {
                window.open(nombre, '_blank');
            } else {
                window.open(`${API.base}/uploads/${nombre}`, '_blank');
            }
        },

        // ---------------------------------------------------
        // Acciones: Crear, Editar, Eliminar
        // ---------------------------------------------------
        iniciarEdicion(v) {
            this.editandoId = v.id;
            this.form.tipo = v.tipo || "Camioneta";
            this.form.placa = (v.placa || "").toUpperCase().trim();
            this.form.conductor = v.conductor || "";
            this.form.licencia_doc = v.licencia_doc || "";
            this.form.licencia_url = v.licencia_url || null;
            this.form.documentos = Array.isArray(v.documentos) && v.documentos.length > 0
                ? v.documentos.map(d => ({
                    tipo_doc: d.tipo_doc || d.tipo || "SOAT",
                    nombre_archivo: d.nombre_archivo || d.nom_documento || ""
                }))
                : [{ tipo_doc: "SOAT", nombre_archivo: "" }];

            this.limpiarMensajes();
            const input = document.getElementById("inputPlacaVehiculoModal");
            if (input) input.focus();
        },

        cancelarEdicion() {
            this.editandoId = null;
            this.form = {
                tipo: "Camioneta",
                placa: "",
                conductor: "",
                licencia_doc: "",
                licencia_url: null,
                documentos: [{ tipo_doc: "SOAT", nombre_archivo: "" }]
            };
        },

        limpiarMensajes() {
            this.mensajeExito = "";
            this.mensajeError = "";
        },

        async guardarVehiculo() {
            this.limpiarMensajes();

            const placa = (this.form.placa || "").toUpperCase().trim();
            const tipo = this.form.tipo || "Camioneta";
            const conductor = (this.form.conductor || "").trim();
            const licencia_doc = (this.form.licencia_doc || "").trim();

            if (!placa) {
                this.mensajeError = "Por favor ingresa la placa del vehículo.";
                return;
            }

            const docsValidos = (this.form.documentos || [])
                .filter(d => d.nombre_archivo && d.nombre_archivo.trim())
                .map(d => ({
                    tipo_doc: d.tipo_doc,
                    nom_documento: d.nombre_archivo.trim(),
                    nombre_archivo: d.nombre_archivo.trim()
                }));

            const payload = {
                tipo: tipo,
                placa: placa,
                conductor: conductor,
                licencia_doc: licencia_doc,
                documentos: docsValidos
            };

            this.guardando = true;

            try {
                if (this.editandoId) {
                    // Actualizar (PATCH /api/v1/vehiculos/{id})
                    const res = await fetch(`${API.vehiculos}/${this.editandoId}`, {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });

                    if (!res.ok) {
                        const err = await res.json().catch(() => ({}));
                        throw new Error(err.detail || err.mensaje || `HTTP ${res.status}`);
                    }

                    this.mensajeExito = `Vehículo ${placa} actualizado con éxito.`;
                } else {
                    // Crear (POST /api/v1/vehiculos/)
                    const res = await fetch(`${API.vehiculos}/`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });

                    if (!res.ok) {
                        const err = await res.json().catch(() => ({}));
                        throw new Error(err.detail || err.mensaje || `HTTP ${res.status}`);
                    }

                    this.mensajeExito = `Vehículo ${placa} registrado con éxito.`;
                }

                this.cancelarEdicion();
                await this.cargarVehiculos();

                setTimeout(() => {
                    this.limpiarMensajes();
                }, 3500);

            } catch (err) {
                console.error("Error al guardar vehículo:", err);
                this.mensajeError = `Error: ${err.message}`;
            } finally {
                this.guardando = false;
            }
        },

        async eliminarVehiculo(id, placa) {
            if (!confirm(`¿Estás seguro de que deseas eliminar el vehículo ${placa || ''}?`)) {
                return;
            }

            this.limpiarMensajes();
            this.cargando = true;

            try {
                const res = await fetch(`${API.vehiculos}/${id}`, {
                    method: "DELETE"
                });

                if (!res.ok) {
                    const err = await res.json().catch(() => ({}));
                    throw new Error(err.detail || err.mensaje || `HTTP ${res.status}`);
                }

                this.mensajeExito = `Vehículo ${placa} eliminado con éxito.`;
                if (this.editandoId === id) this.cancelarEdicion();
                await this.cargarVehiculos();

                setTimeout(() => {
                    this.limpiarMensajes();
                }, 3500);

            } catch (err) {
                console.error("Error al eliminar vehículo:", err);
                this.mensajeError = `Error al eliminar: ${err.message}`;
            } finally {
                this.cargando = false;
            }
        }
    };
}
