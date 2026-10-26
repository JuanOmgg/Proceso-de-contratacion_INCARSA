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

    // Modal 5: Descarga de Certificados (Selección de Empresa o ZIP)
    showCertificadoModal: false,
    personaCertificado: null,
    formularioSeleccionadoCertificado: null,
    empresaSeleccionadaCertificado: "INCARSA",

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
          const matchForm = Array.isArray(item.formularios_realizados) && item.formularios_realizados.some(f => 
            String(f.nombre_formulario || "").toLowerCase().includes(term)
          );
          return nombre.includes(term) || doc.includes(term) || cargo.includes(term) || empresa.includes(term) || resp.includes(term) || matchForm;
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

    getFormVigenciaInfo(f) {
      if (!f) return { badgeClass: "", icono: "", texto: "—" };
      const estado = f.estado_vigencia || "sin_induccion";
      const dias = f.dias_restantes;

      switch (estado) {
        case "vigente":
          return {
            badgeClass: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30",
            dotClass: "bg-emerald-500",
            icono: "fa-solid fa-circle-check",
            texto: dias !== null ? `${dias}d rest. (Vigente)` : "Vigente"
          };
        case "por_vencer":
          return {
            badgeClass: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30",
            dotClass: "bg-amber-500",
            icono: "fa-solid fa-triangle-exclamation",
            texto: dias !== null ? `${dias}d rest. (Por vencer)` : "Por vencer"
          };
        case "vencido":
          return {
            badgeClass: "bg-red-500/15 text-red-600 dark:text-red-400 border border-red-500/30",
            dotClass: "bg-red-500",
            icono: "fa-solid fa-circle-xmark",
            texto: dias !== null ? `Vencido (${Math.abs(dias)}d)` : "Vencido"
          };
        default:
          return {
            badgeClass: "bg-slate-500/15 text-slate-500 border border-slate-500/30",
            dotClass: "bg-slate-400",
            icono: "fa-solid fa-clock-rotate-left",
            texto: "Sin vigencia"
          };
      }
    },

    // ---------------------------------------------------
    // Modal Ficha Ticket (Detalle Solo Lectura)
    // ---------------------------------------------------
    abrirFichaInduccion(item) {
      this.detalleInduccion = { 
        ...item,
        formularios_realizados: item.formularios_realizados ? [...item.formularios_realizados] : []
      };
      this.showFichaModal = true;
    },

    cerrarFichaModal() {
      this.showFichaModal = false;
      this.detalleInduccion = {};
    },

    // ---------------------------------------------------
    // Modal Descarga de Certificados (Selección de Empresa / ZIP)
    // ---------------------------------------------------
    abrirModalCertificado(item, formItem = null) {
      if (!item) return;
      const forms = item.formularios_realizados || [];
      if (forms.length === 0 && !item.id_formulario) {
        if (typeof Swal !== "undefined") {
          Swal.fire({
            icon: "info",
            title: "Sin inducción registrada",
            text: "Esta persona aún no cuenta con inducciones aprobadas para descargar certificados.",
            confirmButtonColor: "#7c3aed"
          });
        } else {
          alert("Esta persona aún no cuenta con inducciones aprobadas para descargar certificados.");
        }
        return;
      }

      this.personaCertificado = { 
        ...item,
        nombre_completo: item.nombre_completo || `${item.persona_nombre || ""} ${item.persona_apellido || ""}`.trim()
      };
      if (formItem && formItem.id_formulario) {
        this.formularioSeleccionadoCertificado = formItem.id_formulario;
      } else if (forms.length > 0 && forms[0].id_formulario) {
        this.formularioSeleccionadoCertificado = forms[0].id_formulario;
      } else {
        this.formularioSeleccionadoCertificado = item.id_formulario || null;
      }
      this.empresaSeleccionadaCertificado = "INCARSA";
      this.showCertificadoModal = true;
    },

    cerrarModalCertificado() {
      this.showCertificadoModal = false;
      this.personaCertificado = null;
      this.formularioSeleccionadoCertificado = null;
    },

    descargarCertificadoEmpresa(empresaNombre) {
      if (!this.personaCertificado || !this.personaCertificado.id_persona) return;
      const pid = this.personaCertificado.id_persona;
      const fid = this.formularioSeleccionadoCertificado || "";
      const emp = empresaNombre ? encodeURIComponent(empresaNombre) : "INCARSA";
      const url = `/api/v1/inducciones/persona/${pid}/certificado?empresa=${emp}&descargar=true` + (fid ? `&id_form=${fid}` : "");
      
      const link = document.createElement("a");
      link.href = url;
      link.target = "_blank";
      document.body.appendChild(link);
      link.click();
      setTimeout(() => {
        if (link.parentNode) link.parentNode.removeChild(link);
      }, 100);
    },

    descargarCertificadosZip() {
      if (!this.personaCertificado || !this.personaCertificado.id_persona) return;
      const pid = this.personaCertificado.id_persona;
      const fid = this.formularioSeleccionadoCertificado || "";
      const url = `/api/v1/inducciones/persona/${pid}/certificado/zip` + (fid ? `?id_form=${fid}` : "");
      
      const link = document.createElement("a");
      link.href = url;
      link.target = "_blank";
      document.body.appendChild(link);
      link.click();
      setTimeout(() => {
        if (link.parentNode) link.parentNode.removeChild(link);
      }, 100);
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
    get esFechaHoy() {
      const hoy = new Date();
      const hoyIso = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, "0")}-${String(hoy.getDate()).padStart(2, "0")}`;
      return this.formInduccion.fecha_induccion === hoyIso;
    },

    actualizarFechasInduccion(nuevaFechaStr) {
      if (!nuevaFechaStr) return;
      let y, m, d;
      const strLimpia = String(nuevaFechaStr).split("T")[0].split(" ")[0];
      if (strLimpia.includes("-")) {
        const partes = strLimpia.split("-");
        y = parseInt(partes[0], 10);
        m = parseInt(partes[1], 10);
        d = parseInt(partes[2], 10);
      } else {
        const fechaObj = new Date(nuevaFechaStr);
        if (isNaN(fechaObj.getTime())) return;
        y = fechaObj.getFullYear();
        m = fechaObj.getMonth() + 1;
        d = fechaObj.getDate();
      }

      const isoInd = `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      this.formInduccion.fecha_induccion = isoInd;
      this.formInduccion.fecha_induccion_texto = this.formatearFecha(isoInd);

      // Calcular vigencia exacta (+1 Año)
      const yVig = y + 1;
      let dVig = d;
      if (m === 2 && d === 29) {
        dVig = 28; // Manejo seguro de año bisiesto
      }
      const isoVig = `${yVig}-${String(m).padStart(2, "0")}-${String(dVig).padStart(2, "0")}`;
      this.formInduccion.fecha_vigencia = isoVig;
      this.formInduccion.fecha_vigencia_texto = this.formatearFecha(isoVig);

      // Calcular días restantes de vigencia a partir de hoy
      const hoy = new Date();
      hoy.setHours(0, 0, 0, 0);
      const fechaVigObj = new Date(yVig, m - 1, dVig);
      fechaVigObj.setHours(0, 0, 0, 0);
      const diffMs = fechaVigObj.getTime() - hoy.getTime();
      const diffDias = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
      this.formInduccion.dias_restantes = diffDias;
    },

    fijarFechaHoy() {
      const hoy = new Date();
      const hoyIso = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, "0")}-${String(hoy.getDate()).padStart(2, "0")}`;
      this.actualizarFechasInduccion(hoyIso);
      if (this.$refs.fechaInduccionInput && this.$refs.fechaInduccionInput._flatpickr) {
        this.$refs.fechaInduccionInput._flatpickr.setDate(hoyIso, true);
      }
    },

    initFlatpickrFechaInduccion(el) {
      if (typeof flatpickr === "undefined" || !el) return;
      if (el._flatpickr) {
        el._flatpickr.destroy();
      }
      const self = this;
      flatpickr(el, {
        locale: (typeof flatpickr !== "undefined" && flatpickr.l10ns && flatpickr.l10ns.es) ? flatpickr.l10ns.es : "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d M Y",
        altInputClass: "text-xs font-bold text-[var(--paper-ink)] dark:text-white bg-transparent border-0 p-0 focus:ring-0 cursor-pointer w-full truncate mt-0.5",
        defaultDate: self.formInduccion.fecha_induccion || "today",
        onChange(selectedDates, dateStr) {
          if (dateStr) {
            self.actualizarFechasInduccion(dateStr);
          }
        }
      });
    },

    normalizarAFechaIso(val) {
      if (!val || val === "None" || val === "null" || val === "—") return null;
      try {
        const str = String(val).trim();
        const limpia = str.replace("T", " ").split(" ")[0].trim();
        if (/^\d{4}-\d{2}-\d{2}$/.test(limpia)) {
          return limpia;
        }
        if (limpia.includes("/")) {
          const partes = limpia.split("/");
          if (partes.length === 3) {
            const d = String(parseInt(partes[0], 10)).padStart(2, "0");
            const m = String(parseInt(partes[1], 10)).padStart(2, "0");
            const y = parseInt(partes[2], 10);
            if (!isNaN(y) && y > 1900) {
              return `${y}-${m}-${d}`;
            }
          }
        }
        const dObj = new Date(str);
        if (!isNaN(dObj.getTime())) {
          const y = dObj.getFullYear();
          const m = String(dObj.getMonth() + 1).padStart(2, "0");
          const d = String(dObj.getDate()).padStart(2, "0");
          return `${y}-${m}-${d}`;
        }
        return null;
      } catch (e) {
        return null;
      }
    },

    abrirFormularioInduccion(item) {
      const hoy = new Date();
      const hoyIso = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, "0")}-${String(hoy.getDate()).padStart(2, "0")}`;

      const fechaRegistradaIso = this.normalizarAFechaIso(item.fecha_induccion);
      const fechaInicialIso = fechaRegistradaIso || hoyIso;

      this.formInduccion = {
        id_persona: item.id_persona,
        persona_nombre: item.nombre_completo || `${item.persona_nombre || ""} ${item.persona_apellido || ""}`.trim(),
        persona_identificacion: item.identificacion,
        persona_tipo_doc: item.tipo_doc || "CC",
        persona_cargo: item.cargo || "General",
        id_empresa: item.id_empresa || null,
        nombre_empresa: item.nombre_empresa || "Sin empresa asignada",
        responsable: this.auditorActualNombre,
        fecha_induccion: fechaInicialIso,
        fecha_induccion_texto: this.formatearFecha(fechaInicialIso),
        fecha_vigencia: "",
        fecha_vigencia_texto: "",
        dias_restantes: 365,
        anotaciones: item.anotaciones || ""
      };

      this.actualizarFechasInduccion(fechaInicialIso);

      this.mensajeExitoForm = "";
      this.mensajeErrorForm = "";
      this.guardandoInduccion = false;
      this.showFormModal = true;

      this.$nextTick(() => {
        if (this.$refs.fechaInduccionInput) {
          if (this.$refs.fechaInduccionInput._flatpickr) {
            this.$refs.fechaInduccionInput._flatpickr.setDate(this.formInduccion.fecha_induccion, true);
          } else {
            this.initFlatpickrFechaInduccion(this.$refs.fechaInduccionInput);
          }
        }
      });
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
          id_empresa: this.formInduccion.id_empresa || null,
          fecha_induccion: this.formInduccion.fecha_induccion,
          fecha_vigencia: this.formInduccion.fecha_vigencia
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
          dias_restantes: this.formInduccion.dias_restantes
        };

        // Sincronizar inmediatamente en memoria para evitar discrepancias
        const idPersonaActual = this.formInduccion.id_persona;
        const itemEnLista = this.inducciones.find(i => i.id_persona === idPersonaActual);
        if (itemEnLista) {
          itemEnLista.fecha_induccion = this.formInduccion.fecha_induccion;
          itemEnLista.fecha_vigencia = this.formInduccion.fecha_vigencia;
          itemEnLista.responsable = payload.responsable;
          itemEnLista.anotaciones = payload.anotaciones;
          itemEnLista.dias_restantes = this.formInduccion.dias_restantes;
          itemEnLista.estado_vigencia = this.formInduccion.dias_restantes < 0 ? "vencido" : (this.formInduccion.dias_restantes <= 30 ? "por_vencer" : "vigente");
        }

        if (this.detalleInduccion && this.detalleInduccion.id_persona === idPersonaActual) {
          this.detalleInduccion.fecha_induccion = this.formInduccion.fecha_induccion;
          this.detalleInduccion.fecha_vigencia = this.formInduccion.fecha_vigencia;
          this.detalleInduccion.responsable = payload.responsable;
          this.detalleInduccion.anotaciones = payload.anotaciones;
          this.detalleInduccion.dias_restantes = this.formInduccion.dias_restantes;
          this.detalleInduccion.estado_vigencia = itemEnLista ? itemEnLista.estado_vigencia : "vigente";
        }

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
