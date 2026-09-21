/**
 * ============================================================================
 * inducciones.js — Gestión, Consulta y Renovación de Inducciones (INCARSA)
 * ============================================================================
 */

function induccionesModule() {
  return {
    // ---------------------------------------------------
    // Estado y Datos
    // ---------------------------------------------------
    inducciones: [],
    cargando: true,

    // Filtros y búsqueda
    search: "",
    filtroVigencia: "todos", // 'todos', 'vigente', 'por_vencer', 'vencido', 'sin_induccion'

    // Paginación
    currentPage: 1,
    pageSize: 8,

    // Modales
    showFichaModal: false,
    detalleInduccion: {},

    showFormModal: false,
    guardandoInduccion: false,
    mensajeExitoForm: "",
    mensajeErrorForm: "",
    formInduccion: {
      id_persona: null,
      persona_nombre: "",
      persona_identificacion: "",
      persona_tipo_doc: "CC",
      persona_cargo: "",
      nombre_empresa: "",
      responsable: "",
      fecha_induccion: "",
      fecha_vigencia: "",
      anotaciones: ""
    },

    // Modal 3: Confirmación de Renovación Rápida (Estilo Ticket)
    showConfirmModal: false,
    personaARenovar: null,
    renovandoRapido: false,

    // Modal 4: Éxito de Renovación / Voucher (Estilo Ticket)
    showSuccessModal: false,
    datosExitoRenovacion: {},

    // ---------------------------------------------------
    // Inicialización
    // ---------------------------------------------------
    async init() {
      await this.getInducciones();

      this.$watch("search", () => (this.currentPage = 1));
      this.$watch("filtroVigencia", () => (this.currentPage = 1));
      this.$watch("pageSize", () => (this.currentPage = 1));
    },

    // ---------------------------------------------------
    // Carga de Datos desde API
    // ---------------------------------------------------
    async getInducciones() {
      this.cargando = true;
      try {
        const token = typeof getAuthToken === "function" ? getAuthToken() : null;
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const url = (window.API && window.API.inducciones) 
          ? `${window.API.inducciones}/getAll`
          : "/api/v1/inducciones/getAll";

        const res = await fetch(url, { headers });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        this.inducciones = Array.isArray(data) ? data : (data.datos || data.data || []);
      } catch (err) {
        console.warn("Aviso al consultar inducciones:", err.message);
        this.inducciones = [];
      } finally {
        this.cargando = false;
      }
    },

    // ---------------------------------------------------
    // KPIs / Indicadores Computados
    // ---------------------------------------------------
    get totalRegistros() {
      return this.inducciones.length;
    },

    get totalVigentes() {
      return this.inducciones.filter(i => i.estado_vigencia === "vigente").length;
    },

    get totalPorVencer() {
      return this.inducciones.filter(i => i.estado_vigencia === "por_vencer").length;
    },

    get totalVencidos() {
      return this.inducciones.filter(i => i.estado_vigencia === "vencido").length;
    },

    get totalSinInduccion() {
      return this.inducciones.filter(i => i.estado_vigencia === "sin_induccion").length;
    },

    // ---------------------------------------------------
    // Filtro y Búsqueda
    // ---------------------------------------------------
    get induccionesFiltradas() {
      let lista = this.inducciones;

      // Filtro por estado de vigencia
      if (this.filtroVigencia !== "todos") {
        lista = lista.filter(item => item.estado_vigencia === this.filtroVigencia);
      }

      // Buscador
      if (this.search.trim()) {
        const term = this.search.toLowerCase().trim();
        lista = lista.filter(item => {
          const nombre = (item.nombre_completo || `${item.persona_nombre || ""} ${item.persona_apellido || ""}`).toLowerCase();
          const doc = String(item.identificacion || "").toLowerCase();
          const cargo = String(item.cargo || "").toLowerCase();
          const empresa = String(item.nombre_empresa || "").toLowerCase();
          const resp = String(item.responsable || "").toLowerCase();
          return nombre.includes(term) || doc.includes(term) || cargo.includes(term) || empresa.includes(term) || resp.includes(term);
        });
      }

      return lista;
    },

    // ---------------------------------------------------
    // Paginación
    // ---------------------------------------------------
    get totalPaginas() {
      return Math.ceil(this.induccionesFiltradas.length / this.pageSize) || 1;
    },

    get induccionesPagina() {
      const inicio = (this.currentPage - 1) * this.pageSize;
      return this.induccionesFiltradas.slice(inicio, inicio + this.pageSize);
    },

    get rangoMostrado() {
      if (this.induccionesFiltradas.length === 0) return "0 de 0";
      const inicio = (this.currentPage - 1) * this.pageSize + 1;
      const fin = Math.min(this.currentPage * this.pageSize, this.induccionesFiltradas.length);
      return `${inicio} - ${fin} de ${this.induccionesFiltradas.length}`;
    },

    goToPage(p) {
      if (p >= 1 && p <= this.totalPaginas) {
        this.currentPage = p;
      }
    },

    resetPage() {
      this.currentPage = 1;
    },

    // ---------------------------------------------------
    // Helpers de Formato
    // ---------------------------------------------------
    obtenerIniciales(item) {
      const nom = (item.persona_nombre || item.nombre_completo || "?").trim();
      const ape = (item.persona_apellido || "").trim();
      if (ape) {
        return (nom[0] + ape[0]).toUpperCase();
      }
      const partes = nom.split(" ");
      if (partes.length >= 2) {
        return (partes[0][0] + partes[1][0]).toUpperCase();
      }
      return nom.substring(0, 2).toUpperCase();
    },

    formatearFecha(fechaStr, textoVacio = "—") {
      if (!fechaStr || fechaStr === "None" || fechaStr === "null" || fechaStr === "—" || fechaStr === "-" || fechaStr === "Sin fecha" || fechaStr === "Sin vigencia") {
        return textoVacio;
      }
      try {
        const meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

        // Si ya es un objeto Date
        if (fechaStr instanceof Date && !isNaN(fechaStr.getTime())) {
          const dia = String(fechaStr.getDate()).padStart(2, "0");
          const mesNombre = meses[fechaStr.getMonth()];
          const anio = fechaStr.getFullYear();
          return `${dia} ${mesNombre} ${anio}`;
        }

        const str = String(fechaStr).trim();
        const limpia = str.replace("T", " ").split(" ")[0];

        // Formato ISO / SQL: YYYY-MM-DD
        if (limpia.includes("-")) {
          const fPartes = limpia.split("-");
          if (fPartes.length === 3) {
            const anio = fPartes[0];
            const mesIdx = parseInt(fPartes[1], 10) - 1;
            const dia = String(parseInt(fPartes[2], 10)).padStart(2, "0");
            const mesNombre = meses[mesIdx] || fPartes[1];
            if (dia && mesNombre && anio) {
              return `${dia} ${mesNombre} ${anio}`;
            }
          }
        }

        // Formato con barras: DD/MM/YYYY
        if (limpia.includes("/")) {
          const fPartes = limpia.split("/");
          if (fPartes.length === 3) {
            const dia = String(parseInt(fPartes[0], 10)).padStart(2, "0");
            const mesIdx = parseInt(fPartes[1], 10) - 1;
            const anio = fPartes[2];
            const mesNombre = meses[mesIdx] || fPartes[1];
            if (dia && mesNombre && anio) {
              return `${dia} ${mesNombre} ${anio}`;
            }
          }
        }

        // Fallback Date parsing
        const d = new Date(str);
        if (!isNaN(d.getTime())) {
          const dia = String(d.getDate()).padStart(2, "0");
          const mesNombre = meses[d.getMonth()];
          const anio = d.getFullYear();
          return `${dia} ${mesNombre} ${anio}`;
        }

        return limpia;
      } catch (e) {
        return fechaStr;
      }
    },

    getEstadoVigenciaInfo(item) {
      const estado = item.estado_vigencia || "sin_induccion";
      const dias = item.dias_restantes;

      switch (estado) {
        case "vigente":
          return {
            estado: "vigente",
            etiqueta: "Vigente",
            badgeClass: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30",
            dotClass: "bg-emerald-500",
            icono: "fa-solid fa-circle-check",
            textoDias: dias !== null ? `${dias} días rest.` : "Al día"
          };
        case "por_vencer":
          return {
            estado: "por_vencer",
            etiqueta: "Por vencer",
            badgeClass: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30",
            dotClass: "bg-amber-500",
            icono: "fa-solid fa-triangle-exclamation",
            textoDias: dias !== null ? `${dias} días rest.` : "≤ 30 días"
          };
        case "vencido":
          return {
            estado: "vencido",
            etiqueta: "Vencido",
            badgeClass: "bg-red-500/15 text-red-600 dark:text-red-400 border border-red-500/30",
            dotClass: "bg-red-500",
            icono: "fa-solid fa-circle-xmark",
            textoDias: dias !== null ? `Venció hace ${Math.abs(dias)}d` : "Vencida"
          };
        case "sin_induccion":
        default:
          return {
            estado: "sin_induccion",
            etiqueta: "Sin inducción",
            badgeClass: "bg-slate-500/15 text-slate-600 dark:text-slate-400 border border-slate-500/30",
            dotClass: "bg-slate-400",
            icono: "fa-solid fa-clock-rotate-left",
            textoDias: "Pendiente"
          };
      }
    },

    // ---------------------------------------------------
    // Modal Ficha Ticket (Detalle Solo Lectura)
    // ---------------------------------------------------
    abrirFichaInduccion(item) {
      this.detalleInduccion = { ...item };
      this.showFichaModal = true;
    },

    cerrarFichaModal() {
      this.showFichaModal = false;
      this.detalleInduccion = {};
    },

    // ---------------------------------------------------
    // Auditor Responsable (Usuario GESCO actual)
    // ---------------------------------------------------
    get auditorActualNombre() {
      const sesion = typeof getAuthSession === "function" ? getAuthSession() : null;
      if (sesion && sesion.nombre) {
        return sesion.nombre;
      }
      return "Auditor GESCO";
    },

    // ---------------------------------------------------
    // Modal Formulario de Renovación
    // ---------------------------------------------------
    abrirFormularioInduccion(item) {
      const hoy = new Date();
      const fechaHoyTexto = this.formatearFecha(hoy);

      const fechaMasUnAno = new Date(hoy);
      fechaMasUnAno.setFullYear(fechaMasUnAno.getFullYear() + 1);
      const fechaVigTexto = this.formatearFecha(fechaMasUnAno);

      this.formInduccion = {
        id_persona: item.id_persona,
        persona_nombre: item.nombre_completo || `${item.persona_nombre} ${item.persona_apellido || ""}`.trim(),
        persona_identificacion: item.identificacion,
        persona_tipo_doc: item.tipo_doc || "CC",
        persona_cargo: item.cargo || "General",
        id_empresa: item.id_empresa || null,
        nombre_empresa: item.nombre_empresa || "Sin empresa asignada",
        responsable: this.auditorActualNombre,
        fecha_induccion_texto: fechaHoyTexto,
        fecha_vigencia_texto: fechaVigTexto,
        anotaciones: item.anotaciones || ""
      };

      this.mensajeExitoForm = "";
      this.mensajeErrorForm = "";
      this.guardandoInduccion = false;
      this.showFormModal = true;
    },

    cerrarFormModal() {
      this.showFormModal = false;
      this.mensajeExitoForm = "";
      this.mensajeErrorForm = "";
      this.guardandoInduccion = false;
    },

    async guardarInduccion() {
      if (!this.formInduccion.id_persona) return;
      this.guardandoInduccion = true;
      this.mensajeExitoForm = "";
      this.mensajeErrorForm = "";

      try {
        const token = typeof getAuthToken === "function" ? getAuthToken() : null;
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        // El auditor responsable siempre es el usuario autenticado de GESCO que renueva
        const payload = {
          responsable: this.auditorActualNombre,
          anotaciones: this.formInduccion.anotaciones ? this.formInduccion.anotaciones.trim() : null,
          id_empresa: this.formInduccion.id_empresa || null
        };

        const res = await fetch(`/api/v1/inducciones/persona/${this.formInduccion.id_persona}`, {
          method: "PATCH",
          headers,
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || data.mensaje || "Error al actualizar la inducción");

        // Preparar datos para el Ticket de Éxito
        this.datosExitoRenovacion = {
          nombre_completo: this.formInduccion.persona_nombre,
          identificacion: this.formInduccion.persona_identificacion,
          tipo_doc: this.formInduccion.persona_tipo_doc,
          cargo: this.formInduccion.persona_cargo,
          nombre_empresa: this.formInduccion.nombre_empresa,
          fecha_induccion: this.formInduccion.fecha_induccion_texto,
          fecha_vigencia: this.formInduccion.fecha_vigencia_texto,
          dias_restantes: 365
        };

        this.cerrarFormModal();
        this.showSuccessModal = true;
        await this.getInducciones();

      } catch (err) {
        this.mensajeErrorForm = err.message || "No fue posible guardar la inducción.";
      } finally {
        this.guardandoInduccion = false;
      }
    },

    // ---------------------------------------------------
    // Modal 3: Confirmación de Renovación Rápida Estilo Ticket
    // ---------------------------------------------------
    renovarRapido(item) {
      const hoy = new Date();
      const fechaHoyTexto = this.formatearFecha(hoy);

      const fechaMasUnAno = new Date(hoy);
      fechaMasUnAno.setFullYear(fechaMasUnAno.getFullYear() + 1);
      const fechaVigTexto = this.formatearFecha(fechaMasUnAno);

      this.personaARenovar = {
        ...item,
        nombre_completo: item.nombre_completo || `${item.persona_nombre || ""} ${item.persona_apellido || ""}`.trim(),
        fecha_induccion_nueva: fechaHoyTexto,
        fecha_vigencia_nueva: fechaVigTexto
      };

      this.showConfirmModal = true;
    },

    cerrarConfirmModal() {
      this.showConfirmModal = false;
      this.personaARenovar = null;
      this.renovandoRapido = false;
    },

    async confirmarRenovacionRapida() {
      if (!this.personaARenovar || !this.personaARenovar.id_persona) return;
      this.renovandoRapido = true;

      const item = this.personaARenovar;
      const nombre = item.nombre_completo || item.persona_nombre || "esta persona";

      try {
        const token = typeof getAuthToken === "function" ? getAuthToken() : null;
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`/api/v1/inducciones/persona/${item.id_persona}/renovar`, {
          method: "POST",
          headers
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || data.mensaje || "Error al renovar la inducción");

        // Preparar datos para el Ticket de Éxito
        this.datosExitoRenovacion = {
          nombre_completo: nombre,
          identificacion: item.identificacion,
          tipo_doc: item.tipo_doc || "CC",
          cargo: item.cargo || "General",
          nombre_empresa: item.nombre_empresa || "Sin asignar",
          fecha_induccion: item.fecha_induccion_nueva,
          fecha_vigencia: item.fecha_vigencia_nueva,
          dias_restantes: 365
        };

        // Cerrar modal de confirmación y abrir el ticket de éxito
        this.showConfirmModal = false;
        this.personaARenovar = null;
        this.showSuccessModal = true;

        await this.getInducciones();

      } catch (err) {
        if (typeof Alerta !== "undefined" && Alerta.error) {
          Alerta.error("Error al renovar", err.message);
        } else {
          alert(`Error al renovar: ${err.message}`);
        }
      } finally {
        this.renovandoRapido = false;
      }
    },

    // ---------------------------------------------------
    // Modal 4: Éxito de Renovación (Ticket Oficial)
    // ---------------------------------------------------
    cerrarSuccessModal() {
      this.showSuccessModal = false;
      this.datosExitoRenovacion = {};
    }
  };
}
