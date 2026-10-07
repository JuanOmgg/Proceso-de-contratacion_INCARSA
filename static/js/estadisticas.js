/**
 * estadisticas.js — Lógica interactiva del Módulo de Estadísticas de Ingreso a Plantas
 * PSI / INCARSA
 * 
 * Gestiona:
 * - Carga de filtros (fechas, plantas, estados).
 * - Deduplicación estricta de personas registradas en múltiples solicitudes.
 * - Tarjetas KPIs con estética neón.
 * - Gráficos interactivos de tendencia diaria y distribución por planta con Chart.js.
 * - Tabla con búsqueda, paginación y modal de inspección detallada de personas por día y planta.
 */

document.addEventListener('alpine:init', () => {
  Alpine.data('estadisticasApp', () => ({
    cargando: false,
    cargandoDetalle: false,
    plantas: [],
    
    // Filtros
    filtroRapido: 'mes_actual',
    dropdownPlantasOpen: false,
    inputPlantaTexto: '',
    filtros: {
      fecha_inicio: '',
      fecha_fin: '',
      id_planta: '',
      estado: 'APROBADO'
    },

    // KPIs
    kpis: {
      total_personas_unicas_periodo: 0,
      total_ingresos_acumulados: 0,
      total_personas_en_espera: 0,
      total_solicitudes_en_espera: 0,
      promedio_diario: 0,
      dias_consultados: 0,
      dia_pico: { fecha: null, total: 0 },
      planta_mayor_afluencia: { planta: 'Ninguna', total: 0 }
    },

    // Datos recibidos
    serie_tiempo: [],
    distribucion_plantas: [],
    registros: [],

    // Búsqueda y Paginación en tabla
    search: '',
    filtroFechaTabla: '',
    paginaActual: 1,
    porPagina: 12,

    // Modal de Detalle
    modalDetalleAbierto: false,
    detalleHeader: {
      fecha: '',
      fecha_formateada: '',
      planta: '',
      id_planta: null,
      total_personas: 0
    },
    personasDetalle: [],
    searchPersonaModal: '',
    paginaModal: 1,
    porPaginaModal: 3,

    // Instancias de Chart.js y Flatpickr
    chartTendencia: null,
    chartPlantas: null,
    fpInicio: null,
    fpFin: null,
    fpTablaInstance: null,

    async init() {
      this.aplicarRangoRapido('mes_actual', false);
      await this.cargarPlantas();
      await this.cargarEstadisticas();
      this.escucharCambioTema();
    },

    initFlatpickrInicio(el) {
      if (typeof flatpickr === "undefined" || !el) return;
      this.fpInicio = flatpickr(el, {
        locale: flatpickr.l10ns?.es || "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        altInputClass: "input-field w-full pl-9 pr-3 py-2 text-xs sm:text-sm rounded-lg cursor-pointer font-medium text-[var(--text-primary)] bg-[var(--bg-subtle)] border border-[var(--border-subtle)] focus:outline-none transition-all",
        disableMobile: "true",
        defaultDate: this.filtros.fecha_inicio || null,
        onChange: (selectedDates, dateStr) => {
          if (!dateStr) return;
          this.filtros.fecha_inicio = dateStr;
          if (this.fpFin) {
            this.fpFin.set("minDate", dateStr);
          }
          this.onFechaManual();
        }
      });
    },

    initFlatpickrFin(el) {
      if (typeof flatpickr === "undefined" || !el) return;
      this.fpFin = flatpickr(el, {
        locale: flatpickr.l10ns?.es || "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        altInputClass: "input-field w-full pl-9 pr-3 py-2 text-xs sm:text-sm rounded-lg cursor-pointer font-medium text-[var(--text-primary)] bg-[var(--bg-subtle)] border border-[var(--border-subtle)] focus:outline-none transition-all",
        disableMobile: "true",
        defaultDate: this.filtros.fecha_fin || null,
        onChange: (selectedDates, dateStr) => {
          if (!dateStr) return;
          this.filtros.fecha_fin = dateStr;
          if (this.fpInicio) {
            this.fpInicio.set("maxDate", dateStr);
          }
          this.onFechaManual();
        }
      });
    },

    initFlatpickrTabla(el) {
      if (typeof flatpickr === "undefined" || !el) return;
      this.fpTablaInstance = flatpickr(el, {
        locale: flatpickr.l10ns?.es || "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        altInputClass: "w-full pl-9 pr-8 py-2 text-xs sm:text-sm rounded-lg bg-[var(--bg-subtle)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 cursor-pointer font-medium placeholder:text-[var(--text-muted)]",
        disableMobile: "true",
        allowInput: true,
        placeholder: "Filtrar por fecha...",
        onChange: (selectedDates, dateStr) => {
          this.filtroFechaTabla = dateStr || '';
          this.paginaActual = 1;
        }
      });
      if (this.filtros.fecha_inicio && this.fpTablaInstance) {
        this.fpTablaInstance.set("minDate", this.filtros.fecha_inicio);
      }
      if (this.filtros.fecha_fin && this.fpTablaInstance) {
        this.fpTablaInstance.set("maxDate", this.filtros.fecha_fin);
      }
    },

    limpiarFiltroFechaTabla() {
      this.filtroFechaTabla = '';
      if (this.fpTablaInstance) {
        this.fpTablaInstance.clear();
      }
      this.paginaActual = 1;
    },

    formatearFecha(fechaStr) {
      if (!fechaStr || fechaStr === 'Sin registros' || fechaStr === '—' || fechaStr === 'null') {
        return 'Sin registros';
      }
      try {
        const str = String(fechaStr).trim().split('T')[0].split(' ')[0];
        const partes = str.split('-');
        if (partes.length === 3) {
          const [y, m, d] = partes;
          const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
          const mesIdx = parseInt(m, 10) - 1;
          const mesNombre = meses[mesIdx] || m;
          return `${d.padStart(2, '0')} ${mesNombre} ${y}`;
        }
        return fechaStr;
      } catch (e) {
        return fechaStr;
      }
    },

    // ----------------------------------------------------
    // MANEJO DE FILTROS DE FECHA
    // ----------------------------------------------------
    aplicarRangoRapido(tipo, recargar = true) {
      this.filtroRapido = tipo;
      const hoy = new Date();
      const format = (d) => {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
      };

      if (tipo === 'hoy') {
        this.filtros.fecha_inicio = format(hoy);
        this.filtros.fecha_fin = format(hoy);
      } else if (tipo === '7dias') {
        const pasada = new Date();
        pasada.setDate(hoy.getDate() - 6);
        this.filtros.fecha_inicio = format(pasada);
        this.filtros.fecha_fin = format(hoy);
      } else if (tipo === 'mes_actual') {
        const primero = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
        const ultimo = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 0);
        this.filtros.fecha_inicio = format(primero);
        this.filtros.fecha_fin = format(ultimo);
      } else if (tipo === 'mes_anterior') {
        const primero = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1);
        const ultimo = new Date(hoy.getFullYear(), hoy.getMonth(), 0);
        this.filtros.fecha_inicio = format(primero);
        this.filtros.fecha_fin = format(ultimo);
      } else if (tipo === 'ano_actual') {
        this.filtros.fecha_inicio = `${hoy.getFullYear()}-01-01`;
        this.filtros.fecha_fin = `${hoy.getFullYear()}-12-31`;
      }

      // Sincronizar instancias de Flatpickr sin disparar onChange
      if (this.fpInicio) {
        this.fpInicio.set('maxDate', this.filtros.fecha_fin || null);
        this.fpInicio.setDate(this.filtros.fecha_inicio, false);
      }
      if (this.fpFin) {
        this.fpFin.set('minDate', this.filtros.fecha_inicio || null);
        this.fpFin.setDate(this.filtros.fecha_fin, false);
      }

      if (recargar) {
        this.cargarEstadisticas();
      }
    },

    onFechaManual() {
      this.filtroRapido = 'personalizado';
      this.cargarEstadisticas();
    },

    // ----------------------------------------------------
    // CARGA DE DATOS DE API
    // ----------------------------------------------------
    async cargarPlantas() {
      try {
        const res = await fetch('/api/v1/estadisticas/plantas');
        if (res.ok) {
          this.plantas = await res.json();
          if (this.filtros.id_planta) {
            this.inputPlantaTexto = this.nombrePlantaSeleccionada;
          }
        }
      } catch (err) {
        console.error('Error cargando lista de plantas:', err);
      }
    },

    get plantasDropdownFiltradas() {
      if (!this.inputPlantaTexto || !this.inputPlantaTexto.trim()) {
        return this.plantas || [];
      }
      if (this.filtros.id_planta && this.inputPlantaTexto.trim().toLowerCase() === this.nombrePlantaSeleccionada.trim().toLowerCase()) {
        return this.plantas || [];
      }
      const q = this.inputPlantaTexto.toLowerCase().trim();
      return (this.plantas || []).filter(p => 
        (p.nombre && p.nombre.toLowerCase().includes(q)) ||
        (p.empresa && p.empresa.toLowerCase().includes(q))
      );
    },

    get nombrePlantaSeleccionada() {
      if (!this.filtros.id_planta) return 'Todas las plantas';
      const p = (this.plantas || []).find(x => String(x.id) === String(this.filtros.id_planta));
      if (!p) return 'Todas las plantas';
      return p.empresa ? `${p.nombre} (${p.empresa})` : p.nombre;
    },

    abrirDropdownPlanta(inputEl) {
      this.dropdownPlantasOpen = true;
      if (inputEl && typeof inputEl.select === 'function') {
        inputEl.select();
      }
    },

    toggleDropdownPlanta(inputEl) {
      this.dropdownPlantasOpen = !this.dropdownPlantasOpen;
      if (this.dropdownPlantasOpen && inputEl) {
        this.$nextTick(() => {
          inputEl.focus();
          if (typeof inputEl.select === 'function') inputEl.select();
        });
      }
    },

    cerrarDropdownPlanta() {
      this.dropdownPlantasOpen = false;
      if (this.filtros.id_planta) {
        this.inputPlantaTexto = this.nombrePlantaSeleccionada;
      } else {
        this.inputPlantaTexto = '';
      }
    },

    seleccionarPlanta(id) {
      this.filtros.id_planta = id ? String(id) : '';
      this.dropdownPlantasOpen = false;
      if (this.filtros.id_planta) {
        this.inputPlantaTexto = this.nombrePlantaSeleccionada;
      } else {
        this.inputPlantaTexto = '';
      }
      this.cargarEstadisticas();
    },

    limpiarPlanta() {
      this.filtros.id_planta = '';
      this.inputPlantaTexto = '';
      this.dropdownPlantasOpen = false;
      this.cargarEstadisticas();
    },

    async cargarEstadisticas() {
      this.cargando = true;
      try {
        const params = new URLSearchParams();
        if (this.filtros.fecha_inicio) params.append('fecha_inicio', this.filtros.fecha_inicio);
        if (this.filtros.fecha_fin) params.append('fecha_fin', this.filtros.fecha_fin);
        if (this.filtros.id_planta) params.append('id_planta', this.filtros.id_planta);
        if (this.filtros.estado) params.append('estado', this.filtros.estado);

        const res = await fetch(`/api/v1/estadisticas/ingresos-diarios?${params.toString()}`);
        if (!res.ok) throw new Error('Error en la respuesta del servidor');

        const data = await res.json();
        if (data.exito) {
          this.kpis = data.kpis || {};
          if (this.kpis.dia_pico && this.kpis.dia_pico.fecha) {
            this.kpis.dia_pico.fecha_formateada = this.kpis.dia_pico.fecha_formateada || this.formatearFecha(this.kpis.dia_pico.fecha);
          }
          this.serie_tiempo = data.serie_tiempo || [];
          this.distribucion_plantas = data.distribucion_plantas || [];
          this.registros = data.registros || [];
          this.paginaActual = 1;

          if (this.fpTablaInstance) {
            if (this.filtros.fecha_inicio) this.fpTablaInstance.set("minDate", this.filtros.fecha_inicio);
            if (this.filtros.fecha_fin) this.fpTablaInstance.set("maxDate", this.filtros.fecha_fin);
          }

          this.$nextTick(() => {
            this.renderizarGraficos();
          });
        }
      } catch (err) {
        console.error('Error al consultar estadísticas:', err);
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'error',
            title: 'Error al consultar',
            text: 'No se pudieron cargar las estadísticas. Por favor intenta nuevamente.',
            confirmButtonColor: '#10b981'
          });
        }
      } finally {
        this.cargando = false;
      }
    },

    // ----------------------------------------------------
    // TABLA: FILTRADO Y PAGINACIÓN
    // ----------------------------------------------------
    get registrosFiltrados() {
      let lista = this.registros;

      // 1. Filtro exacto por fecha del selector de la tabla
      if (this.filtroFechaTabla) {
        lista = lista.filter(r => r.fecha === this.filtroFechaTabla);
      }

      // 2. Buscador de texto libre (planta, empresa o fecha en texto)
      if (this.search && this.search.trim()) {
        const q = this.search.toLowerCase().trim();

        // Convertir formato dd/mm o dd/mm/yyyy si el usuario busca por fecha escrita
        let qIso = "";
        if (/^\d{1,2}\/\d{1,2}(\/\d{2,4})?$/.test(q)) {
          const parts = q.split('/');
          const d = parts[0].padStart(2, '0');
          const m = parts[1].padStart(2, '0');
          const y = parts[2] ? (parts[2].length === 2 ? '20' + parts[2] : parts[2]) : '';
          qIso = y ? `${y}-${m}-${d}` : `-${m}-${d}`;
        }

        lista = lista.filter(r => 
          (r.planta && r.planta.toLowerCase().includes(q)) ||
          (r.fecha && r.fecha.toLowerCase().includes(q)) ||
          (r.empresa && r.empresa.toLowerCase().includes(q)) ||
          (r.fecha_formateada && r.fecha_formateada.toLowerCase().includes(q)) ||
          (qIso && r.fecha && r.fecha.includes(qIso))
        );
      }
      return lista;
    },

    get totalPaginas() {
      return Math.max(1, Math.ceil(this.registrosFiltrados.length / this.porPagina));
    },

    get registrosPaginados() {
      const inicio = (this.paginaActual - 1) * this.porPagina;
      return this.registrosFiltrados.slice(inicio, inicio + this.porPagina);
    },

    paginaSiguiente() {
      if (this.paginaActual < this.totalPaginas) this.paginaActual++;
    },

    paginaAnterior() {
      if (this.paginaActual > 1) this.paginaActual--;
    },

    // ----------------------------------------------------
    // MODAL DE DETALLE DE PERSONAS (DEDUPLICADAS)
    // ----------------------------------------------------
    async abrirDetalle(registro) {
      this.detalleHeader = {
        fecha: registro.fecha,
        fecha_formateada: registro.fecha_formateada || registro.fecha,
        planta: registro.planta,
        id_planta: registro.id_planta,
        total_personas: registro.total_personas_unicas
      };
      this.personasDetalle = [];
      this.searchPersonaModal = '';
      this.paginaModal = 1;
      this.modalDetalleAbierto = true;
      this.cargandoDetalle = true;

      try {
        const params = new URLSearchParams({
          fecha: registro.fecha,
          id_planta: registro.id_planta,
          estado: this.filtros.estado || 'APROBADO'
        });
        const res = await fetch(`/api/v1/estadisticas/detalle-dia-planta?${params.toString()}`);
        if (!res.ok) throw new Error('Error al consultar detalle');
        const data = await res.json();
        if (data.exito) {
          this.personasDetalle = data.personas || [];
        }
      } catch (err) {
        console.error('Error al cargar detalle de personas:', err);
      } finally {
        this.cargandoDetalle = false;
      }
    },

    cerrarDetalle() {
      this.modalDetalleAbierto = false;
      this.paginaModal = 1;
      this.searchPersonaModal = '';
    },

    get personasDetalleFiltradas() {
      if (!this.searchPersonaModal || !this.searchPersonaModal.trim()) {
        return this.personasDetalle;
      }
      const q = this.searchPersonaModal.toLowerCase().trim();
      return this.personasDetalle.filter(p => 
        (p.nombre_completo && p.nombre_completo.toLowerCase().includes(q)) ||
        (p.identificacion && p.identificacion.includes(q)) ||
        (p.cargo && p.cargo.toLowerCase().includes(q)) ||
        (p.empresa_contratista && p.empresa_contratista.toLowerCase().includes(q)) ||
        (p.radicados && p.radicados.some(rad => rad.toLowerCase().includes(q)))
      );
    },

    get totalPaginasModal() {
      return Math.max(1, Math.ceil(this.personasDetalleFiltradas.length / this.porPaginaModal));
    },

    get personasDetallePaginadas() {
      if (this.paginaModal > this.totalPaginasModal) {
        this.paginaModal = this.totalPaginasModal;
      }
      const inicio = (this.paginaModal - 1) * this.porPaginaModal;
      return this.personasDetalleFiltradas.slice(inicio, inicio + this.porPaginaModal);
    },

    get rangoPersonasModal() {
      if (this.personasDetalleFiltradas.length === 0) return '0';
      const inicio = (this.paginaModal - 1) * this.porPaginaModal + 1;
      const fin = Math.min(this.paginaModal * this.porPaginaModal, this.personasDetalleFiltradas.length);
      return `${inicio} - ${fin}`;
    },

    paginaSiguienteModal() {
      if (this.paginaModal < this.totalPaginasModal) {
        this.paginaModal++;
        this.scrollArribaModal();
      }
    },

    paginaAnteriorModal() {
      if (this.paginaModal > 1) {
        this.paginaModal--;
        this.scrollArribaModal();
      }
    },

    scrollArribaModal() {
      setTimeout(() => {
        const el = document.getElementById('lista_personas_modal_scroll');
        if (el) el.scrollTop = 0;
      }, 10);
    },

    // ----------------------------------------------------
    // GRÁFICOS INTERACTIVOS (CHART.JS)
    // ----------------------------------------------------
    getThemeColors() {
      const isDark = document.documentElement.classList.contains('dark') || localStorage.getItem('darkMode') === 'true';
      return {
        isDark,
        text: isDark ? '#cbd5e1' : '#475569',
        grid: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)',
        tooltipBg: isDark ? 'rgba(18, 18, 22, 0.96)' : 'rgba(255, 255, 255, 0.98)',
        tooltipText: isDark ? '#f8fafc' : '#0f172a',
        tooltipBorder: isDark ? 'rgba(0, 255, 136, 0.45)' : 'rgba(16, 185, 129, 0.2)'
      };
    },

    renderizarGraficos() {
      if (typeof Chart === 'undefined') return;

      const theme = this.getThemeColors();

      // 1. Gráfico de Tendencia Diaria (Línea Neón Fosforescente en Modo Oscuro)
      const ctxTendencia = document.getElementById('chartTendenciaDiaria');
      if (ctxTendencia) {
        if (this.chartTendencia) {
          this.chartTendencia.destroy();
        }

        const labels = this.serie_tiempo.map(d => d.fecha_corta);
        const dataAprobados = this.serie_tiempo.map(d => d.personas_aprobadas ?? d.total_personas ?? 0);
        const dataPendientes = this.serie_tiempo.map(d => d.personas_pendientes ?? 0);

        // Crear gradientes suaves
        const ctx2d = ctxTendencia.getContext('2d');
        const gradientVerde = ctx2d.createLinearGradient(0, 0, 0, 300);
        gradientVerde.addColorStop(0, theme.isDark ? 'rgba(0, 255, 136, 0.35)' : 'rgba(16, 185, 129, 0.25)');
        gradientVerde.addColorStop(1, 'rgba(0, 255, 136, 0.00)');

        const gradientNaranja = ctx2d.createLinearGradient(0, 0, 0, 300);
        gradientNaranja.addColorStop(0, theme.isDark ? 'rgba(245, 158, 11, 0.35)' : 'rgba(245, 158, 11, 0.25)');
        gradientNaranja.addColorStop(1, 'rgba(245, 158, 11, 0.00)');

        const lineGlowPlugin = {
          id: 'linePhosphorGlow',
          beforeDatasetDraw: (chart) => {
            if (!theme.isDark) return;
            chart.ctx.save();
            chart.ctx.shadowColor = 'rgba(0, 255, 136, 0.65)';
            chart.ctx.shadowBlur = 12;
            chart.ctx.shadowOffsetX = 0;
            chart.ctx.shadowOffsetY = 0;
          },
          afterDatasetDraw: (chart) => {
            if (!theme.isDark) return;
            chart.ctx.restore();
          }
        };

        this.chartTendencia = new Chart(ctxTendencia, {
          type: 'line',
          plugins: [lineGlowPlugin],
          data: {
            labels: labels,
            datasets: [
              {
                label: 'Aprobados / Activos',
                data: dataAprobados,
                borderColor: theme.isDark ? '#00ff88' : '#10b981',
                backgroundColor: gradientVerde,
                borderWidth: theme.isDark ? 3 : 2.5,
                fill: true,
                tension: 0.35,
                pointRadius: labels.length > 20 ? 2 : 4,
                pointHoverRadius: 6,
                pointBackgroundColor: theme.isDark ? '#00ff88' : '#10b981',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 1.5
              },
              {
                label: 'Faltantes por aprobar',
                data: dataPendientes,
                borderColor: theme.isDark ? '#f59e0b' : '#d97706',
                backgroundColor: gradientNaranja,
                borderWidth: theme.isDark ? 2.5 : 2,
                borderDash: [5, 4],
                fill: true,
                tension: 0.35,
                pointRadius: labels.length > 20 ? 2 : 4,
                pointHoverRadius: 6,
                pointBackgroundColor: theme.isDark ? '#f59e0b' : '#d97706',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 1.5
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
              intersect: false,
              mode: 'index'
            },
            plugins: {
              legend: {
                display: true,
                position: 'top',
                align: 'end',
                labels: {
                  color: theme.text,
                  font: { size: 11, weight: '600', family: 'system-ui' },
                  usePointStyle: true,
                  boxWidth: 8,
                  boxHeight: 8,
                  padding: 12
                }
              },
              tooltip: {
                backgroundColor: theme.tooltipBg,
                titleColor: theme.tooltipText,
                bodyColor: theme.tooltipText,
                borderColor: theme.tooltipBorder,
                borderWidth: 1,
                padding: 10,
                boxPadding: 4,
                usePointStyle: true,
                callbacks: {
                  label: function(context) {
                    return ` ${context.dataset.label}: ${context.parsed.y} personas`;
                  }
                }
              }
            },
            scales: {
              x: {
                grid: {
                  color: theme.grid
                },
                ticks: {
                  color: theme.text,
                  font: { size: 11, weight: '500' },
                  maxRotation: 45
                }
              },
              y: {
                beginAtZero: true,
                grid: {
                  color: theme.grid
                },
                ticks: {
                  color: theme.text,
                  font: { size: 11 },
                  precision: 0
                }
              }
            }
          }
        });
      }

      // 2. Gráfico de Distribución por Planta (Barras Fosforescentes con Halo Neón en Modo Oscuro)
      const ctxPlantas = document.getElementById('chartDistribucionPlantas');
      if (ctxPlantas) {
        if (this.chartPlantas) {
          this.chartPlantas.destroy();
        }

        const topPlantas = this.distribucion_plantas.slice(0, 6);
        const labelsPlantas = topPlantas.map(p => p.planta);
        const dataConteo = topPlantas.map(p => p.total_personas_unicas);

        const ctx2d = ctxPlantas.getContext('2d');
        const chartH = ctxPlantas.clientHeight || 260;

        // Paleta Neón Fosforescente vibrante para Modo Oscuro y Clásica para Modo Claro
        const fosforescentePalette = [
          { top: '#00ff88', mid: 'rgba(0, 255, 136, 0.90)', bottom: 'rgba(0, 255, 136, 0.30)', border: '#00ff88', glow: 'rgba(0, 255, 136, 0.85)' }, // Verde radiactivo / fosforescente
          { top: '#00f0ff', mid: 'rgba(0, 240, 255, 0.90)', bottom: 'rgba(0, 240, 255, 0.30)', border: '#00f0ff', glow: 'rgba(0, 240, 255, 0.85)' }, // Cian eléctrico
          { top: '#d946ef', mid: 'rgba(217, 70, 239, 0.90)', bottom: 'rgba(217, 70, 239, 0.30)', border: '#e879f9', glow: 'rgba(217, 70, 239, 0.85)' }, // Violeta / Magenta neón
          { top: '#ffee00', mid: 'rgba(255, 238, 0, 0.90)', bottom: 'rgba(255, 238, 0, 0.30)', border: '#ffee00', glow: 'rgba(255, 238, 0, 0.85)' }, // Amarillo resaltador neón
          { top: '#ff007f', mid: 'rgba(255, 0, 127, 0.90)', bottom: 'rgba(255, 0, 127, 0.30)', border: '#ff2a85', glow: 'rgba(255, 0, 127, 0.85)' }, // Rosa eléctrico
          { top: '#38bdf8', mid: 'rgba(56, 189, 248, 0.90)', bottom: 'rgba(56, 189, 248, 0.30)', border: '#38bdf8', glow: 'rgba(56, 189, 248, 0.85)' }  // Azul eléctrico
        ];

        const lightPalette = [
          { top: '#10b981', border: '#059669' },
          { top: '#06b6d4', border: '#0891b2' },
          { top: '#8b5cf6', border: '#7c3aed' },
          { top: '#f59e0b', border: '#d97706' },
          { top: '#ec4899', border: '#db2777' },
          { top: '#3b82f6', border: '#2563eb' }
        ];

        const backgroundColors = labelsPlantas.map((_, i) => {
          if (theme.isDark) {
            const c = fosforescentePalette[i % fosforescentePalette.length];
            const g = ctx2d.createLinearGradient(0, 0, 0, chartH);
            g.addColorStop(0, c.top);
            g.addColorStop(0.35, c.mid);
            g.addColorStop(1, c.bottom);
            return g;
          }
          return lightPalette[i % lightPalette.length].top;
        });

        const borderColors = labelsPlantas.map((_, i) => {
          return theme.isDark 
            ? fosforescentePalette[i % fosforescentePalette.length].border 
            : lightPalette[i % lightPalette.length].border;
        });

        const glowColors = labelsPlantas.map((_, i) => {
          return fosforescentePalette[i % fosforescentePalette.length].glow;
        });

        // Plugin para emitir halo fosforescente brillante alrededor de cada barra
        const barPhosphorGlowPlugin = {
          id: 'barPhosphorGlow',
          beforeDatasetsDraw: (chart) => {
            if (!theme.isDark) return;
            const meta = chart.getDatasetMeta(0);
            if (!meta || !meta.data) return;
            meta.data.forEach((bar, idx) => {
              if (!bar._phosphorGlowAttached) {
                const origDraw = bar.draw;
                bar.draw = function(ctx) {
                  if (theme.isDark) {
                    ctx.save();
                    ctx.shadowColor = glowColors[idx % glowColors.length] || 'rgba(0, 255, 136, 0.85)';
                    ctx.shadowBlur = 18;
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 0;
                    origDraw.apply(this, arguments);
                    ctx.restore();
                  } else {
                    origDraw.apply(this, arguments);
                  }
                };
                bar._phosphorGlowAttached = true;
              }
            });
          }
        };

        this.chartPlantas = new Chart(ctxPlantas, {
          type: 'bar',
          plugins: [barPhosphorGlowPlugin],
          data: {
            labels: labelsPlantas,
            datasets: [
              {
                label: 'Personas acumuladas',
                data: dataConteo,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: theme.isDark ? 2 : 1.5,
                borderRadius: 8,
                borderSkipped: false
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                backgroundColor: theme.tooltipBg,
                titleColor: theme.tooltipText,
                bodyColor: theme.tooltipText,
                borderColor: theme.tooltipBorder,
                borderWidth: 1,
                padding: 10,
                callbacks: {
                  label: function(context) {
                    return ` ${context.parsed.y} personas`;
                  }
                }
              }
            },
            scales: {
              x: {
                grid: {
                  display: false
                },
                ticks: {
                  color: theme.text,
                  font: { size: 11, weight: '500' },
                  callback: function(val) {
                    const label = this.getLabelForValue(val);
                    return label.length > 14 ? label.substring(0, 12) + '...' : label;
                  }
                }
              },
              y: {
                beginAtZero: true,
                grid: {
                  color: theme.grid
                },
                ticks: {
                  color: theme.text,
                  font: { size: 11 },
                  precision: 0
                }
              }
            }
          }
        });
      }
    },

    escucharCambioTema() {
      const observer = new MutationObserver(() => {
        this.renderizarGraficos();
      });
      observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    }
  }));
});
