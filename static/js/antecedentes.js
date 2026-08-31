/**
 * Lógica de Antecedentes y Seguimiento por Persona · INCARSA
 */

function antecedentesModule() {
  return {
    // ---------------------------------------------------
    // Estado y Datos
    // ---------------------------------------------------
    antecedentes: [],
    empresas: [],
    personas: [],
    cargando: true,

    // Filtros y búsqueda
    search: "",
    filtroVigencia: "todos", // 'todos', 'vigente', 'por_vencer', 'vencido'
    fechaDesde: "",
    fechaHasta: "",
    criterioFecha: "consulta", // 'consulta' (Vigencia +1 año) o 'revision' (Última Revisión)

    // Paginación principal
    currentPage: 1,
    pageSize: 8,

    // Filtros y paginación en Modal de Historial (Modal 1)
    searchHistorial: "",
    fechaDesdeHistorial: "",
    fechaHastaHistorial: "",
    historialPage: 1,
    historialPageSize: 5,

    // Filtros y paginación en Modal de Formulario (Modal 2)
    searchFormHistorial: "",
    searchFormFechaDesde: "",
    searchFormFechaHasta: "",
    formHistorialPage: 1,
    formHistorialPageSize: 5,

    // Modal Formulario de Antecedentes y Detalles (Actualiza vigencia)
    showFormModal: false,
    cargandoDetalle: false,
    guardando: false,
    mensajeExito: "",
    mensajeError: "",
    copiadoFeedback: null, // ID del radicado copiado recientemente

    formAntecedente: {
      id: null,
      id_persona: null,
      persona_nombre: "",
      persona_apellido: "",
      persona_tipo_doc: "CC",
      persona_identificacion: "",
      persona_cargo: "",
      responsable: "",
      anotaciones: "",
      id_empresa: null,
      ultima_empresa_solicitante: "",
      ultima_revision: null,
      fecha_consulta: null,
      total_solicitudes: 0,
      historial: []
    },

    // Modal Exclusivo de Historial de Solicitudes y Observaciones (Solo Lectura, NO actualiza vigencia)
    showHistorialModal: false,
    cargandoHistorial: false,
    detalleHistorial: {
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
      ultima_empresa_solicitante: "",
      ultima_revision: null,
      fecha_consulta: null,
      total_solicitudes: 0,
      historial: []
    },

    // ---------------------------------------------------
    // Inicialización
    // ---------------------------------------------------
    async init() {
      await Promise.all([
        this.getEmpresas(),
        this.getAntecedentes(),
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
    // Carga de Empresas (Para información referencial)
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
            const person = await fetch(`${API.personas}/getall`);
            if (!person.ok) throw new Error(`HTTP ${person.status}`);
            const data = await person.json();
            this.personas = Array.isArray(data) ? data : (data.datos || data.data || []);            
        } catch (error) {
            console.warn("No fue posible cargar las personas: ", error.message);            
        }
    },

    // ---------------------------------------------------
    // Carga de Listado de Antecedentes
    // ---------------------------------------------------
    async getAntecedentes() {
      this.cargando = true;
      try {
        const res = await fetch(`${API.antecedentes}/getAll`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        
        const lista = data.data || data.datos || (Array.isArray(data) ? data : []);
        this.antecedentes = lista.map(item => this.normalizarAntecedente(item));
      } catch (err) {
        console.warn("Aviso al consultar antecedentes:", err.message);
        // Fallback desde personas si aún no se han creado registros
        try {
          const resP = await fetch(`${API.personas}/getAll`);
          if (resP.ok) {
            const dataP = await resP.json();
            const listaP = dataP.datos_person || dataP.datos || dataP.data || (Array.isArray(dataP) ? dataP : []);
            this.antecedentes = listaP.map(p => ({
              id: null,
              id_persona: p.id || p.id_persona,
              nombre_persona: p.nombre_persona,
              persona_tipo_doc: p.tipo_doc || p.tipoDoc || "CC",
              persona_identificacion: String(p.identificacion || p.numDoc || ""),
              persona_cargo: p.cargo || "General",
              responsable: "",
              anotaciones: "",
              id_empresa: null,
              ultima_empresa_solicitante: "Sin registro",
              ultima_revision: null,
              fecha_consulta: null,
              total_solicitudes: 0
            }));
          }
        } catch (e) {
          this.antecedentes = [];
        }
      } finally {
        this.cargando = false;
      }
    },

    parsearFechaLocal(fechaStr) {
      if (!fechaStr || fechaStr === "None" || fechaStr === "null" || fechaStr === "Pendiente" || fechaStr === "No registrada") return null;
      if (fechaStr instanceof Date) return fechaStr;
      const str = String(fechaStr).trim();
      // Formato YYYY-MM-DD (solo fecha)
      if (/^\d{4}-\d{2}-\d{2}$/.test(str)) {
        const [y, m, d] = str.split('-').map(Number);
        return new Date(y, m - 1, d, 12, 0, 0); // Mediodía local evita saltos de zona horaria
      }
      // Formato YYYY-MM-DD HH:mm:ss o YYYY-MM-DDTHH:mm:ss
      if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}/.test(str)) {
        const clean = str.replace(' ', 'T').replace('Z', '');
        const [dPart, tPart] = clean.split('T');
        const [y, m, d] = dPart.split('-').map(Number);
        const timeParts = (tPart || '00:00:00').split(':').map(Number);
        return new Date(y, m - 1, d, timeParts[0] || 0, timeParts[1] || 0, timeParts[2] || 0);
      }
      return new Date(str);
    },

    obtenerFechaHoraLocal(d = new Date()) {
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const dia = String(d.getDate()).padStart(2, '0');
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      const ss = String(d.getSeconds()).padStart(2, '0');
      return `${y}-${m}-${dia} ${hh}:${mm}:${ss}`;
    },

    obtenerFechaMasUnAnio(fechaBase = null) {
      const d = fechaBase ? (this.parsearFechaLocal(fechaBase) || new Date()) : new Date();
      d.setFullYear(d.getFullYear() + 1);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const dia = String(d.getDate()).padStart(2, '0');
      return `${y}-${m}-${dia}`;
    },

    calcularFechaConsulta(ultimaRevisionStr, fechaConsultaExistente = null) {
      if (fechaConsultaExistente && fechaConsultaExistente !== "None" && fechaConsultaExistente !== "null" && fechaConsultaExistente !== "Pendiente") {
        const clean = String(fechaConsultaExistente).split("T")[0].split(" ")[0].trim();
        if (/^\d{4}-\d{2}-\d{2}$/.test(clean)) return clean;
      }
      if (!ultimaRevisionStr || ultimaRevisionStr === "None" || ultimaRevisionStr === "null" || ultimaRevisionStr === "No registrada") return null;
      try {
        return this.obtenerFechaMasUnAnio(ultimaRevisionStr);
      } catch {
        return null;
      }
    },

    normalizarAntecedente(a) {
      const ultimaRevision = a.ultima_revision || null;
      const fechaConsulta = this.calcularFechaConsulta(ultimaRevision, a.fecha_consulta);
      
      const pNombre = a.persona_nombre || a.nombre || a.nombres || "";
      const pApellido = a.persona_apellido || a.apellido || a.apellidos || "";
      const full = a.nombre_persona || `${pNombre} ${pApellido}`.trim() || "Sin nombre";

      return {
        id: a.id || null,
        id_persona: a.id_persona || a.id,
        persona_nombre: pNombre || full,
        persona_apellido: pApellido,
        nombre_persona: full,
        persona_tipo_doc: a.persona_tipo_doc || a.tipo_doc || a.tipoDoc || "CC",
        persona_identificacion: String(a.persona_identificacion || a.identificacion || a.numDoc || ""),
        persona_cargo: a.persona_cargo || a.cargo || "General",
        responsable: a.responsable || "",
        anotaciones: a.anotaciones || "",
        id_empresa: a.id_empresa || null,
        ultima_empresa_solicitante: a.ultima_empresa_solicitante || a.nombre_empresa || "Sin registro",
        ultima_revision: ultimaRevision,
        fecha_consulta: fechaConsulta,
        fecha_creacion: a.fecha_creacion || null,
        total_solicitudes: Number(a.total_solicitudes || 0),
        historial: Array.isArray(a.historial) ? a.historial : []
      };
    },

    // ---------------------------------------------------
    // Métricas y Getters
    // ---------------------------------------------------
    get totalRegistros() {
      return this.antecedentes.length;
    },

    get totalVigentes() {
      return this.antecedentes.filter(a => this.getEstadoVigencia(a.fecha_consulta).estado === 'vigente').length;
    },

    get totalPorVencer() {
      return this.antecedentes.filter(a => this.getEstadoVigencia(a.fecha_consulta).estado === 'por_vencer').length;
    },

    get totalVencidos() {
      return this.antecedentes.filter(a => this.getEstadoVigencia(a.fecha_consulta).estado === 'vencido' || this.getEstadoVigencia(a.fecha_consulta).estado === 'sin_revision').length;
    },

    get totalIngresosHistoricos() {
      return this.antecedentes.reduce((acc, curr) => acc + (curr.total_solicitudes || 0), 0);
    },

    // ---------------------------------------------------
    // Lógica de Filtros y Búsqueda
    // ---------------------------------------------------
    get antecedentesFiltrados() {
      const q = this.search.trim().toLowerCase();

      return this.antecedentes.filter(a => {
        const nombreCompleto = `${a.persona_nombre || ''} ${a.persona_apellido || ''} ${a.nombre_persona || ''}`.toLowerCase();
        const matchQuery = !q ||
          nombreCompleto.includes(q) ||
          (a.persona_identificacion && a.persona_identificacion.toLowerCase().includes(q)) ||
          (a.persona_cargo && a.persona_cargo.toLowerCase().includes(q));

        // Filtro Vigencia
        const est = this.getEstadoVigencia(a.fecha_consulta).estado;
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
          const dateStr = this.criterioFecha === 'revision' ? a.ultima_revision : (a.fecha_consulta || a.ultima_revision);
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
      return Math.max(1, Math.ceil(this.antecedentesFiltrados.length / this.pageSize));
    },

    get antecedentesPagina() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.antecedentesFiltrados.slice(start, start + this.pageSize);
    },

    get rangoMostrado() {
      if (this.antecedentesFiltrados.length === 0) return "0 de 0";
      const start = (this.currentPage - 1) * this.pageSize + 1;
      const end = Math.min(this.currentPage * this.pageSize, this.antecedentesFiltrados.length);
      return `${start}–${end} de ${this.antecedentesFiltrados.length}`;
    },

    // ---------------------------------------------------
    // Getters y Paginación para Historial (Modal 1)
    // ---------------------------------------------------
    get historialFiltrado() {
      const lista = this.detalleHistorial?.historial || [];
      const q = (this.searchHistorial || "").trim().toLowerCase();

      return lista.filter(h => {
        const rad = String(h.codigo_radicado || "").toLowerCase();
        const emp = String(h.nombre_empresa || "").toLowerCase();
        const con = String(h.nombre_contratista || "").toLowerCase();
        const matchQuery = !q || rad.includes(q) || emp.includes(q) || con.includes(q);

        // Filtro por Fechas de Solicitud / Periodo
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
    // Getters y Paginación para Historial en Formulario (Modal 2)
    // ---------------------------------------------------
    get formHistorialFiltrado() {
      const lista = this.formAntecedente?.historial || [];
      const q = (this.searchFormHistorial || "").trim().toLowerCase();

      return lista.filter(h => {
        const rad = String(h.codigo_radicado || "").toLowerCase();
        const emp = String(h.nombre_empresa || "").toLowerCase();
        const con = String(h.nombre_contratista || "").toLowerCase();
        const matchQuery = !q || rad.includes(q) || emp.includes(q) || con.includes(q);

        // Filtro por Fechas en Formulario
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
      if (!item) return "P";
      const n = (item.persona_nombre || item.nombre_persona || "").trim();
      const a = (item.persona_apellido || (item.nombre_persona ? item.nombre_persona.split(" ")[1] : "") || "").trim();
      const in1 = n ? n[0] : "";
      const in2 = a ? a[0] : "";
      return (in1 + in2).toUpperCase() || "P";
    },

    obtenerNombreCompleto(item) {
      if (!item) return "Sin nombre";
      const full = (item.nombre_persona || `${item.persona_nombre || ''} ${item.persona_apellido || ''}`).trim();
      return full || "Sin nombre";
    },

    // ---------------------------------------------------
    // Helpers de Fechas y Vigencia
    // ---------------------------------------------------
    getEstadoVigencia(fechaConsultaStr) {
      if (!fechaConsultaStr) {
        return {
          estado: 'sin_revision',
          etiqueta: 'Sin revisión',
          textoDias: 'Sin revisión',
          icono: 'fa-solid fa-circle-question',
          badgeClass: 'bg-slate-100 text-slate-600 border-slate-200',
          dotClass: 'bg-slate-400',
          dias: null
        };
      }

      const hoy = new Date();
      hoy.setHours(0, 0, 0, 0);

      const fechaLimite = this.parsearFechaLocal(fechaConsultaStr);
      if (!fechaLimite || isNaN(fechaLimite.getTime())) {
        return {
          estado: 'sin_revision',
          etiqueta: 'Fecha inválida',
          textoDias: 'Fecha inválida',
          icono: 'fa-solid fa-circle-question',
          badgeClass: 'bg-slate-100 text-slate-600 border-slate-200',
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
          etiqueta: `Vencido (${diasVencidos}d)`,
          textoDias: `Vencido hace ${diasVencidos} ${diasVencidos === 1 ? 'día' : 'días'}`,
          icono: 'fa-solid fa-circle-xmark',
          badgeClass: 'bg-red-50 text-red-700 border-red-200',
          dotClass: 'bg-red-500',
          dias: diffDias
        };
      } else if (diffDias === 0) {
        return {
          estado: 'por_vencer',
          etiqueta: 'Vence hoy',
          textoDias: 'Vence hoy',
          icono: 'fa-solid fa-triangle-exclamation',
          badgeClass: 'bg-amber-50 text-amber-700 border-amber-200',
          dotClass: 'bg-amber-500',
          dias: 0
        };
      } else if (diffDias <= 30) {
        return {
          estado: 'por_vencer',
          etiqueta: `Por vencer (${diffDias}d)`,
          textoDias: `${diffDias} ${diffDias === 1 ? 'día restante' : 'días restantes'}`,
          icono: 'fa-solid fa-triangle-exclamation',
          badgeClass: 'bg-amber-50 text-amber-700 border-amber-200',
          dotClass: 'bg-amber-500',
          dias: diffDias
        };
      } else {
        return {
          estado: 'vigente',
          etiqueta: `Vigente (${diffDias}d)`,
          textoDias: `${diffDias} días restantes`,
          icono: 'fa-solid fa-circle-check',
          badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          dotClass: 'bg-emerald-500',
          dias: diffDias
        };
      }
    },

    formatearFecha(fechaStr, incluirHora = false) {
      if (!fechaStr || fechaStr === "Pendiente" || fechaStr === "No registrada") return fechaStr || "Pendiente";
      try {
        const fecha = this.parsearFechaLocal(fechaStr);
        if (!fecha || isNaN(fecha.getTime())) return fechaStr;
        
        // Si el string original es solo fecha YYYY-MM-DD, nunca incluir hora
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
      const str = String(fechaStr).trim();
      if (str.includes("T")) return str.split("T")[0];
      if (str.includes(" ")) return str.split(" ")[0];
      return str;
    },

    // ---------------------------------------------------
    // Copiar al Portapapeles con Feedback
    // ---------------------------------------------------
    async copiarCodigo(codigo) {
      if (!codigo) return;
      try {
        await navigator.clipboard.writeText(codigo);
        this.copiadoFeedback = codigo;
        setTimeout(() => {
          if (this.copiadoFeedback === codigo) {
            this.copiadoFeedback = null;
          }
        }, 2000);
      } catch (err) {
        console.warn("No se pudo copiar automáticamente:", err);
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
      this.filtroVigencia = "todos";
      this.fechaDesde = "";
      this.fechaHasta = "";
      this.criterioFecha = "consulta";
      this.currentPage = 1;
    },

    // ---------------------------------------------------
    // ABRIR MODAL DE DETALLE Y FORMULARIO DE ANTECEDENTES
    // (Auto-actualiza 'ultima_revision' a hoy y 'fecha_consulta' a +1 año)
    // ---------------------------------------------------
    async abrirFormularioAntecedentes(item) {
      const idPersona = item.id_persona || item.id;
      this.cargandoDetalle = true;
      this.mensajeExito = "";
      this.mensajeError = "";
      this.copiadoFeedback = null;
      this.searchFormHistorial = "";
      this.searchFormFechaDesde = "";
      this.searchFormFechaHasta = "";
      this.formHistorialPage = 1;
      this.showFormModal = true;

      // Calcular hoy como nueva última revisión local y exactamente +1 año como nueva fecha de consulta (YYYY-MM-DD)
      const ahora = new Date();
      const nuevaRevision = this.obtenerFechaHoraLocal(ahora);
      const nuevaConsulta = this.obtenerFechaMasUnAnio(ahora);

      this.formAntecedente = {
        id: item.id || null,
        id_persona: idPersona,
        persona_nombre: item.persona_nombre || "",
        persona_apellido: item.persona_apellido || "",
        persona_tipo_doc: item.persona_tipo_doc || "CC",
        persona_identificacion: String(item.persona_identificacion || ""),
        persona_cargo: item.persona_cargo || "General",
        responsable: item.responsable || "",
        anotaciones: item.anotaciones || "",
        id_empresa: item.id_empresa || null,
        ultima_empresa_solicitante: item.ultima_empresa_solicitante || "Sin registro previo",
        ultima_revision: nuevaRevision,
        fecha_consulta: nuevaConsulta,
        total_solicitudes: item.total_solicitudes || (item.historial ? item.historial.length : 0),
        historial: Array.isArray(item.historial) ? item.historial : []
      };

      // Actualizar de inmediato en la tabla local
      const idx = this.antecedentes.findIndex(a => a.id_persona === idPersona);
      if (idx > -1) {
        this.antecedentes[idx] = {
          ...this.antecedentes[idx],
          ultima_revision: nuevaRevision,
          fecha_consulta: nuevaConsulta
        };
      }

      try {
        const payloadSync = {
          ultima_revision: nuevaRevision,
          fecha_consulta: nuevaConsulta ? nuevaConsulta.split("T")[0] : null
        };

        const res = await fetch(`${API.antecedentes}/persona/${idPersona}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payloadSync)
        });

        if (res.ok) {
          const resData = await res.json().catch(() => ({}));
          const data = resData.data || resData;

          if (data && typeof data === 'object') {
            if (data.id) this.formAntecedente.id = data.id;
            if (data.responsable) this.formAntecedente.responsable = data.responsable;
            if (data.anotaciones) this.formAntecedente.anotaciones = data.anotaciones;
            if (data.historial && Array.isArray(data.historial)) this.formAntecedente.historial = data.historial;
            if (data.total_solicitudes) this.formAntecedente.total_solicitudes = data.total_solicitudes;
            
            const revisionFinal = data.ultima_revision || nuevaRevision;
            const consultaFinal = this.calcularFechaConsulta(revisionFinal, data.fecha_consulta);

            this.formAntecedente.ultima_revision = revisionFinal;
            this.formAntecedente.fecha_consulta = consultaFinal;

            if (idx > -1) {
              this.antecedentes[idx] = {
                ...this.antecedentes[idx],
                id: data.id || this.antecedentes[idx].id,
                responsable: this.formAntecedente.responsable,
                anotaciones: this.formAntecedente.anotaciones,
                ultima_revision: revisionFinal,
                fecha_consulta: consultaFinal,
                total_solicitudes: this.formAntecedente.total_solicitudes
              };
            }
          }
        }
      } catch (err) {
        console.warn("Aviso al sincronizar vigencia con backend:", err.message);
      } finally {
        this.cargandoDetalle = false;
      }
    },

    cerrarFormularioAntecedentes() {
      this.showFormModal = false;
      this.mensajeExito = "";
      this.mensajeError = "";
    },

    // ---------------------------------------------------
    // MODAL DE HISTORIAL (SOLO LECTURA, NO ACTUALIZA VIGENCIA)
    // ---------------------------------------------------
    async abrirHistorialModal(item) {
      const idPersona = item.id_persona || item.id;
      this.cargandoHistorial = true;
      this.copiadoFeedback = null;
      this.searchHistorial = "";
      this.fechaDesdeHistorial = "";
      this.fechaHastaHistorial = "";
      this.historialPage = 1;
      this.showHistorialModal = true;

      // Asignar datos previos conocidos
      this.detalleHistorial = {
        id: item.id || null,
        id_persona: idPersona,
        persona_nombre: item.persona_nombre || "",
        persona_apellido: item.persona_apellido || "",
        persona_tipo_doc: item.persona_tipo_doc || "CC",
        persona_identificacion: String(item.persona_identificacion || ""),
        persona_cargo: item.persona_cargo || "General",
        responsable: item.responsable || "",
        anotaciones: item.anotaciones || "",
        id_empresa: item.id_empresa || null,
        ultima_empresa_solicitante: item.ultima_empresa_solicitante || "Sin registro",
        ultima_revision: item.ultima_revision,
        fecha_consulta: item.fecha_consulta || this.calcularFechaConsulta(item.ultima_revision),
        total_solicitudes: item.total_solicitudes || (item.historial ? item.historial.length : 0),
        historial: Array.isArray(item.historial) ? item.historial : []
      };

      try {
        const res = await fetch(`${API.antecedentes}/persona/${idPersona}?actualizar_revision=false`);
        if (res.ok) {
          const resData = await res.json().catch(() => ({}));
          const data = resData.data || resData;

          if (data && typeof data === 'object') {
            this.detalleHistorial = {
              id: data.id || this.detalleHistorial.id,
              id_persona: data.id_persona || idPersona,
              persona_nombre: data.persona_nombre || this.detalleHistorial.persona_nombre,
              persona_apellido: data.persona_apellido || this.detalleHistorial.persona_apellido,
              persona_tipo_doc: data.persona_tipo_doc || this.detalleHistorial.persona_tipo_doc,
              persona_identificacion: String(data.persona_identificacion || this.detalleHistorial.persona_identificacion),
              persona_cargo: data.persona_cargo || this.detalleHistorial.persona_cargo,
              responsable: data.responsable || this.detalleHistorial.responsable,
              anotaciones: data.anotaciones || this.detalleHistorial.anotaciones,
              id_empresa: data.id_empresa || this.detalleHistorial.id_empresa,
              ultima_empresa_solicitante: data.ultima_empresa_solicitante || this.detalleHistorial.ultima_empresa_solicitante,
              ultima_revision: data.ultima_revision || this.detalleHistorial.ultima_revision,
              fecha_consulta: this.calcularFechaConsulta(data.ultima_revision || this.detalleHistorial.ultima_revision, data.fecha_consulta || this.detalleHistorial.fecha_consulta),
              total_solicitudes: data.total_solicitudes || (data.historial ? data.historial.length : this.detalleHistorial.total_solicitudes),
              historial: Array.isArray(data.historial) ? data.historial : this.detalleHistorial.historial
            };
          }
        }
      } catch (err) {
        console.warn("Aviso al cargar detalle de historial:", err.message);
      } finally {
        this.cargandoHistorial = false;
      }
    },

    cerrarHistorialModal() {
      this.showHistorialModal = false;
    },

    // ---------------------------------------------------
    // Guardar Manualmente Responsable y Anotaciones
    // (La última empresa se gestiona automáticamente por solicitudes)
    // ---------------------------------------------------
    async guardarAntecedente() {
      if (!this.formAntecedente.id_persona) return;

      this.guardando = true;
      this.mensajeExito = "";
      this.mensajeError = "";

      const fechaConsultaSincronizada = this.calcularFechaConsulta(this.formAntecedente.ultima_revision, this.formAntecedente.fecha_consulta);
      this.formAntecedente.fecha_consulta = fechaConsultaSincronizada;

      const fechaSoloDate = fechaConsultaSincronizada ? fechaConsultaSincronizada.split("T")[0] : null;

      const payload = {
        responsable: this.formAntecedente.responsable ? this.formAntecedente.responsable.trim() : null,
        anotaciones: this.formAntecedente.anotaciones ? this.formAntecedente.anotaciones.trim() : null,
        ultima_revision: this.formAntecedente.ultima_revision,
        fecha_consulta: fechaSoloDate
      };

      try {
        const res = await fetch(`${API.antecedentes}/persona/${this.formAntecedente.id_persona}`, {
          method: "PATCH",
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
          } else if (err.detail && typeof err.detail === "object") {
            errorMsg = JSON.stringify(err.detail);
          }
          throw new Error(errorMsg);
        }

        const dataRes = await res.json();
        const data = dataRes.data || dataRes;

        // Actualizar datos locales del formulario
        if (data.responsable !== undefined) this.formAntecedente.responsable = data.responsable;
        if (data.anotaciones !== undefined) this.formAntecedente.anotaciones = data.anotaciones;
        if (data.ultima_revision !== undefined) this.formAntecedente.ultima_revision = data.ultima_revision;
        if (data.fecha_consulta !== undefined) this.formAntecedente.fecha_consulta = data.fecha_consulta;

        // Actualizar en la lista general
        const idx = this.antecedentes.findIndex(a => a.id_persona === this.formAntecedente.id_persona);
        if (idx > -1) {
          this.antecedentes[idx] = {
            ...this.antecedentes[idx],
            responsable: this.formAntecedente.responsable,
            anotaciones: this.formAntecedente.anotaciones,
            ultima_revision: this.formAntecedente.ultima_revision,
            fecha_consulta: fechaConsultaSincronizada
          };
        }

        this.mensajeExito = "¡Responsable y vigencia guardados exitosamente!";
        setTimeout(() => {
          this.mensajeExito = "";
        }, 3000);

      } catch (err) {
        console.error("Error al guardar antecedentes:", err);
        this.mensajeError = `Error al guardar: ${err.message}`;
      } finally {
        this.guardando = false;
      }
    }
  };
}