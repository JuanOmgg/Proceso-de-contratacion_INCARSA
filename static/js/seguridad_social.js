/**
 * Lógica de Seguridad Social y Seguimiento por Persona · INCARSA
 * Gestionado por SST con fecha de vigencia dictaminada manualmente.
 */

function seguridadSocialModule() {
  return {
    // ---------------------------------------------------
    // Estado y Datos
    // ---------------------------------------------------
    registros: [],
    empresas: [],
    personas: [],
    cargando: true,
    guardando: false,

    // Filtros y búsqueda
    search: "",
    filtroVigencia: "todos", // 'todos', 'vigente', 'por_vencer', 'vencido'
    fechaDesde: "",
    fechaHasta: "",
    criterioFecha: "vigencia", // 'vigencia' o 'revision'

    // Paginación principal
    currentPage: 1,
    pageSize: 8,

    // Feedback de alertas
    mensajeExito: "",
    mensajeError: "",
    copiadoFeedback: null,

    // Flatpickr instances para filtros principales
    fpDesdeInstance: null,
    fpHastaInstance: null,

    // Formulario de Edición / Dictamen SST (Modal Unificado - Ticket)
    showSeguridadSocialModal: false,
    showFormModal: false,
    fpVigenciaModalInstance: null,
    formSeguridadSocial: {
      id: null,
      id_persona: null,
      persona_nombre: "",
      persona_apellido: "",
      nombre_persona: "",
      persona_tipo_doc: "CC",
      persona_identificacion: "",
      persona_cargo: "",
      responsable: "",
      anotaciones: "",
      id_empresa: null,
      ultima_empresa_contratista: "",
      ultima_empresa_solicitante: "",
      ultima_revision: null,
      fecha_vigencia: null,
      total_solicitudes: 0,
      historial: []
    },

    // Modal Exclusivo de Historial de Solicitudes (Solo Lectura - Modal 1)
    showHistorialModal: false,
    cargandoHistorial: false,
    searchHistorial: "",
    fechaDesdeHistorial: "",
    fechaHastaHistorial: "",
    historialPage: 1,
    historialPageSize: 5,
    fpHistorialDesdeInstance: null,
    fpHistorialHastaInstance: null,
    detalleHistorial: {
      id: null,
      id_persona: null,
      nombre_persona: "",
      persona_tipo_doc: "CC",
      persona_identificacion: "",
      persona_cargo: "",
      responsable: "",
      ultimo_usuario_solicitud: "",
      anotaciones: "",
      ultima_empresa_contratista: "",
      ultima_revision: null,
      fecha_vigencia: null,
      total_solicitudes: 0,
      historial: []
    },

    // Filtros de historial dentro del modal formulario
    searchFormHistorial: "",
    searchFormFechaDesde: "",
    searchFormFechaHasta: "",
    formHistorialPage: 1,
    formHistorialPageSize: 5,
    fpFormDesdeInstance: null,
    fpFormHastaInstance: null,

    // ---------------------------------------------------
    // Inicialización
    // ---------------------------------------------------
    async init() {
      await Promise.all([
        this.getEmpresas(),
        this.getRegistros(),
        this.getPersonas()
      ]);

      this.$watch("search", () => (this.currentPage = 1));
      this.$watch("filtroVigencia", () => (this.currentPage = 1));
      this.$watch("fechaDesde", () => (this.currentPage = 1));
      this.$watch("fechaHasta", () => (this.currentPage = 1));
      this.$watch("criterioFecha", () => (this.currentPage = 1));

      this.$watch("searchHistorial", () => (this.historialPage = 1));
      this.$watch("fechaDesdeHistorial", () => (this.historialPage = 1));
      this.$watch("fechaHastaHistorial", () => (this.historialPage = 1));

      this.$watch("searchFormHistorial", () => (this.formHistorialPage = 1));
      this.$watch("searchFormFechaDesde", () => (this.formHistorialPage = 1));
      this.$watch("searchFormFechaHasta", () => (this.formHistorialPage = 1));
    },

    // ---------------------------------------------------
    // Carga de Datos
    // ---------------------------------------------------
    async getEmpresas() {
      try {
        const res = await fetch(`${API.empresas}/getall`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        this.empresas = Array.isArray(data) ? data : (data.datos || data.data || []);
      } catch (err) {
        console.warn("No se pudieron cargar empresas:", err.message);
      }
    },

    async getPersonas() {
      try {
        const res = await fetch(`${API.personas}/getall`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        this.personas = Array.isArray(data) ? data : (data.datos_person || data.datos || data.data || []);
      } catch (err) {
        console.warn("No se pudieron cargar personas:", err.message);
      }
    },

    async getRegistros() {
      this.cargando = true;
      try {
        const res = await fetch(`${API.seguridad_social}/getAll`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const lista = Array.isArray(data) ? data : (data.datos || data.data || []);
        this.registros = lista.map(item => this.normalizarRegistro(item));
      } catch (err) {
        console.warn("Aviso al consultar seguridad social:", err.message);
        // Fallback desde personas si aún no se han creado registros
        try {
          const resP = await fetch(`${API.personas}/getAll`);
          if (resP.ok) {
            const dataP = await resP.json();
            const listaP = dataP.datos_person || dataP.datos || dataP.data || (Array.isArray(dataP) ? dataP : []);
            this.registros = listaP.map(p => ({
              id: null,
              id_persona: p.id || p.id_persona,
              nombre_persona: p.nombre_persona || `${p.nombre || ''} ${p.apellido || ''}`.trim(),
              persona_tipo_doc: p.tipo_doc || p.tipoDoc || "CC",
              persona_identificacion: String(p.identificacion || p.numDoc || ""),
              persona_cargo: p.cargo || "General",
              responsable: "Sin asignar",
              anotaciones: "",
              id_empresa: null,
              ultima_empresa_contratista: "Sin registro",
              ultima_empresa_solicitante: "Sin registro",
              ultima_revision: null,
              fecha_vigencia: null,
              total_solicitudes: 0,
              historial: []
            }));
          }
        } catch (e) {
          this.registros = [];
        }
      } finally {
        this.cargando = false;
      }
    },

    normalizarRegistro(a) {
      const pNombre = a.persona_nombre || a.nombre || a.nombres || "";
      const pApellido = a.persona_apellido || a.apellido || a.apellidos || "";
      const full = a.nombre_persona || `${pNombre} ${pApellido}`.trim() || "Sin nombre";

      const vig = a.fecha_vigencia || a.fecha_consulta || null;
      const cleanVig = (vig && vig !== "None" && vig !== "null" && vig !== "Pendiente") ? String(vig).split("T")[0].split(" ")[0].trim() : null;

      return {
        id: a.id || null,
        id_persona: a.id_persona || a.id,
        persona_nombre: pNombre || full,
        persona_apellido: pApellido,
        nombre_persona: full,
        persona_tipo_doc: a.persona_tipo_doc || a.tipo_doc || a.tipoDoc || "CC",
        persona_identificacion: String(a.persona_identificacion || a.identificacion || a.numDoc || ""),
        responsable: (a.responsable && a.responsable !== "Sin asignar") ? a.responsable : "Sin asignar",
        ultimo_usuario_solicitud: a.ultimo_usuario_solicitud || "Sin registro",
        anotaciones: a.anotaciones || "",
        id_empresa: a.id_empresa || null,
        nombre_empresa: a.nombre_empresa || "Sin registro",
        ultima_empresa_contratista: a.ultima_empresa_contratista || a.nombre_contratista || a.ultima_empresa_solicitante || "Sin registro",
        ultima_empresa_solicitante: a.ultima_empresa_contratista || a.nombre_contratista || a.ultima_empresa_solicitante || "Sin registro",
        ultima_revision: a.ultima_revision || null,
        fecha_vigencia: cleanVig,
        fecha_consulta: cleanVig, // Alias
        fecha_creacion: a.fecha_creacion || null,
        total_solicitudes: Number(a.total_solicitudes || 0),
        historial: Array.isArray(a.historial) ? a.historial : []
      };
    },

    // ---------------------------------------------------
    // Métricas y Getters
    // ---------------------------------------------------
    get totalRegistros() {
      return this.registros.length;
    },

    get totalVigentes() {
      return this.registros.filter(a => this.getEstadoVigencia(a.fecha_vigencia).estado === 'vigente').length;
    },

    get totalPorVencer() {
      return this.registros.filter(a => this.getEstadoVigencia(a.fecha_vigencia).estado === 'por_vencer').length;
    },

    get totalVencidos() {
      return this.registros.filter(a => {
        const est = this.getEstadoVigencia(a.fecha_vigencia).estado;
        return est === 'vencido' || est === 'sin_revision';
      }).length;
    },

    get totalIngresosHistoricos() {
      return this.registros.reduce((acc, curr) => acc + (curr.total_solicitudes || 0), 0);
    },

    // ---------------------------------------------------
    // Lógica de Filtros y Búsqueda
    // ---------------------------------------------------
    get registrosFiltrados() {
      const q = (this.search || "").trim().toLowerCase();

      return this.registros.filter(a => {
        const nombreCompleto = this.obtenerNombreCompleto(a).toLowerCase();
        const matchQuery = !q ||
          nombreCompleto.includes(q) ||
          (a.persona_identificacion && a.persona_identificacion.toLowerCase().includes(q)) ||
          (a.persona_cargo && a.persona_cargo.toLowerCase().includes(q));

        // Filtro Vigencia
        const est = this.getEstadoVigencia(a.fecha_vigencia).estado;
        let matchVigencia = true;
        if (this.filtroVigencia === "vigente") {
          matchVigencia = est === "vigente";
        } else if (this.filtroVigencia === "por_vencer") {
          matchVigencia = est === "por_vencer";
        } else if (this.filtroVigencia === "vencido") {
          matchVigencia = est === "vencido" || est === "sin_revision";
        }

        // Filtro por Fechas (Desde / Hasta)
        let matchFecha = true;
        if (this.fechaDesde || this.fechaHasta) {
          const dateStr = this.criterioFecha === 'revision' ? a.ultima_revision : (a.fecha_vigencia || a.ultima_revision);
          if (!dateStr) {
            matchFecha = false;
          } else {
            const d = new Date(dateStr);
            if (isNaN(d.getTime())) {
              matchFecha = false;
            } else {
              if (this.fechaDesde) {
                const fd = new Date(this.fechaDesde + "T00:00:00");
                if (d < fd) matchFecha = false;
              }
              if (this.fechaHasta) {
                const fh = new Date(this.fechaHasta + "T23:59:59");
                if (d > fh) matchFecha = false;
              }
            }
          }
        }

        return matchQuery && matchVigencia && matchFecha;
      });
    },

    get totalPaginas() {
      return Math.max(1, Math.ceil(this.registrosFiltrados.length / this.pageSize));
    },

    get registrosPagina() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.registrosFiltrados.slice(start, start + this.pageSize);
    },

    get rangoMostrado() {
      if (this.registrosFiltrados.length === 0) return "0 de 0";
      const start = (this.currentPage - 1) * this.pageSize + 1;
      const end = Math.min(this.currentPage * this.pageSize, this.registrosFiltrados.length);
      return `${start}–${end} de ${this.registrosFiltrados.length}`;
    },

    // ---------------------------------------------------
    // Getters y Paginación para Historial (Modal 1)
    // ---------------------------------------------------
    get historialFiltrado() {
      const lista = (this.formSeguridadSocial?.historial && this.formSeguridadSocial.historial.length > 0)
        ? this.formSeguridadSocial.historial
        : (this.detalleHistorial?.historial || []);
      const q = (this.searchHistorial || "").trim().toLowerCase();

      return lista.filter(h => {
        const rad = String(h.codigo_radicado || "").toLowerCase();
        const emp = String(h.nombre_empresa || "").toLowerCase();
        const con = String(h.nombre_contratista || "").toLowerCase();
        const matchQuery = !q || rad.includes(q) || emp.includes(q) || con.includes(q);

        let matchFecha = true;
        if (this.fechaDesdeHistorial || this.fechaHastaHistorial) {
          const dateStr = h.fecha_solicitud || h.fecha_inicio || h.fecha_fin;
          if (!dateStr) {
            matchFecha = false;
          } else {
            const d = new Date(dateStr);
            if (isNaN(d.getTime())) {
              matchFecha = false;
            } else {
              if (this.fechaDesdeHistorial) {
                const fd = new Date(this.fechaDesdeHistorial + "T00:00:00");
                if (d < fd) matchFecha = false;
              }
              if (this.fechaHastaHistorial) {
                const fh = new Date(this.fechaHastaHistorial + "T23:59:59");
                if (d > fh) matchFecha = false;
              }
            }
          }
        }

        return matchQuery && matchFecha;
      });
    },

    get totalPaginasHistorial() {
      return Math.max(1, Math.ceil(this.historialFiltrado.length / this.historialPageSize));
    },

    get historialPagina() {
      const start = (this.historialPage - 1) * this.historialPageSize;
      return this.historialFiltrado.slice(start, start + this.historialPageSize);
    },

    get rangoHistorialMostrado() {
      if (this.historialFiltrado.length === 0) return "0 de 0";
      const start = (this.historialPage - 1) * this.historialPageSize + 1;
      const end = Math.min(this.historialPage * this.historialPageSize, this.historialFiltrado.length);
      return `${start}–${end} de ${this.historialFiltrado.length}`;
    },

    goToHistorialPage(n) {
      if (n >= 1 && n <= this.totalPaginasHistorial) {
        this.historialPage = n;
      }
    },

    // ---------------------------------------------------
    // Getters y Paginación Historial Formulario (Modal 2)
    // ---------------------------------------------------
    get formHistorialFiltrado() {
      const lista = this.formSeguridadSocial?.historial || [];
      const q = (this.searchFormHistorial || "").trim().toLowerCase();

      return lista.filter(h => {
        const rad = String(h.codigo_radicado || "").toLowerCase();
        const emp = String(h.nombre_empresa || "").toLowerCase();
        const con = String(h.nombre_contratista || "").toLowerCase();
        const matchQuery = !q || rad.includes(q) || emp.includes(q) || con.includes(q);

        let matchFecha = true;
        if (this.searchFormFechaDesde || this.searchFormFechaHasta) {
          const dateStr = h.fecha_solicitud || h.fecha_inicio || h.fecha_fin;
          if (!dateStr) {
            matchFecha = false;
          } else {
            const d = new Date(dateStr);
            if (isNaN(d.getTime())) {
              matchFecha = false;
            } else {
              if (this.searchFormFechaDesde) {
                const fd = new Date(this.searchFormFechaDesde + "T00:00:00");
                if (d < fd) matchFecha = false;
              }
              if (this.searchFormFechaHasta) {
                const fh = new Date(this.searchFormFechaHasta + "T23:59:59");
                if (d > fh) matchFecha = false;
              }
            }
          }
        }

        return matchQuery && matchFecha;
      });
    },

    get totalPaginasFormHistorial() {
      return Math.max(1, Math.ceil(this.formHistorialFiltrado.length / this.formHistorialPageSize));
    },

    get formHistorialPagina() {
      const start = (this.formHistorialPage - 1) * this.formHistorialPageSize;
      return this.formHistorialFiltrado.slice(start, start + this.formHistorialPageSize);
    },

    get rangoFormHistorialMostrado() {
      if (this.formHistorialFiltrado.length === 0) return "0 de 0";
      const start = (this.formHistorialPage - 1) * this.formHistorialPageSize + 1;
      const end = Math.min(this.formHistorialPage * this.formHistorialPageSize, this.formHistorialFiltrado.length);
      return `${start}–${end} de ${this.formHistorialFiltrado.length}`;
    },

    goToFormHistorialPage(n) {
      if (n >= 1 && n <= this.totalPaginasFormHistorial) {
        this.formHistorialPage = n;
      }
    },

    // ---------------------------------------------------
    // Helpers de Nombres e Iniciales
    // ---------------------------------------------------
    obtenerIniciales(item) {
      if (!item) return "SS";
      const n = (item.persona_nombre || item.nombre_persona || "").trim();
      const a = (item.persona_apellido || (item.nombre_persona ? item.nombre_persona.split(" ")[1] : "") || "").trim();
      const in1 = n ? n[0] : "";
      const in2 = a ? a[0] : "";
      return (in1 + in2).toUpperCase() || "SS";
    },

    obtenerNombreCompleto(item) {
      if (!item) return "Sin nombre";
      const full = (item.nombre_persona || `${item.persona_nombre || ''} ${item.persona_apellido || ''}`).trim();
      return full || "Sin nombre";
    },

    // ---------------------------------------------------
    // Helpers de Fechas y Vigencia Dictaminada por SST
    // ---------------------------------------------------
    parsearFechaLocal(fechaStr) {
      if (!fechaStr || fechaStr === "None" || fechaStr === "null" || fechaStr === "Pendiente" || fechaStr === "No registrada") return null;
      if (fechaStr instanceof Date) return fechaStr;
      const str = String(fechaStr).trim();
      if (/^\d{4}-\d{2}-\d{2}$/.test(str)) {
        const [y, m, d] = str.split('-').map(Number);
        return new Date(y, m - 1, d, 12, 0, 0);
      }
      if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}/.test(str)) {
        const clean = str.replace(' ', 'T').replace('Z', '');
        const [dPart, tPart] = clean.split('T');
        const [y, m, d] = dPart.split('-').map(Number);
        const timeParts = (tPart || '00:00:00').split(':').map(Number);
        return new Date(y, m - 1, d, timeParts[0] || 0, timeParts[1] || 0, timeParts[2] || 0);
      }
      return new Date(str);
    },

    getEstadoVigencia(fechaVigenciaStr) {
      if (!fechaVigenciaStr || fechaVigenciaStr === "Pendiente" || fechaVigenciaStr === "None" || fechaVigenciaStr === "null") {
        return {
          estado: 'sin_revision',
          etiqueta: 'Sin vigencia',
          textoDias: 'Pendiente SST',
          icono: 'fa-regular fa-clock',
          badgeClass: 'vigencia-badge-neon is-sin-revision',
          dotClass: 'bg-slate-400',
          dias: null
        };
      }

      const hoy = new Date();
      hoy.setHours(0, 0, 0, 0);

      const fechaLimite = this.parsearFechaLocal(fechaVigenciaStr);
      if (!fechaLimite || isNaN(fechaLimite.getTime())) {
        return {
          estado: 'sin_revision',
          etiqueta: 'Fecha inválida',
          textoDias: 'Fecha no válida',
          icono: 'fa-solid fa-circle-question',
          badgeClass: 'vigencia-badge-neon is-sin-revision',
          dotClass: 'bg-slate-400',
          dias: null
        };
      }
      fechaLimite.setHours(0, 0, 0, 0);

      const diffMs = fechaLimite.getTime() - hoy.getTime();
      const diffDias = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

      if (diffDias < 0) {
        const diasVencidos = Math.abs(diffDias);
        return {
          estado: 'vencido',
          etiqueta: `Vencida (${diasVencidos}d)`,
          textoDias: `Vencida hace ${diasVencidos} ${diasVencidos === 1 ? 'día' : 'días'}`,
          icono: 'fa-solid fa-circle-xmark',
          badgeClass: 'vigencia-badge-neon is-vencido',
          dotClass: 'bg-red-500',
          dias: diffDias
        };
      } else if (diffDias === 0) {
        return {
          estado: 'por_vencer',
          etiqueta: 'Vence hoy',
          textoDias: 'Vence hoy',
          icono: 'fa-solid fa-triangle-exclamation',
          badgeClass: 'vigencia-badge-neon is-por-vencer',
          dotClass: 'bg-amber-500',
          dias: 0
        };
      } else if (diffDias <= 5) {
        return {
          estado: 'por_vencer',
          etiqueta: `Vence en ${diffDias}d`,
          textoDias: `Por vencer en ${diffDias} ${diffDias === 1 ? 'día' : 'días'}`,
          icono: 'fa-solid fa-triangle-exclamation',
          badgeClass: 'vigencia-badge-neon is-por-vencer',
          dotClass: 'bg-amber-500',
          dias: diffDias
        };
      } else {
        return {
          estado: 'vigente',
          etiqueta: `Vigente (${diffDias}d)`,
          textoDias: `${diffDias} días de vigencia`,
          icono: 'fa-solid fa-circle-check',
          badgeClass: 'vigencia-badge-neon is-vigente',
          dotClass: 'bg-emerald-500',
          dias: diffDias
        };
      }
    },

    formatearFechaVisual(fechaStr) {
      if (!fechaStr || fechaStr === "None" || fechaStr === "null" || fechaStr === "Pendiente" || fechaStr === "No registrada" || fechaStr === "—") return null;
      try {
        const d = this.parsearFechaLocal(fechaStr);
        if (!d || isNaN(d.getTime())) return null;
        const meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
        const dia = String(d.getDate()).padStart(2, '0');
        const mes = meses[d.getMonth()];
        const anio = d.getFullYear();
        return `${dia} ${mes} ${anio}`;
      } catch {
        return null;
      }
    },

    formatearHoraVisual(fechaStr) {
      if (!fechaStr || fechaStr === "None" || fechaStr === "null" || fechaStr === "Pendiente" || fechaStr === "No registrada" || fechaStr === "—") return null;
      try {
        const d = this.parsearFechaLocal(fechaStr);
        if (!d || isNaN(d.getTime())) return null;
        const raw = String(fechaStr).trim();
        // Si no tiene hora en el string original (ej: YYYY-MM-DD), no inventar hora
        if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return null;

        let hh = d.getHours();
        const mm = String(d.getMinutes()).padStart(2, '0');
        const ampm = hh >= 12 ? 'PM' : 'AM';
        hh = hh % 12;
        hh = hh ? hh : 12;
        const hhStr = String(hh).padStart(2, '0');
        return `${hhStr}:${mm} ${ampm}`;
      } catch {
        return null;
      }
    },

    formatearFechaRevision(fechaStr) {
      if (!fechaStr || fechaStr === "None" || fechaStr === "null" || fechaStr === "No registrada" || fechaStr === "Pendiente") {
        return "No registrada";
      }
      try {
        const fecha = this.parsearFechaLocal(fechaStr);
        if (!fecha || isNaN(fecha.getTime())) return "No registrada";
        
        const esSoloFecha = /^\d{4}-\d{2}-\d{2}$/.test(String(fechaStr).trim());
        const opciones = {
          year: "numeric",
          month: "short",
          day: "numeric"
        };
        if (!esSoloFecha) {
          opciones.hour = "2-digit";
          opciones.minute = "2-digit";
        }
        return fecha.toLocaleDateString("es-CO", opciones);
      } catch {
        return "No registrada";
      }
    },

    formatearFecha(fechaStr, incluirHora = false) {
      if (!fechaStr || fechaStr === "None" || fechaStr === "null" || fechaStr === "Pendiente" || fechaStr === "No registrada") {
        return incluirHora ? "No registrada" : "Pendiente";
      }
      try {
        const fecha = this.parsearFechaLocal(fechaStr);
        if (!fecha || isNaN(fecha.getTime())) return incluirHora ? "No registrada" : "Pendiente";
        
        const esSoloFecha = /^\d{4}-\d{2}-\d{2}$/.test(String(fechaStr).trim());
        const opciones = {
          year: "numeric",
          month: "short",
          day: "numeric"
        };
        if (incluirHora && !esSoloFecha) {
          opciones.hour = "2-digit";
          opciones.minute = "2-digit";
        }
        return fecha.toLocaleDateString("es-CO", opciones);
      } catch {
        return fechaStr;
      }
    },

    formatearSoloFecha(fechaStr) {
      if (!fechaStr || fechaStr === "None" || fechaStr === "null") return "—";
      try {
        const str = String(fechaStr).trim().split("T")[0].split(" ")[0];
        const [y, m, d] = str.split("-");
        if (y && m && d) return `${d.padStart(2, "0")}/${m.padStart(2, "0")}/${y}`;
        return str;
      } catch {
        return fechaStr;
      }
    },

    formatearFechaVigencia(fechaStr) {
      if (!fechaStr || fechaStr === "None" || fechaStr === "null" || fechaStr === "Pendiente" || fechaStr === "No registrada" || fechaStr === "—") {
        return "Pendiente";
      }
      try {
        const fecha = this.parsearFechaLocal(fechaStr);
        if (!fecha || isNaN(fecha.getTime())) return "Pendiente";
        const opciones = {
          year: "numeric",
          month: "short",
          day: "numeric"
        };
        return fecha.toLocaleDateString("es-CO", opciones);
      } catch {
        return "Pendiente";
      }
    },

    // ---------------------------------------------------
    // Flatpickr Initializers
    // ---------------------------------------------------
    initFlatpickrFiltro(el, tipo) {
      if (typeof flatpickr === "undefined") return;
      const isDesde = tipo === "desde";
      const instance = flatpickr(el, {
        locale: flatpickr.l10ns?.es || "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        altInputClass: "text-xs bg-transparent border-0 p-0 text-[var(--text-primary)] dark:text-white focus:ring-0 focus:outline-none cursor-pointer w-20 font-medium placeholder:text-[var(--text-muted)]",
        disableMobile: "true",
        allowInput: false,
        placeholder: "dd/mm/aaaa",
        onChange: (selectedDates, dateStr) => {
          if (isDesde) {
            this.fechaDesde = dateStr;
            if (this.fpHastaInstance) this.fpHastaInstance.set("minDate", dateStr || null);
          } else {
            this.fechaHasta = dateStr;
            if (this.fpDesdeInstance) this.fpDesdeInstance.set("maxDate", dateStr || null);
          }
          this.currentPage = 1;
        }
      });
      if (isDesde) this.fpDesdeInstance = instance;
      else this.fpHastaInstance = instance;
    },

    initFlatpickrVigencia(el) {
      if (typeof flatpickr === "undefined" || !el) return;
      if (this.fpVigenciaModalInstance) {
        try { this.fpVigenciaModalInstance.destroy(); } catch (e) {}
      }
      const self = this;
      this.fpVigenciaModalInstance = flatpickr(el, {
        locale: flatpickr.l10ns?.es || "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        altInputClass: "input-field w-full pl-9 pr-3 py-2 text-xs sm:text-sm rounded-xl border border-[var(--paper-shadow)] cursor-pointer font-bold text-slate-800 dark:text-slate-100",
        disableMobile: "true",
        allowInput: true,
        placeholder: "Seleccionar fecha de vigencia...",
        onChange: (selectedDates, dateStr) => {
          self.formSeguridadSocial.fecha_vigencia = dateStr;
          self.formSeguridadSocial = { ...self.formSeguridadSocial, fecha_vigencia: dateStr };
        },
        onValueUpdate: (selectedDates, dateStr) => {
          self.formSeguridadSocial.fecha_vigencia = dateStr;
          self.formSeguridadSocial = { ...self.formSeguridadSocial, fecha_vigencia: dateStr };
        },
        onClose: (selectedDates, dateStr) => {
          if (dateStr) {
            self.formSeguridadSocial.fecha_vigencia = dateStr;
            self.formSeguridadSocial = { ...self.formSeguridadSocial, fecha_vigencia: dateStr };
          }
        }
      });

      if (this.fpVigenciaModalInstance.altInput) {
        this.fpVigenciaModalInstance.altInput.addEventListener('input', (e) => {
          const val = e.target.value.trim();
          if (/^\d{2}\/\d{2}\/\d{4}$/.test(val)) {
            const [d, m, y] = val.split('/');
            const iso = `${y}-${m}-${d}`;
            self.formSeguridadSocial.fecha_vigencia = iso;
            self.formSeguridadSocial = { ...self.formSeguridadSocial, fecha_vigencia: iso };
          }
        });
        this.fpVigenciaModalInstance.altInput.addEventListener('change', (e) => {
          const val = e.target.value.trim();
          if (/^\d{2}\/\d{2}\/\d{4}$/.test(val)) {
            const [d, m, y] = val.split('/');
            const iso = `${y}-${m}-${d}`;
            self.formSeguridadSocial.fecha_vigencia = iso;
            self.formSeguridadSocial = { ...self.formSeguridadSocial, fecha_vigencia: iso };
            try { self.fpVigenciaModalInstance.setDate(iso, false); } catch (_) {}
          }
        });
      }

      if (this.formSeguridadSocial.fecha_vigencia) {
        this.fpVigenciaModalInstance.setDate(this.formSeguridadSocial.fecha_vigencia, false);
      }
    },

    limpiarFechaVigenciaModal() {
      this.formSeguridadSocial.fecha_vigencia = null;
      this.formSeguridadSocial = { ...this.formSeguridadSocial, fecha_vigencia: null };
      if (this.fpVigenciaModalInstance) {
        this.fpVigenciaModalInstance.clear();
      }
    },

    initFlatpickrHistorial(el, tipo) {
      if (typeof flatpickr === "undefined") return;
      const isDesde = tipo === "desde";
      const instance = flatpickr(el, {
        locale: flatpickr.l10ns?.es || "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        altInputClass: "text-xs bg-transparent border-0 p-0 text-[var(--paper-ink)] dark:text-white focus:ring-0 focus:outline-none cursor-pointer w-20 font-medium placeholder:text-[var(--paper-muted)]",
        disableMobile: "true",
        allowInput: false,
        placeholder: "dd/mm/aaaa",
        onChange: (selectedDates, dateStr) => {
          if (isDesde) {
            this.fechaDesdeHistorial = dateStr;
            if (this.fpHistorialHastaInstance) this.fpHistorialHastaInstance.set("minDate", dateStr || null);
          } else {
            this.fechaHastaHistorial = dateStr;
            if (this.fpHistorialDesdeInstance) this.fpHistorialDesdeInstance.set("maxDate", dateStr || null);
          }
          this.historialPage = 1;
        }
      });
      if (isDesde) this.fpHistorialDesdeInstance = instance;
      else this.fpHistorialHastaInstance = instance;
    },

    initFlatpickrForm(el, tipo) {
      if (typeof flatpickr === "undefined") return;
      const isDesde = tipo === "desde";
      const instance = flatpickr(el, {
        locale: flatpickr.l10ns?.es || "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        altInputClass: "text-xs bg-transparent border-0 p-0 text-[var(--paper-ink)] dark:text-white focus:ring-0 focus:outline-none cursor-pointer w-20 font-medium placeholder:text-[var(--paper-muted)]",
        disableMobile: "true",
        allowInput: false,
        placeholder: "dd/mm/aaaa",
        onChange: (selectedDates, dateStr) => {
          if (isDesde) {
            this.searchFormFechaDesde = dateStr;
            if (this.fpFormHastaInstance) this.fpFormHastaInstance.set("minDate", dateStr || null);
          } else {
            this.searchFormFechaHasta = dateStr;
            if (this.fpFormDesdeInstance) this.fpFormDesdeInstance.set("maxDate", dateStr || null);
          }
          this.formHistorialPage = 1;
        }
      });
      if (isDesde) this.fpFormDesdeInstance = instance;
      else this.fpFormHastaInstance = instance;
    },

    limpiarFiltros() {
      this.search = "";
      this.filtroVigencia = "todos";
      this.fechaDesde = "";
      this.fechaHasta = "";
      this.criterioFecha = "vigencia";
      this.currentPage = 1;
      if (this.fpDesdeInstance) {
        this.fpDesdeInstance.clear();
        this.fpDesdeInstance.set("maxDate", null);
      }
      if (this.fpHastaInstance) {
        this.fpHastaInstance.clear();
        this.fpHastaInstance.set("minDate", null);
      }
    },

    limpiarFiltrosHistorial() {
      this.searchHistorial = "";
      this.fechaDesdeHistorial = "";
      this.fechaHastaHistorial = "";
      this.historialPage = 1;
      if (this.fpHistorialDesdeInstance) {
        this.fpHistorialDesdeInstance.clear();
        this.fpHistorialDesdeInstance.set("maxDate", null);
      }
      if (this.fpHistorialHastaInstance) {
        this.fpHistorialHastaInstance.clear();
        this.fpHistorialHastaInstance.set("minDate", null);
      }
    },

    limpiarFiltrosFormHistorial() {
      this.searchFormHistorial = "";
      this.searchFormFechaDesde = "";
      this.searchFormFechaHasta = "";
      this.formHistorialPage = 1;
      if (this.fpFormDesdeInstance) {
        this.fpFormDesdeInstance.clear();
        this.fpFormDesdeInstance.set("maxDate", null);
      }
      if (this.fpFormHastaInstance) {
        this.fpFormHastaInstance.clear();
        this.fpFormHastaInstance.set("minDate", null);
      }
    },

    // ---------------------------------------------------
    // Modales: Abrir y Cerrar Unificados
    // ---------------------------------------------------
    abrirSeguridadSocialModal(item) {
      this.abrirFormularioSeguridadSocial(item);
      this.showSeguridadSocialModal = true;
    },

    cerrarSeguridadSocialModal() {
      this.showSeguridadSocialModal = false;
      this.cerrarFormularioSeguridadSocial();
      this.cerrarHistorialSoloLectura();
    },

    abrirHistorialModal(item) {
      this.abrirSeguridadSocialModal(item);
    },

    async abrirHistorialSoloLectura(item) {
      this.cargandoHistorial = true;
      this.showHistorialModal = true;
      this.limpiarFiltrosHistorial();

      try {
        const res = await fetch(`${API.seguridad_social}/persona/${item.id_persona}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const norm = this.normalizarRegistro(data);
        this.detalleHistorial = { ...norm };
      } catch (err) {
        console.warn("Aviso al cargar historial SS:", err.message);
        this.detalleHistorial = { ...item };
      } finally {
        this.cargandoHistorial = false;
      }
    },

    cerrarHistorialSoloLectura() {
      this.showHistorialModal = false;
      this.limpiarFiltrosHistorial();
    },

    async abrirFormularioSeguridadSocial(item) {
      this.showFormModal = true;
      this.mensajeExito = "";
      this.mensajeError = "";
      this.limpiarFiltrosFormHistorial();

      // Pre-cargar datos conocidos inmediatamente
      this.formSeguridadSocial = { ...item };

      // Obtener el usuario SST activo autenticado en sesión
      let usuarioSST = "";
      try {
        const sesion = (typeof getAuthSession === 'function') 
          ? getAuthSession() 
          : JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || '{}');
        const nombres = sesion?.nombres || sesion?.nombre || "";
        const apellidos = sesion?.apellidos || sesion?.apellido || "";
        usuarioSST = `${nombres} ${apellidos}`.trim() || sesion?.usuario || "";
      } catch (e) {}

      // El responsable en el modal es el usuario SST activo que realiza la actualización
      this.formSeguridadSocial.responsable = usuarioSST || "Usuario SST";

      try {
        const res = await fetch(`${API.seguridad_social}/persona/${item.id_persona}`);
        if (res.ok) {
          const data = await res.json();
          const norm = this.normalizarRegistro(data);
          this.formSeguridadSocial = { 
            ...norm,
            // Forzar responsable al usuario SST en sesión
            responsable: usuarioSST || norm.responsable || "Usuario SST"
          };
        }
      } catch (err) {
        console.warn("Aviso al cargar seguridad social para edición:", err.message);
      }

      // Inicializar y cargar fecha en Flatpickr
      this.$nextTick(() => {
        const el = this.$refs.fpVigenciaInput;
        if (el) {
          if (!this.fpVigenciaModalInstance) {
            this.initFlatpickrVigencia(el);
          } else {
            if (this.formSeguridadSocial.fecha_vigencia) {
              this.fpVigenciaModalInstance.setDate(this.formSeguridadSocial.fecha_vigencia, false);
            } else {
              this.fpVigenciaModalInstance.clear();
            }
          }
        }
      });
    },

    cerrarFormularioSeguridadSocial() {
      this.showFormModal = false;
      this.mensajeExito = "";
      this.mensajeError = "";
      this.limpiarFiltrosFormHistorial();
    },

    // ---------------------------------------------------
    // Guardar / Dictaminar Vigencia (Manejado por SST)
    // ---------------------------------------------------
    async guardarSeguridadSocial() {
      if (!this.formSeguridadSocial.id_persona) return;
      this.guardando = true;
      this.mensajeExito = "";
      this.mensajeError = "";

      // Extraer fecha final con máxima tolerancia (selectedDates, input, altInput, ref)
      let fv = this.formSeguridadSocial.fecha_vigencia;
      if (this.fpVigenciaModalInstance) {
        if (this.fpVigenciaModalInstance.selectedDates && this.fpVigenciaModalInstance.selectedDates.length > 0) {
          fv = this.fpVigenciaModalInstance.formatDate(this.fpVigenciaModalInstance.selectedDates[0], "Y-m-d");
        } else if (this.fpVigenciaModalInstance.altInput && this.fpVigenciaModalInstance.altInput.value) {
          const raw = this.fpVigenciaModalInstance.altInput.value.trim();
          if (/^\d{2}\/\d{2}\/\d{4}$/.test(raw)) {
            const [d, m, y] = raw.split('/');
            fv = `${y}-${m}-${d}`;
          } else if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
            fv = raw;
          }
        } else if (this.fpVigenciaModalInstance.input && this.fpVigenciaModalInstance.input.value) {
          const raw = this.fpVigenciaModalInstance.input.value.trim();
          if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) fv = raw;
        }
      }
      if (!fv && this.$refs.fpVigenciaInput && this.$refs.fpVigenciaInput.value) {
        const raw = this.$refs.fpVigenciaInput.value.trim();
        if (/^\d{2}\/\d{2}\/\d{4}$/.test(raw)) {
          const [d, m, y] = raw.split('/');
          fv = `${y}-${m}-${d}`;
        } else if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
          fv = raw;
        }
      }

      if (fv) {
        fv = String(fv).split('T')[0].split(' ')[0].trim();
      }

      if (!fv || fv === 'null' || fv === 'None' || fv === 'Pendiente') {
        this.mensajeError = "Por favor seleccione una fecha límite de vigencia dictaminada por SST.";
        this.guardando = false;
        return;
      }
      this.formSeguridadSocial.fecha_vigencia = fv;

      // Asegurar responsable SST autenticado en sesión
      let usuarioSST = "";
      try {
        const sesion = (typeof getAuthSession === 'function') 
          ? getAuthSession() 
          : JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || '{}');
        const nombres = sesion?.nombres || sesion?.nombre || "";
        const apellidos = sesion?.apellidos || sesion?.apellido || "";
        usuarioSST = `${nombres} ${apellidos}`.trim() || sesion?.usuario || "";
      } catch (e) {}

      const responsableFinal = usuarioSST || this.formSeguridadSocial.responsable || "Usuario SST";
      this.formSeguridadSocial.responsable = responsableFinal;

      const payload = {
        fecha_vigencia: fv,
        anotaciones: this.formSeguridadSocial.anotaciones || "",
        responsable: responsableFinal
      };

      try {
        const headers = { "Content-Type": "application/json" };
        const token = (typeof getAuthToken === 'function') ? getAuthToken() : null;
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${API.seguridad_social}/persona/${this.formSeguridadSocial.id_persona}`, {
          method: "PATCH",
          headers: headers,
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Error HTTP ${res.status}`);
        }

        this.mensajeExito = "Seguridad social y vigencia dictaminada guardada exitosamente.";

        // Actualizar reactivamente la fila en la tabla
        const idBuscado = Number(this.formSeguridadSocial.id_persona);
        const idx = this.registros.findIndex(r => Number(r.id_persona) === idBuscado);
        if (idx !== -1) {
          this.registros[idx].fecha_vigencia = fv;
          this.registros[idx].fecha_consulta = fv;
          this.registros[idx].responsable = responsableFinal;
          this.registros[idx].anotaciones = this.formSeguridadSocial.anotaciones;
          this.registros[idx].ultima_revision = new Date().toISOString().replace('T', ' ').substring(0, 19);
        }

        // Mostrar SweetAlert si está disponible
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'success',
            title: '¡Vigencia Dictaminada!',
            text: `Vigencia registrada hasta ${this.formatearFecha(fv, false)} por ${responsableFinal}.`,
            timer: 2000,
            showConfirmButton: false,
            timerProgressBar: true
          });
        }

        // Recargar datos en segundo plano
        this.getRegistros();

        setTimeout(() => {
          this.cerrarFormularioSeguridadSocial();
        }, 1200);

      } catch (err) {
        console.error("Error al guardar seguridad social:", err);
        this.mensajeError = err.message || "No fue posible guardar la seguridad social.";
      } finally {
        this.guardando = false;
      }
    },

    copiarRadicado(codigo) {
      if (!codigo) return;
      navigator.clipboard.writeText(codigo).then(() => {
        this.copiadoFeedback = codigo;
        setTimeout(() => {
          if (this.copiadoFeedback === codigo) this.copiadoFeedback = null;
        }, 1800);
      });
    },

    copiarCodigo(codigo) {
      return this.copiarRadicado(codigo);
    },

    // ---------------------------------------------------
    // Aliases de compatibilidad total para plantillas
    // ---------------------------------------------------
    get formAntecedente() { return this.formSeguridadSocial; },
    set formAntecedente(v) { this.formSeguridadSocial = v; },
    get antecedentesPagina() { return this.registrosPagina; },
    get antecedentesFiltrados() { return this.registrosFiltrados; },
    abrirFormularioAntecedentes(item) { return this.abrirFormularioSeguridadSocial(item); },
    cerrarFormularioAntecedentes() { return this.cerrarFormularioSeguridadSocial(); },
    guardarAntecedente() { return this.guardarSeguridadSocial(); },
    abrirHistorialModal(item) { return this.abrirHistorialSoloLectura(item); },
    cerrarHistorialModal() { return this.cerrarHistorialSoloLectura(); },

    // ---------------------------------------------------
    // Paginación Principal
    // ---------------------------------------------------
    prevPage() {
      if (this.currentPage > 1) this.currentPage--;
    },
    nextPage() {
      if (this.currentPage < this.totalPaginas) this.currentPage++;
    },
    goToPage(n) {
      if (n >= 1 && n <= this.totalPaginas) this.currentPage = n;
    }
  };
}

window.seguridadSocialModule = seguridadSocialModule;
// Compatibilidad de alias si la plantilla llama antecedentesModule
window.antecedentesModule = window.antecedentesModule || seguridadSocialModule;
