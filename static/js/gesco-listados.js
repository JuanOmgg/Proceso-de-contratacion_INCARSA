/**
 * ============================================================================
 * gesco-listados.js — Gestión, Consulta y Control de Formularios GESCO
 * ============================================================================
 * Componentes Alpine.js para la tabla y tarjetas de métricas de Formularios GESCO.
 * Conectado directamente a las APIs REST del backend (FastAPI).
 */

function formulariosGescoCards() {
  return {
    totalFormularios: 0,
    totalActivos: 0,
    totalInactivos: 0,
    promedioVigencia: 365,
    cargando: true,

    init() {
      window.addEventListener("formularios-gesco-updated", (e) => {
        const list = e.detail || [];
        this.actualizarConteo(list);
      });
      this.cargarInicial();
    },

    actualizarConteo(lista) {
      this.totalFormularios = lista.length;
      this.totalActivos = lista.filter(f => f.is_active === 1 || f.is_active === true || f.is_active === "1").length;
      this.totalInactivos = lista.filter(f => f.is_active === 0 || f.is_active === false || f.is_active === "0").length;

      if (lista.length > 0) {
        const sumaVigencias = lista.reduce((acc, curr) => acc + (Number(curr.vigencia) || 365), 0);
        this.promedioVigencia = Math.round(sumaVigencias / lista.length);
      } else {
        this.promedioVigencia = 365;
      }

      this.cargando = false;
    },

    async cargarInicial() {
      this.cargando = true;
      try {
        const token = typeof getAuthToken === "function" ? getAuthToken() : null;
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const url = (window.API && window.API.formularios_gesco)
          ? `${window.API.formularios_gesco}/getAll`
          : "/api/v1/formularios-gesco/getAll";

        const res = await fetch(url, { headers });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        const formularios = Array.isArray(data) ? data : (data.datos || data.data || []);
        this.actualizarConteo(formularios);
      } catch (error) {
        console.warn("Aviso al consultar formularios GESCO para tarjetas:", error.message);
        this.actualizarConteo([]);
      } finally {
        this.cargando = false;
      }
    }
  };
}

function formulariosGescoTable() {
  return {
    // ---------------------------------------------------
    // Datos
    // ---------------------------------------------------
    formularios: [],
    cargando: true,

    // ---------------------------------------------------
    // Filtros / búsqueda
    // ---------------------------------------------------
    search: "",
    filtroTipo: "", // '' | 'TODOS' | 'Contratista' | 'Proveedor' | 'Visitante'
    filtroEstado: "todos", // 'todos' | 'activos' | 'inactivos'

    // ---------------------------------------------------
    // Paginación
    // ---------------------------------------------------
    currentPage: 1,
    pageSize: 6,

    // ---------------------------------------------------
    // Detalle de Formulario (Modal Ticket)
    // ---------------------------------------------------
    showDetailModal: false,
    formularioDetalle: null,

    // ---------------------------------------------------
    // Estadísticas y Analíticas
    // ---------------------------------------------------
    showStatsModal: false,
    cargandoStats: false,
    estadisticasData: null,
    statsSearchPregunta: "",
    statsFiltroCategoria: "TODAS",

    // ---------------------------------------------------
    // Eliminación
    // ---------------------------------------------------
    showDeleteModal: false,
    deleteModalOpen: false,
    formularioAEliminar: null,
    eliminando: false,

    // ---------------------------------------------------
    // Catálogos auxiliares
    // ---------------------------------------------------
    tiposPersonalDisponibles: [
      { id: "TODOS", label: "Todos los tipos" },
      { id: "Contratista", label: "Contratistas" },
      { id: "Proveedor", label: "Proveedores" },
      { id: "Visitante", label: "Visitantes" },
      { id: "Interno", label: "Personal Interno" }
    ],

    // ---------------------------------------------------
    // Inicialización
    // ---------------------------------------------------
    async init() {
      await this.getFormularios();

      this.$watch("search", () => (this.currentPage = 1));
      this.$watch("filtroTipo", () => (this.currentPage = 1));
      this.$watch("filtroEstado", () => (this.currentPage = 1));
      this.$watch("pageSize", () => (this.currentPage = 1));
    },

    notificarCambio() {
      window.dispatchEvent(new CustomEvent("formularios-gesco-updated", { detail: this.formularios }));
    },

    // ---------------------------------------------------
    // Carga desde API
    // ---------------------------------------------------
    async getFormularios() {
      this.cargando = true;
      try {
        const token = typeof getAuthToken === "function" ? getAuthToken() : null;
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const url = (window.API && window.API.formularios_gesco)
          ? `${window.API.formularios_gesco}/getAll`
          : "/api/v1/formularios-gesco/getAll";

        const res = await fetch(url, { headers });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        this.formularios = Array.isArray(data) ? data : (data.datos || data.data || []);
        this.notificarCambio();
      } catch (error) {
        console.error("Error al cargar formularios GESCO:", error);
        this.formularios = [];
      } finally {
        this.cargando = false;
      }
    },

    // ---------------------------------------------------
    // Filtrado reactivo
    // ---------------------------------------------------
    get formulariosFiltrados() {
      const texto = this.search.trim().toLowerCase();
      const tipo = this.filtroTipo.trim().toUpperCase();

      return this.formularios.filter(f => {
        if (!f) return false;

        const nombre = String(f.nombre || "").toLowerCase();
        const descripcion = String(f.descripcion || "").toLowerCase();
        const tipoPersonal = String(f.tipo_personal || "").toLowerCase();
        const vigenciaStr = `${f.vigencia || 365} días`;

        const matchTexto =
          !texto ||
          nombre.includes(texto) ||
          descripcion.includes(texto) ||
          tipoPersonal.includes(texto) ||
          vigenciaStr.includes(texto);

        let matchTipo = true;
        if (tipo) {
          const tpUpper = String(f.tipo_personal || "").toUpperCase();
          matchTipo = (tipo === "TODOS")
            ? tpUpper.includes("TODOS") || tpUpper === "TODOS"
            : tpUpper.includes(tipo) || tpUpper.includes("TODOS");
        }

        const isActive = f.is_active === 1 || f.is_active === true || f.is_active === "1";
        const matchEstado =
          this.filtroEstado === "todos" ||
          (this.filtroEstado === "activos" && isActive) ||
          (this.filtroEstado === "inactivos" && !isActive);

        return matchTexto && matchTipo && matchEstado;
      });
    },

    get totalFormularios() {
      return this.formularios.length;
    },
    get totalActivos() {
      return this.formularios.filter(f => f.is_active === 1 || f.is_active === true || f.is_active === "1").length;
    },
    get totalInactivos() {
      return this.formularios.filter(f => f.is_active === 0 || f.is_active === false || f.is_active === "0").length;
    },

    // ---------------------------------------------------
    // Paginación computada
    // ---------------------------------------------------
    get totalPaginas() {
      return Math.max(1, Math.ceil(this.formulariosFiltrados.length / this.pageSize));
    },
    get formulariosPagina() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.formulariosFiltrados.slice(start, start + this.pageSize);
    },
    get rangoMostrado() {
      if (this.formulariosFiltrados.length === 0) return "0 de 0";
      const start = (this.currentPage - 1) * this.pageSize + 1;
      const end = Math.min(this.currentPage * this.pageSize, this.formulariosFiltrados.length);
      return `${start}–${end} de ${this.formulariosFiltrados.length}`;
    },
    get paginasVisibles() {
      const total = this.totalPaginas;
      let startP = Math.max(1, this.currentPage - 2);
      let endP = Math.min(total, startP + 4);
      startP = Math.max(1, endP - 4);

      const pages = [];
      for (let i = startP; i <= endP; i++) {
        pages.push(i);
      }
      return pages;
    },

    cambiarPagina(pagina) {
      if (pagina >= 1 && pagina <= this.totalPaginas) {
        this.currentPage = pagina;
      }
    },

    goToPage(pagina) {
      this.cambiarPagina(pagina);
    },

    resetPage() {
      this.currentPage = 1;
    },

    limpiarFiltros() {
      this.search = "";
      this.filtroTipo = "";
      this.filtroEstado = "todos";
      this.currentPage = 1;
    },

    // ---------------------------------------------------
    // Acciones: Toggle Activo / Inactivo
    // ---------------------------------------------------
    async toggleActivo(formulario) {
      if (!formulario || !formulario.id) return;

      const estadoPrevio = formulario.is_active;
      const nuevoEstado = !(estadoPrevio === 1 || estadoPrevio === true || estadoPrevio === "1");

      // Optimistic UI update
      formulario.is_active = nuevoEstado;

      try {
        const token = typeof getAuthToken === "function" ? getAuthToken() : null;
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const url = (window.API && window.API.formularios_gesco)
          ? `${window.API.formularios_gesco}/${formulario.id}/toggle-activo`
          : `/api/v1/formularios-gesco/${formulario.id}/toggle-activo`;

        const res = await fetch(url, {
          method: "PATCH",
          headers
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || errData.mensaje || `HTTP ${res.status}`);
        }

        const data = await res.json();
        formulario.is_active = data.is_active !== undefined ? data.is_active : nuevoEstado;
        this.notificarCambio();
      } catch (error) {
        // Revertir optimistic update
        formulario.is_active = estadoPrevio;
        console.error("Error al alternar estado del formulario:", error);
        alert(`No se pudo cambiar el estado: ${error.message}`);
      }
    },

    // ---------------------------------------------------
    // Modal de Detalle (Ticket Style)
    // ---------------------------------------------------
    verDetalle(formulario) {
      this.formularioDetalle = { ...formulario };
      this.showDetailModal = true;
    },

    cerrarDetalle() {
      this.showDetailModal = false;
      this.formularioDetalle = null;
    },

    // ---------------------------------------------------
    // Modal y Métodos de Estadísticas y Aciertos
    // ---------------------------------------------------
    async abrirEstadisticas(formulario) {
      if (!formulario || !formulario.id) return;
      this.formularioDetalle = { ...formulario };
      this.showStatsModal = true;
      this.cargandoStats = true;
      this.estadisticasData = null;
      this.statsSearchPregunta = "";
      this.statsFiltroCategoria = "TODAS";

      try {
        const token = typeof getAuthToken === "function" ? getAuthToken() : null;
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const apiBase = (window.API && window.API.formularios_gesco)
          ? window.API.formularios_gesco
          : "/api/v1/formularios-gesco";
        const url = `${apiBase}/${formulario.id}/estadisticas`;

        const res = await fetch(url, { headers });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || errData.mensaje || `HTTP ${res.status}`);
        }
        const data = await res.json();
        this.estadisticasData = data;
      } catch (error) {
        console.error("Error al cargar estadísticas del formulario:", error);
        alert(`No se pudieron cargar las estadísticas: ${error.message}`);
        this.showStatsModal = false;
      } finally {
        this.cargandoStats = false;
      }
    },

    cerrarEstadisticas() {
      this.showStatsModal = false;
      this.estadisticasData = null;
      this.cargandoStats = false;
    },

    get preguntasEstadisticasFiltradas() {
      if (!this.estadisticasData || !Array.isArray(this.estadisticasData.estadisticas_preguntas)) {
        return [];
      }
      let list = this.estadisticasData.estadisticas_preguntas;
      const cat = this.statsFiltroCategoria;
      if (cat && cat !== "TODAS") {
        list = list.filter(p => (p.tipo_pregunta || "GENERAL").toUpperCase() === cat.toUpperCase());
      }
      const q = String(this.statsSearchPregunta || "").trim().toLowerCase();
      if (q) {
        list = list.filter(p => (p.enunciado || "").toLowerCase().includes(q));
      }
      return list;
    },

    // ---------------------------------------------------
    // Modal y Acción de Eliminación
    // ---------------------------------------------------
    confirmarEliminar(formulario) {
      this.formularioAEliminar = formulario;
      this.showDeleteModal = true;
      this.deleteModalOpen = true;
    },

    cerrarModalEliminar() {
      this.showDeleteModal = false;
      this.deleteModalOpen = false;
      this.formularioAEliminar = null;
      this.eliminando = false;
    },

    async eliminarFormulario() {
      if (!this.formularioAEliminar || !this.formularioAEliminar.id) return;

      this.eliminando = true;
      const idEliminar = this.formularioAEliminar.id;

      try {
        const token = typeof getAuthToken === "function" ? getAuthToken() : null;
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const url = (window.API && window.API.formularios_gesco)
          ? `${window.API.formularios_gesco}/${idEliminar}`
          : `/api/v1/formularios-gesco/${idEliminar}`;

        const res = await fetch(url, {
          method: "DELETE",
          headers
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || errData.mensaje || `HTTP ${res.status}`);
        }

        const data = await res.json();
        this.cerrarModalEliminar();

        // Recargar lista actualizada
        await this.getFormularios();

        // Si fue soft-delete (desactivado) o hard-delete
        if (data.mensaje) {
          // Toast o aviso sutil
          console.log("Resultado eliminación:", data.mensaje);
        }
      } catch (error) {
        console.error("Error al eliminar formulario:", error);
        alert(`Error al eliminar formulario: ${error.message}`);
      } finally {
        this.eliminando = false;
      }
    },

    // ---------------------------------------------------
    // Utilidades de Visualización
    // ---------------------------------------------------
    formatearFecha(fechaStr) {
      if (!fechaStr) return "—";
      try {
        const d = new Date(fechaStr);
        if (isNaN(d.getTime())) return String(fechaStr).split("T")[0] || fechaStr;
        return d.toLocaleDateString("es-CO", {
          day: "2-digit",
          month: "short",
          year: "numeric"
        });
      } catch (e) {
        return fechaStr;
      }
    },

    formatearFechaCorta(fechaStr) {
      if (!fechaStr) return "";
      try {
        const d = new Date(fechaStr);
        if (isNaN(d.getTime())) return String(fechaStr).split("T")[0];
        return d.toLocaleDateString("es-CO", { day: "2-digit", month: "short" });
      } catch (e) {
        return "";
      }
    },

    tipoPersonalPills(tipoPersonalStr) {
      if (!tipoPersonalStr) return ["TODOS"];
      return String(tipoPersonalStr)
        .split(",")
        .map(t => t.trim())
        .filter(Boolean);
    },

    vigenciaLegible(dias) {
      const num = Number(dias) || 365;
      if (num === 365) return "365 días (1 año)";
      if (num === 730) return "730 días (2 años)";
      if (num === 180) return "180 días (6 meses)";
      if (num === 90) return "90 días (3 meses)";
      if (num === 30) return "30 días (1 mes)";
      return `${num} días`;
    }
  };
}

// Registro global para compatibilidad con scripts inline de Jinja2
window.formulariosGescoCards = formulariosGescoCards;
window.formulariosGescoTable = formulariosGescoTable;
