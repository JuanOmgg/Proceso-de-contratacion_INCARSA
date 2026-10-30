/**
 * ============================================================================
 * parqueos.js — Control de Parqueos Nocturnos por Zona (INCARSA)
 * ============================================================================
 * Lógica reactiva en Alpine.js:
 * 1. Tabla principal que enlista fecha, zona y nombre en 'reportador'.
 * 2. Acción 'Ver carros de la zona': muestra cuáles se quedaron aquí y cuáles no ese día.
 *    - Si se queda en su zona: SIN observación.
 *    - Si pernocta en zona diferente: observación en color AMARILLO.
 *    - Si al final del día no fue reportado en ninguna zona: observación en color ROJO ('No pernoctó en ninguna zona').
 * 3. Modal de nuevo reporte por zona (evaluación rápida de vehículos).
 * 4. Catálogo de vehículos internos y su zona asignada oficial (placa, zona, descripción).
 */

function parqueosModule() {
  return {
    // ---------------------------------------------------
    // Estado General y Navegación
    // ---------------------------------------------------
    tabActiva: 'reportes', // 'reportes' | 'vehiculos'
    cargando: true,
    zonasDisponibles: ['UBATÉ', 'SAMACÁ', 'VALDERRAMA'],

    mesesDisponibles: [
      { valor: '01', nombre: 'Enero' },
      { valor: '02', nombre: 'Febrero' },
      { valor: '03', nombre: 'Marzo' },
      { valor: '04', nombre: 'Abril' },
      { valor: '05', nombre: 'Mayo' },
      { valor: '06', nombre: 'Junio' },
      { valor: '07', nombre: 'Julio' },
      { valor: '08', nombre: 'Agosto' },
      { valor: '09', nombre: 'Septiembre' },
      { valor: '10', nombre: 'Octubre' },
      { valor: '11', nombre: 'Noviembre' },
      { valor: '12', nombre: 'Diciembre' }
    ],

    get aniosDisponibles() {
      const anioActual = new Date().getFullYear();
      const anios = [];
      // Rango ampliado de años: desde 3 años atrás (mínimo 2023) hasta 10 años en el futuro (ej. 2036)
      const anioInicio = Math.min(2023, anioActual - 3);
      const anioFin = Math.max(2035, anioActual + 10);
      for (let y = anioInicio; y <= anioFin; y++) {
        anios.push(y);
      }
      return anios;
    },

    // ---------------------------------------------------
    // 1. Tabla Principal de Reportes
    // ---------------------------------------------------
    reportes: [],
    cargandoReportes: false,
    descargandoExcel: false,
    filtroFecha: 'hoy', // 'hoy' | 'ayer' | '7dias' | 'todos'
    filtroZona: 'TODAS',
    busqueda: '',
    metricas: {
      total_reportes: 0,
      total_quedados: 0,
      total_no_quedados: 0
    },

    // ---------------------------------------------------
    // Paginación de Reportes (Compatible con components/pagination.html)
    // ---------------------------------------------------
    currentPage: 1,
    pageSize: 5,

    get totalPaginas() {
      return Math.max(1, Math.ceil((this.reportes || []).length / this.pageSize));
    },

    get totalPages() {
      return this.totalPaginas;
    },

    get reportesPagina() {
      const start = (this.currentPage - 1) * this.pageSize;
      return (this.reportes || []).slice(start, start + this.pageSize);
    },

    get rangoMostrado() {
      const total = (this.reportes || []).length;
      if (total === 0) return '0 de 0';
      const start = (this.currentPage - 1) * this.pageSize + 1;
      const end = Math.min(this.currentPage * this.pageSize, total);
      return `${start}–${end} de ${total}`;
    },

    resetPage() {
      this.currentPage = 1;
    },

    goToPage(n) {
      if (n >= 1 && n <= this.totalPaginas) {
        this.currentPage = n;
      }
    },

    // ---------------------------------------------------
    // 2. Modal: Ver Carros de la Zona (Detalle)
    // ---------------------------------------------------
    showModalDetalle: false,
    cargandoDetalle: false,
    detalleReporte: {
      reporte: {},
      vehiculos_zona: [],
      vehiculos_foraneos: [],
      se_quedaron_aqui: [],
      no_se_quedaron_aqui: [],
      resumen: {}
    },

    // ---------------------------------------------------
    // 3. Modal / Formulario: Nuevo Reporte de Zona
    // ---------------------------------------------------
    showModalNuevoReporte: false,
    guardandoReporte: false,
    formReporte: {
      fecha: new Date().toISOString().split('T')[0],
      zona: '',
      reportador: '',
      observaciones: '',
      vehiculos: [] // { id_vehiculo, vehiculo, zona_asignada, se_quedo: bool, observacion: '' }
    },
    // Vehículos asignados, catálogo general y buscador
    cargandoVehiculosZona: false,
    otrosVehiculosDisponibles: [],
    todosLosVehiculos: [],
    vehiculosYaReportados: {},
    vehiculoOtroSeleccionado: '',
    busquedaGeneral: '',
    mostrarDropdownBusqueda: false,
    busquedaForaneo: '',
    mostrarDropdownForaneos: false,

    esDeEstaZona(zona) {
      return (zona || '').trim().toUpperCase() === (this.formReporte.zona || '').trim().toUpperCase();
    },

    estaEnLista(placa) {
      const p = (placa || '').trim().toUpperCase();
      return this.formReporte.vehiculos.some(x => (x.vehiculo || '').toUpperCase() === p);
    },

    get vehiculosListado() {
      const query = (this.busquedaGeneral || this.busquedaForaneo || '').trim().toUpperCase();
      if (!query) return this.formReporte.vehiculos;
      return this.formReporte.vehiculos.filter(v => 
        (v.vehiculo || '').toUpperCase().includes(query) ||
        (v.zona_asignada && v.zona_asignada.toUpperCase().includes(query)) ||
        (v.descripcion && v.descripcion.toUpperCase().includes(query))
      );
    },

    get vehiculosFiltrados() {
      const query = (this.busquedaGeneral || this.busquedaForaneo || '').trim().toUpperCase();
      // Solo deben aparecer disponibles vehículos que no hayan pernoctado en ninguna zona
      const disponibles = (this.todosLosVehiculos || []).filter(v => 
        !this.vehiculosYaReportados || !this.vehiculosYaReportados[v.placa.toUpperCase()]
      );

      if (!query) {
        const enLista = new Set(this.formReporte.vehiculos.map(x => (x.vehiculo || '').toUpperCase()));
        const noEnLista = disponibles.filter(v => !enLista.has(v.placa.toUpperCase()));
        return noEnLista.length > 0 ? noEnLista : disponibles;
      }
      return disponibles.filter(v => 
        v.placa.toUpperCase().includes(query) || 
        (v.zona && v.zona.toUpperCase().includes(query)) ||
        (v.descripcion && v.descripcion.toUpperCase().includes(query))
      );
    },

    get foraneosFiltrados() {
      return this.vehiculosFiltrados;
    },

    // ---------------------------------------------------
    // 4. Catálogo de Vehículos Internos (Placa, Zona, Descripción)
    // ---------------------------------------------------
    vehiculosInternos: [],
    cargandoVehiculos: false,
    showModalVehiculo: false,
    editandoVehiculo: false,
    formVehiculo: {
      id: null,
      placa: '',
      zona: '',
      descripcion: ''
    },
    guardandoVehiculo: false,

    // Filtros y Paginación de Vehículos Internos
    filtroPlacaVehiculo: '',
    filtroZonaVehiculo: 'TODAS',
    currentPageVehiculos: 1,
    pageSizeVehiculos: 10,

    get vehiculosFiltradosCatalogo() {
      let lista = this.vehiculosInternos || [];
      if (this.filtroZonaVehiculo && this.filtroZonaVehiculo !== 'TODAS') {
        const zNorm = this.filtroZonaVehiculo.trim().toUpperCase();
        lista = lista.filter(v => (v.zona || '').trim().toUpperCase() === zNorm);
      }
      if (this.filtroPlacaVehiculo && this.filtroPlacaVehiculo.trim()) {
        const q = this.filtroPlacaVehiculo.trim().toUpperCase();
        lista = lista.filter(v => 
          (v.placa || '').toUpperCase().includes(q) ||
          (v.descripcion || '').toUpperCase().includes(q)
        );
      }
      return lista;
    },

    get totalPaginasVehiculos() {
      const total = (this.vehiculosFiltradosCatalogo || []).length;
      return Math.max(1, Math.ceil(total / this.pageSizeVehiculos));
    },

    get vehiculosPagina() {
      const start = (this.currentPageVehiculos - 1) * this.pageSizeVehiculos;
      return (this.vehiculosFiltradosCatalogo || []).slice(start, start + this.pageSizeVehiculos);
    },

    get rangoMostradoVehiculos() {
      const total = (this.vehiculosFiltradosCatalogo || []).length;
      if (total === 0) return '0 de 0';
      const start = (this.currentPageVehiculos - 1) * this.pageSizeVehiculos + 1;
      const end = Math.min(this.currentPageVehiculos * this.pageSizeVehiculos, total);
      return `${start}–${end} de ${total}`;
    },

    resetPageVehiculos() {
      this.currentPageVehiculos = 1;
    },

    goToPageVehiculos(n) {
      if (n >= 1 && n <= this.totalPaginasVehiculos) {
        this.currentPageVehiculos = n;
      }
    },

    limpiarFiltrosVehiculos() {
      this.filtroPlacaVehiculo = '';
      this.filtroZonaVehiculo = 'TODAS';
      this.resetPageVehiculos();
    },

    // ---------------------------------------------------
    // 5. Modal de Confirmación de Eliminación (Estilo Ticket)
    // ---------------------------------------------------
    showModalConfirmarEliminar: false,
    modalConfirmar: {
      tipo: 'reporte', // 'reporte' | 'vehiculo'
      titulo: '',
      subtitulo: '',
      item: null,
      zona: '',
      fecha: '',
      reportador: '',
      placa: '',
      descripcion: '',
      id: null,
      eliminando: false,
      errorMsg: ''
    },

    // ---------------------------------------------------
    // Helpers de Formato de Fechas y Horas
    // ---------------------------------------------------
    get fechaActualFormateada() {
      try {
        const hoy = new Date();
        const opciones = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        const str = hoy.toLocaleDateString('es-CO', opciones);
        return str.charAt(0).toUpperCase() + str.slice(1);
      } catch (e) {
        return new Date().toLocaleDateString();
      }
    },

    formatearFecha(fechaStr) {
      if (!fechaStr) return '-';
      try {
        const partes = fechaStr.split('-');
        if (partes.length === 3) {
          const año = parseInt(partes[0], 10);
          const mes = parseInt(partes[1], 10) - 1;
          const dia = parseInt(partes[2], 10);
          const d = new Date(año, mes, dia);
          const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
          const diasSemana = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
          return `${diasSemana[d.getDay()]}, ${dia} ${meses[mes]} ${año}`;
        }
        return fechaStr;
      } catch (e) {
        return fechaStr;
      }
    },

    formatearFechaLarga(fechaStr) {
      if (!fechaStr) return '-';
      try {
        const partes = fechaStr.split('-');
        if (partes.length === 3) {
          const año = parseInt(partes[0], 10);
          const mes = parseInt(partes[1], 10) - 1;
          const dia = parseInt(partes[2], 10);
          const d = new Date(año, mes, dia);
          const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
          const diasSemana = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
          return `${diasSemana[d.getDay()]}, ${dia} de ${meses[mes]} de ${año}`;
        }
        return fechaStr;
      } catch (e) {
        return fechaStr;
      }
    },

    formatearHora(created_at) {
      if (!created_at) return '';
      try {
        const timePart = created_at.includes('T') ? created_at.split('T')[1] : (created_at.includes(' ') ? created_at.split(' ')[1] : '');
        if (!timePart) return '';
        const [h, m] = timePart.split(':');
        let horaNum = parseInt(h, 10);
        const ampm = horaNum >= 12 ? 'PM' : 'AM';
        horaNum = horaNum % 12 || 12;
        return `${horaNum}:${m} ${ampm}`;
      } catch (e) {
        return '';
      }
    },

    // ---------------------------------------------------
    // Inicialización
    // ---------------------------------------------------
    async init() {
      this.detectarReportador();
      await this.cargarZonas();
      await this.cargarReportes();
      await this.cargarCatalogoVehiculos();
      this.cargando = false;
    },

    detectarReportador() {
      try {
        const raw = sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session');
        if (raw) {
          const ses = JSON.parse(raw);
          const nom = ses.nombre || (ses.usuario && (ses.usuario.nombres || ses.usuario.nombre)) || '';
          const ape = ses.apellido || (ses.usuario && (ses.usuario.apellidos || ses.usuario.apellido)) || '';
          const rol = ses.rol || (ses.usuario && ses.usuario.rol) || '';
          const completo = `${nom} ${ape}`.trim();
          this.formReporte.reportador = completo ? `${completo}${rol ? ' (' + rol + ')' : ''}` : 'Vigilancia Turno Noche';
          return;
        }
      } catch (e) {}
      this.formReporte.reportador = 'Vigilancia Turno Noche';
    },

    async cargarZonas() {
      try {
        const res = await fetch('/api/v1/parqueos/zonas');
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data.zonas) && data.zonas.length > 0) {
            this.zonasDisponibles = data.zonas;
            if (!this.formReporte.zona) {
              this.formReporte.zona = data.zonas[0];
            }
          }
        }
      } catch (e) {
        console.warn('Aviso cargando zonas:', e);
      }
    },

    // ---------------------------------------------------
    // Carga de la Tabla Principal de Reportes
    // ---------------------------------------------------
    async cargarReportes() {
      this.cargandoReportes = true;
      try {
        let params = new URLSearchParams();

        const hoy = new Date().toISOString().split('T')[0];
        if (this.filtroFecha === 'hoy') {
          params.set('fecha', hoy);
        } else if (this.filtroFecha === 'ayer') {
          const dAyer = new Date();
          dAyer.setDate(dAyer.getDate() - 1);
          params.set('fecha', dAyer.toISOString().split('T')[0]);
        } else if (this.filtroFecha === '7dias') {
          const dInicio = new Date();
          dInicio.setDate(dInicio.getDate() - 7);
          params.set('fecha_inicio', dInicio.toISOString().split('T')[0]);
          params.set('fecha_fin', hoy);
        }

        if (this.filtroZona && this.filtroZona !== 'TODAS') {
          params.set('zona', this.filtroZona);
        }

        if (this.busqueda && this.busqueda.trim()) {
          params.set('busqueda', this.busqueda.trim());
        }

        const res = await fetch(`/api/v1/parqueos/reportes?${params.toString()}`);
        if (res.ok) {
          const data = await res.json();
          this.reportes = data.datos || [];
          this.metricas = data.metricas || { total_reportes: 0, total_quedados: 0, total_no_quedados: 0 };
          this.currentPage = 1;
        }
      } catch (e) {
        console.error('Error al cargar reportes de parqueo:', e);
      } finally {
        this.cargandoReportes = false;
      }
    },

    // ---------------------------------------------------
    // Exportar Auditoría y Reportes a Excel (Por Mes / Periodo)
    // ---------------------------------------------------
    showModalExportarExcel: false,
    exportandoExcelModal: false,
    fpExcelDesdeInstance: null,
    fpExcelHastaInstance: null,
    formExcel: {
      modo: 'mes', // 'mes' | 'rango' | 'rapido'
      mes: new Date().toISOString().slice(0, 7),
      mesNumero: String(new Date().getMonth() + 1).padStart(2, '0'),
      anio: new Date().getFullYear().toString(),
      fechaInicio: '',
      fechaFin: '',
      rapido: 'este_mes',
      zona: 'TODAS'
    },

    descargarExcelReportes() {
      this.abrirModalExportarExcel();
    },

    abrirModalExportarExcel() {
      const hoy = new Date();
      const anioActual = hoy.getFullYear().toString();
      const mesNumActual = String(hoy.getMonth() + 1).padStart(2, '0');
      const mesActual = `${anioActual}-${mesNumActual}`;
      
      this.formExcel.zona = this.filtroZona || 'TODAS';
      this.formExcel.anio = anioActual;
      this.formExcel.mesNumero = mesNumActual;
      this.formExcel.mes = mesActual;
      
      const primerDia = `${mesActual}-01`;
      this.formExcel.fechaInicio = primerDia;
      this.formExcel.fechaFin = hoy.toISOString().split('T')[0];
      this.showModalExportarExcel = true;

      this.$nextTick(() => {
        this.sincronizarFlatpickrExcel();
      });
    },

    cerrarModalExportarExcel() {
      if (this.fpExcelDesdeInstance) this.fpExcelDesdeInstance.close();
      if (this.fpExcelHastaInstance) this.fpExcelHastaInstance.close();
      this.showModalExportarExcel = false;
    },

    initFlatpickrExcelDesde(el) {
      if (typeof flatpickr === "undefined" || !el) return;
      this.fpExcelDesdeInstance = flatpickr(el, {
        locale: flatpickr.l10ns?.es || "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        altInputClass: "flatpickr-input-custom w-full text-xs font-semibold pl-9 pr-3 py-2.5 rounded-xl bg-white dark:bg-[#1a1f26] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--signal-500)] cursor-pointer shadow-xs transition-all",
        disableMobile: "true",
        defaultDate: this.formExcel.fechaInicio || null,
        onChange: (selectedDates, dateStr) => {
          this.formExcel.fechaInicio = dateStr;
          if (this.fpExcelHastaInstance) {
            this.fpExcelHastaInstance.set("minDate", dateStr || null);
          }
        }
      });
    },

    initFlatpickrExcelHasta(el) {
      if (typeof flatpickr === "undefined" || !el) return;
      this.fpExcelHastaInstance = flatpickr(el, {
        locale: flatpickr.l10ns?.es || "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        altInputClass: "flatpickr-input-custom w-full text-xs font-semibold pl-9 pr-3 py-2.5 rounded-xl bg-white dark:bg-[#1a1f26] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--signal-500)] cursor-pointer shadow-xs transition-all",
        disableMobile: "true",
        defaultDate: this.formExcel.fechaFin || null,
        onChange: (selectedDates, dateStr) => {
          this.formExcel.fechaFin = dateStr;
          if (this.fpExcelDesdeInstance) {
            this.fpExcelDesdeInstance.set("maxDate", dateStr || null);
          }
        }
      });
    },

    sincronizarFlatpickrExcel() {
      if (this.fpExcelDesdeInstance) {
        this.fpExcelDesdeInstance.setDate(this.formExcel.fechaInicio || null, false);
        if (this.formExcel.fechaFin) {
          this.fpExcelDesdeInstance.set("maxDate", this.formExcel.fechaFin);
        } else {
          this.fpExcelDesdeInstance.set("maxDate", null);
        }
      }
      if (this.fpExcelHastaInstance) {
        this.fpExcelHastaInstance.setDate(this.formExcel.fechaFin || null, false);
        if (this.formExcel.fechaInicio) {
          this.fpExcelHastaInstance.set("minDate", this.formExcel.fechaInicio);
        } else {
          this.fpExcelHastaInstance.set("minDate", null);
        }
      }
    },

    limpiarRangoFechasExcel() {
      this.formExcel.fechaInicio = '';
      this.formExcel.fechaFin = '';
      if (this.fpExcelDesdeInstance) {
        this.fpExcelDesdeInstance.clear();
        this.fpExcelDesdeInstance.set('maxDate', null);
      }
      if (this.fpExcelHastaInstance) {
        this.fpExcelHastaInstance.clear();
        this.fpExcelHastaInstance.set('minDate', null);
      }
    },

    formatearRangoTextoExcel() {
      const fi = this.formExcel.fechaInicio ? this.formatearFechaCorta(this.formExcel.fechaInicio) : '...';
      const ff = this.formExcel.fechaFin ? this.formatearFechaCorta(this.formExcel.fechaFin) : '...';
      return `${fi} al ${ff}`;
    },

    formatearFechaCorta(fStr) {
      if (!fStr) return '';
      const partes = fStr.split('-');
      if (partes.length === 3) {
        return `${partes[2]}/${partes[1]}/${partes[0]}`;
      }
      return fStr;
    },

    getNombreMesSeleccionadoExcel() {
      const m = (this.mesesDisponibles || []).find(item => item.valor === this.formExcel.mesNumero);
      return m ? m.nombre : 'Mes';
    },

    setMesActualExcel() {
      const hoy = new Date();
      this.formExcel.anio = hoy.getFullYear().toString();
      this.formExcel.mesNumero = String(hoy.getMonth() + 1).padStart(2, '0');
      this.formExcel.mes = `${this.formExcel.anio}-${this.formExcel.mesNumero}`;
    },

    setMesAnteriorExcel() {
      const hoy = new Date();
      const dAnt = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1);
      this.formExcel.anio = dAnt.getFullYear().toString();
      this.formExcel.mesNumero = String(dAnt.getMonth() + 1).padStart(2, '0');
      this.formExcel.mes = `${this.formExcel.anio}-${this.formExcel.mesNumero}`;
    },

    setPeriodoRapidoExcel(tipo) {
      this.formExcel.rapido = tipo;
      const hoy = new Date();
      const hoyStr = hoy.toISOString().split('T')[0];

      if (tipo === 'hoy') {
        this.formExcel.fechaInicio = hoyStr;
        this.formExcel.fechaFin = hoyStr;
      } else if (tipo === 'ayer') {
        const dAyer = new Date();
        dAyer.setDate(dAyer.getDate() - 1);
        const ayerStr = dAyer.toISOString().split('T')[0];
        this.formExcel.fechaInicio = ayerStr;
        this.formExcel.fechaFin = ayerStr;
      } else if (tipo === '7dias') {
        const d7 = new Date();
        d7.setDate(d7.getDate() - 7);
        this.formExcel.fechaInicio = d7.toISOString().split('T')[0];
        this.formExcel.fechaFin = hoyStr;
      } else if (tipo === 'este_mes') {
        const mesActual = hoy.toISOString().slice(0, 7);
        this.formExcel.fechaInicio = `${mesActual}-01`;
        this.formExcel.fechaFin = hoyStr;
      } else if (tipo === 'mes_anterior') {
        const dPrimerDiaMesAnt = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1);
        const dUltimoDiaMesAnt = new Date(hoy.getFullYear(), hoy.getMonth(), 0);
        this.formExcel.fechaInicio = dPrimerDiaMesAnt.toISOString().split('T')[0];
        this.formExcel.fechaFin = dUltimoDiaMesAnt.toISOString().split('T')[0];
      } else if (tipo === 'todos') {
        this.formExcel.fechaInicio = '';
        this.formExcel.fechaFin = '';
      }

      this.$nextTick(() => {
        this.sincronizarFlatpickrExcel();
      });
    },

    async ejecutarDescargaExcel() {
      if (this.exportandoExcelModal) return;
      this.exportandoExcelModal = true;
      try {
        let params = new URLSearchParams();

        if (this.formExcel.modo === 'mes') {
          if (!this.formExcel.mesNumero || !this.formExcel.anio) {
            alert('Por favor selecciona el mes y el año a exportar.');
            this.exportandoExcelModal = false;
            return;
          }
          const mesCompuesto = `${this.formExcel.anio}-${this.formExcel.mesNumero}`;
          this.formExcel.mes = mesCompuesto;
          params.set('mes', mesCompuesto);
        } else if (this.formExcel.modo === 'rango') {
          if (!this.formExcel.fechaInicio || !this.formExcel.fechaFin) {
            alert('Por favor selecciona la fecha de inicio y fecha de fin.');
            this.exportandoExcelModal = false;
            return;
          }
          if (this.formExcel.fechaInicio > this.formExcel.fechaFin) {
            alert('La fecha de inicio no puede ser posterior a la fecha de fin.');
            this.exportandoExcelModal = false;
            return;
          }
          params.set('fecha_inicio', this.formExcel.fechaInicio);
          params.set('fecha_fin', this.formExcel.fechaFin);
        } else if (this.formExcel.modo === 'rapido') {
          if (this.formExcel.rapido === 'hoy') {
            params.set('fecha', new Date().toISOString().split('T')[0]);
          } else if (this.formExcel.rapido === 'ayer') {
            const dAyer = new Date();
            dAyer.setDate(dAyer.getDate() - 1);
            params.set('fecha', dAyer.toISOString().split('T')[0]);
          } else if (this.formExcel.rapido === '7dias') {
            const d7 = new Date();
            d7.setDate(d7.getDate() - 7);
            params.set('fecha_inicio', d7.toISOString().split('T')[0]);
            params.set('fecha_fin', new Date().toISOString().split('T')[0]);
          } else if (this.formExcel.rapido === 'este_mes') {
            const mesActual = new Date().toISOString().slice(0, 7);
            params.set('mes', mesActual);
          } else if (this.formExcel.rapido === 'mes_anterior') {
            const hoy = new Date();
            const dMesAnt = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1);
            const mesAntStr = dMesAnt.toISOString().slice(0, 7);
            params.set('mes', mesAntStr);
          }
        }

        if (this.formExcel.zona && this.formExcel.zona !== 'TODAS') {
          params.set('zona', this.formExcel.zona);
        }

        if (this.busqueda && this.busqueda.trim()) {
          params.set('busqueda', this.busqueda.trim());
        }

        const url = `/api/v1/parqueos/exportar-excel?${params.toString()}`;
        const res = await fetch(url);
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || err.mensaje || 'Error al generar archivo Excel de auditoría.');
        }

        const blob = await res.blob();
        let filename = `Auditoria_Parqueos.xlsx`;
        const disposition = res.headers.get('Content-Disposition');
        if (disposition && disposition.indexOf('filename=') !== -1) {
          const matches = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
          if (matches != null && matches[1]) {
            filename = matches[1].replace(/['"]/g, '');
          }
        }

        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(link.href);

        this.cerrarModalExportarExcel();
      } catch (e) {
        console.error('Error al exportar reporte en Excel:', e);
        alert('No se pudo descargar el reporte de auditoría en Excel: ' + e.message);
      } finally {
        this.exportandoExcelModal = false;
      }
    },

    // ---------------------------------------------------
    // Acción: Ver Carros de la Zona
    // ---------------------------------------------------
    async verCarrosZona(idReporte) {
      this.cargandoDetalle = true;
      this.showModalDetalle = true;
      this.detalleReporte = {
        reporte: {},
        vehiculos_zona: [],
        vehiculos_foraneos: [],
        se_quedaron_aqui: [],
        no_se_quedaron_aqui: [],
        resumen: {}
      };

      try {
        const res = await fetch(`/api/v1/parqueos/reportes/${idReporte}/detalle`);
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || err.mensaje || 'Error al obtener detalle de la zona.');
        }

        const data = await res.json();
        this.detalleReporte = {
          reporte: data.reporte || {},
          vehiculos_zona: data.vehiculos_zona || [],
          vehiculos_foraneos: data.vehiculos_foraneos || [],
          se_quedaron_aqui: data.se_quedaron_aqui || [],
          no_se_quedaron_aqui: data.no_se_quedaron_aqui || [],
          resumen: data.resumen || {}
        };
      } catch (e) {
        console.error('Error al cargar detalle de zona:', e);
        alert(e.message);
        this.showModalDetalle = false;
      } finally {
        this.cargandoDetalle = false;
      }
    },

    cerrarModalDetalle() {
      this.showModalDetalle = false;
    },

    // ---------------------------------------------------
    // Confirmación y Eliminación (Ticket Style)
    // ---------------------------------------------------
    cerrarModalConfirmarEliminar() {
      if (this.modalConfirmar.eliminando) return;
      this.showModalConfirmarEliminar = false;
      this.modalConfirmar.item = null;
      this.modalConfirmar.errorMsg = '';
    },

    eliminarReporte(r) {
      if (!r || !r.id) return;
      this.modalConfirmar = {
        tipo: 'reporte',
        titulo: '¿Eliminar reporte?',
        subtitulo: 'Se eliminará la auditoría de parqueo nocturno de esta sede',
        item: r,
        zona: r.zona || '',
        fecha: r.fecha || '',
        reportador: r.reportador || '',
        placa: '',
        descripcion: '',
        id: r.id,
        eliminando: false,
        errorMsg: ''
      };
      this.showModalConfirmarEliminar = true;
    },

    eliminarVehiculoInterno(v) {
      if (!v || !v.id) return;
      this.modalConfirmar = {
        tipo: 'vehiculo',
        titulo: '¿Eliminar vehículo?',
        subtitulo: 'Se eliminará el vehículo del catálogo interno oficial',
        item: v,
        zona: v.zona || v.zona_asignada || '',
        fecha: '',
        reportador: '',
        placa: v.placa || '',
        descripcion: v.descripcion || '',
        id: v.id,
        eliminando: false,
        errorMsg: ''
      };
      this.showModalConfirmarEliminar = true;
    },

    async ejecutarEliminacionConfirmada() {
      if (!this.modalConfirmar.id || this.modalConfirmar.eliminando) return;
      this.modalConfirmar.eliminando = true;
      this.modalConfirmar.errorMsg = '';

      try {
        if (this.modalConfirmar.tipo === 'reporte') {
          const res = await fetch(`/api/v1/parqueos/reportes/${this.modalConfirmar.id}`, { method: 'DELETE' });
          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || err.mensaje || 'Error al eliminar reporte.');
          }
          this.cerrarModalConfirmarEliminar();
          await this.cargarReportes();
          if (typeof window.showToast === 'function') {
            window.showToast('Reporte de parqueo eliminado con éxito.', 'success');
          }
        } else if (this.modalConfirmar.tipo === 'vehiculo') {
          const res = await fetch(`/api/v1/parqueos/vehiculos/${this.modalConfirmar.id}`, { method: 'DELETE' });
          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || err.mensaje || 'Error al eliminar vehículo.');
          }
          this.cerrarModalConfirmarEliminar();
          await this.cargarCatalogoVehiculos();
          await this.cargarZonas();
          if (typeof window.showToast === 'function') {
            window.showToast('Vehículo eliminado del catálogo con éxito.', 'success');
          }
        }
      } catch (e) {
        this.modalConfirmar.errorMsg = e.message;
      } finally {
        this.modalConfirmar.eliminando = false;
      }
    },

    // ---------------------------------------------------
    // Formulario de Nuevo Reporte por Zona
    // ---------------------------------------------------
    abrirModalNuevoReporte() {
      this.formReporte.fecha = new Date().toISOString().split('T')[0];
      if (!this.formReporte.zona && this.zonasDisponibles.length > 0) {
        this.formReporte.zona = this.zonasDisponibles[0];
      }
      this.detectarReportador();
      this.formReporte.observaciones = '';
      this.formReporte.vehiculos = [];
      this.otrosVehiculosDisponibles = [];
      this.vehiculoOtroSeleccionado = '';
      this.showModalNuevoReporte = true;

      this.alCambiarZonaReporte();
    },

    cerrarModalNuevoReporte() {
      this.showModalNuevoReporte = false;
      this.guardandoReporte = false;
    },

    async alCambiarZonaReporte() {
      const zona = this.formReporte.zona;
      if (!zona) return;

      this.cargandoVehiculosZona = true;
      try {
        const fecha = this.formReporte.fecha || '';
        const url = `/api/v1/parqueos/vehiculos-por-zona/${encodeURIComponent(zona)}` + (fecha ? `?fecha=${encodeURIComponent(fecha)}` : '');
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          const asignados = data.asignados || [];
          this.otrosVehiculosDisponibles = data.otros_disponibles || [];
          this.todosLosVehiculos = [...asignados, ...this.otrosVehiculosDisponibles];
          this.vehiculosYaReportados = data.vehiculos_ya_reportados || {};

          // Los vehículos NO se precargan; solo se identifican e ingresan a través del buscador
          this.formReporte.vehiculos = [];
        }
      } catch (e) {
        console.error('Error al cargar vehículos de zona:', e);
      } finally {
        this.cargandoVehiculosZona = false;
      }
    },

    marcarTodos(valorBooleano) {
      this.formReporte.vehiculos.forEach(v => {
        v.se_quedo = valorBooleano;
      });
    },

    seleccionarVehiculoGeneral(item) {
      let placa = '';
      let zona = '';
      let idVehiculo = null;
      let descripcion = '';

      if (typeof item === 'object' && item !== null) {
        placa = (item.placa || item.vehiculo || '').trim().toUpperCase();
        zona = item.zona || item.zona_asignada || '';
        idVehiculo = item.id || item.id_vehiculo || null;
        descripcion = item.descripcion || '';
      } else if (typeof item === 'string') {
        placa = item.trim().toUpperCase();
        const enc = (this.todosLosVehiculos || []).find(x => x.placa.toUpperCase() === placa);
        if (enc) {
          zona = enc.zona;
          idVehiculo = enc.id;
          descripcion = enc.descripcion || '';
        } else {
          zona = 'NO REGISTRADO';
        }
      }

      if (!placa) return;

      // Validación preventiva: si ya pernoctó en cualquier zona hoy, advertir y no permitir agregarlo
      if (this.vehiculosYaReportados && this.vehiculosYaReportados[placa]) {
        const rep = this.vehiculosYaReportados[placa];
        const horaTxt = rep.hora ? ` a las ${rep.hora}` : '';
        const repTxt = rep.reportador ? ` (Reportado por: ${rep.reportador})` : '';
        const zonaTxt = rep.zona ? ` en la zona ${rep.zona}` : '';
        alert(`⚠️ ATENCIÓN: El vehículo ${placa} ya fue reportado pernoctando${zonaTxt}${horaTxt}${repTxt}.\n\nSolo es posible registrar vehículos que no hayan pernoctado en ninguna zona hasta el momento.`);
        this.busquedaGeneral = '';
        this.busquedaForaneo = '';
        this.mostrarDropdownBusqueda = false;
        this.mostrarDropdownForaneos = false;
        return;
      }

      if (!zona) {
        const enc = (this.todosLosVehiculos || []).find(x => x.placa.toUpperCase() === placa);
        if (enc) {
          zona = enc.zona;
          idVehiculo = idVehiculo || enc.id;
          descripcion = descripcion || enc.descripcion || '';
        } else {
          zona = 'NO REGISTRADO';
        }
      }

      const esPropio = this.esDeEstaZona(zona);
      const existente = this.formReporte.vehiculos.find(x => (x.vehiculo || '').toUpperCase() === placa);

      if (existente) {
        this.busquedaGeneral = '';
        this.mostrarDropdownBusqueda = false;
        return;
      }

      this.formReporte.vehiculos.unshift({
        id_vehiculo: idVehiculo,
        vehiculo: placa,
        zona_asignada: zona || (esPropio ? this.formReporte.zona : 'OTRA ZONA'),
        descripcion: descripcion,
        se_quedo: true,
        es_foraneo: !esPropio,
        observacion: esPropio ? '' : `Asignado a ${zona || 'otra zona'}`
      });

      this.busquedaGeneral = '';
      this.busquedaForaneo = '';
      this.mostrarDropdownBusqueda = false;
      this.mostrarDropdownForaneos = false;
    },

    onKeydownBuscarGeneral(event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        const filtrados = this.vehiculosFiltrados;
        if (filtrados.length > 0) {
          this.seleccionarVehiculoGeneral(filtrados[0]);
        } else if (this.busquedaGeneral.trim() || this.busquedaForaneo.trim()) {
          const txt = (this.busquedaGeneral || this.busquedaForaneo).trim();
          this.seleccionarVehiculoGeneral(txt);
        }
      } else if (event.key === 'Escape') {
        this.mostrarDropdownBusqueda = false;
        this.mostrarDropdownForaneos = false;
      }
    },

    adjuntarVehiculoForaneo(item) {
      this.seleccionarVehiculoGeneral(item);
    },

    onKeydownBuscarForaneo(event) {
      this.onKeydownBuscarGeneral(event);
    },

    agregarVehiculoOtro() {
      if (!this.vehiculoOtroSeleccionado) return;
      this.adjuntarVehiculoForaneo(this.vehiculoOtroSeleccionado);
      this.vehiculoOtroSeleccionado = '';
    },

    quitarVehiculoDeReporte(itemOrIndex) {
      if (typeof itemOrIndex === 'object' && itemOrIndex !== null) {
        const idx = this.formReporte.vehiculos.findIndex(x => (x.vehiculo || '').toUpperCase() === (itemOrIndex.vehiculo || '').toUpperCase());
        if (idx !== -1) this.formReporte.vehiculos.splice(idx, 1);
      } else if (typeof itemOrIndex === 'number') {
        this.formReporte.vehiculos.splice(itemOrIndex, 1);
      }
    },

    async guardarReporteZona() {
      if (!this.formReporte.zona) {
        alert('Seleccione la zona a reportar.');
        return;
      }
      if (!this.formReporte.reportador.trim()) {
        alert('Ingrese el nombre de la persona que realiza el reporte.');
        return;
      }
      if (this.formReporte.vehiculos.length === 0) {
        alert('Debe evaluar al menos un vehículo en esta zona.');
        return;
      }

      this.guardandoReporte = true;
      try {
        const payload = {
          fecha: this.formReporte.fecha,
          zona: this.formReporte.zona,
          reportador: this.formReporte.reportador.trim(),
          observaciones: this.formReporte.observaciones.trim(),
          vehiculos: this.formReporte.vehiculos.map(v => ({
            id_vehiculo: v.id_vehiculo,
            vehiculo: v.vehiculo,
            zona_asignada: v.zona_asignada,
            se_quedo: v.se_quedo,
            observacion: v.observacion.trim()
          }))
        };

        const res = await fetch('/api/v1/parqueos/reportar-zona', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || err.mensaje || 'Error al guardar el reporte.');
        }

        const data = await res.json();
        this.cerrarModalNuevoReporte();
        await this.cargarReportes();

        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'success',
            title: '¡Reporte Guardado!',
            text: data.mensaje || 'Reporte de zona registrado exitosamente.',
            timer: 2000,
            showConfirmButton: false
          });
        }
      } catch (e) {
        console.error('Error guardando reporte de zona:', e);
        alert(e.message);
      } finally {
        this.guardandoReporte = false;
      }
    },

    // ---------------------------------------------------
    // Catálogo de Vehículos Internos (Placa, Zona, Descripción)
    // ---------------------------------------------------
    async cargarCatalogoVehiculos() {
      this.cargandoVehiculos = true;
      try {
        const res = await fetch('/api/v1/parqueos/vehiculos');
        if (res.ok) {
          const data = await res.json();
          this.vehiculosInternos = data.datos || [];
          if (this.currentPageVehiculos > this.totalPaginasVehiculos) {
            this.currentPageVehiculos = Math.max(1, this.totalPaginasVehiculos);
          }
        }
      } catch (e) {
        console.error('Error cargando vehículos internos:', e);
      } finally {
        this.cargandoVehiculos = false;
      }
    },

    abrirModalNuevoVehiculo() {
      this.editandoVehiculo = false;
      this.formVehiculo = {
        id: null,
        placa: '',
        zona: this.zonasDisponibles[0] || 'UBATÉ',
        descripcion: ''
      };
      this.showModalVehiculo = true;
    },

    abrirModalEditarVehiculo(v) {
      this.editandoVehiculo = true;
      this.formVehiculo = {
        id: v.id,
        placa: v.placa,
        zona: v.zona,
        descripcion: v.descripcion || ''
      };
      this.showModalVehiculo = true;
    },

    cerrarModalVehiculo() {
      this.showModalVehiculo = false;
      this.guardandoVehiculo = false;
    },

    async guardarVehiculoInterno() {
      const placa = this.formVehiculo.placa.trim().toUpperCase();
      const zona = this.formVehiculo.zona.trim().toUpperCase();

      if (!placa || !zona) {
        alert('Placa y zona asignada son obligatorias.');
        return;
      }

      this.guardandoVehiculo = true;
      try {
        const payload = {
          placa: placa,
          zona: zona,
          descripcion: this.formVehiculo.descripcion.trim()
        };

        let url = '/api/v1/parqueos/vehiculos';
        let method = 'POST';

        if (this.editandoVehiculo && this.formVehiculo.id) {
          url = `/api/v1/parqueos/vehiculos/${this.formVehiculo.id}`;
          method = 'PUT';
        }

        const res = await fetch(url, {
          method: method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || err.mensaje || 'Error al guardar vehículo.');
        }

        this.cerrarModalVehiculo();
        await this.cargarZonas();
        await this.cargarCatalogoVehiculos();
      } catch (e) {
        alert(e.message);
      } finally {
        this.guardandoVehiculo = false;
      }
    }
  };
}
