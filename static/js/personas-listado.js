/**
 * personas-listado.js
 * Componente Alpine.js para la gestión de Personas (trabajadores / contratistas):
 * - Listado con búsqueda reactiva, filtro por cargo y paginación.
 * - Conteo de métricas.
 * - Modal de detalle completo con visualización de documentos y observaciones.
 * - Modal para crear y editar personas conectado al backend.
 * - Eliminación con confirmación visual y soporte REST.
 */

function personasTable() {
  return {
    // ---------------------------------------------------
    // Estado y Datos
    // ---------------------------------------------------
    personas: [],
    cargando: true,

    // Filtros y búsqueda
    search: "",
    filtroCargo: "",

    // Paginación
    currentPage: 1,
    pageSize: 8,

    // Modal de Detalle
    showDetailModal: false,
    personaDetalle: null,

    // Modal de Documentos
    showDocsModal: false,
    personaDocs: null,

    tiposDocPersona: [
      "ARL",
      "Cédula de Ciudadanía",
      "Certificado de Alturas",
      "Examen Médico Ocupacional",
      "Certificado de Espacios Confinados",
      "EPS / Seguridad Social",
      "Hoja de Vida / Certificación",
      "Soporte de GESCO",
      "Otro documento"
    ],

    // Modal de Creación / Edición
    showFormModal: false,
    editandoId: null,
    guardando: false,
    mensajeExito: "",
    mensajeError: "",
    form: {
      nombre: "",
      apellido: "",
      tipo_doc: "CC",
      identificacion: "",
      cargo: "",
      observacion: "",
      documentos: [
        { tipo_doc: "ARL (Afiliación / Pago)", nombre_archivo: "" }
      ]
    },

    // Modal de Eliminación
    showDeleteModal: false,
    personaEliminar: null,

    // ---------------------------------------------------
    // Inicialización
    // ---------------------------------------------------
    async init() {
      await this.getPersonas();

      this.$watch("search", () => (this.currentPage = 1));
      this.$watch("filtroCargo", () => (this.currentPage = 1));
    },

    notificarCambio() {
      window.dispatchEvent(new CustomEvent("personas-updated", { detail: this.personas }));
    },

    // ---------------------------------------------------
    // Carga de Datos desde Backend
    // ---------------------------------------------------
    async getPersonas() {
      this.cargando = true;
      try {
        const res = await fetch(`${API.personas}/getAll`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const lista = data.datos_person || data.datos || data.data || (Array.isArray(data) ? data : []);
        
        this.personas = lista.map(p => this.normalizarPersona(p));
        this.notificarCambio();
      } catch (error) {
        console.warn("Error al cargar personas desde backend:", error.message);
        if (this.personas.length === 0) {
          this.personas = [];
        }
      } finally {
        this.cargando = false;
      }
    },

    normalizarPersona(p) {
      return {
        id: p.id || p.id_persona,
        nombre: p.nombre || p.nombres || "",
        apellido: p.apellido || p.apellidos || "",
        tipo_doc: p.tipo_doc || p.tipoDoc || "CC",
        identificacion: String(p.identificacion || p.numDoc || p.documento || ""),
        cargo: p.cargo || "General",
        observacion: p.observacion || "",
        documentos: Array.isArray(p.documentos) ? p.documentos : (p.documentos_ids || []),
        fecha_creacion: p.fecha_creacion || p.created_at || p.creado_en || null
      };
    },

    // ---------------------------------------------------
    // Getters y Métricas
    // ---------------------------------------------------
    get totalPersonas() {
      return this.personas.length;
    },

    get totalConDocumentos() {
      return this.personas.filter(p => p.documentos && p.documentos.length > 0).length;
    },

    get cargosDisponibles() {
      const set = new Set();
      this.personas.forEach(p => {
        if (p.cargo && p.cargo.trim()) set.add(p.cargo.trim());
      });
      return Array.from(set).sort();
    },

    get personasFiltrados() {
      const q = this.search.trim().toLowerCase();
      return this.personas.filter(p => {
        const nombreCompleto = `${p.nombre} ${p.apellido}`.toLowerCase();
        const matchQuery = !q ||
          nombreCompleto.includes(q) ||
          p.identificacion.toLowerCase().includes(q) ||
          (p.cargo && p.cargo.toLowerCase().includes(q)) ||
          (p.observacion && p.observacion.toLowerCase().includes(q));

        const matchCargo = !this.filtroCargo || p.cargo === this.filtroCargo;

        return matchQuery && matchCargo;
      });
    },

    get totalPaginas() {
      return Math.max(1, Math.ceil(this.personasFiltrados.length / this.pageSize));
    },

    get personasPagina() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.personasFiltrados.slice(start, start + this.pageSize);
    },

    get rangoMostrado() {
      if (this.personasFiltrados.length === 0) return "0 de 0";
      const start = (this.currentPage - 1) * this.pageSize + 1;
      const end = Math.min(this.currentPage * this.pageSize, this.personasFiltrados.length);
      return `${start}–${end} de ${this.personasFiltrados.length}`;
    },

    // ---------------------------------------------------
    // Helpers
    // ---------------------------------------------------
    formatearFecha(fechaStr) {
      if (!fechaStr) return "No registrada";
      try {
        const strLimpio = typeof fechaStr === "string" ? fechaStr.replace(" ", "T") : fechaStr;
        const fecha = new Date(strLimpio);
        if (isNaN(fecha.getTime())) return fechaStr;
        return fecha.toLocaleDateString("es-CO", {
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit"
        });
      } catch {
        return fechaStr;
      }
    },

    // ---------------------------------------------------
    // Paginación
    // ---------------------------------------------------
    resetPage() {
      this.currentPage = 1;
    },
    goToPage(n) {
      if (n >= 1 && n <= this.totalPaginas) this.currentPage = n;
    },
    limpiarFiltros() {
      this.search = "";
      this.filtroCargo = "";
      this.currentPage = 1;
    },

    // ---------------------------------------------------
    // Modal Detalle
    // ---------------------------------------------------
    verPersona(p) {
      this.personaDetalle = p;
      this.showDetailModal = true;
    },
    cerrarDetalle() {
      this.showDetailModal = false;
      this.personaDetalle = null;
    },

    // ---------------------------------------------------
    // Modal Documentos
    // ---------------------------------------------------
    abrirModalDocs(p) {
      this.personaDocs = p;
      this.showDocsModal = true;
    },
    cerrarModalDocs() {
      this.showDocsModal = false;
      this.personaDocs = null;
    },
    abrirDocumento(doc) {
      const rutaOArchivo = typeof doc === 'string' ? doc : (doc.url_documento || doc.url || doc.nombre_archivo || doc.nom_documento || '');
      if (!rutaOArchivo) return;
      if (rutaOArchivo.startsWith('http://') || rutaOArchivo.startsWith('https://') || rutaOArchivo.startsWith('blob:') || rutaOArchivo.startsWith('data:')) {
        window.open(rutaOArchivo, '_blank');
      } else if (rutaOArchivo.startsWith('/uploads/')) {
        window.open(`${API.base}${rutaOArchivo}`, '_blank');
      } else {
        window.open(`${API.base}/uploads/${rutaOArchivo}`, '_blank');
      }
    },

    // ---------------------------------------------------
    // Gestión de Documentos en Formulario
    // ---------------------------------------------------
    addDocumento() {
      this.form.documentos.push({
        tipo_doc: "Certificado de Alturas",
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

      const MAX_SIZE_MB = 10;
      const MAX_BYTES = MAX_SIZE_MB * 1024 * 1024;
      const extension = (file.name.split('.').pop() || '').toLowerCase().trim();
      const formatosPermitidos = ['pdf', 'png', 'jpg', 'jpeg'];

      // 1. Validación Frontend: Archivo vacío
      if (file.size === 0) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Archivo vacío',
            text: 'El archivo seleccionado está vacío (0 bytes).',
            confirmButtonColor: '#f59e0b',
            confirmButtonText: 'Entendido'
          });
        } else {
          alert('El archivo seleccionado está vacío (0 bytes).');
        }
        return null;
      }

      // 2. Validación Frontend: Extensión permitida
      if (!formatosPermitidos.includes(extension)) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'error',
            title: 'Formato no permitido',
            html: `La extensión <b>.${extension}</b> no está permitida.<br>Solo se admiten documentos en formato <b>PDF, PNG o JPG</b>.`,
            confirmButtonColor: '#ef4444',
            confirmButtonText: 'Entendido'
          });
        } else {
          alert(`Formato .${extension} no permitido. Solo se admiten PDF, PNG o JPG.`);
        }
        return null;
      }

      // 3. Validación Frontend: Tamaño máximo (10 MB)
      if (file.size > MAX_BYTES) {
        const tamanoMB = (file.size / (1024 * 1024)).toFixed(2);
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Tamaño excedido',
            html: `El archivo pesa <b>${tamanoMB} MB</b> y supera el límite de <b>${MAX_SIZE_MB} MB</b>.<br>Por favor comprímelo o sube un documento más liviano.`,
            confirmButtonColor: '#f59e0b',
            confirmButtonText: 'Entendido'
          });
        } else {
          alert(`El archivo pesa ${tamanoMB} MB y supera el límite de ${MAX_SIZE_MB} MB.`);
        }
        return null;
      }

      // 4. Envío al backend
      const formData = new FormData();
      formData.append("file", file);
      formData.append("tipo_documento", tipoDocumento);

      try {
        const res = await fetch(`${API.solicitudes}/subir-documento/`, {
          method: "POST",
          body: formData
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          const detalle = err.detail || `Error al procesar el archivo (${res.status})`;

          if (typeof Swal !== 'undefined') {
            Swal.fire({
              icon: 'error',
              title: 'Archivo rechazado por el servidor',
              text: detalle,
              confirmButtonColor: '#ef4444',
              confirmButtonText: 'Aceptar'
            });
          } else {
            alert(detalle);
          }
          return null;
        }

        const data = await res.json();

        if (typeof Swal !== 'undefined') {
          Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'success',
            title: 'Documento cargado correctamente',
            showConfirmButton: false,
            timer: 2500,
            timerProgressBar: true
          });
        }

        return {
          nombre_archivo: data.nombre_archivo,
          url_documento: data.url_documento,
          nombre_original: data.nombre_original || file.name
        };
      } catch (error) {
        console.error("❌ Error al subir archivo:", error);
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'error',
            title: 'Error de conexión',
            text: 'No fue posible conectarse con el servidor para subir el documento.',
            confirmButtonColor: '#ef4444',
            confirmButtonText: 'Cerrar'
          });
        }
        return null;
      }
    },

    async handleDocumentoFile(event, idx) {
      const file = event.target.files[0];
      if (file && this.form.documentos[idx]) {
        const tipo = this.form.documentos[idx].tipo_doc || "general";
        const uploaded = await this.uploadArchivo(file, tipo);
        if (uploaded) {
          this.form.documentos[idx].nombre_archivo = uploaded.nombre_archivo;
          this.form.documentos[idx].url_documento = uploaded.url_documento;
        } else {
          event.target.value = "";
          this.form.documentos[idx].nombre_archivo = "";
          this.form.documentos[idx].url_documento = null;
        }
      }
    },

    // ---------------------------------------------------
    // Modal Formulario Crear / Editar
    // ---------------------------------------------------
    abrirCrear() {
      this.editandoId = null;
      this.form = {
        nombre: "",
        apellido: "",
        tipo_doc: "CC",
        identificacion: "",
        cargo: "",
        observacion: "",
        documentos: [
          { tipo_doc: "ARL (Afiliación / Pago)", nombre_archivo: "" }
        ]
      };
      this.mensajeExito = "";
      this.mensajeError = "";
      this.showFormModal = true;
    },

    abrirEditar(p) {
      this.editandoId = p.id;
      const docs = Array.isArray(p.documentos) && p.documentos.length > 0
        ? p.documentos.map(d => ({
            tipo_doc: d.tipo_doc || d.tipo || "Documento",
            nombre_archivo: d.nombre_archivo || d.nom_documento || (typeof d === 'string' ? d : "")
          }))
        : [{ tipo_doc: "ARL (Afiliación / Pago)", nombre_archivo: "" }];

      this.form = {
        nombre: p.nombre,
        apellido: p.apellido,
        tipo_doc: p.tipo_doc || "CC",
        identificacion: p.identificacion,
        cargo: p.cargo,
        observacion: p.observacion || "",
        documentos: docs,
        fecha_creacion: p.fecha_creacion || null
      };
      this.mensajeExito = "";
      this.mensajeError = "";
      this.showFormModal = true;
    },

    cerrarForm() {
      this.showFormModal = false;
      this.editandoId = null;
      this.guardando = false;
    },

    async guardarPersona() {
      if (!this.form.nombre || !this.form.apellido || !this.form.identificacion) {
        this.mensajeError = "Por favor completa los nombres, apellidos y número de documento.";
        return;
      }

      this.guardando = true;
      this.mensajeExito = "";
      this.mensajeError = "";

      const docsValidos = (this.form.documentos || [])
        .filter(d => d.nombre_archivo && d.nombre_archivo.trim())
        .map(d => ({
          tipo_doc: d.tipo_doc || "Documento",
          nombre_archivo: d.nombre_archivo.trim()
        }));

      const payload = {
        nombre: this.form.nombre.trim(),
        apellido: this.form.apellido.trim(),
        tipo_doc: this.form.tipo_doc,
        identificacion: this.form.identificacion.trim(),
        cargo: this.form.cargo ? this.form.cargo.trim() : "General",
        observacion: this.form.observacion ? this.form.observacion.trim() : "",
        documentos_ids: docsValidos
      };

      try {
        if (this.editandoId) {
          // Modo Edición
          let url = `${API.personas}/${this.editandoId}`;
          let res = await fetch(url, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });

          // Fallback a PATCH si PUT no está habilitado
          if (!res.ok && res.status === 405) {
            res = await fetch(url, {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload)
            });
          }

          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || err.mensaje || `HTTP ${res.status}`);
          }

          // Actualización optimista local
          const idx = this.personas.findIndex(p => p.id === this.editandoId);
          if (idx > -1) {
            this.personas[idx] = { 
              ...this.personas[idx], 
              ...payload,
              documentos: docsValidos
            };
          }
          this.mensajeExito = "Persona y documentos actualizados con éxito.";
        } else {
          // Modo Creación
          const res = await fetch(`${API.personas}/create`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });

          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            let errorMsg = `HTTP ${res.status}`;
            if (typeof err.detail === "string") {
              errorMsg = err.detail;
            } else if (Array.isArray(err.detail)) {
              errorMsg = err.detail.map(d => d.msg || (d.loc ? d.loc.join(".") : "") || JSON.stringify(d)).join(", ");
            } else if (err.mensaje) {
              errorMsg = typeof err.mensaje === "string" ? err.mensaje : JSON.stringify(err.mensaje);
            }
            throw new Error(errorMsg);
          }

          const data = await res.json().catch(() => ({}));
          let idCreado = data.persona || data.id || `per-${Date.now()}`;

          const nueva = {
            id: idCreado,
            ...payload,
            documentos: docsValidos,
            fecha_creacion: new Date().toISOString()
          };
          this.personas.unshift(nueva);
          this.mensajeExito = "Persona registrada con éxito.";
        }

        this.notificarCambio();
        setTimeout(() => {
          this.cerrarForm();
        }, 1200);

      } catch (err) {
        console.error("Error al guardar persona:", err);
        this.mensajeError = `Error al guardar: ${err.message}`;
      } finally {
        this.guardando = false;
      }
    },

    // ---------------------------------------------------
    // Eliminación
    // ---------------------------------------------------
    confirmarEliminar(p) {
      this.personaEliminar = p;
      this.showDeleteModal = true;
    },

    cancelarEliminar() {
      this.personaEliminar = null;
      this.showDeleteModal = false;
    },

    async eliminarPersona() {
      if (!this.personaEliminar) return;
      const id = this.personaEliminar.id;

      // Eliminación optimista local
      this.personas = this.personas.filter(p => p.id !== id);
      this.notificarCambio();
      this.showDeleteModal = false;
      this.personaEliminar = null;

      if (this.currentPage > this.totalPaginas) {
        this.currentPage = Math.max(1, this.totalPaginas);
      }

      try {
        let res = await fetch(`${API.personas}/${id}`, { method: "DELETE" });
        if (!res.ok && res.status === 404) {
          // Intentar ruta alternativa si existe /delete/{id}
          res = await fetch(`${API.personas}/delete/${id}`, { method: "DELETE" });
        }
        if (!res.ok) {
          console.warn(`Aviso: DELETE en servidor respondió ${res.status}`);
        }
      } catch (err) {
        console.error("Error al eliminar persona en backend:", err);
      }
    }
  };
}
