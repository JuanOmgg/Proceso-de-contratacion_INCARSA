/**
 * ============================================================================
 * formulario-gesco.js — Creación y Edición de Formularios GESCO (Wizard 2 Pasos)
 * ============================================================================
 * Controlador Alpine.js para la pantalla dedicada de alta y modificación:
 * - Paso 1: Parámetros del Formulario (Nombre, Vigencia, Personal, Estado)
 * - Paso 2: Banco de Preguntas y Respuestas (Constructor interactivo)
 */

function slugifyFormulario(texto) {
  if (!texto) return "";
  return String(texto)
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function formularioGescoForm() {
  return {
    // ---------------------------------------------------
    // Estado del Wizard
    // ---------------------------------------------------
    currentStep: 1,
    isEdit: false,
    formId: null,
    cargando: false,
    guardando: false,
    submitted: false,
    mensajeExito: "",
    mensajeError: "",
    errors: {},

    // ---------------------------------------------------
    // Paso 1: Modelo del Formulario
    // ---------------------------------------------------
    form: {
      nombre: "",
      descripcion: "",
      vigencia: 365,
      Tipo_pregunta: "GENERAL",
      cantidad_preguntas: null,
      config_cuotas: {
        SST: null,
        AMBIENTAL: null,
        SEGURIDAD_VIAL: null,
        CALIDAD: null,
        BIOMECANICA: null,
        GENERAL: null
      },
      tipos_seleccionados: ["TODOS"],
      is_active: true,
      es_interno: false,
      fecha_limite: null,
      id_creador: null,
      creador_nombre: "",
      slug: "",
      url_simulacion: ""
    },

    // ---------------------------------------------------
    // Paso 2: Preguntas y Opciones
    // ---------------------------------------------------
    preguntas: [],
    filtroCategoriaStep2: "TODAS",

    // ---------------------------------------------------
    // Catálogos y Opciones
    // ---------------------------------------------------
    catalogoCategorias: [
      { id: "SST", label: "SST", tag: "Seguridad y Salud en el Trabajo", colorClass: "cat-badge-sst", icon: "fa-solid fa-helmet-safety" },
      { id: "AMBIENTAL", label: "Ambiental", tag: "Gestión Ambiental", colorClass: "cat-badge-ambiental", icon: "fa-solid fa-leaf" },
      { id: "SEGURIDAD_VIAL", label: "Seguridad Vial", tag: "Seguridad Vial y Transporte", colorClass: "cat-badge-seguridad_vial", icon: "fa-solid fa-car-side" },
      { id: "CALIDAD", label: "Calidad", tag: "Gestión de Calidad", colorClass: "cat-badge-calidad", icon: "fa-solid fa-award" },
      { id: "BIOMECANICA", label: "Biomecánica", tag: "Riesgo Biomecánico y Ergonomía", colorClass: "cat-badge-biomecanica", icon: "fa-solid fa-person-walking" },
      { id: "GENERAL", label: "General", tag: "Inducción General", colorClass: "cat-badge-general", icon: "fa-solid fa-shield-halved" }
    ],

    catalogoTipos: [
      {
        id: "TODOS",
        label: "Todos los tipos",
        tag: "Acceso Global",
        theme: "purple",
        icon: "fa-solid fa-users",
        desc: "Aplicar a todas las personas que entren en las solicitudes."
      },
      {
        id: "Contratista",
        label: "Contratistas",
        tag: "Operativo & Faena",
        theme: "cyan",
        icon: "fa-solid fa-helmet-safety",
        desc: "Personal de empresas contratistas de mantenimiento o instalaciones."
      },
      {
        id: "Proveedor",
        label: "Proveedores",
        tag: "Carga & Despacho",
        theme: "amber",
        icon: "fa-solid fa-truck-fast",
        desc: "Conductores, transportadores de carga y despachadores de insumos."
      },
      {
        id: "Visitante",
        label: "Visitantes",
        tag: "Auditoría & Visita",
        theme: "emerald",
        icon: "fa-solid fa-id-badge",
        desc: "Comisiones técnicas, auditorías externas, directivos y visitas temporales."
      },
      {
        id: "Interno",
        label: "Personal Interno",
        tag: "Diálogos & Planta",
        theme: "indigo",
        icon: "fa-solid fa-building-user",
        desc: "Trabajadores propios y personal interno para diálogos mensuales, charlas y capacitaciones."
      }
    ],

    toggleEsInterno() {
      this.form.es_interno = !this.form.es_interno;
      if (this.form.es_interno) {
        this.form.tipo_personal = "Interno";
        this.form.tipos_seleccionados = ["Interno"];
        this.form.cantidad_preguntas = null;
        this.form.config_cuotas = {
          SST: null,
          AMBIENTAL: null,
          SEGURIDAD_VIAL: null,
          CALIDAD: null,
          BIOMECANICA: null,
          GENERAL: null
        };
        this.$nextTick(() => {
          if (this.$refs.fechaLimiteInput) {
            this.initFlatpickrFechaLimite(this.$refs.fechaLimiteInput);
          }
        });
      } else {
        this.form.tipos_seleccionados = ["TODOS"];
      }
    },

    fpFechaLimite: null,

    initFlatpickrFechaLimite(el) {
      if (typeof flatpickr === "undefined" || !el) return;
      if (el._flatpickr) {
        this.fpFechaLimite = el._flatpickr;
        return;
      }
      const self = this;
      this.fpFechaLimite = flatpickr(el, {
        locale: (typeof flatpickr !== "undefined" && flatpickr.l10ns && flatpickr.l10ns.es) ? flatpickr.l10ns.es : "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        altInputClass: "gesco-date-input flatpickr-input",
        minDate: "today",
        defaultDate: self.form.fecha_limite || null,
        disableMobile: true,
        onChange(selectedDates, dateStr) {
          self.form.fecha_limite = dateStr || null;
        }
      });
    },

    abrirCalendarioFechaLimite() {
      if (this.fpFechaLimite) {
        this.fpFechaLimite.open();
      } else if (this.$refs.fechaLimiteInput) {
        this.initFlatpickrFechaLimite(this.$refs.fechaLimiteInput);
        setTimeout(() => this.fpFechaLimite && this.fpFechaLimite.open(), 50);
      }
    },

    quitarFechaLimite() {
      this.form.fecha_limite = null;
      if (this.fpFechaLimite) {
        this.fpFechaLimite.clear();
      }
    },

    establecerFechaLimite(dias) {
      const d = new Date();
      d.setDate(d.getDate() + dias);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      const dateStr = `${yyyy}-${mm}-${dd}`;
      this.form.fecha_limite = dateStr;
      if (this.fpFechaLimite) {
        this.fpFechaLimite.setDate(dateStr, true);
      }
    },

    isPresetActive(dias) {
      if (!this.form.fecha_limite) return false;
      const d = new Date();
      d.setDate(d.getDate() + dias);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      return this.form.fecha_limite === `${yyyy}-${mm}-${dd}`;
    },

    presetsVigencia: [
      { dias: 90, label: "90 días (3 meses)" },
      { dias: 180, label: "180 días (6 meses)" },
      { dias: 365, label: "365 días (1 año)", destacado: true },
      { dias: 730, label: "730 días (2 años)" }
    ],

    tiposPreguntaDisponibles: [
      { id: "MULTIPLE", label: "Opción múltiple" },
      { id: "UNICA", label: "Selección única" },
      { id: "VERDADERO_FALSO", label: "Verdadero / Falso" },
      { id: "TEXTO", label: "Respuesta abierta" }
    ],

    get totalCuotasConfiguradas() {
      let sum = 0;
      if (!this.form.config_cuotas) return 0;
      for (const val of Object.values(this.form.config_cuotas)) {
        if (val !== null && val !== "" && !isNaN(Number(val)) && Number(val) > 0) {
          sum += Number(val);
        }
      }
      return sum;
    },

    getConteoBancoPorCategoria(catId) {
      return (this.preguntas || []).filter(p => (p.tipo_pregunta || "GENERAL") === catId).length;
    },

    getCategoriaMeta(catId) {
      const catClean = (catId || "GENERAL").toUpperCase();
      return this.catalogoCategorias.find(c => c.id === catClean) || {
        id: catClean,
        label: catClean,
        colorClass: "cat-badge-general",
        icon: "fa-solid fa-tag"
      };
    },

    // ---------------------------------------------------
    // Computed / Helpers
    // ---------------------------------------------------
    get isPaso1Completado() {
      const nom = String(this.form.nombre || "").trim();
      const vig = Number(this.form.vigencia);
      const tipos = this.form.tipos_seleccionados || [];
      return nom.length >= 3 && vig >= 1 && tipos.length > 0;
    },

    get tipoPersonalTexto() {
      if (this.form.tipos_seleccionados.includes("TODOS")) {
        return "Todas las personas sin excepción";
      }
      return this.form.tipos_seleccionados.join(", ");
    },

    get urlSimulacion() {
      if (this.form && this.form.url_simulacion) return this.form.url_simulacion;
      const slug = (this.form && (this.form.slug || slugifyFormulario(this.form.nombre))) || this.formId || "";
      return `/evaluacion-induccion/${slug}?simulacion=1`;
    },

    // ---------------------------------------------------
    // Helper de endpoints API seguro
    // ---------------------------------------------------
    getEndpoint(key, fallback) {
      if (typeof window !== "undefined" && window.API && window.API[key]) {
        return window.API[key];
      }
      if (typeof API !== "undefined" && API[key]) {
        return API[key];
      }
      return fallback;
    },

    // ---------------------------------------------------
    // Inicialización
    // ---------------------------------------------------
    async init() {
      const rawId = window.__FORMULARIO_ID__;
      if (rawId && !isNaN(Number(rawId)) && Number(rawId) > 0) {
        this.isEdit = true;
        this.formId = Number(rawId);
        await this.cargarDatosEdicion();
      }
    },

    async cargarDatosEdicion() {
      this.cargando = true;
      this.mensajeError = "";
      try {
        const token = typeof getAuthToken === "function" ? getAuthToken() : null;
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const apiBase = this.getEndpoint("formularios_gesco", "/api/v1/formularios-gesco");
        const url = `${apiBase}/${this.formId}`;

        const res = await fetch(url, { headers });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `HTTP ${res.status}`);
        }

        const data = await res.json();
        const f = data.datos || data;

        this.form.nombre = f.nombre || "";
        this.form.descripcion = f.descripcion || "";
        this.form.vigencia = Number(f.vigencia) || 365;
        this.form.Tipo_pregunta = f.Tipo_pregunta || "GENERAL";
        this.form.cantidad_preguntas = f.cantidad_preguntas !== null && f.cantidad_preguntas !== undefined ? Number(f.cantidad_preguntas) : null;
        this.form.is_active = f.is_active === 1 || f.is_active === true || f.is_active === "1";
        this.form.es_interno = Boolean(f.es_interno || (f.tipo_personal && String(f.tipo_personal).toLowerCase().includes('interno')));
        this.form.fecha_limite = f.fecha_limite ? String(f.fecha_limite).slice(0, 10) : null;
        if (this.fpFechaLimite) {
          if (this.form.fecha_limite) {
            this.fpFechaLimite.setDate(this.form.fecha_limite, false);
          } else {
            this.fpFechaLimite.clear();
          }
        }
        this.form.id_creador = f.id_creador || null;
        this.form.creador_nombre = f.creador_nombre || "";
        this.form.slug = f.slug || slugifyFormulario(f.nombre || "");
        this.form.url_simulacion = f.url_simulacion || `/evaluacion-induccion/${this.form.slug || this.formId}?simulacion=1`;

        // Cargar cuotas independientes por categoría si existen
        this.form.config_cuotas = {
          SST: null,
          AMBIENTAL: null,
          SEGURIDAD_VIAL: null,
          CALIDAD: null,
          BIOMECANICA: null,
          GENERAL: null
        };
        if (f.config_cuotas && typeof f.config_cuotas === "object") {
          for (const [k, v] of Object.entries(f.config_cuotas)) {
            const kUp = String(k).toUpperCase();
            if (kUp in this.form.config_cuotas) {
              this.form.config_cuotas[kUp] = (v !== null && v !== "" && !isNaN(Number(v))) ? Number(v) : null;
            }
          }
        }

        // Parsear tipos de personal
        const tpStr = String(f.tipo_personal || "TODOS").trim();
        if (tpStr.toUpperCase() === "TODOS") {
          this.form.tipos_seleccionados = ["TODOS"];
        } else {
          this.form.tipos_seleccionados = tpStr
            .split(",")
            .map(t => t.trim())
            .filter(Boolean);
        }

        // Cargar preguntas asociadas al formulario
        await this.cargarPreguntasEdicion();
      } catch (err) {
        console.error("Error al cargar formulario para edición:", err);
        this.mensajeError = `No se pudieron cargar los datos del formulario: ${err.message}`;
      } finally {
        this.cargando = false;
      }
    },

    // ---------------------------------------------------
    // Helper de URLs e IDs de YouTube
    // ---------------------------------------------------
    extractYouTubeId(input) {
      if (!input) return null;
      let str = String(input).trim();
      if (!str) return null;
      // Extraer si pegaron un código iframe completo (<iframe src="...">)
      const iframeMatch = str.match(/src=["']([^"']+)["']/i);
      if (iframeMatch && iframeMatch[1]) {
        str = iframeMatch[1].trim();
      }
      // Si pegaron directamente el ID de 11 caracteres
      if (/^[a-zA-Z0-9_-]{11}$/.test(str)) {
        return str;
      }
      // Soporta watch?v=, youtu.be, shorts, live, embed, con parámetros previos o posteriores
      const regExp = /(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?|shorts|live)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})/i;
      const match = str.match(regExp);
      return match && match[1] ? match[1] : null;
    },

    getYouTubeEmbedUrl(url) {
      const id = this.extractYouTubeId(url);
      return id ? `https://www.youtube.com/embed/${id}?playsinline=1&rel=0` : null;
    },

    async cargarPreguntasEdicion() {
      try {
        const token = typeof getAuthToken === "function" ? getAuthToken() : null;
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const apiBase = this.getEndpoint("formularios_gesco", "/api/v1/formularios-gesco");
        const url = `${apiBase}/${this.formId}/preguntas`;

        const res = await fetch(url, { headers });
        if (res.ok) {
          const data = await res.json();
          const rawList = Array.isArray(data) ? data : (data.datos || []);
          this.preguntas = rawList.map(p => {
            const hasVideo = Boolean(p.video_url && String(p.video_url).trim());
            const hasImage = Boolean(p.imagen_url && String(p.imagen_url).trim());
            let tipoMedia = "NINGUNO";
            if (hasVideo) tipoMedia = "VIDEO";
            else if (hasImage) tipoMedia = "IMAGEN";

            return {
              ...p,
              tipo_pregunta: (p.tipo_pregunta || "GENERAL").toUpperCase(),
              imagen_url: (tipoMedia === "IMAGEN") ? (p.imagen_url || "") : "",
              video_url: (tipoMedia === "VIDEO") ? (p.video_url || "") : "",
              tipo_multimedia: tipoMedia,
              es_calificable: p.es_calificable !== undefined ? Boolean(p.es_calificable) : true,
              _showMedia: tipoMedia !== "NINGUNO",
              _uploading: false
            };
          });
        }
      } catch (err) {
        console.warn("No se pudieron precargar las preguntas:", err);
      }
    },

    // ---------------------------------------------------
    // Gestión Multimedia Exclusiva (Foto O Video)
    // ---------------------------------------------------
    cambiarTipoMultimedia(q, nuevoTipo) {
      if (q.tipo_multimedia === nuevoTipo) {
        q._showMedia = !q._showMedia;
        return;
      }
      q.tipo_multimedia = nuevoTipo;
      if (nuevoTipo === "IMAGEN") {
        q.video_url = "";
        q._showMedia = true;
      } else if (nuevoTipo === "VIDEO") {
        q.imagen_url = "";
        q._showMedia = true;
      } else {
        q.imagen_url = "";
        q.video_url = "";
        q._showMedia = false;
      }
    },

    toggleMultimedia(q) {
      if (q._showMedia) {
        q._showMedia = false;
      } else {
        if (!q.tipo_multimedia || q.tipo_multimedia === "NINGUNO") {
          q.tipo_multimedia = "IMAGEN";
        }
        q._showMedia = true;
      }
    },

    async subirImagenPregunta(event, q) {
      const file = event.target.files && event.target.files[0];
      if (!file) return;

      const formatosValidos = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/svg+xml", "image/gif"];
      if (!formatosValidos.includes(file.type.toLowerCase())) {
        Swal.fire({
          icon: "warning",
          title: "Formato no compatible",
          text: "Solo se permiten imágenes (PNG, JPG, JPEG, WEBP, SVG o GIF).",
          confirmButtonColor: "#F0323E"
        });
        event.target.value = "";
        return;
      }

      if (file.size > 15 * 1024 * 1024) {
        Swal.fire({
          icon: "warning",
          title: "Archivo muy pesado",
          text: "La imagen no debe superar los 15 MB de tamaño.",
          confirmButtonColor: "#F0323E"
        });
        event.target.value = "";
        return;
      }

      q._uploading = true;
      try {
        const formData = new FormData();
        formData.append("file", file);

        const token = typeof getAuthToken === "function" ? getAuthToken() : null;
        const headers = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch("/api/v1/formularios-gesco/upload-imagen", {
          method: "POST",
          headers,
          body: formData
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Error HTTP ${res.status}`);
        }

        const data = await res.json();
        q.imagen_url = data.imagen_url || data.url_imagen;
        q.video_url = "";
        q.tipo_multimedia = "IMAGEN";
        q._showMedia = true;

        const Toast = Swal.mixin({
          toast: true,
          position: "top-end",
          showConfirmButton: false,
          timer: 2000,
          timerProgressBar: true
        });
        Toast.fire({
          icon: "success",
          title: "Imagen subida exitosamente"
        });
      } catch (err) {
        console.error("Error al subir imagen:", err);
        Swal.fire({
          icon: "error",
          title: "Error al subir imagen",
          text: err.message || "No se pudo subir la imagen a la carpeta del servidor.",
          confirmButtonColor: "#F0323E"
        });
      } finally {
        q._uploading = false;
        event.target.value = "";
      }
    },

    eliminarImagen(q) {
      q.imagen_url = "";
      q.tipo_multimedia = "NINGUNO";
      q._showMedia = false;
    },

    eliminarVideo(q) {
      q.video_url = "";
      q.tipo_multimedia = "NINGUNO";
      q._showMedia = false;
    },

    // ---------------------------------------------------
    // Navegación entre Pasos
    // ---------------------------------------------------
    irAlPaso(paso) {
      if (paso === 2) {
        if (!this.validarPaso1()) {
          const primerError = Object.values(this.errors)[0];
          this.mensajeError = primerError || "Completa los campos obligatorios del Paso 1.";
          return;
        }
        this.mensajeError = "";
        this.currentStep = 2;
        // Si no tiene preguntas agregadas, inicializar con la primera pregunta
        if (this.preguntas.length === 0) {
          this.agregarPregunta();
        }
        window.scrollTo({ top: 0, behavior: "smooth" });
      } else {
        this.mensajeError = "";
        this.currentStep = 1;
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    },

    // ---------------------------------------------------
    // Paso 1: Métodos de Formulario
    // ---------------------------------------------------
    setVigenciaPreset(dias) {
      this.form.vigencia = Number(dias);
      if (this.errors.vigencia) delete this.errors.vigencia;
    },

    toggleTipo(tipoId) {
      if (this.errors.tipo_personal) delete this.errors.tipo_personal;

      if (tipoId === "TODOS") {
        this.form.tipos_seleccionados = ["TODOS"];
        return;
      }

      let list = this.form.tipos_seleccionados.filter(t => t !== "TODOS");
      const idx = list.indexOf(tipoId);
      if (idx > -1) {
        list.splice(idx, 1);
      } else {
        list.push(tipoId);
      }

      if (list.length === 0) {
        this.form.tipos_seleccionados = ["TODOS"];
      } else {
        this.form.tipos_seleccionados = list;
      }
    },

    isTipoSeleccionado(tipoId) {
      return this.form.tipos_seleccionados.includes(tipoId);
    },

    vigenciaLegible(dias) {
      const num = Number(dias) || 365;
      if (num === 365) return "365 días (1 año)";
      if (num === 730) return "730 días (2 años)";
      if (num === 180) return "180 días (6 meses)";
      if (num === 90) return "90 días (3 meses)";
      return `${num} días`;
    },

    // ---------------------------------------------------
    // Paso 2: Constructor de Preguntas
    // ---------------------------------------------------
    agregarPregunta() {
      const catDefault = (this.filtroCategoriaStep2 && this.filtroCategoriaStep2 !== "TODAS")
        ? this.filtroCategoriaStep2
        : "GENERAL";
      this.preguntas.push({
        id: null,
        pregunta: "",
        tipo_respuesta: "MULTIPLE",
        tipo_pregunta: catDefault,
        imagen_url: "",
        video_url: "",
        tipo_multimedia: "NINGUNO",
        es_calificable: true,
        estado: true,
        _showMedia: false,
        _uploading: false,
        opciones: [
          { id: null, opcion: "", is_correct: true },
          { id: null, opcion: "", is_correct: false }
        ]
      });
    },

    eliminarPregunta(index) {
      this.preguntas.splice(index, 1);
    },

    cambiarTipoPregunta(qIndex, nuevoTipo) {
      const q = this.preguntas[qIndex];
      if (!q) return;
      q.tipo_respuesta = nuevoTipo;

      if (nuevoTipo === "VERDADERO_FALSO") {
        q.opciones = [
          { id: null, opcion: "Verdadero", is_correct: true },
          { id: null, opcion: "Falso", is_correct: false }
        ];
      } else if (nuevoTipo === "TEXTO") {
        q.opciones = [];
      } else if (!q.opciones || q.opciones.length === 0) {
        q.opciones = [
          { id: null, opcion: "", is_correct: true },
          { id: null, opcion: "", is_correct: false }
        ];
      }
    },

    agregarOpcion(qIndex) {
      const q = this.preguntas[qIndex];
      if (!q) return;
      if (!Array.isArray(q.opciones)) q.opciones = [];
      q.opciones.push({
        id: null,
        opcion: "",
        is_correct: false
      });
    },

    eliminarOpcion(qIndex, opcIndex) {
      const q = this.preguntas[qIndex];
      if (!q || !Array.isArray(q.opciones)) return;
      if (q.opciones.length <= 2) {
        // Alerta suave: mínimo 2 opciones para preguntas de selección
        return;
      }
      q.opciones.splice(opcIndex, 1);
    },

    marcarCorrecta(qIndex, opcIndex) {
      const q = this.preguntas[qIndex];
      if (!q || !q.opciones || !q.opciones[opcIndex]) return;

      if (q.tipo_respuesta === "UNICA" || q.tipo_respuesta === "VERDADERO_FALSO") {
        // En selección única o V/F solo puede haber una verdadera
        q.opciones.forEach((opc, i) => {
          opc.is_correct = (i === opcIndex);
        });
      } else {
        // En múltiple se alterna
        q.opciones[opcIndex].is_correct = !q.opciones[opcIndex].is_correct;
      }
    },

    // ---------------------------------------------------
    // Validaciones
    // ---------------------------------------------------
    validarPaso1() {
      this.errors = {};
      const nom = String(this.form.nombre || "").trim();
      const vig = Number(this.form.vigencia);

      if (!nom) {
        this.errors.nombre = "El nombre del formulario es obligatorio.";
      } else if (nom.length < 8) {
        this.errors.nombre = "El nombre debe tener al menos 8 caracteres.";
      } else if (nom.length > 50) {
        this.errors.nombre = "El nombre no puede exceder los 50 caracteres.";
      }

      if (!vig || isNaN(vig) || vig < 1) {
        this.errors.vigencia = "La vigencia debe ser de al menos 1 día.";
      } else if (vig > 3650) {
        this.errors.vigencia = "La vigencia máxima es de 3650 días (10 años).";
      }

      if (!this.form.es_interno) {
        if (!this.form.tipos_seleccionados || this.form.tipos_seleccionados.length === 0) {
          this.errors.tipo_personal = "Debes seleccionar al menos un tipo de personal aplicable.";
        }
      }

      return Object.keys(this.errors).length === 0;
    },

    validarPaso2() {
      if (!this.preguntas || this.preguntas.length === 0) {
        this.mensajeError = "Debes agregar al menos una pregunta al cuestionario de inducción.";
        return false;
      }

      // Validar cada pregunta si existen preguntas añadidas
      for (let i = 0; i < this.preguntas.length; i++) {
        const q = this.preguntas[i];
        const numPreg = i + 1;
        const texto = String(q.pregunta || "").trim();

        if (!texto || texto.length < 10) {
          this.mensajeError = `La Pregunta #${numPreg} debe tener un enunciado válido (mínimo 10 letras).`;
          return false;
        }

        if (q.tipo_respuesta !== "TEXTO") {
          if (!q.opciones || q.opciones.length < 2) {
            this.mensajeError = `La Pregunta #${numPreg} debe tener al menos 2 opciones de respuesta.`;
            return false;
          }

          let tieneCorrecta = false;
          for (let j = 0; j < q.opciones.length; j++) {
            const o = q.opciones[j];
            if (!String(o.opcion || "").trim()) {
              this.mensajeError = `La opción #${j + 1} de la Pregunta #${numPreg} no puede estar vacía.`;
              return false;
            }
            if (o.is_correct) tieneCorrecta = true;
          }

          if (q.es_calificable !== false && !tieneCorrecta) {
            this.mensajeError = `Debes marcar al menos una opción correcta en la Pregunta #${numPreg}.`;
            return false;
          }
        }
      }
      return true;
    },

    // ---------------------------------------------------
    // Guardar / Actualizar Formulario Completo + Preguntas
    // ---------------------------------------------------
    async submitForm() {
      if (!this.validarPaso1()) {
        this.currentStep = 1;
        this.mensajeError = Object.values(this.errors)[0] || "Corrige los datos del formulario en el Paso 1.";
        return;
      }

      if (!this.validarPaso2()) {
        this.currentStep = 2;
        return;
      }

      this.guardando = true;
      this.mensajeError = "";
      this.mensajeExito = "";

      const esInterno = Boolean(this.form.es_interno);
      const tipoFinal = esInterno
        ? "Interno"
        : (this.form.tipos_seleccionados.includes("TODOS")
            ? "TODOS"
            : this.form.tipos_seleccionados.join(", "));

      const rawCant = this.form.cantidad_preguntas;
      const cantFinal = (!esInterno && rawCant !== null && rawCant !== "" && !isNaN(Number(rawCant)) && Number(rawCant) > 0)
        ? Number(rawCant)
        : null;

      // Limpiar cuotas válidas mayores a 0 si no es interno
      const cleanCuotas = {};
      let tieneCuotas = false;
      if (!esInterno && this.form.config_cuotas) {
        for (const [k, v] of Object.entries(this.form.config_cuotas)) {
          if (v !== null && v !== "" && !isNaN(Number(v)) && Number(v) > 0) {
            cleanCuotas[k.toUpperCase()] = Number(v);
            tieneCuotas = true;
          }
        }
      }

      const payloadForm = {
        nombre: this.form.nombre.trim(),
        descripcion: (this.form.descripcion || "").trim() || null,
        vigencia: Number(this.form.vigencia) || 365,
        tipo_personal: tipoFinal,
        Tipo_pregunta: this.form.Tipo_pregunta || "GENERAL",
        cantidad_preguntas: cantFinal,
        config_cuotas: tieneCuotas ? cleanCuotas : null,
        is_active: this.form.is_active === 1 || this.form.is_active === true || this.form.is_active === "1",
        es_interno: esInterno,
        fecha_limite: (esInterno && this.form.fecha_limite) ? this.form.fecha_limite : null
      };

      try {
        const token = typeof getAuthToken === "function" ? getAuthToken() : null;
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const apiBase = this.getEndpoint("formularios_gesco", "/api/v1/formularios-gesco");

        let url = apiBase;
        let method = "POST";
        if (this.isEdit && this.formId) {
          url = `${apiBase}/${this.formId}`;
          method = "PUT";
        }

        // 1. Guardar Formulario
        const resForm = await fetch(url, {
          method,
          headers,
          body: JSON.stringify(payloadForm)
        });

        if (!resForm.ok) {
          const errData = await resForm.json().catch(() => ({}));
          throw new Error(errData.detail || errData.mensaje || `HTTP ${resForm.status}`);
        }

        const resData = await resForm.json();
        const targetId = this.isEdit ? this.formId : (resData.id || resData.datos?.id);

        // 2. Sincronizar Preguntas si se definieron
        if (targetId && this.preguntas.length > 0) {
          const syncUrl = `${apiBase}/${targetId}/preguntas/sync`;
          const syncPayload = {
            preguntas: this.preguntas.map(p => ({
              id: p.id || null,
              pregunta: p.pregunta.trim(),
              tipo_respuesta: p.tipo_respuesta || "MULTIPLE",
              tipo_pregunta: (p.tipo_pregunta || "GENERAL").toUpperCase(),
              imagen_url: (p.tipo_multimedia === "IMAGEN" ? ((p.imagen_url || "").trim() || null) : null),
              video_url: (p.tipo_multimedia === "VIDEO" ? (() => {
                const rawV = (p.video_url || "").trim();
                if (!rawV) return null;
                const ytId = this.extractYouTubeId(rawV);
                return ytId ? `https://www.youtube.com/watch?v=${ytId}` : rawV;
              })() : null),
              es_calificable: p.es_calificable !== undefined ? Boolean(p.es_calificable) : true,
              estado: Boolean(p.estado),
              opciones: (p.opciones || []).map(o => ({
                id: o.id || null,
                opcion: o.opcion.trim(),
                is_correct: Boolean(o.is_correct)
              }))
            }))
          };

          const resSync = await fetch(syncUrl, {
            method: "POST",
            headers,
            body: JSON.stringify(syncPayload)
          });

          if (!resSync.ok) {
            const errSync = await resSync.json().catch(() => ({}));
            console.warn("Aviso al sincronizar preguntas:", errSync);
            throw new Error(errSync.detail || errSync.mensaje || "Error al guardar las preguntas del cuestionario.");
          }
        }

        this.submitted = true;
        this.mensajeExito = this.isEdit
          ? "Formulario y preguntas actualizados exitosamente."
          : "Formulario y preguntas creados exitosamente.";

        setTimeout(() => {
          window.location.href = "/formularios-gesco";
        }, 1300);
      } catch (err) {
        console.error("Error al guardar formulario GESCO:", err);
        this.mensajeError = err.message || "Error al procesar la solicitud.";
      } finally {
        this.guardando = false;
      }
    }
  };
}

// Registro global
window.formularioGescoForm = formularioGescoForm;
