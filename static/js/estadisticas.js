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

    // Instancias de Chart.js y Flatpickr
    chartTendencia: null,
    chartPlantas: null,
    fpInicio: null,
    fpFin: null,

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
        }
      } catch (err) {
        console.error('Error cargando lista de plantas:', err);
      }
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
      if (this.search && this.search.trim()) {
        const q = this.search.toLowerCase().trim();
        lista = lista.filter(r => 
          (r.planta && r.planta.toLowerCase().includes(q)) ||
          (r.fecha && r.fecha.toLowerCase().includes(q)) ||
          (r.empresa && r.empresa.toLowerCase().includes(q)) ||
          (r.fecha_formateada && r.fecha_formateada.toLowerCase().includes(q))
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

    // ----------------------------------------------------
    // GRÁFICOS INTERACTIVOS (CHART.JS)
    // ----------------------------------------------------
    getThemeColors() {
      const isDark = document.documentElement.classList.contains('dark') || localStorage.getItem('darkMode') === 'true';
      return {
        isDark,
        text: isDark ? '#94a3b8' : '#475569',
        grid: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)',
        tooltipBg: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.98)',
        tooltipText: isDark ? '#f8fafc' : '#0f172a',
        tooltipBorder: isDark ? 'rgba(16, 185, 129, 0.3)' : 'rgba(16, 185, 129, 0.2)'
      };
    },

    renderizarGraficos() {
      if (typeof Chart === 'undefined') return;

      const theme = this.getThemeColors();

      // 1. Gráfico de Tendencia Diaria
      const ctxTendencia = document.getElementById('chartTendenciaDiaria');
      if (ctxTendencia) {
        if (this.chartTendencia) {
          this.chartTendencia.destroy();
        }

        const labels = this.serie_tiempo.map(d => d.fecha_corta);
        const dataPersonas = this.serie_tiempo.map(d => d.total_personas);

        // Crear gradiente suave
        const ctx2d = ctxTendencia.getContext('2d');
        const gradient = ctx2d.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, theme.isDark ? 'rgba(16, 185, 129, 0.45)' : 'rgba(16, 185, 129, 0.35)');
        gradient.addColorStop(1, theme.isDark ? 'rgba(16, 185, 129, 0.01)' : 'rgba(16, 185, 129, 0.01)');

        this.chartTendencia = new Chart(ctxTendencia, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [
              {
                label: 'Personas',
                data: dataPersonas,
                borderColor: '#10b981',
                backgroundColor: gradient,
                borderWidth: 2.5,
                fill: true,
                tension: 0.35,
                pointRadius: labels.length > 20 ? 2 : 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#10b981',
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
                display: false
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
                    return ` ${context.parsed.y} personas`;
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
                  font: { size: 11 },
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

      // 2. Gráfico de Distribución por Planta
      const ctxPlantas = document.getElementById('chartDistribucionPlantas');
      if (ctxPlantas) {
        if (this.chartPlantas) {
          this.chartPlantas.destroy();
        }

        const topPlantas = this.distribucion_plantas.slice(0, 6);
        const labelsPlantas = topPlantas.map(p => p.planta);
        const dataConteo = topPlantas.map(p => p.total_personas_unicas);

        const neonPalette = [
          '#10b981', // Esmeralda
          '#06b6d4', // Cian
          '#8b5cf6', // Violeta
          '#f59e0b', // Ámbar
          '#ec4899', // Rosa
          '#3b82f6'  // Azul
        ];

        this.chartPlantas = new Chart(ctxPlantas, {
          type: 'bar',
          data: {
            labels: labelsPlantas,
            datasets: [
              {
                label: 'Personas acumuladas',
                data: dataConteo,
                backgroundColor: neonPalette.slice(0, labelsPlantas.length),
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
                  font: { size: 11 },
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
