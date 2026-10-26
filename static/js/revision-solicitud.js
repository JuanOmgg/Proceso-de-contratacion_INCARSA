/**
 * INCARSA - Sistema de Gestión de Solicitudes
 * revision-solicitud.js - Lógica para la Vista Dedicada de Revisión y Dictamen de Roles
 */

function formatearFechaHoraEspanol(fechaStr) {
  if (window.Fechas && typeof window.Fechas.formatearFechaHora === 'function') {
    return window.Fechas.formatearFechaHora(fechaStr);
  }
  return fechaStr || '—';
}

function formatearFechaCorta(fechaStr) {
  if (window.Fechas && typeof window.Fechas.formatearCorta === 'function') {
    return window.Fechas.formatearCorta(fechaStr);
  }
  return fechaStr || '—';
}

function revisionSolicitudApp() {
  return {
    solicitudId: null,
    solicitud: null,
    cargando: true,
    guardando: false,
    error: null,

    // Sidebar estado responsive
    sidebarCollapsed: true,
    sidebarOpenMobile: false,
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
    },
    toggleMobileSidebar() {
      this.sidebarOpenMobile = !this.sidebarOpenMobile;
    },
    closeMobileSidebar() {
      this.sidebarOpenMobile = false;
    },

    // Modo oscuro
    darkMode: localStorage.getItem('darkMode') === 'true',
    toggleDarkMode() {
      this.darkMode = !this.darkMode;
      document.documentElement.classList.toggle('dark', this.darkMode);
      localStorage.setItem('darkMode', this.darkMode);
    },

    // Notificaciones y Centro de Notificaciones (Integración con Sidebar y SSE)
    notificationsOpen: false,
    modalTodasNotificacionesOpen: false,
    filtroNotifTab: 'todas',
    busquedaNotif: '',
    notifPage: 1,
    notifPageSize: 8,
    notifications: [],
    unreadNotificationsCount: 0,

    get notificacionesFiltradas() {
      let lista = this.notifications || [];
      if (this.filtroNotifTab === 'no_leidas') {
        lista = lista.filter(n => !n.leido);
      } else if (this.filtroNotifTab === 'info') {
        lista = lista.filter(n => !n.tipo || n.tipo === 'info');
      } else if (this.filtroNotifTab === 'alertas') {
        lista = lista.filter(n => ['warning', 'error', 'danger'].includes(n.tipo));
      }

      if (this.busquedaNotif && this.busquedaNotif.trim()) {
        const q = this.busquedaNotif.toLowerCase().trim();
        lista = lista.filter(n =>
          (n.titulo && n.titulo.toLowerCase().includes(q)) ||
          (n.mensaje && n.mensaje.toLowerCase().includes(q))
        );
      }
      return lista;
    },

    get notificacionesModalPagina() {
      const filtradas = this.notificacionesFiltradas;
      const start = (this.notifPage - 1) * this.notifPageSize;
      return filtradas.slice(start, start + this.notifPageSize);
    },

    get notifTotalPaginas() {
      return Math.ceil(this.notificacionesFiltradas.length / this.notifPageSize) || 1;
    },

    abrirModalTodasNotificaciones() {
      this.modalTodasNotificacionesOpen = true;
      this.notificationsOpen = false;
      this.sidebarOpenMobile = false;
      this.filtroNotifTab = 'todas';
      this.busquedaNotif = '';
      this.notifPage = 1;
      this.cargarNotificaciones(100);
    },

    cerrarModalTodasNotificaciones() {
      this.modalTodasNotificacionesOpen = false;
    },

    async cargarNotificaciones(limit = 50) {
      try {
        const notifUrl = (typeof API !== 'undefined' && API.notificaciones)
          ? API.notificaciones
          : `${window.location.origin}/api/v1/notificaciones`;
        const params = new URLSearchParams();
        const uId = this.usuarioSesion?.id || this.usuarioSesion?.id_usuario;
        const rId = this.usuarioSesion?.id_rol;
        if (uId) params.append('id_usuario', uId);
        if (rId) params.append('id_rol', rId);
        if (limit) params.append('limit', limit);

        const res = await fetch(`${notifUrl}?${params.toString()}`);
        if (res.ok) {
          const data = await res.json();
          this.notifications = data.notificaciones || [];
          this.unreadNotificationsCount = data.no_leidas || 0;
        }
      } catch (err) {
        console.warn('Aviso al cargar notificaciones en vista revisión:', err);
      }
    },

    async marcarNotificacionLeida(n) {
      if (!n.leido) {
        try {
          const notifUrl = (typeof API !== 'undefined' && API.notificaciones)
            ? API.notificaciones
            : `${window.location.origin}/api/v1/notificaciones`;
          await fetch(`${notifUrl}/${n.id}/leer`, { method: 'PATCH' });
          n.leido = true;
          if (this.unreadNotificationsCount > 0) {
            this.unreadNotificationsCount--;
          }
        } catch (e) {
          console.warn('Aviso al marcar notificación como leída:', e);
        }
      }
      if (n.enlace) {
        window.location.href = n.enlace;
      }
    },

    async marcarTodasNotificacionesLeidas() {
      try {
        const notifUrl = (typeof API !== 'undefined' && API.notificaciones)
          ? API.notificaciones
          : `${window.location.origin}/api/v1/notificaciones`;
        const uId = this.usuarioSesion?.id || this.usuarioSesion?.id_usuario;
        const rId = this.usuarioSesion?.id_rol;
        await fetch(`${notifUrl}/marcar-todas-leidas`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id_usuario: uId, id_rol: rId })
        });
        (this.notifications || []).forEach(n => n.leido = true);
        this.unreadNotificationsCount = 0;
      } catch (e) {
        console.warn('Aviso al marcar todas las notificaciones:', e);
      }
    },

    formatearTiempoRelativo(fechaStr) {
      if (typeof window.formatearTiempoRelativo === 'function') {
        return window.formatearTiempoRelativo(fechaStr);
      }
      return fechaStr || '';
    },

    formatearFechaHora(fechaStr) {
      if (typeof formatearFechaHoraEspanol === 'function') {
        return formatearFechaHoraEspanol(fechaStr);
      }
      if (typeof window.formatearFechaHoraEspanol === 'function') {
        return window.formatearFechaHoraEspanol(fechaStr);
      }
      return fechaStr || '';
    },

    formatearTextoEnlace(url) {
      if (typeof window.formatearTextoEnlace === 'function') {
        return window.formatearTextoEnlace(url);
      }
      return url || '';
    },

    esNotifPreaprobada(n) {
      return window.esNotifPreaprobada ? window.esNotifPreaprobada(n) : false;
    },

    obtenerCodigoSolicitudDeNotif(n) {
      return window.obtenerCodigoSolicitudDeNotif ? window.obtenerCodigoSolicitudDeNotif(n) : null;
    },

    async revisarSolicitudNotif(n) {
      if (window.revisarSolicitudNotif) {
        await window.revisarSolicitudNotif(n);
        if (this.unreadNotificationsCount > 0 && n.leido) this.unreadNotificationsCount--;
      }
    },

    async confirmarAprobacionDirectaNotif(n) {
      if (window.confirmarAprobacionDirectaNotif) {
        await window.confirmarAprobacionDirectaNotif(n);
        if (this.unreadNotificationsCount > 0 && n.aprobadoExitoso) this.unreadNotificationsCount--;
      }
    },

    // Sesión y Rol actual
    usuarioSesion: null,
    rolActual: "SST", // 'SST' | 'GESCO' | 'SCR' | 'Administrador' | 'SOLICITANTE'
    rolNombre: "SST",

    get esSuperAdmin() {
      if (typeof tieneRol === 'function' && tieneRol('SUPERADMIN')) {
        return true;
      }
      if (!this.usuarioSesion) return false;
      const rol = String(this.usuarioSesion.rol || this.usuarioSesion.nombre_rol || "").trim().toUpperCase();
      const idRol = Number(this.usuarioSesion.id_rol || 0);
      return rol === "SUPERADMIN" || idRol === 2;
    },

    get esRolDictamenSCR() {
      const rol = this.editandoRevision ? this.editandoRevision.rol : this.rolActual;
      return String(rol || "").trim().toUpperCase() === "SCR";
    },

    /**
     * Determina si el usuario actual tiene permisos para ver y auditar antecedentes en revisión.
     * Habilitado exclusivamente para SCR y roles superiores (ADMINISTRADOR y SUPERADMIN).
     */
    get puedeVerAntecedentes() {
      const rolActualNorm = String(this.rolActual || "").trim().toUpperCase();
      const rolSesionNorm = String(this.usuarioSesion?.rol || this.usuarioSesion?.nombre_rol || "").trim().toUpperCase();
      const idRol = Number(this.usuarioSesion?.id_rol || 0);

      // Si el rol activo (simulado o real) es un rol operativo sin atribución de antecedentes
      const rolesExcluidos = ["SST", "GESCO", "SOLICITANTE", "VIGILANTE", "COORDINADOR"];
      if (rolesExcluidos.includes(rolActualNorm)) {
        return false;
      }

      // SuperAdmin siempre tiene acceso
      if (this.esSuperAdmin || idRol === 2 || rolSesionNorm === "SUPERADMIN") {
        return true;
      }

      // SCR y roles superiores (ADMINISTRADOR y SUPERADMIN)
      const rolesPermitidos = ["SCR", "ADMINISTRADOR", "ADMIN", "SUPERADMIN"];
      if (rolesPermitidos.includes(rolActualNorm) || rolesPermitidos.includes(rolSesionNorm)) {
        return true;
      }

      if ([1, 2, 8].includes(idRol)) {
        return true;
      }

      if (typeof window.puedeModulo === "function" && window.puedeModulo("antecedentes")) {
        return true;
      }

      return false;
    },

    /**
     * Determina si el usuario actual tiene permisos para ver y auditar la vigencia de inducciones.
     * Habilitado para GESCO, SCR y roles superiores (ADMINISTRADOR y SUPERADMIN).
     */
    get puedeVerInduccion() {
      const rolActualNorm = String(this.rolActual || "").trim().toUpperCase();
      const rolSesionNorm = String(this.usuarioSesion?.rol || this.usuarioSesion?.nombre_rol || "").trim().toUpperCase();
      const idRol = Number(this.usuarioSesion?.id_rol || 0);

      // Si el rol activo (simulado o real) es SST, no audita vigencia de inducciones
      if (rolActualNorm === "SST") {
        return false;
      }

      if (this.esSuperAdmin || idRol === 2 || rolSesionNorm === "SUPERADMIN" || rolActualNorm === "SUPERADMIN") {
        return true;
      }

      const rolesPermitidos = ["GESCO", "SCR", "ADMINISTRADOR", "ADMIN", "SUPERADMIN"];
      if (rolesPermitidos.includes(rolActualNorm) || rolesPermitidos.includes(rolSesionNorm)) {
        return true;
      }

      if ([1, 2, 4, 8].includes(idRol)) {
        return true;
      }

      return false;
    },

    /**
     * Determina si el usuario actual tiene permisos para ver y dictaminar Seguridad Social.
     * Habilitado para SST, SCR y roles superiores (ADMINISTRADOR y SUPERADMIN).
     */
    get puedeVerSeguridadSocial() {
      const rolActualNorm = String(this.rolActual || "").trim().toUpperCase();
      const rolSesionNorm = String(this.usuarioSesion?.rol || this.usuarioSesion?.nombre_rol || "").trim().toUpperCase();
      const idRol = Number(this.usuarioSesion?.id_rol || 0);

      if (this.esSuperAdmin || idRol === 2 || rolSesionNorm === "SUPERADMIN" || rolActualNorm === "SUPERADMIN") {
        return true;
      }

      const rolesPermitidos = ["SST", "SCR", "ADMINISTRADOR", "ADMIN", "SUPERADMIN"];
      if (rolesPermitidos.includes(rolActualNorm) || rolesPermitidos.includes(rolSesionNorm)) {
        return true;
      }

      if ([1, 2, 7, 8].includes(idRol)) {
        return true;
      }

      if (typeof window.puedeModulo === "function" && window.puedeModulo("seguridad_social")) {
        return true;
      }

      return false;
    },

    /**
     * Determina si el rol del usuario es SCR o un rol superior (ADMINISTRADOR, SUPERADMIN).
     */
    get esScrOSuperior() {
      const rolActualNorm = String(this.rolActual || "").trim().toUpperCase();
      const rolSesionNorm = String(this.usuarioSesion?.rol || this.usuarioSesion?.nombre_rol || "").trim().toUpperCase();
      const idRol = Number(this.usuarioSesion?.id_rol || 0);

      if (this.esSuperAdmin || idRol === 2 || rolSesionNorm === "SUPERADMIN") return true;
      if (["SCR", "ADMINISTRADOR", "ADMIN", "SUPERADMIN"].includes(rolActualNorm)) return true;
      if (["SCR", "ADMINISTRADOR", "ADMIN", "SUPERADMIN"].includes(rolSesionNorm)) return true;
      if ([1, 2, 8].includes(idRol)) return true;
      return false;
    },

    get esSstOGesco() {
      const rolActualNorm = String(this.rolActual || "").trim().toUpperCase();
      const rolSesionNorm = String(this.usuarioSesion?.rol || this.usuarioSesion?.nombre_rol || "").trim().toUpperCase();
      const idRol = Number(this.usuarioSesion?.id_rol || 0);
      return ["SST", "GESCO"].includes(rolActualNorm) || ["SST", "GESCO"].includes(rolSesionNorm) || [6, 7].includes(idRol);
    },

    get esAdminOSuperadmin() {
      const rolActualNorm = String(this.rolActual || "").trim().toUpperCase();
      const rolSesionNorm = String(this.usuarioSesion?.rol || this.usuarioSesion?.nombre_rol || "").trim().toUpperCase();
      const idRol = Number(this.usuarioSesion?.id_rol || 0);
      if (this.esSuperAdmin || idRol === 2 || rolSesionNorm === "SUPERADMIN" || rolActualNorm === "SUPERADMIN") return true;
      if (["ADMINISTRADOR", "ADMIN"].includes(rolActualNorm) || ["ADMINISTRADOR", "ADMIN"].includes(rolSesionNorm) || idRol === 1) return true;
      return false;
    },

    get esRevisionFinalizada() {
      const estado = String(this.solicitud?.estado || "").trim().toUpperCase();
      return ["APROBADO", "FINALIZADO", "RECHAZADO"].includes(estado);
    },

    get userDisplayName() {
      if (this.usuarioSesion && (this.usuarioSesion.nombres || this.usuarioSesion.nombre)) {
        return `${this.usuarioSesion.nombres || this.usuarioSesion.nombre} ${this.usuarioSesion.apellidos || ''}`.trim();
      }
      return "Usuario Activo";
    },
    get userInitials() {
      const name = this.userDisplayName;
      const parts = name.split(" ").filter(Boolean);
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
      }
      return (name.slice(0, 2) || "UA").toUpperCase();
    },

    // Control de cambios en personas
    hayCambiosPersonas: false,
    guardandoPersonas: false,

    // Estado de revisiones por roles (se almacena localmente y se sincroniza)
    revisionesHistorial: [],
    plantaSeleccionadaDictamen: null,
    editandoRevision: null, // Guarda { rol, id_planta, plantaNombre } si se está editando una revisión específica
    revisiones: {
      sst: {
        aprobado: false,
        rechazado: false,
        revisor: "",
        fecha: "",
        observacion: "",
        motivoRechazo: ""
      },
      gesco: {
        aprobado: false,
        rechazado: false,
        revisor: "",
        fecha: "",
        observacion: "",
        motivoRechazo: ""
      },
      scr: {
        aprobado: false,
        rechazado: false,
        revisor: "",
        fecha: "",
        observacion: "",
        motivoRechazo: ""
      }
    },

    // Formulario de dictamen del rol activo
    dictamenForm: {
      decision: "aprobar", // 'preaprobar' | 'aprobar' | 'rechazar' | 'devolver'
      motivoRechazo: "",
      motivoDevolucion: "",
      observaciones: ""
    },

    // Modal de confirmación rápida para solicitudes pre-aprobadas
    showModalConfirmacionPreaprobada: false,

    // Modal de Dispositivos y Equipos de Cómputo (Solo Lectura)
    showModalDispositivos: false,
    filtroDispositivos: "",
    dispositivoCopiado: null,

    // Verificación individual de ítems (Checklist de auditoría)
    verificaciones: {
      personas: {},
      vehiculos: {},
      equipos: {}
    },

    // Modales de antecedentes e historial de solicitudes
    showHistorialModal: false,
    showFormModal: false,
    cargandoHistorial: false,
    guardandoAntecedente: false,
    copiadoFeedback: null,
    mensajeExitoAntecedente: "",
    mensajeErrorAntecedente: "",

    // Modales de inducciones y vigencia (GESCO)
    showInduccionModal: false,
    showFormInduccionModal: false,
    cargandoInduccion: false,
    guardandoInduccion: false,
    mensajeExitoInduccion: "",
    mensajeErrorInduccion: "",
    personaSeleccionadaInduccion: null,
    detalleInduccion: {},
    formInduccion: {
      id_persona: null,
      persona_nombre: "",
      persona_apellido: "",
      persona_identificacion: "",
      persona_tipo_doc: "CC",
      persona_cargo: "",
      responsable: "",
      anotaciones: "",
      fecha_induccion: "",
      fecha_vigencia: ""
    },

    // Modal de Seguridad Social (SST)
    showSeguridadSocialModal: false,
    cargandoSeguridadSocial: false,
    guardandoSeguridadSocial: false,
    mensajeExitoSS: "",
    mensajeErrorSS: "",
    personaSeleccionadaSS: null,
    formSeguridadSocial: {
      id: null,
      id_persona: null,
      persona_nombre: "",
      persona_apellido: "",
      persona_identificacion: "",
      persona_tipo_doc: "CC",
      persona_cargo: "",
      responsable: "",
      anotaciones: "",
      ultima_empresa_contratista: "",
      ultima_revision: null,
      fecha_vigencia: null,
      historial: []
    },
    detalleSeguridadSocial: {
      id: null,
      id_persona: null,
      persona_nombre: "",
      persona_apellido: "",
      persona_identificacion: "",
      persona_tipo_doc: "CC",
      persona_cargo: "",
      responsable: "",
      anotaciones: "",
      fecha_vigencia: null,
      ultima_revision: null,
      ultima_empresa_contratista: "",
      historial: []
    },
    formSeguridadSocialRevision: {
      id_persona: null,
      persona_identificacion: "",
      responsable: "",
      fecha_vigencia: null,
      anotaciones: ""
    },
    fpVigenciaSSRevisionInstance: null,

    // Filtros de historial SS en modal
    searchHistorialSS: "",
    fechaDesdeHistorialSS: "",
    fechaHastaHistorialSS: "",
    historialSSPage: 1,
    historialSSPageSize: 5,
    fpDesdeHistorialSSInstance: null,
    fpHastaHistorialSSInstance: null,

    // Filtros del historial
    searchHistorial: "",
    fechaDesdeHistorial: "",
    fechaHastaHistorial: "",
    historialPage: 1,
    historialPageSize: 5,
    fpDesdeHistorialInstance: null,
    fpHastaHistorialInstance: null,

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
            if (this.fpHastaHistorialInstance) {
              this.fpHastaHistorialInstance.set("minDate", dateStr || null);
            }
          } else {
            this.fechaHastaHistorial = dateStr;
            if (this.fpDesdeHistorialInstance) {
              this.fpDesdeHistorialInstance.set("maxDate", dateStr || null);
            }
          }
          this.historialPage = 1;
        }
      });

      if (isDesde) {
        this.fpDesdeHistorialInstance = instance;
      } else {
        this.fpHastaHistorialInstance = instance;
      }
    },

    limpiarFiltrosHistorial() {
      this.searchHistorial = "";
      this.fechaDesdeHistorial = "";
      this.fechaHastaHistorial = "";
      this.historialPage = 1;
      if (this.fpDesdeHistorialInstance) {
        this.fpDesdeHistorialInstance.clear();
        this.fpDesdeHistorialInstance.set("maxDate", null);
      }
      if (this.fpHastaHistorialInstance) {
        this.fpHastaHistorialInstance.clear();
        this.fpHastaHistorialInstance.set("minDate", null);
      }
    },

    // Detalle de historial cargado para el modal
    detalleHistorial: {
      id: null,
      id_persona: null,
      persona_nombre: "",
      persona_apellido: "",
      persona_tipo_doc: "CC",
      persona_identificacion: "",
      persona_cargo: "",
      responsable: "",
      ultimo_usuario_solicitud: "",
      anotaciones: "",
      id_empresa: null,
      ultima_empresa_solicitante: "",
      ultima_revision: null,
      fecha_consulta: null,
      total_solicitudes: 0,
      historial: []
    },

    // Formulario de actualización de vigencia
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
      historial: [],
      total_solicitudes: 0
    },

    personaSeleccionadaAntecedente: null,

    get historialFiltrado() {
      let srcList = [];
      if (this.showSeguridadSocialModal) {
        srcList = this.formSeguridadSocial?.historial || this.detalleSeguridadSocial?.historial || [];
      } else {
        srcList = this.detalleHistorial?.historial || [];
      }
      if (!Array.isArray(srcList)) return [];
      let list = [...srcList];

      if (this.searchHistorial && this.searchHistorial.trim() !== '') {
        const q = this.searchHistorial.toLowerCase().trim();
        list = list.filter(h =>
          (h.codigo_radicado && h.codigo_radicado.toLowerCase().includes(q)) ||
          (h.nombre_empresa && h.nombre_empresa.toLowerCase().includes(q)) ||
          (h.nombre_contratista && h.nombre_contratista.toLowerCase().includes(q))
        );
      }

      if (this.fechaDesdeHistorial) {
        list = list.filter(h => {
          const f = (h.fecha_inicio || h.fecha_solicitud || "").split('T')[0];
          return f >= this.fechaDesdeHistorial;
        });
      }

      if (this.fechaHastaHistorial) {
        list = list.filter(h => {
          const f = (h.fecha_fin || h.fecha_solicitud || "").split('T')[0];
          return f <= this.fechaHastaHistorial;
        });
      }

      return list;
    },

    get totalPaginasHistorial() {
      const total = this.historialFiltrado.length;
      return Math.max(1, Math.ceil(total / this.historialPageSize));
    },

    get historialPagina() {
      const start = (this.historialPage - 1) * this.historialPageSize;
      return this.historialFiltrado.slice(start, start + this.historialPageSize);
    },

    get rangoHistorialMostrado() {
      const total = this.historialFiltrado.length;
      if (total === 0) return '0 de 0';
      const start = (this.historialPage - 1) * this.historialPageSize + 1;
      const end = Math.min(start + this.historialPageSize - 1, total);
      return `${start} - ${end} de ${total}`;
    },

    // Paginación y filtros del historial de Seguridad Social
    get historialSSFiltrado() {
      if (!this.detalleSeguridadSocial || !Array.isArray(this.detalleSeguridadSocial.historial)) return [];
      let list = [...this.detalleSeguridadSocial.historial];

      if (this.searchHistorialSS && this.searchHistorialSS.trim() !== '') {
        const q = this.searchHistorialSS.toLowerCase().trim();
        list = list.filter(h =>
          (h.codigo_radicado && h.codigo_radicado.toLowerCase().includes(q)) ||
          (h.nombre_empresa && h.nombre_empresa.toLowerCase().includes(q)) ||
          (h.nombre_contratista && h.nombre_contratista.toLowerCase().includes(q))
        );
      }

      if (this.fechaDesdeHistorialSS) {
        list = list.filter(h => {
          const f = (h.fecha_inicio || h.fecha_solicitud || "").split('T')[0];
          return f >= this.fechaDesdeHistorialSS;
        });
      }

      if (this.fechaHastaHistorialSS) {
        list = list.filter(h => {
          const f = (h.fecha_fin || h.fecha_solicitud || "").split('T')[0];
          return f <= this.fechaHastaHistorialSS;
        });
      }

      return list;
    },

    get totalPaginasHistorialSS() {
      const total = this.historialSSFiltrado.length;
      return Math.max(1, Math.ceil(total / this.historialSSPageSize));
    },

    get historialSSPagina() {
      const start = (this.historialSSPage - 1) * this.historialSSPageSize;
      return this.historialSSFiltrado.slice(start, start + this.historialSSPageSize);
    },

    get rangoHistorialSSMostrado() {
      const total = this.historialSSFiltrado.length;
      if (total === 0) return '0 de 0';
      const start = (this.historialSSPage - 1) * this.historialSSPageSize + 1;
      const end = Math.min(this.historialSSPage * this.historialSSPageSize, total);
      return `${start}-${end} de ${total}`;
    },

    goToHistorialSSPage(num) {
      if (num >= 1 && num <= this.totalPaginasHistorialSS) {
        this.historialSSPage = num;
      }
    },

    initFlatpickrHistorialSS(el, tipo) {
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
            this.fechaDesdeHistorialSS = dateStr;
            if (this.fpHastaHistorialSSInstance) {
              this.fpHastaHistorialSSInstance.set("minDate", dateStr || null);
            }
          } else {
            this.fechaHastaHistorialSS = dateStr;
            if (this.fpDesdeHistorialSSInstance) {
              this.fpDesdeHistorialSSInstance.set("maxDate", dateStr || null);
            }
          }
          this.historialSSPage = 1;
        }
      });

      if (isDesde) {
        this.fpDesdeHistorialSSInstance = instance;
      } else {
        this.fpHastaHistorialSSInstance = instance;
      }
    },

    limpiarFiltrosHistorialSS() {
      this.searchHistorialSS = "";
      this.fechaDesdeHistorialSS = "";
      this.fechaHastaHistorialSS = "";
      this.historialSSPage = 1;
      if (this.fpDesdeHistorialSSInstance) {
        this.fpDesdeHistorialSSInstance.clear();
        this.fpDesdeHistorialSSInstance.set("maxDate", null);
      }
      if (this.fpHastaHistorialSSInstance) {
        this.fpHastaHistorialSSInstance.clear();
        this.fpHastaHistorialSSInstance.set("minDate", null);
      }
    },

    // Visor de documentos
    docModalOpen: false,
    docActual: {
      titulo: "",
      tipo: "",
      url: "",
      esPdf: false,
      esImagen: false
    },

    // Toast de notificación
    toast: {
      visible: false,
      tipo: "success", // 'success' | 'error' | 'info'
      mensaje: ""
    },

    // Catálogos para resolución de IDs a nombres
    catalogoPlantas: [],
    catalogoEmpresas: [],
    catalogoContratistas: [],

    async init() {
      // 0. Sincronizar estado de modo oscuro
      this.darkMode = document.documentElement.classList.contains('dark') || localStorage.getItem('darkMode') === 'true';
      document.documentElement.classList.toggle('dark', this.darkMode);

      // 1. Obtener ID o Código de la URL
      const params = new URLSearchParams(window.location.search);
      this.solicitudId = params.get("codigo") || params.get("id");

      if (!this.solicitudId) {
        const segs = window.location.pathname.split("/").filter(Boolean);
        const idxRev = segs.indexOf("revision");
        if (idxRev !== -1 && segs[idxRev + 1]) {
          this.solicitudId = decodeURIComponent(segs[idxRev + 1]);
        }
      }

      // 2. Obtener y sincronizar sesión de usuario más reciente
      if (typeof window.syncAuthSessionWithServer === "function") {
        try {
          await window.syncAuthSessionWithServer();
        } catch (eSync) {}
      }

      try {
        const sesion = (typeof getAuthSession === "function")
          ? getAuthSession()
          : JSON.parse(
              sessionStorage.getItem("incarsa_session") ||
              localStorage.getItem("incarsa_session") ||
              "null"
            );
        if (sesion) {
          this.usuarioSesion = sesion;
          const mapaRoles = { 1: "Administrador", 2: "Superadmin", 3: "Vigilante", 4: "Coordinador", 5: "Solicitante", 6: "SST", 7: "GESCO", 8: "SCR" };
          const rol = sesion.rol || sesion.nombre_rol || mapaRoles[sesion.id_rol] || "Solicitante";
          this.rolActual = rol;
          this.rolNombre = rol;
        }
      } catch (e) {
        console.warn("No se pudo parsear sesión:", e);
      }

      // Escuchar actualización de sesión en caliente vía SSE (cambio de plantas por administrador)
      window.addEventListener("sesion-actualizada-en-caliente", (e) => {
        if (e.detail) {
          this.usuarioSesion = e.detail;
          const mapaRoles = { 1: "Administrador", 2: "Superadmin", 3: "Vigilante", 4: "Coordinador", 5: "Solicitante", 6: "SST", 7: "GESCO", 8: "SCR" };
          const rol = this.usuarioSesion.rol || this.usuarioSesion.nombre_rol || mapaRoles[this.usuarioSesion.id_rol] || this.rolActual;
          this.rolActual = rol;
          this.rolNombre = rol;
          if (this.misPlantasDictaminables && this.misPlantasDictaminables.length > 0) {
            if (this.misPlantasDictaminables.length > 1) {
              this.plantaSeleccionadaDictamen = "todas";
            } else if (!this.plantaSeleccionadaDictamen || !this.misPlantasDictaminables.some(p => Number(p.id) === Number(this.plantaSeleccionadaDictamen))) {
              this.plantaSeleccionadaDictamen = this.misPlantasDictaminables[0].id;
            }
          }
          this.mostrarToast("Tus zonas asignadas fueron actualizadas por el Administrador. Permisos actualizados en tiempo real.", "info");
        }
      });

      if (!this.solicitudId) {
        this.error = "No se especificó un ID de solicitud válido.";
        this.cargando = false;
        return;
      }

      await this.cargarSolicitud();

      // Cargar notificaciones del usuario y escuchar eventos SSE en vivo
      this.cargarNotificaciones(50);
      window.addEventListener("notificacion-en-caliente", (e) => {
        if (e.detail) {
          this.notifications.unshift(e.detail);
          this.unreadNotificationsCount++;
        }
      });

      // Si la URL contiene el parámetro ?confirmar=true y la solicitud está preaprobada en estado POR APROBAR
      const paramsConfirmar = params.get("confirmar");
      if ((paramsConfirmar === "true" || paramsConfirmar === "1") && (this.rolActual === "SCR" || this.esSuperAdmin) && this.solicitud?.pre_aprobado && this.solicitud?.estado === "POR APROBAR") {
        setTimeout(() => this.confirmarAprobacionFinalPreaprobada(), 350);
      }
    },

    mostrarToast(mensaje, tipo = "success") {
      this.toast.mensaje = mensaje;
      this.toast.tipo = tipo;
      this.toast.visible = true;
      setTimeout(() => {
        this.toast.visible = false;
      }, 3500);
    },

    async cargarSolicitud() {
      this.cargando = true;
      this.error = null;

      try {
        // Consultar la API
        let data = null;
        try {
          const res = await fetch(`${API.solicitudes}/${this.solicitudId}`);
          if (res.ok) {
            data = await res.json();
          }
        } catch (errApi) {
          console.warn("Fallo al obtener solicitud del backend, buscando en cache local:", errApi);
        }

        // Si no responde la API, buscar en cache local
        if (!data) {
          const locales = JSON.parse(localStorage.getItem("incarsa_solicitudes") || "[]");
          const creadas = JSON.parse(localStorage.getItem("incarsa_solicitudes_creadas") || "[]");
          const todasLocales = [...locales, ...creadas];
          data = todasLocales.find(s => String(s.id) === String(this.solicitudId));
        }

        if (!data) {
          throw new Error(`Solicitud #${this.solicitudId} no encontrada.`);
        }

        if (data.id) {
          this.solicitudId = data.id;
        }

        this.solicitud = this.normalizar(data);

        // Limpiar cualquier cache obsoleto de autorizaciones en localStorage para que la base de datos sea la única fuente de la verdad
        try {
          localStorage.removeItem(`incarsa_solicitud_${this.solicitudId}_personas`);
          localStorage.removeItem(`incarsa_solicitud_${this.solicitudId}_vehiculos`);
        } catch (e) {}

        // Si se ingresa a revisar la solicitud desde cualquier lugar (listado, búsqueda, URL directa),
        // marcar automáticamente las notificaciones pendientes de esta solicitud como leídas para su usuario/rol.
        try {
          const codOId = data.codigo || data.id || this.solicitudId;
          const userSes = this.usuarioSesion || {};
          fetch(`/api/v1/notificaciones/marcar-leida-solicitud`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              id_o_codigo: String(codOId),
              id_usuario: userSes.id || null,
              id_rol: userSes.id_rol || null
            })
          }).then(() => {
            window.dispatchEvent(new CustomEvent("notificaciones-actualizadas"));
            localStorage.setItem("incarsa_notificaciones_reload", Date.now().toString());
          }).catch(() => {});
        } catch (eNotif) {
          console.warn("Aviso al auto-marcar notificación como leída:", eNotif);
        }

        // Cargar dictámenes previos desde backend o storage local
        if (Array.isArray(data.revisiones)) {
          this.revisionesHistorial = data.revisiones;
        } else {
          this.cargarRevisionesGuardadas();
        }

        // Preseleccionar planta(s) para dictamen: si tiene más de 1 planta asignada, preseleccionar 'todas'
        if (this.misPlantasDictaminables && this.misPlantasDictaminables.length > 1) {
          this.plantaSeleccionadaDictamen = "todas";
        } else if (this.misPlantasDictaminables && this.misPlantasDictaminables.length === 1) {
          this.plantaSeleccionadaDictamen = this.misPlantasDictaminables[0].id;
        }

        // Si el rol activo para dictamen es SCR y la solicitud está en estados previos a 'POR APROBAR', preseleccionar 'preaprobar'
        const rolDictamenInit = String(this.editandoRevision ? this.editandoRevision.rol : this.rolActual).trim().toUpperCase();
        if (rolDictamenInit === "SCR" && this.solicitud.estado !== "POR APROBAR") {
          this.dictamenForm.decision = "preaprobar";
        } else {
          this.dictamenForm.decision = "aprobar";
        }

        // Cargar vigencias de antecedentes, inducciones y seguridad social de cada ingresante
        if (this.puedeVerAntecedentes || this.puedeVerInduccion || this.puedeVerSeguridadSocial) {
          await this.cargarVigenciasPersonas();
        }

        // Si la solicitud está en 'ENVIADO' y entra un rol auditor/revisor, actualizar visualmente a 'EN REVISIÓN'
        const estadoActual = (this.solicitud.estado || "").toUpperCase();
        if (estadoActual === "ENVIADO" && (this.rolActual === "SST" || this.rolActual === "GESCO" || this.rolActual === "Administrador")) {
          this.solicitud.estado = "EN REVISIÓN";
        }

      } catch (e) {
        console.error("Error al cargar expediente:", e);
        this.error = e.message || "Error al cargar la solicitud.";
      } finally {
        this.cargando = false;
      }
    },

    normalizar(s) {
      if (!s) return {};

      let cadenaPlanta = "—";
      if (Array.isArray(s.plantas) && s.plantas.length > 0) {
        cadenaPlanta = s.plantas.map(p => (typeof p === "object" ? (p.nombre || p.nombre_planta || p.planta) : p)).filter(Boolean).join(", ");
      } else if (typeof s.planta === "string" && s.planta.trim() !== "") {
        cadenaPlanta = s.planta;
      } else if (typeof s.plantas === "string" && s.plantas.trim() !== "") {
        cadenaPlanta = s.plantas;
      }

      let plantasLista = [];
      if (Array.isArray(s.plantas)) {
        plantasLista = s.plantas.map(p => ({
          id: Number(typeof p === "object" ? (p.id || p.id_planta) : p),
          nombre: typeof p === "object" ? (p.nombre || p.nombre_planta || `Planta ${p.id}`) : `Planta ${p}`
        })).filter(p => p.id);
      }
      if (plantasLista.length === 0 && s.plantas_ids) {
        const rawIds = String(s.plantas_ids).replace(/[\[\]]/g, "").split(",").map(x => parseInt(x.trim(), 10)).filter(n => !isNaN(n));
        plantasLista = rawIds.map(pid => ({ id: pid, nombre: `Planta #${pid}` }));
      }

      let listaComputos = [];
      if (typeof s.computos === 'string' && s.computos.trim() !== '') {
        listaComputos = s.computos.split('###').map(c => {
          const [id, marca, modelo, serie] = c.split('|||');
          return { id, marca, modelo, serie };
        });
      } else if (Array.isArray(s.computos)) {
        listaComputos = s.computos;
      } else if (Array.isArray(s.eq_computo)) {
        listaComputos = s.eq_computo;
      }

      let listaVehiculos = [];
      if (typeof s.vehiculos === 'string' && s.vehiculos.trim() !== '') {
        listaVehiculos = s.vehiculos.split('###').map(v => {
          const [id, tipo, placa, licencia, autorizado, motivo_rechazo] = v.split('|||');
          const isAut = autorizado !== '0' && autorizado !== false && autorizado !== 'false';
          return {
            id, tipo: tipo || "Vehículo", placa, licencia,
            licencia_doc: licencia || "—",
            autorizado: isAut,
            denegadoEnBd: !isAut,
            motivo_rechazo: motivo_rechazo || "",
            documentos: [
              { tipo_doc: "soat", nombre_archivo: `SOAT_${placa || 'DOC'}.pdf` },
              { tipo_doc: "tecnomecanica", nombre_archivo: `RTM_${placa || 'DOC'}.pdf` },
              { tipo_doc: "tarjeta_propiedad", nombre_archivo: `Tarjeta_${placa || 'DOC'}.pdf` }
            ]
          };
        });
      } else if (Array.isArray(s.vehiculos) || Array.isArray(s.vehiculo)) {
        const rawV = Array.isArray(s.vehiculos) ? s.vehiculos : s.vehiculo;
        listaVehiculos = rawV.map((v, vIdx) => {
          const isAut = v.autorizado !== false && v.autorizado !== 0 && v.autorizado !== '0' && v.autorizado !== 'false';
          return {
            id: v.id || v.id_vehiculo || vIdx,
            tipo: v.tipo || "Vehículo",
            placa: v.placa || "—",
            licencia: v.licencia_doc || v.licencia || "—",
            licencia_doc: v.licencia_doc || v.licencia || "—",
            autorizado: isAut,
            denegadoEnBd: !isAut,
            motivo_rechazo: v.motivo_rechazo || v.motivo || "",
            documentos: Array.isArray(v.documentos) && v.documentos.length > 0 ? v.documentos.map((d, dIdx) => ({
              id: d.id || dIdx,
              tipo_doc: d.tipo_doc || "documento",
              nombre_archivo: d.nom_documento || d.nombre_archivo || `doc_${v.placa || 'veh'}_${dIdx}.pdf`,
              url_acceso: d.url_acceso || (d.nom_documento ? `/uploads/documentos/vehiculos/${d.nom_documento}` : null)
            })) : [
              { tipo_doc: "soat", nombre_archivo: `SOAT_${v.placa || 'DOC'}.pdf` },
              { tipo_doc: "tecnomecanica", nombre_archivo: `RTM_${v.placa || 'DOC'}.pdf` }
            ]
          };
        });
      }

      let listaPersonas = [];
      if (typeof s.personas === 'string' && s.personas.trim() !== '') {
        if (s.personas.includes('|||') || s.personas.includes('###')) {
          listaPersonas = s.personas.split('###').map(p => {
            const [id, ap_nombre, tipo_doc, identificacion, cargo, autorizado, motivo_rechazo] = p.split('|||');
            const isAut = autorizado !== '0' && autorizado !== false && autorizado !== 'false';
            return {
              id,
              nombre: ap_nombre || "Contratista",
              tipo_doc: tipo_doc || "CC",
              identificacion: identificacion || "—",
              cargo: cargo || "Operario",
              autorizado: isAut,
              denegadaEnBd: !isAut,
              motivo_rechazo: motivo_rechazo || "",
              documentos: [
                { tipo_doc: "cedula", nombre_archivo: `Cedula_${identificacion || 'doc'}.pdf` },
                { tipo_doc: "arl", nombre_archivo: `ARL_${identificacion || 'doc'}.pdf` },
                { tipo_doc: "examen_medico", nombre_archivo: `Examen_Medico_${identificacion || 'doc'}.pdf` },
                { tipo_doc: "induccion", nombre_archivo: `Certificado_Induccion_${identificacion || 'doc'}.pdf` }
              ]
            };
          });
        }
      } else if (Array.isArray(s.personas) || Array.isArray(s.ingresantes)) {
        const rawP = Array.isArray(s.personas) ? s.personas : s.ingresantes;
        listaPersonas = rawP.map(p => {
          const isAut = p.autorizado !== false && p.autorizado !== 0 && p.autorizado !== '0' && p.autorizado !== 'false';
          return {
            id: p.id,
            id_persona: p.id_persona || p.id,
            nombre: `${p.nombre || ''} ${p.apellido || ''}`.trim() || p.ap_nombre || "Contratista",
            tipo_doc: p.tipo_doc || "CC",
            identificacion: p.identificacion || "—",
            cargo: p.cargo || "Operario",
            autorizado: isAut,
            denegadaEnBd: !isAut,
            denegado_por: p.denegado_por || null,
            denegado_por_nombre: p.denegado_por_nombre || "",
            motivo_rechazo: p.motivo_rechazo || "",
            estado_datos: String(p.estado_datos || "PENDIENTE").trim().toUpperCase(),
            token_autorizacion: p.token_autorizacion || null,
            fecha_respuesta_datos: p.fecha_respuesta_datos || null,
            _reenviandoCorreo: false,
            fecha_consulta: (p.fecha_consulta && p.fecha_consulta !== "None" && p.fecha_consulta !== "null" && p.fecha_consulta !== "Pendiente" && p.fecha_consulta !== "No registrada") ? p.fecha_consulta : null,
            ultima_revision: (p.ultima_revision && p.ultima_revision !== "None" && p.ultima_revision !== "null" && p.ultima_revision !== "No registrada") ? p.ultima_revision : null,
            responsable: p.responsable || null,
            anotaciones: p.anotaciones || "",
            fecha_induccion: (p.fecha_induccion && p.fecha_induccion !== "None" && p.fecha_induccion !== "null") ? p.fecha_induccion : null,
            fecha_vigencia_induccion: (p.fecha_vigencia_induccion && p.fecha_vigencia_induccion !== "None" && p.fecha_vigencia_induccion !== "null") ? p.fecha_vigencia_induccion : null,
            responsable_induccion: p.responsable_induccion || null,
            anotaciones_induccion: p.anotaciones_induccion || "",
            estadoVigenciaInduccion: this.getEstadoVigenciaInduccion(p.fecha_vigencia_induccion || (p.fecha_induccion ? this.obtenerFechaMasUnAnio(p.fecha_induccion) : null)),
            fecha_vigencia_ss: (p.fecha_vigencia_ss && p.fecha_vigencia_ss !== "None" && p.fecha_vigencia_ss !== "null" && p.fecha_vigencia_ss !== "Pendiente" && p.fecha_vigencia_ss !== "No registrada") ? p.fecha_vigencia_ss : null,
            responsable_ss: p.responsable_ss || null,
            anotaciones_ss: p.anotaciones_ss || "",
            estadoVigenciaSS: this.getEstadoVigenciaSS(p.fecha_vigencia_ss || null),
            documentos: Array.isArray(p.documentos) && p.documentos.length > 0 ? p.documentos : [
              { tipo_doc: "cedula", nombre_archivo: `Cedula_${p.identificacion || 'doc'}.pdf` },
              { tipo_doc: "arl", nombre_archivo: `ARL_${p.identificacion || 'doc'}.pdf` },
              { tipo_doc: "examen_medico", nombre_archivo: `Examen_${p.identificacion || 'doc'}.pdf` },
              { tipo_doc: "induccion", nombre_archivo: `Induccion_${p.identificacion || 'doc'}.pdf` }
            ]
          };
        });
      }

      // Código alfanumérico
      let codigoVal = s.codigo_radicado || s.codigo;
      if (!codigoVal) {
        const strId = String(s.id || '1');
        codigoVal = `RAD-${strId.padStart(4, '0')}`;
      }

      const nombreEmpresaOrigen = s.nombre_empresa || s.empresa_origen || s.empresaOrigen || "INCARSA";
      const nombreContratista = s.nombre_emContratista || s.empresa_contratista || s.contratista || "—";
      const diligenciadorNombre = s.diligenciador || "Administrador";

      return {
        id: s.id,
        codigo: codigoVal,
        observaciones: s.observaciones || s.observacion || "",
        empresa_origen: nombreEmpresaOrigen,
        nombre_empresa: nombreEmpresaOrigen,
        empresaOrigen: nombreEmpresaOrigen,
        empresa_contratista: nombreContratista,
        nombre_emContratista: nombreContratista,
        contratista: nombreContratista,
        diligenciador: diligenciadorNombre,
        fecha_ingreso: formatearFechaCorta(s.fecha_ingreso || s.fecha_inicio || s.fechaIngreso),
        fecha_salida: formatearFechaCorta(s.fecha_salida || s.fecha_fin || s.fechaSalida),
        fecha_creacion: formatearFechaHoraEspanol(s.fecha_creacion),
        nivel_de_riesgo: s.nivel_de_riesgo || s.riesgo || "Bajo",
        actividad: s.actividad || "Mantenimiento e inspección operativa",
        planta: cadenaPlanta,
        plantas: cadenaPlanta,
        plantas_lista: plantasLista,
        estado: (() => {
          const rawE = String(s.estado || "ENVIADO").trim().toUpperCase();
          if (rawE === "EN REVISIÓN" || rawE === "EN REVISION") return "EN REVISIÓN";
          if (rawE === "POR APROBAR") return "POR APROBAR";
          if (rawE === "APROBADO") return "APROBADO";
          if (rawE === "RECHAZADO") return "RECHAZADO";
          if (rawE === "ENVIADO") return "ENVIADO";
          return rawE;
        })(),
        personas: listaPersonas,
        vehiculos: listaVehiculos,
        computos: listaComputos
      };
    },

    // -------------------------------------------------------------
    // Gestión de Autorización Individual de Personas
    // -------------------------------------------------------------
    get totalPersonas() {
      return this.solicitud?.personas?.length || 0;
    },

    get totalPersonasAutorizadas() {
      return this.solicitud?.personas?.filter(p => p.autorizado === true).length || 0;
    },

    get totalPersonasAutorizadasCompletas() {
      return this.solicitud?.personas?.filter(p => p.autorizado === true && String(p.estado_datos || 'PENDIENTE').toUpperCase() === 'AUTORIZADO').length || 0;
    },

    get totalPersonasPendientesDatos() {
      return this.solicitud?.personas?.filter(p => p.autorizado === true && String(p.estado_datos || 'PENDIENTE').toUpperCase() !== 'AUTORIZADO').length || 0;
    },

    get totalPersonasDenegadas() {
      return this.solicitud?.personas?.filter(p => p.autorizado === false).length || 0;
    },

    // -------------------------------------------------------------
    // Gestión de Autorización Individual de Vehículos
    // -------------------------------------------------------------
    get totalVehiculos() {
      return this.solicitud?.vehiculos?.length || 0;
    },

    get totalVehiculosAutorizados() {
      return this.solicitud?.vehiculos?.filter(v => v.autorizado === true).length || 0;
    },

    get totalVehiculosDenegados() {
      return this.solicitud?.vehiculos?.filter(v => v.autorizado === false).length || 0;
    },

    get yaAproboRolActual() {
      const estado = String(this.solicitud?.estado || "").toUpperCase();
      if (estado === "APROBADO") return true;

      // Si el rol es SST o GESCO, verificar si ya emitió dictamen en su planta o en la solicitud
      if (this.rolActual === "SST" || this.rolActual === "GESCO") {
        if (this.miPlantaYaFirmada) return true;
        const revs = this.revisionesHistorial || [];
        const tieneDictamen = revs.some(
          r => String(r.rol).toUpperCase() === this.rolActual.toUpperCase() && 
               (r.decision === "APROBADO" || r.decision === "RECHAZADO")
        );
        if (tieneDictamen && !this.puedeDictaminar) return true;
        return false;
      }

      // Si el rol es SCR
      if (this.rolActual === "SCR") {
        return Boolean(this.dictamenSCR?.aprobado || this.dictamenSCR?.rechazado);
      }

      return false;
    },

    get puedeEditarAutorizacion() {
      // SCR y roles superiores tienen potestad para editar autorizaciones en todo momento
      if (this.esScrOSuperior) {
        return true;
      }

      const estado = String(this.solicitud?.estado || "").toUpperCase();
      // Si la solicitud ya está en estado final RECHAZADO para roles operativos
      if (estado === "RECHAZADO") {
        return false;
      }

      // SST y GESCO pueden autorizar personas de una solicitud aunque ya hayan enviado su visto bueno
      if (this.esSstOGesco) {
        if (!this.tienePlantaAsignadaParaSolicitud) return false;
        return true;
      }

      // Si la solicitud ya fue APROBADA de forma definitiva para otros roles operativos
      if (estado === "APROBADO") {
        return false;
      }

      // Si el usuario con su rol actual ya aprobó o emitió dictamen
      if (this.yaAproboRolActual) {
        return false;
      }

      // Solo puede editar quien tiene permisos y acciones activas para dictaminar en esta etapa
      return Boolean(this.puedeDictaminar);
    },

    puedeAutorizarPersona(persona) {
      if (!this.puedeEditarAutorizacion) return false;

      // Si la persona NO estaba denegada en BD, cualquier revisor con permisos puede autorizarla
      if (!persona || !persona.denegadaEnBd) {
        return true;
      }

      // Si estaba denegada en BD:
      // REGLA 1: "si un usuario en la revision no autoriza a una persona, otros usuarios no pueden reautorizarla, SOLO la persona que nego el acceso puede volver a autorizar"
      const idMiUsuario = this.usuarioSesion?.id || this.usuarioSesion?.id_usuario;
      if (this.esSuperAdmin) {
        return true;
      }
      if (persona.denegado_por && idMiUsuario) {
        return String(persona.denegado_por) === String(idMiUsuario);
      }

      // Si por datos anteriores no se registró denegado_por, solo SCR o Superadmin
      if (!persona.denegado_por && this.esScrOSuperior) {
        return true;
      }

      return false;
    },

    puedeDenegarPersona(persona) {
      if (!this.puedeEditarAutorizacion) return false;

      // REGLA 2: "ademas al finalizar el proceso de la revision los que hayan finalizado con autorizacion no pueden ser editados a no autorizado A MENOS que sea rol admin o superadmin"
      if (this.esRevisionFinalizada) {
        if (persona?.denegadaEnBd === false || persona?.autorizado) {
          return this.esAdminOSuperadmin;
        }
      }

      return true;
    },

    getTooltipAutorizar(persona) {
      if (!this.puedeEditarAutorizacion) {
        return "Autorización bloqueada: no tienes permisos de edición en esta etapa.";
      }
      if (persona && persona.denegadaEnBd && !this.puedeAutorizarPersona(persona)) {
        const nom = persona.denegado_por_nombre || "otro revisor";
        return `No puedes autorizar a este ingresante: fue denegado por ${nom}. Solo quien negó el acceso puede volver a autorizarlo.`;
      }
      return "Autorizar ingresante";
    },

    getTooltipDenegar(persona) {
      if (!this.puedeEditarAutorizacion) {
        return "Autorización bloqueada: no tienes permisos de edición en esta etapa.";
      }
      if (!this.puedeDenegarPersona(persona)) {
        return "El proceso de revisión ya finalizó. Solo un Administrador o Superadmin puede revocar la autorización de una persona aprobada.";
      }
      return "Denegar acceso a este ingresante";
    },

    puedeAutorizarVehiculo(vehiculo) {
      if (!this.puedeEditarAutorizacion) return false;
      if (this.esScrOSuperior || this.esSstOGesco) {
        return true;
      }
      if (vehiculo && vehiculo.denegadoEnBd) {
        return false;
      }
      return true;
    },

    setAutorizacionPersona(persona, estaAutorizado, motivo = "") {
      if (!this.puedeEditarAutorizacion) {
        this.mostrarToast("No puedes modificar la autorización: la solicitud está bloqueada para tu rol.", "info");
        return;
      }
      if (estaAutorizado && !this.puedeAutorizarPersona(persona)) {
        const nom = persona.denegado_por_nombre || "otro revisor";
        this.mostrarToast(`No puedes autorizar a este ingresante: fue denegado por ${nom}. Solo quien negó el acceso puede volver a autorizarlo.`, "warning");
        return;
      }
      if (!estaAutorizado && !this.puedeDenegarPersona(persona)) {
        this.mostrarToast("El proceso de revisión ya finalizó. Solo un Administrador o Superadmin puede revocar la autorización de una persona aprobada.", "warning");
        return;
      }
      persona.autorizado = estaAutorizado;
      if (!estaAutorizado && motivo) {
        persona.motivo_rechazo = motivo;
      } else if (estaAutorizado) {
        persona.motivo_rechazo = "";
      }
      this.hayCambiosPersonas = true;
      const nombre = persona.nombre || "Ingresante";
      this.mostrarToast(
        estaAutorizado ? `✅ ${nombre} marcado como Autorizado (recuerda guardar cambios)` : `⛔ Acceso denegado a ${nombre} (recuerda guardar cambios)`,
        estaAutorizado ? "success" : "info"
      );
    },

    toggleAutorizacionPersona(persona) {
      if (!this.puedeEditarAutorizacion) return;
      if (!persona.autorizado && !this.puedeAutorizarPersona(persona)) {
        const nom = persona.denegado_por_nombre || "otro revisor";
        this.mostrarToast(`No puedes autorizar a este ingresante: fue denegado por ${nom}. Solo quien negó el acceso puede volver a autorizarlo.`, "warning");
        return;
      }
      if (persona.autorizado && !this.puedeDenegarPersona(persona)) {
        this.mostrarToast("El proceso de revisión ya finalizó. Solo un Administrador o Superadmin puede revocar la autorización de una persona aprobada.", "warning");
        return;
      }
      this.setAutorizacionPersona(persona, !persona.autorizado);
    },

    autorizarTodasPersonas() {
      if (!this.puedeEditarAutorizacion) {
        this.mostrarToast("No puedes modificar autorizaciones: la solicitud está bloqueada.", "info");
        return;
      }
      if (!this.solicitud?.personas || this.solicitud.personas.length === 0) return;
      let omitidas = 0;
      this.solicitud.personas.forEach(p => {
        if (this.puedeAutorizarPersona(p)) {
          p.autorizado = true;
          p.motivo_rechazo = "";
        } else {
          omitidas++;
        }
      });
      this.hayCambiosPersonas = true;
      if (omitidas > 0) {
        this.mostrarToast(`Se autorizaron los ingresantes disponibles (${omitidas} ingresante(s) se mantuvieron denegados porque solo quien los denegó puede reautorizarlos). Recuerda guardar cambios.`, "info");
      } else {
        this.mostrarToast("Todas las personas marcadas como autorizadas (recuerda guardar cambios)", "success");
      }
    },

    denegarTodasPersonas() {
      if (!this.puedeEditarAutorizacion) {
        this.mostrarToast("No puedes modificar autorizaciones: la solicitud está bloqueada.", "info");
        return;
      }
      if (!this.solicitud?.personas || this.solicitud.personas.length === 0) return;
      let omitidas = 0;
      this.solicitud.personas.forEach(p => {
        if (this.puedeDenegarPersona(p)) {
          p.autorizado = false;
        } else {
          omitidas++;
        }
      });
      this.hayCambiosPersonas = true;
      if (omitidas > 0) {
        this.mostrarToast(`Se denegaron los ingresantes disponibles (${omitidas} persona(s) con aprobación final no pudieron modificarse porque solo Admin/Superadmin tienen potestad). Recuerda guardar cambios.`, "warning");
      } else {
        this.mostrarToast("Todas las personas marcadas como No Autorizadas (recuerda guardar cambios)", "info");
      }
    },

    getPersonaCardClass(persona) {
      if (!persona) return '';
      if (!persona.autorizado) return 'is-denegado';
      const est = String(persona.estado_datos || 'PENDIENTE').trim().toUpperCase();
      if (est === 'AUTORIZADO') return 'is-autorizado';
      return 'is-pendiente-datos';
    },

    getPersonaNumBadgeClass(persona) {
      if (!persona) return '';
      if (!persona.autorizado) return 'bg-red-100 text-red-800 border border-red-300 dark:bg-red-950/60 dark:text-red-300 dark:border-red-700/60';
      const est = String(persona.estado_datos || 'PENDIENTE').trim().toUpperCase();
      if (est === 'AUTORIZADO') return 'bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-500/40';
      return 'bg-amber-100 text-amber-900 border border-amber-300 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-500/40';
    },

    copiarEnlaceAutorizacionDatos(persona) {
      if (!persona?.token_autorizacion) {
        this.mostrarToast("Esta persona no tiene un enlace de autorización disponible.", "warning");
        return;
      }
      const url = `${window.location.origin}/autorizacion-datos/${persona.token_autorizacion}`;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url)
          .then(() => {
            this.mostrarToast(`📋 Enlace de autorización copiado para ${persona.nombre || 'el ingresante'}.`, "success");
          })
          .catch(() => {
            prompt("Copia el siguiente enlace:", url);
          });
      } else {
        prompt("Copia el siguiente enlace:", url);
      }
    },

    async reenviarCorreoAutorizacionDatos(persona) {
      if (!persona) return;
      const sId = this.solicitud?.id || this.solicitudId;
      const pId = persona.id || persona.id_persona;
      if (!sId || !pId) {
        this.mostrarToast("No se pudo identificar la persona o solicitud.", "error");
        return;
      }
      persona._reenviandoCorreo = true;
      try {
        const token = (typeof getAuthToken === "function") ? getAuthToken() : (this.usuarioSesion?.token || null);
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`/api/v1/solicitudes/${sId}/personas/${pId}/reenviar-autorizacion`, {
          method: "POST",
          headers
        });
        const data = await res.json().catch(() => ({}));
        if (res.ok && (data.exito || data.status === "success")) {
          this.mostrarToast(`📧 Correo de autorización reenviado exitosamente a ${persona.nombre || 'el ingresante'}.`, "success");
        } else {
          const msg = data.mensaje || data.detail || "Error al reenviar el correo de autorización.";
          this.mostrarToast(msg, "error");
        }
      } catch (err) {
        console.error("Error al reenviar correo de autorización:", err);
        this.mostrarToast("Error de conexión al reenviar correo.", "error");
      } finally {
        persona._reenviandoCorreo = false;
      }
    },

    async persistirPersonasEnStorage() {
      // Intencionalmente vacío: los cambios en autorizaciones no se guardan en localStorage
      // para asegurar que solo se apliquen en la base de datos al presionar el botón de guardar.
      return;
    },

    async guardarCambiosPersonas() {
      if (!this.solicitud?.personas || this.solicitud.personas.length === 0) return;
      this.guardandoPersonas = true;
      try {
        const nombreUsuario = (
          this.usuarioSesion?.nombre || 
          this.usuarioSesion?.nombre_completo || 
          (this.usuarioSesion?.nombres ? `${this.usuarioSesion.nombres} ${this.usuarioSesion.apellidos || ''}`.trim() : '')
        ) || `Revisor (${this.rolActual})`;

        const token = (typeof getAuthToken === "function") ? getAuthToken() : (this.usuarioSesion?.token || null);
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const targetId = this.solicitud?.id || this.solicitudId;
        const payload = {
          rol: this.rolActual,
          id_usuario: this.usuarioSesion?.id || null,
          nombre_revisor: nombreUsuario,
          personas: (this.solicitud?.personas || []).map(p => ({
            id: p.id || p.id_persona,
            autorizado: Boolean(p.autorizado),
            motivo: p.motivo_rechazo || p.motivo || ""
          }))
        };

        const res = await fetch(`${API.solicitudes}/${targetId}/personas-autorizacion`, {
          method: "POST",
          headers: headers,
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          this.hayCambiosPersonas = false;
          try {
            localStorage.removeItem(`incarsa_solicitud_${targetId}_personas`);
          } catch (e) {}
          this.mostrarToast("✅ Autorizaciones actualizadas en la base de datos y notificadas a SCR.", "success");
          await this.cargarSolicitud();
        } else {
          const errData = await res.json().catch(() => ({}));
          const errMsg = errData.detail || errData.mensaje || `Error del servidor (${res.status})`;
          this.mostrarToast(`Error al guardar autorizaciones: ${errMsg}`, "error");
        }
      } catch (err) {
        console.error("Error al guardar autorizaciones de personas:", err);
        this.mostrarToast("Error de conexión al guardar autorizaciones: " + err.message, "error");
      } finally {
        this.guardandoPersonas = false;
      }
    },

    async descartarCambiosPersonas() {
      this.hayCambiosPersonas = false;
      try {
        localStorage.removeItem(`incarsa_solicitud_${this.solicitudId}_personas`);
      } catch (e) {}
      await this.cargarSolicitud();
      this.mostrarToast("Cambios descartados. Se restauró el estado registrado en base de datos.", "info");
    },

    setAutorizacionVehiculo(vehiculo, estaAutorizado, motivo = "") {
      if (!this.puedeEditarAutorizacion) {
        this.mostrarToast("No puedes modificar la autorización: ya has emitido dictamen o la solicitud ya fue procesada.", "info");
        return;
      }
      if (estaAutorizado && !this.puedeAutorizarVehiculo(vehiculo)) {
        this.mostrarToast("No puedes autorizar este vehículo: fue denegado en una revisión previa. Solo SCR o superiores en modo de edición de revisión pueden reautorizarlo.", "warning");
        return;
      }
      vehiculo.autorizado = estaAutorizado;
      if (!estaAutorizado && motivo) {
        vehiculo.motivo_rechazo = motivo;
      } else if (estaAutorizado) {
        vehiculo.motivo_rechazo = "";
      }
      this.persistirVehiculosEnStorage();
      const placa = vehiculo.placa || "Vehículo";
      this.mostrarToast(
        estaAutorizado ? `✅ Vehículo [${placa}] ha sido autorizado` : `⛔ Acceso denegado a vehículo [${placa}]`,
        estaAutorizado ? "success" : "info"
      );
    },

    toggleAutorizacionVehiculo(vehiculo) {
      if (!this.puedeEditarAutorizacion) return;
      if (!vehiculo.autorizado && !this.puedeAutorizarVehiculo(vehiculo)) {
        this.mostrarToast("No puedes autorizar este vehículo: fue denegado en una revisión previa. Solo SCR o superior en edición pueden reautorizarlo.", "warning");
        return;
      }
      this.setAutorizacionVehiculo(vehiculo, !vehiculo.autorizado);
    },

    autorizarTodosVehiculos() {
      if (!this.puedeEditarAutorizacion) {
        this.mostrarToast("No puedes modificar autorizaciones: ya has emitido tu dictamen.", "info");
        return;
      }
      if (!this.solicitud?.vehiculos || this.solicitud.vehiculos.length === 0) return;
      let omitidos = 0;
      this.solicitud.vehiculos.forEach(v => {
        if (this.puedeAutorizarVehiculo(v)) {
          v.autorizado = true;
          v.motivo_rechazo = "";
        } else {
          omitidos++;
        }
      });
      this.persistirVehiculosEnStorage();
      if (omitidos > 0) {
        this.mostrarToast(`Se autorizaron los vehículos disponibles (${omitidos} vehículo(s) se mantuvieron denegados por revisión previa).`, "info");
      } else {
        this.mostrarToast("Todos los vehículos de la solicitud han sido autorizados", "success");
      }
    },

    denegarTodosVehiculos() {
      if (!this.puedeEditarAutorizacion) {
        this.mostrarToast("No puedes modificar autorizaciones: ya has emitido tu dictamen.", "info");
        return;
      }
      if (!this.solicitud?.vehiculos || this.solicitud.vehiculos.length === 0) return;
      this.solicitud.vehiculos.forEach(v => {
        v.autorizado = false;
      });
      this.persistirVehiculosEnStorage();
      this.mostrarToast("Todos los vehículos han sido marcados como No Autorizados", "info");
    },

    async persistirVehiculosEnStorage() {
      if (!this.puedeEditarAutorizacion) return;
      try {
        const storageKey = `incarsa_solicitud_${this.solicitudId}_vehiculos`;
        localStorage.setItem(storageKey, JSON.stringify(this.solicitud.vehiculos));

        const locales = JSON.parse(localStorage.getItem("incarsa_solicitudes") || "[]");
        const idx = locales.findIndex(s => String(s.id) === String(this.solicitudId));
        if (idx > -1) {
          locales[idx].vehiculos = this.solicitud.vehiculos;
          localStorage.setItem("incarsa_solicitudes", JSON.stringify(locales));
        }
      } catch (e) {
        console.warn("No se pudo guardar vehículos en storage:", e);
      }
    },

    cargarRevisionesGuardadas() {
      try {
        const storageKey = `incarsa_revisiones_${this.solicitudId}`;
        const guardado = JSON.parse(localStorage.getItem(storageKey) || "null");
        if (guardado) {
          if (Array.isArray(guardado.historial)) {
            this.revisionesHistorial = guardado.historial;
          } else if (Array.isArray(guardado)) {
            this.revisionesHistorial = guardado;
          }
          if (guardado.roles) {
            this.revisiones = { ...this.revisiones, ...guardado.roles };
          }
        }
      } catch (e) {
        console.warn("Error al cargar revisiones guardadas:", e);
      }
    },

    guardarRevisionesEnStorage() {
      try {
        const storageKey = `incarsa_revisiones_${this.solicitudId}`;
        localStorage.setItem(storageKey, JSON.stringify({
          historial: this.revisionesHistorial,
          roles: this.revisiones
        }));
      } catch (e) {}
    },

    // -------------------------------------------------------------
    cambiarRolSimulado(nuevoRol) {
      this.rolActual = nuevoRol;
      this.rolNombre = nuevoRol;
      this.dictamenForm.observaciones = "";
      this.dictamenForm.motivoRechazo = "";
      this.dictamenForm.motivoDevolucion = "";

      const rolUpper = String(nuevoRol || "").trim().toUpperCase();
      if (rolUpper === "SST" || rolUpper === "GESCO") {
        this.dictamenForm.decision = "aprobar";
      } else if (rolUpper === "SCR") {
        this.dictamenForm.decision = (this.solicitud?.estado !== "POR APROBAR") ? "preaprobar" : "aprobar";
      } else {
        this.dictamenForm.decision = "aprobar";
      }

      if (this.misPlantasDictaminables.length > 0) {
        this.plantaSeleccionadaDictamen = this.misPlantasDictaminables.length > 1 ? "todas" : this.misPlantasDictaminables[0].id;
      }
    },

    // -------------------------------------------------------------
    // Reglas de negocio y dictamen Multi-Planta
    // -------------------------------------------------------------
    get plantasSolicitud() {
      return this.solicitud?.plantas_lista || [];
    },

    get totalPlantas() {
      return this.plantasSolicitud.length;
    },

    get matrizRevisionesPorPlanta() {
      const plantas = this.plantasSolicitud;
      const revs = this.revisionesHistorial || [];

      return plantas.map(p => {
        const revSst = revs.find(r => (Number(r.id_planta) === Number(p.id) || (plantas.length === 1 && !r.id_planta)) && String(r.rol).toUpperCase() === 'SST');
        const revGesco = revs.find(r => (Number(r.id_planta) === Number(p.id) || (plantas.length === 1 && !r.id_planta)) && String(r.rol).toUpperCase() === 'GESCO');

        const sstAprobado = revSst?.decision === 'APROBADO';
        const sstRechazado = revSst?.decision === 'RECHAZADO';
        const gescoAprobado = revGesco?.decision === 'APROBADO';
        const gescoRechazado = revGesco?.decision === 'RECHAZADO';

        return {
          id: p.id,
          nombre: p.nombre,
          sst: {
            aprobado: sstAprobado,
            rechazado: sstRechazado,
            revisor: revSst?.nombre_revisor || '',
            fecha: revSst?.fecha_revision ? formatearFechaHoraEspanol(revSst.fecha_revision) : '',
            observacion: revSst?.observacion || '',
            motivoRechazo: revSst?.motivo_rechazo || ''
          },
          gesco: {
            aprobado: gescoAprobado,
            rechazado: gescoRechazado,
            revisor: revGesco?.nombre_revisor || '',
            fecha: revGesco?.fecha_revision ? formatearFechaHoraEspanol(revGesco.fecha_revision) : '',
            observacion: revGesco?.observacion || '',
            motivoRechazo: revGesco?.motivo_rechazo || ''
          },
          completa: sstAprobado && gescoAprobado
        };
      });
    },

    get dictamenSCR() {
      const revs = this.revisionesHistorial || [];
      const revScr = revs.find(r => String(r.rol).toUpperCase() === 'SCR');
      return {
        preaprobado: Boolean(this.solicitud?.pre_aprobado) || revScr?.decision === 'PREAPROBADO',
        aprobado: revScr?.decision === 'APROBADO' || this.solicitud?.estado === 'APROBADO',
        rechazado: revScr?.decision === 'RECHAZADO' || (this.solicitud?.estado === 'RECHAZADO' && revScr?.decision === 'RECHAZADO'),
        revisor: revScr?.nombre_revisor || '',
        fecha: revScr?.fecha_revision ? formatearFechaHoraEspanol(revScr.fecha_revision) : '',
        observacion: revScr?.observacion || '',
        motivoRechazo: revScr?.motivo_rechazo || ''
      };
    },

    get observacionesSSTGESCO() {
      const revs = this.revisionesHistorial || [];
      return revs.filter(r => {
        const rol = String(r.rol || "").toUpperCase();
        return (rol === 'SST' || rol === 'GESCO') && (r.observacion || r.motivo_rechazo || r.motivo_devolucion);
      }).map(r => {
        const planta = (this.plantasSolicitud || []).find(p => Number(p.id) === Number(r.id_planta));
        return {
          rol: r.rol,
          revisor: r.nombre_revisor || 'Auditor',
          planta: planta?.nombre || r.planta_nombre || (r.id_planta ? `Planta ${r.id_planta}` : 'General'),
          decision: r.decision,
          observacion: r.observacion || r.motivo_rechazo || r.motivo_devolucion || '',
          fecha: r.fecha_revision ? formatearFechaHoraEspanol(r.fecha_revision) : ''
        };
      });
    },

    get totalPlantasCompletadas() {
      return this.matrizRevisionesPorPlanta.filter(p => p.completa).length;
    },

    get misPlantasDictaminables() {
      const todas = this.plantasSolicitud;
      const sesion = (typeof getAuthSession === 'function' ? getAuthSession() : null) || this.usuarioSesion;
      const esAdmin = this.rolActual === 'Administrador' || this.rolActual === 'SCR' || 
                      (sesion && (Number(sesion.id_rol) === 1 || String(sesion.rol).toUpperCase().includes("ADMIN")));
      if (esAdmin) {
        return todas;
      }
      const misIds = (sesion?.plantas_ids || []).map(Number);
      if (misIds.length === 0) return todas;
      const filtradas = todas.filter(p => misIds.includes(p.id));
      return filtradas.length > 0 ? filtradas : todas;
    },

    get miPlantaYaFirmada() {
      if (this.rolActual !== 'SST' && this.rolActual !== 'GESCO') return false;
      const rolKey = this.rolActual.toLowerCase();
      const misPlantas = this.misPlantasDictaminables || [];
      if (misPlantas.length === 0) return false;

      // Si seleccionó 'todas' o aún no ha seleccionado:
      if (!this.plantaSeleccionadaDictamen || this.plantaSeleccionadaDictamen === 'todas') {
        const matriz = this.matrizRevisionesPorPlanta || [];
        // Solo se considera ya firmada si TODAS sus plantas asignadas ya tienen dictamen registrado
        return misPlantas.every(p => {
          const item = matriz.find(m => Number(m.id) === Number(p.id));
          return item && Boolean(item[rolKey]?.aprobado || item[rolKey]?.rechazado);
        });
      }

      // Si seleccionó una planta específica:
      const pid = Number(this.plantaSeleccionadaDictamen);
      const item = this.matrizRevisionesPorPlanta.find(p => Number(p.id) === pid);
      if (!item) return false;
      return Boolean(item[rolKey]?.aprobado || item[rolKey]?.rechazado);
    },

    get tienePlantaAsignadaParaSolicitud() {
      if (this.rolActual !== "SST" && this.rolActual !== "GESCO") {
        return true;
      }

      // Si el rol es simulado por un Administrador o no tiene restricciones, permitir
      const sesion = (typeof getAuthSession === 'function' ? getAuthSession() : null) || this.usuarioSesion;
      const esAdmin = sesion && (Number(sesion.id_rol) === 1 || String(sesion.rol).toUpperCase().includes("ADMIN"));
      if (esAdmin) {
        return true;
      }

      const plantasUsuario = (sesion?.plantas_ids || []).map(Number);

      let plantasSol = this.plantasSolicitud.map(p => p.id);
      if (plantasSol.length === 0 && this.solicitud?.plantas_ids) {
        plantasSol = String(this.solicitud.plantas_ids).replace(/[\[\]]/g, "").split(",").map(x => parseInt(x.trim(), 10)).filter(n => !isNaN(n));
      }

      if (plantasUsuario.length > 0) {
        if (plantasSol.length > 0) {
          return plantasSol.some(pid => plantasUsuario.includes(pid));
        }
        return true;
      }

      if (sesion && (sesion.id_rol === 3 || sesion.id_rol === 4)) {
        return false;
      }

      return true;
    },

    get puedeDictaminar() {
      if (typeof window.puedeAccion === "function") {
        if (!window.puedeAccion("solicitudes", "aprobar") && !window.puedeAccion("revision_solicitud", "aprobar")) {
          return false;
        }
      }

      // Si está en modo edición de una revisión activa, puede dictaminar / guardar cambios
      if (this.editandoRevision) {
        return true;
      }

      // SCR y roles superiores pueden emitir o editar revisiones en cualquier momento
      if (this.esScrOSuperior) {
        return true;
      }

      const estado = String(this.solicitud?.estado || "").toUpperCase();

      if (estado === "RECHAZADO" || estado === "APROBADO") {
        return false;
      }

      // Validación para SST y GESCO:
      if (this.rolActual === "SST" || this.rolActual === "GESCO") {
        if (!this.tienePlantaAsignadaParaSolicitud) return false;
        if (estado !== "ENVIADO" && estado !== "EN REVISIÓN" && estado !== "EN REVISION") return false;
        if (this.miPlantaYaFirmada) return false;
        return true;
      }

      return false;
    },

    /**
     * Carga una revisión existente (SST, GESCO o SCR) en el formulario de dictamen para que el revisor o SCR/Admin puedan editarla
     */
    cargarRevisionParaEdicion(rol, id_planta = null, plantaNombre = "") {
      const rolUpper = String(rol).toUpperCase();
      const esMio = (String(this.rolActual).toUpperCase() === rolUpper);
      if (!this.esScrOSuperior && !esMio) {
        this.mostrarToast(`Solo puedes editar revisiones de tu propio rol (${this.rolActual}).`, "warning");
        return;
      }

      const revs = this.revisionesHistorial || [];
      const encontrada = revs.find(r =>
        String(r.rol).toUpperCase() === rolUpper &&
        (id_planta === null || Number(r.id_planta) === Number(id_planta))
      );

      let decision = "aprobar";
      let motivoRechazo = "";
      let motivoDevolucion = "";
      let observaciones = "";

      if (encontrada) {
        const dec = String(encontrada.decision || "").toUpperCase();
        if (dec === "RECHAZADO") decision = "rechazar";
        else if (dec === "DEVUELTO") decision = "devolver";
        else if (dec === "PREAPROBADO") decision = "preaprobar";
        else decision = "aprobar";

        motivoRechazo = encontrada.motivo_rechazo || "";
        motivoDevolucion = encontrada.motivo_devolucion || "";
        observaciones = encontrada.observacion || "";
      }

      this.editandoRevision = {
        rol: rolUpper,
        id_planta: id_planta ? Number(id_planta) : null,
        plantaNombre: plantaNombre || (id_planta ? `Planta #${id_planta}` : "General")
      };

      if (id_planta) {
        this.plantaSeleccionadaDictamen = Number(id_planta);
      }

      this.dictamenForm = {
        decision: decision,
        motivoRechazo: motivoRechazo,
        motivoDevolucion: motivoDevolucion,
        observaciones: observaciones
      };

      // Desplazamiento suave al formulario de dictamen
      this.$nextTick(() => {
        const el = document.getElementById("seccion-dictamen");
        if (el) {
          el.scrollIntoView({ behavior: "smooth" });
        }
      });
      this.mostrarToast(`Modo edición activado: ${rolUpper} (${this.editandoRevision.plantaNombre})`, "info");
    },

    async cancelarEdicionRevision() {
      this.editandoRevision = null;
      const rolActualNorm = String(this.rolActual || "").trim().toUpperCase();
      this.dictamenForm = {
        decision: (rolActualNorm === "SCR" && this.solicitud?.estado !== "POR APROBAR") ? "preaprobar" : "aprobar",
        motivoRechazo: "",
        motivoDevolucion: "",
        observaciones: ""
      };
      await this.cargarSolicitud();
      this.mostrarToast("Edición cancelada.", "info");
    },

    async emitirDictamen() {
      const esEdicion = Boolean(this.editandoRevision);
      const rolDictamen = this.editandoRevision ? this.editandoRevision.rol : this.rolActual;
      let targetPlantasIds = [];
      let idPlantaDictamen = null;

      if (this.editandoRevision) {
        idPlantaDictamen = this.editandoRevision.id_planta;
        targetPlantasIds = [Number(idPlantaDictamen)];
      } else if (this.rolActual === "SST" || this.rolActual === "GESCO") {
        if (!this.plantaSeleccionadaDictamen || this.plantaSeleccionadaDictamen === "todas") {
          targetPlantasIds = this.misPlantasDictaminables.map(p => Number(p.id));
          idPlantaDictamen = targetPlantasIds.length === 1 ? targetPlantasIds[0] : null;
        } else {
          idPlantaDictamen = Number(this.plantaSeleccionadaDictamen);
          targetPlantasIds = [idPlantaDictamen];
        }
      }

      if (!this.esScrOSuperior && (this.rolActual === "SST" || this.rolActual === "GESCO") && !this.tienePlantaAsignadaParaSolicitud) {
        this.mostrarToast("No puedes dictaminar: ninguna planta de esta solicitud coincide con tus zonas asignadas.", "error");
        return;
      }

      if (!this.puedeDictaminar) {
        this.mostrarToast("No tienes permisos para emitir dictamen en la etapa actual o para la planta seleccionada.", "error");
        return;
      }

      const decision = this.dictamenForm.decision;
      const rolDictamenNorm = String(rolDictamen || "").trim().toUpperCase();

      if ((rolDictamenNorm === "SST" || rolDictamenNorm === "GESCO") && (decision === "preaprobar" || decision === "devolver")) {
        this.mostrarToast(`El rol ${rolDictamenNorm} solo puede emitir dictamen de Aprobar o Rechazar.`, "error");
        return;
      }

      const motivo = this.dictamenForm.motivoRechazo.trim();
      const motivoDev = (this.dictamenForm.motivoDevolucion || "").trim();
      const obs = this.dictamenForm.observaciones.trim();

      if (decision === "rechazar" && !motivo) {
        this.mostrarToast("Debes ingresar el motivo del rechazo.", "error");
        return;
      }

      if (decision === "devolver" && !motivoDev) {
        this.mostrarToast("Debes ingresar el motivo de la devolución para corrección.", "error");
        return;
      }

      this.guardando = true;
      const nombreUsuario = (
        this.usuarioSesion?.nombre || 
        this.usuarioSesion?.nombre_completo || 
        (this.usuarioSesion?.nombres ? `${this.usuarioSesion.nombres} ${this.usuarioSesion.apellidos || ''}`.trim() : '')
      ) || `Revisor (${this.rolActual})`;

      try {
        let decisionBackend = "APROBADO";
        if (decision === "rechazar") decisionBackend = "RECHAZADO";
        else if (decision === "devolver") decisionBackend = "DEVUELTO";
        else if (decision === "preaprobar") decisionBackend = "PREAPROBADO";

        const token = (typeof getAuthToken === "function") ? getAuthToken() : (this.usuarioSesion?.token || null);
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const payloadDictamen = {
          id_planta: idPlantaDictamen,
          plantas_ids: targetPlantasIds,
          rol: rolDictamen,
          decision: decisionBackend,
          es_edicion: esEdicion,
          motivo_rechazo: decision === "rechazar" ? motivo : (decision === "devolver" ? motivoDev : null),
          motivo_devolucion: decision === "devolver" ? motivoDev : null,
          observacion: obs || null,
          id_usuario: this.usuarioSesion?.id || null,
          nombre_revisor: nombreUsuario,
          personas: (this.solicitud?.personas || []).map(p => ({
            id: p.id || p.id_persona,
            autorizado: Boolean(p.autorizado),
            motivo: p.motivo_rechazo || p.motivo || ""
          })),
          vehiculos: (this.solicitud?.vehiculos || []).map(v => ({
            id: v.id || v.id_vehiculo,
            autorizado: Boolean(v.autorizado),
            motivo: v.motivo_rechazo || v.motivo || ""
          }))
        };

        await this.persistirPersonasEnStorage();
        await this.persistirVehiculosEnStorage();

        // Enviar a API Backend (usando solicitudId numérico o código)
        const targetId = this.solicitud?.id || this.solicitudId;
        const res = await fetch(`${API.solicitudes}/${targetId}/dictamen`, {
          method: "POST",
          headers: headers,
          body: JSON.stringify(payloadDictamen)
        });

        if (res.ok) {
          const dataRes = await res.json();
          this.hayCambiosPersonas = false;
          this.solicitud.estado = dataRes.nuevo_estado;
          if (decision === "preaprobar" || decisionBackend === "PREAPROBADO") {
            this.solicitud.pre_aprobado = true;
          }
          this.revisionesHistorial = dataRes.revisiones || [];
          this.guardarRevisionesEnStorage();

          if (esEdicion) {
            this.editandoRevision = null;
            this.mostrarToast(`Revisión de ${rolDictamen} actualizada exitosamente (${dataRes.nuevo_estado}).`, "success");
            await this.cargarSolicitud();
          } else {
            const countPlantas = targetPlantasIds.length;
            const extraPlantaMsg = countPlantas > 1 ? ` para ${countPlantas} plantas en simultáneo` : '';
            const mensajeToast = decision === "preaprobar"
              ? `Solicitud PRE-APROBADA por SCR. Redirigiendo a Procesamiento...`
              : (decision === "devolver"
                  ? `Solicitud devuelta al solicitante. Redirigiendo a Procesamiento...`
                  : (decision === "rechazar"
                      ? `Solicitud rechazada${extraPlantaMsg}. Redirigiendo a Procesamiento...`
                      : `Dictamen registrado${extraPlantaMsg} exitosamente (${dataRes.nuevo_estado}). Redirigiendo a Procesamiento...`));
            this.mostrarToast(mensajeToast, "success");

            setTimeout(() => {
              if (typeof window.showPageLoader === "function") {
                window.showPageLoader();
              }
              window.location.href = "/procesamiento";
            }, 1200);
          }
        } else {
          const errData = await res.json().catch(() => ({}));
          const errMsg = errData.detail || errData.mensaje || `Error del servidor (${res.status})`;
          console.error("Error al registrar dictamen en backend:", errMsg);
          this.mostrarToast(`Error al guardar en base de datos: ${errMsg}`, "error");
        }

        this.guardarRevisionesEnStorage();

        // Limpiar formulario si no es edición
        if (!esEdicion) {
          this.dictamenForm.motivoRechazo = "";
          this.dictamenForm.motivoDevolucion = "";
          this.dictamenForm.observaciones = "";
        }

      } catch (err) {
        console.error("Error al emitir dictamen:", err);
        this.mostrarToast("Error al registrar dictamen: " + err.message, "error");
      } finally {
        this.guardando = false;
      }
    },

    abrirModalConfirmacionPreaprobada() {
      this.showModalConfirmacionPreaprobada = true;
    },

    cerrarModalConfirmacionPreaprobada() {
      this.showModalConfirmacionPreaprobada = false;
    },

    irAFormularioDictamen() {
      this.cerrarModalConfirmacionPreaprobada();
      const el = document.getElementById("seccion-dictamen");
      if (el) {
        el.scrollIntoView({ behavior: "smooth" });
      }
    },

    async confirmarAprobacionFinalPreaprobada() {
      this.guardando = true;
      try {
        const nombreUsuario = this.usuarioSesion?.nombre || (this.usuarioSesion?.nombres 
          ? `${this.usuarioSesion.nombres} ${this.usuarioSesion.apellidos || ''}`.trim() 
          : `Auditor SCR (${this.rolActual || 'SCR'})`);

        const token = (typeof getAuthToken === "function") ? getAuthToken() : (this.usuarioSesion?.token || null);

        const payload = {
          id_planta: null,
          rol: "SCR",
          decision: "APROBADO",
          observacion: "Aprobación definitiva confirmada por SCR tras superar revisiones de SST y GESCO.",
          id_usuario: this.usuarioSesion?.id || null,
          nombre_revisor: nombreUsuario,
          personas: (this.solicitud?.personas || []).map(p => ({
            id: p.id || p.id_persona,
            autorizado: Boolean(p.autorizado),
            motivo: p.motivo_rechazo || p.motivo || ""
          })),
          vehiculos: (this.solicitud?.vehiculos || []).map(v => ({
            id: v.id || v.id_vehiculo,
            autorizado: Boolean(v.autorizado),
            motivo: v.motivo_rechazo || v.motivo || ""
          }))
        };

        const targetId = this.solicitud?.id || this.solicitudId;
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${API.solicitudes}/${targetId}/dictamen`, {
          method: "POST",
          headers: headers,
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const dataRes = await res.json();
          this.solicitud.estado = dataRes.nuevo_estado || "APROBADO";
          this.revisionesHistorial = dataRes.revisiones || [];
          this.guardarRevisionesEnStorage();
          this.cerrarModalConfirmacionPreaprobada();
          this.mostrarToast("¡Solicitud Aprobada Definitivamente! Redirigiendo...", "success");

          // Redirigir a procesamiento
          setTimeout(() => {
            if (typeof window.showPageLoader === "function") {
              window.showPageLoader();
            }
            window.location.href = "/procesamiento";
          }, 1200);
        } else {
          const errData = await res.json().catch(() => ({}));
          const errMsg = errData.detail || errData.mensaje || `Error del servidor (${res.status})`;
          this.mostrarToast(`Error al confirmar aprobación: ${errMsg}`, "error");
        }
      } catch (err) {
        console.error("Error al confirmar aprobación:", err);
        this.mostrarToast("Error de conexión al aprobar: " + err.message, "error");
      } finally {
        this.guardando = false;
      }
    },

    async cambiarEstado(nuevoEstado, notificar = true) {
      this.solicitud.estado = nuevoEstado;

      // Actualizar en localStorage
      try {
        const locales = JSON.parse(localStorage.getItem("incarsa_solicitudes") || "[]");
        const idx = locales.findIndex(s => String(s.id) === String(this.solicitudId));
        if (idx > -1) {
          locales[idx].estado = nuevoEstado;
          localStorage.setItem("incarsa_solicitudes", JSON.stringify(locales));
        }
      } catch (e) {}
    },

    // -------------------------------------------------------------
    // Visor de documentos
    // -------------------------------------------------------------
    abrirDocumento(doc, itemPadre = "") {
      const nom = doc.nombre_archivo || doc.nom_documento || doc.nombre || "Documento";
      const tipo = doc.tipo_doc || "adjunto";
      const esPdf = nom.toLowerCase().endsWith(".pdf") || !nom.includes(".");
      const esImagen = !!nom.toLowerCase().match(/\.(jpg|jpeg|png|webp|gif)$/);

      // Generar URL válida apuntando al backend FastAPI
      let url = doc.url_acceso || doc.url || doc.url_documento || "";
      if (!url) {
        url = `${API.base}/uploads/${nom}`;
      } else if (!url.startsWith("http://") && !url.startsWith("https://")) {
        url = url.startsWith("/") ? `${API.base}${url}` : `${API.base}/${url}`;
      }

      // Nombre de tipo limpio sin incluir el nombre del archivo en la parte superior
      let tipoTitulo = "DOCUMENTO ADJUNTO";
      if (tipo && tipo.toLowerCase() !== "adjunto") {
        tipoTitulo = tipo.toUpperCase().replace(/_/g, ' ');
      } else if (doc.nom_documento && doc.nom_documento !== nom) {
        tipoTitulo = doc.nom_documento.toUpperCase().replace(/_/g, ' ');
      }

      this.docActual = {
        titulo: tipoTitulo,
        subtitulo: itemPadre ? `Perteneciente a: ${itemPadre}` : "",
        tipo: tipo,
        url: url,
        esPdf: !!esPdf,
        esImagen: !!esImagen,
        nombreArchivo: nom,
        vigencia: doc.vigencia || null,
        estadoVigencia: this.getEstadoVigenciaDoc(doc)
      };

      this.docModalOpen = true;
    },

    cerrarDocumento() {
      this.docModalOpen = false;
      this.docActual = { titulo: "", tipo: "", url: "", esPdf: false, esImagen: false };
    },

    // -------------------------------------------------------------
    // Helper de simulación de roles (para pair-programming y pruebas)
    // -------------------------------------------------------------
    cambiarRolSimulado(nuevoRol) {
      this.rolActual = nuevoRol;
      this.rolNombre = nuevoRol;
      this.mostrarToast(`Sesión cambiada a rol: ${nuevoRol}`, "info");
      if ((this.puedeVerAntecedentes || this.puedeVerInduccion) && this.solicitud?.personas?.length > 0) {
        this.cargarVigenciasPersonas();
      }
    },

    // Clases y colores de estado
    estadoEstilos(estado) {
      const e = (estado || "").toUpperCase();
      if (e === "ENVIADO") return "status-enviado";
      if (e.includes("DEVUELTO") || e.includes("CORRECCI")) return "status-devuelto";
      if (e.includes("REVISI")) return "status-revision";
      if (e === "POR APROBAR") return "status-aprobar";
      if (e === "APROBADO") return "status-aprobado";
      if (e === "RECHAZADO") return "status-rechazado";
      return "status-enviado";
    },

    // =============================================================
    // GESTIÓN Y AUDITORÍA DE ANTECEDENTES E INDUCCIONES (HISTORIAL Y RENOVACIÓN)
    // =============================================================

    async cargarVigenciasPersonas() {
      if (!this.solicitud || !Array.isArray(this.solicitud.personas)) return;
      
      const tareas = this.solicitud.personas.map(async (p) => {
        const idPersona = p.id_persona || p.id;
        const ident = String(p.identificacion || "").trim();

        // 1. CARGA DE ANTECEDENTES (SCR, Administrador, SuperAdmin)
        if (this.puedeVerAntecedentes) {
          let antecedenteCargado = false;
          // Ver si está en localStorage (guardado recientemente con fecha válida)
          const localKey = `incarsa_antecedente_${ident}`;
          const localSaved = JSON.parse(localStorage.getItem(localKey) || "null");
          if (localSaved && localSaved.fecha_consulta && localSaved.fecha_consulta !== "Pendiente" && localSaved.fecha_consulta !== "No registrada") {
            p.fecha_consulta = localSaved.fecha_consulta;
            p.ultima_revision = localSaved.ultima_revision;
            p.responsable = localSaved.responsable;
            p.anotaciones = localSaved.anotaciones;
            p.estadoVigencia = this.getEstadoVigencia(localSaved.fecha_consulta);
            antecedenteCargado = true;
          } else if (p.fecha_consulta && p.fecha_consulta !== "None" && p.fecha_consulta !== "null" && p.fecha_consulta !== "Pendiente" && p.fecha_consulta !== "No registrada") {
            p.estadoVigencia = this.getEstadoVigencia(p.fecha_consulta);
            antecedenteCargado = true;
          }

          if (!antecedenteCargado) {
            try {
              if (idPersona) {
                const res = await fetch(`${API.antecedentes}/persona/${idPersona}?actualizar_revision=false`);
                if (res.ok) {
                  const resData = await res.json().catch(() => ({}));
                  const data = resData.data || resData;
                  if (data && data.fecha_consulta && data.fecha_consulta !== "Pendiente" && data.fecha_consulta !== "No registrada") {
                    p.fecha_consulta = data.fecha_consulta;
                    p.ultima_revision = data.ultima_revision;
                    p.responsable = data.responsable;
                    p.anotaciones = data.anotaciones;
                    p.estadoVigencia = this.getEstadoVigencia(data.fecha_consulta);
                    antecedenteCargado = true;
                  }
                }
              }
            } catch (e) {}
          }

          if (!antecedenteCargado) {
            p.estadoVigencia = this.getEstadoVigencia(null);
          }
        }

        // 2. CARGA DE INDUCCIONES (GESCO, SCR, Administrador, SuperAdmin)
        if (this.puedeVerInduccion) {
          let induccionCargada = false;
          if (p.fecha_vigencia_induccion || p.fecha_induccion) {
            p.estadoVigenciaInduccion = this.getEstadoVigenciaInduccion(p.fecha_vigencia_induccion || (p.fecha_induccion ? this.obtenerFechaMasUnAnio(p.fecha_induccion) : null));
            induccionCargada = true;
          }

          if (!induccionCargada) {
            try {
              if (idPersona) {
                const resInd = await fetch(`${API.inducciones}/persona/${idPersona}?auto_renovar=false`);
                if (resInd.ok) {
                  const dataInd = await resInd.json().catch(() => ({}));
                  if (dataInd && (dataInd.fecha_vigencia || dataInd.fecha_induccion)) {
                    p.fecha_induccion = dataInd.fecha_induccion;
                    p.fecha_vigencia_induccion = dataInd.fecha_vigencia;
                    p.responsable_induccion = dataInd.responsable;
                    p.anotaciones_induccion = dataInd.anotaciones;
                    p.estadoVigenciaInduccion = this.getEstadoVigenciaInduccion(dataInd.fecha_vigencia || this.obtenerFechaMasUnAnio(dataInd.fecha_induccion));
                    induccionCargada = true;
                  }
                }
              }
            } catch (e) {}
          }

          if (!induccionCargada) {
            p.estadoVigenciaInduccion = this.getEstadoVigenciaInduccion(null);
          }
        }

        // 3. CARGA DE SEGURIDAD SOCIAL (SST, SCR, Administrador, SuperAdmin)
        if (this.puedeVerSeguridadSocial) {
          let ssCargado = false;
          const localKeySS = `incarsa_ss_${ident}`;
          const localSavedSS = JSON.parse(localStorage.getItem(localKeySS) || "null");
          if (localSavedSS && localSavedSS.fecha_vigencia && localSavedSS.fecha_vigencia !== "Pendiente" && localSavedSS.fecha_vigencia !== "No registrada") {
            p.fecha_vigencia_ss = localSavedSS.fecha_vigencia;
            p.ultima_revision_ss = localSavedSS.ultima_revision;
            p.responsable_ss = localSavedSS.responsable;
            p.anotaciones_ss = localSavedSS.anotaciones;
            p.estadoVigenciaSS = this.getEstadoVigenciaSS(localSavedSS.fecha_vigencia);
            ssCargado = true;
          } else if (p.fecha_vigencia_ss && p.fecha_vigencia_ss !== "None" && p.fecha_vigencia_ss !== "null" && p.fecha_vigencia_ss !== "Pendiente" && p.fecha_vigencia_ss !== "No registrada") {
            p.estadoVigenciaSS = this.getEstadoVigenciaSS(p.fecha_vigencia_ss);
            ssCargado = true;
          }

          if (!ssCargado) {
            try {
              if (idPersona) {
                const resSS = await fetch(`${API.seguridad_social}/persona/${idPersona}?actualizar_revision=false`);
                if (resSS.ok) {
                  const resDataSS = await resSS.json().catch(() => ({}));
                  const dataSS = resDataSS.data || resDataSS;
                  if (dataSS && (dataSS.fecha_vigencia || dataSS.fecha_consulta)) {
                    const fVig = dataSS.fecha_vigencia || dataSS.fecha_consulta;
                    p.fecha_vigencia_ss = fVig;
                    p.ultima_revision_ss = dataSS.ultima_revision;
                    p.responsable_ss = dataSS.responsable;
                    p.anotaciones_ss = dataSS.anotaciones;
                    p.estadoVigenciaSS = this.getEstadoVigenciaSS(fVig);
                    ssCargado = true;
                  }
                }
              }
            } catch (e) {}
          }

          if (!ssCargado) {
            p.estadoVigenciaSS = this.getEstadoVigenciaSS(null);
          }
        }
      });

      await Promise.all(tareas);
    },

    parsearFechaLocal(fechaStr) {
      if (!fechaStr || fechaStr === "None" || fechaStr === "null" || fechaStr === "Pendiente" || fechaStr === "No registrada") return null;
      if (fechaStr instanceof Date) return fechaStr;
      const str = String(fechaStr).trim();
      // Formato DD/MM/YYYY o DD-MM-YYYY
      if (/^\d{2}[\/\-]\d{2}[\/\-]\d{4}$/.test(str)) {
        const sep = str.includes('/') ? '/' : '-';
        const [d, m, y] = str.split(sep).map(Number);
        return new Date(y, m - 1, d, 12, 0, 0);
      }
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

    getEstadoVigencia(fechaConsultaStr) {
      if (!fechaConsultaStr) {
        return {
          estado: 'sin_revision',
          etiqueta: 'Sin revisión',
          textoDias: 'Sin revisión',
          icono: 'fa-solid fa-circle-question',
          badgeClass: 'bg-slate-500/20 text-slate-700 dark:text-slate-100 border-slate-400/40 vigencia-badge-neon is-sin-revision',
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
          badgeClass: 'bg-slate-500/20 text-slate-700 dark:text-slate-100 border-slate-400/40 vigencia-badge-neon is-sin-revision',
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
          badgeClass: 'bg-red-500/20 text-red-700 dark:text-red-200 border-red-400/40 vigencia-badge-neon is-vencido',
          dotClass: 'bg-red-500',
          dias: diffDias
        };
      } else if (diffDias === 0) {
        return {
          estado: 'por_vencer',
          etiqueta: 'Vence hoy',
          textoDias: 'Vence hoy',
          icono: 'fa-solid fa-triangle-exclamation',
          badgeClass: 'bg-amber-500/20 text-amber-700 dark:text-amber-200 border-amber-400/40 vigencia-badge-neon is-por-vencer',
          dotClass: 'bg-amber-500',
          dias: 0
        };
      } else if (diffDias <= 30) {
        return {
          estado: 'por_vencer',
          etiqueta: `Por vencer (${diffDias}d)`,
          textoDias: `${diffDias} ${diffDias === 1 ? 'día restante' : 'días restantes'}`,
          icono: 'fa-solid fa-triangle-exclamation',
          badgeClass: 'bg-amber-500/20 text-amber-700 dark:text-amber-200 border-amber-400/40 vigencia-badge-neon is-por-vencer',
          dotClass: 'bg-amber-500',
          dias: diffDias
        };
      } else {
        return {
          estado: 'vigente',
          etiqueta: `Vigente (${diffDias}d)`,
          textoDias: `${diffDias} días restantes`,
          icono: 'fa-solid fa-circle-check',
          badgeClass: 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-200 border-emerald-400/40 vigencia-badge-neon is-vigente',
          dotClass: 'bg-emerald-500',
          dias: diffDias
        };
      }
    },

    getEstadoVigenciaInduccion(fechaVigenciaStr) {
      if (!fechaVigenciaStr) {
        return {
          estado: 'sin_induccion',
          etiqueta: 'Sin inducción',
          textoDias: 'Sin curso de inducción registrado',
          icono: 'fa-solid fa-graduation-cap',
          badgeClass: 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-white/10 dark:text-slate-300 dark:border-white/10',
          dotClass: 'bg-slate-400',
          dias: null
        };
      }

      const hoy = new Date();
      hoy.setHours(0, 0, 0, 0);

      const fechaLimite = this.parsearFechaLocal(fechaVigenciaStr);
      if (!fechaLimite || isNaN(fechaLimite.getTime())) {
        return {
          estado: 'sin_induccion',
          etiqueta: 'Fecha inválida',
          textoDias: 'Fecha inválida',
          icono: 'fa-solid fa-circle-question',
          badgeClass: 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-white/10 dark:text-slate-300 dark:border-white/10',
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
          textoDias: `Inducción vencida hace ${diasVencidos} ${diasVencidos === 1 ? 'día' : 'días'}`,
          icono: 'fa-solid fa-circle-xmark',
          badgeClass: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800/60',
          dotClass: 'bg-red-500',
          dias: diffDias
        };
      } else if (diffDias === 0) {
        return {
          estado: 'por_vencer',
          etiqueta: 'Vence hoy',
          textoDias: 'La inducción vence hoy',
          icono: 'fa-solid fa-triangle-exclamation',
          badgeClass: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800/60',
          dotClass: 'bg-amber-500',
          dias: 0
        };
      } else if (diffDias <= 30) {
        return {
          estado: 'por_vencer',
          etiqueta: `Por vencer (${diffDias}d)`,
          textoDias: `${diffDias} ${diffDias === 1 ? 'día restante de vigencia' : 'días restantes de vigencia'}`,
          icono: 'fa-solid fa-triangle-exclamation',
          badgeClass: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800/60',
          dotClass: 'bg-amber-500',
          dias: diffDias
        };
      } else {
        return {
          estado: 'vigente',
          etiqueta: `Vigente (${diffDias}d)`,
          textoDias: `${diffDias} días restantes de vigencia`,
          icono: 'fa-solid fa-circle-check',
          badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800/60',
          dotClass: 'bg-emerald-500',
          dias: diffDias
        };
      }
    },

    getEstadoVigenciaSS(fechaVigenciaStr) {
      if (!fechaVigenciaStr || fechaVigenciaStr === "None" || fechaVigenciaStr === "null" || fechaVigenciaStr === "Pendiente" || fechaVigenciaStr === "No registrada" || fechaVigenciaStr === "Sin fecha" || fechaVigenciaStr === "Sin vigencia registrada") {
        return {
          estado: 'sin_revision',
          etiqueta: 'Sin revisión',
          textoDias: 'Sin dictamen SST registrado',
          icono: 'fa-solid fa-circle-question',
          badgeClass: 'vigencia-badge-neon is-sin-revision text-slate-400 border-slate-500/30 bg-slate-500/10',
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
          textoDias: 'Fecha inválida',
          icono: 'fa-solid fa-circle-question',
          badgeClass: 'vigencia-badge-neon is-sin-revision text-slate-400 border-slate-500/30 bg-slate-500/10',
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
          textoDias: `Planilla vencida hace ${diasVencidos} ${diasVencidos === 1 ? 'día' : 'días'}`,
          icono: 'fa-solid fa-circle-xmark',
          badgeClass: 'vigencia-badge-neon is-vencido text-red-400 border-red-500/40 bg-red-500/15',
          dotClass: 'bg-red-500',
          dias: diffDias
        };
      } else if (diffDias === 0) {
        return {
          estado: 'por_vencer',
          etiqueta: 'Vence hoy',
          textoDias: 'La planilla vence hoy',
          icono: 'fa-solid fa-triangle-exclamation',
          badgeClass: 'vigencia-badge-neon is-por-vencer text-amber-400 border-amber-500/40 bg-amber-500/15',
          dotClass: 'bg-amber-500',
          dias: 0
        };
      } else if (diffDias <= 5) {
        return {
          estado: 'por_vencer',
          etiqueta: `Por vencer (${diffDias}d)`,
          textoDias: `Planilla por vencer en ${diffDias} ${diffDias === 1 ? 'día' : 'días'}`,
          icono: 'fa-solid fa-triangle-exclamation',
          badgeClass: 'vigencia-badge-neon is-por-vencer text-amber-400 border-amber-500/40 bg-amber-500/15',
          dotClass: 'bg-amber-500',
          dias: diffDias
        };
      } else {
        return {
          estado: 'vigente',
          etiqueta: `Vigente (${diffDias}d)`,
          textoDias: `Planilla vigente por ${diffDias} días`,
          icono: 'fa-solid fa-circle-check',
          badgeClass: 'vigencia-badge-neon is-vigente text-emerald-400 border-emerald-500/40 bg-emerald-500/15',
          dotClass: 'bg-emerald-500',
          dias: diffDias
        };
      }
    },

    esDocPlanilla(doc) {
      if (!doc) return false;
      const t = String(doc.tipo_doc || doc.tipo || doc.titulo || '').toLowerCase();
      return t.includes('planilla');
    },

    obtenerPlanillaPersona(persona) {
      if (!persona || !persona.documentos) return null;
      return persona.documentos.find(d => this.esDocPlanilla(d)) || null;
    },

    getEstadoVigenciaDoc(doc) {
      if (!doc) return null;
      const fechaVigenciaStr = doc.vigencia;
      if (!fechaVigenciaStr) {
        return {
          estado: 'sin_vigencia',
          etiqueta: 'Sin vigencia',
          textoDias: 'Sin fecha de vigencia registrada',
          icono: 'fa-solid fa-clock-rotate-left',
          badgeClass: 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-white/10 dark:text-slate-300 dark:border-white/10',
          dotClass: 'bg-slate-400',
          dias: null
        };
      }

      const hoy = new Date();
      hoy.setHours(0, 0, 0, 0);

      const fechaLimite = this.parsearFechaLocal(fechaVigenciaStr);
      if (!fechaLimite || isNaN(fechaLimite.getTime())) {
        return {
          estado: 'sin_vigencia',
          etiqueta: 'Fecha inválida',
          textoDias: 'Fecha inválida',
          icono: 'fa-solid fa-circle-question',
          badgeClass: 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-white/10 dark:text-slate-300 dark:border-white/10',
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
          textoDias: `Planilla vencida hace ${diasVencidos} ${diasVencidos === 1 ? 'día' : 'días'}`,
          icono: 'fa-solid fa-circle-xmark',
          badgeClass: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800/60',
          dotClass: 'bg-red-500',
          dias: diffDias
        };
      } else if (diffDias === 0) {
        return {
          estado: 'por_vencer',
          etiqueta: 'Vence hoy',
          textoDias: 'La planilla vence hoy',
          icono: 'fa-solid fa-triangle-exclamation',
          badgeClass: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800/60',
          dotClass: 'bg-amber-500',
          dias: 0
        };
      } else if (diffDias <= 15) {
        return {
          estado: 'por_vencer',
          etiqueta: `Por vencer (${diffDias}d)`,
          textoDias: `Planilla por vencer en ${diffDias} ${diffDias === 1 ? 'día' : 'días'}`,
          icono: 'fa-solid fa-triangle-exclamation',
          badgeClass: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800/60',
          dotClass: 'bg-amber-500',
          dias: diffDias
        };
      } else {
        return {
          estado: 'vigente',
          etiqueta: `Vigente (${diffDias}d)`,
          textoDias: `Planilla vigente por ${diffDias} días`,
          icono: 'fa-solid fa-circle-check',
          badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800/60',
          dotClass: 'bg-emerald-500',
          dias: diffDias
        };
      }
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

    formatearFecha(fechaStr, incluirHora = false) {
      if (!fechaStr || fechaStr === "Pendiente" || fechaStr === "No registrada") return fechaStr || "Pendiente";
      try {
        const fecha = this.parsearFechaLocal(fechaStr);
        if (!fecha || isNaN(fecha.getTime())) return fechaStr;
        
        const esSoloFecha = /^\d{4}-\d{2}-\d{2}$/.test(String(fechaStr).trim());
        const opciones = { year: "numeric", month: "short", day: "numeric" };
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
      if (!fechaStr) return "—";
      try {
        const str = String(fechaStr).split("T")[0];
        const [y, m, d] = str.split("-");
        if (y && m && d) return `${d}/${m}/${y}`;
        return str;
      } catch {
        return fechaStr;
      }
    },

    formatearFechaLegible(fechaStr) {
      if (!fechaStr || fechaStr === "—" || fechaStr === "-" || fechaStr === "No registrada" || fechaStr === "Sin fecha" || fechaStr === "Sin vigencia registrada") {
        return fechaStr || "—";
      }
      try {
        const str = String(fechaStr).trim().split("T")[0].split(" ")[0];
        const fPartes = str.split("-");
        if (fPartes.length === 3) {
          const anio = fPartes[0];
          const mesIdx = parseInt(fPartes[1], 10) - 1;
          const dia = parseInt(fPartes[2], 10);
          const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
          const mesNombre = meses[mesIdx] || fPartes[1];
          return `${dia} ${mesNombre} ${anio}`;
        }
        return this.formatearSoloFecha(fechaStr);
      } catch {
        return fechaStr;
      }
    },

    formatearFechaVigencia(fechaStr) {
      if (!fechaStr || fechaStr === "None" || fechaStr === "null" || fechaStr === "Pendiente" || fechaStr === "No registrada" || fechaStr === "—") {
        return "Pendiente de consulta";
      }
      try {
        const fecha = this.parsearFechaLocal(fechaStr);
        if (!fecha || isNaN(fecha.getTime())) return fechaStr;
        const dia = fecha.getDate();
        const meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
        const mes = meses[fecha.getMonth()];
        const anio = fecha.getFullYear();
        return `${dia} de ${mes} de ${anio}`;
      } catch {
        return fechaStr;
      }
    },

    copiarCodigo(codigo) {
      if (!codigo) return;
      navigator.clipboard.writeText(codigo).then(() => {
        this.copiadoFeedback = codigo;
        setTimeout(() => { this.copiadoFeedback = null; }, 2000);
      }).catch(() => {});
    },

    goToHistorialPage(num) {
      if (num >= 1 && num <= this.totalPaginasHistorial) {
        this.historialPage = num;
      }
    },

    async abrirHistorialModal(persona) {
      if (!this.puedeVerAntecedentes) {
        this.mostrarToast("No tienes permisos para consultar antecedentes.", "warning");
        return;
      }
      this.personaSeleccionadaAntecedente = persona;
      const idPersona = persona.id_persona || persona.id;
      const identificacion = String(persona.identificacion || "").trim();
      const tipoDoc = persona.tipo_doc || "CC";
      const cargo = persona.cargo || "Operario";
      const nombre = persona.nombre || "Persona";

      this.cargandoHistorial = true;
      this.copiadoFeedback = null;
      this.limpiarFiltrosHistorial();
      this.showHistorialModal = true;

      const contratistaSolicitud = this.solicitud?.nombre_emContratista || this.solicitud?.contratista || this.solicitud?.empresa_contratista || this.solicitud?.nombre_contratista || persona.contratista || "Sin contratista asignado";
      const empresaSolicitud = this.solicitud?.nombre_empresa || this.solicitud?.empresa_solicitante || "INCARSA S.A.S.";

      // 1. Estado inicial conocido (usar la empresa contratista, no la solicitante)
      this.detalleHistorial = {
        id: persona.antecedente_id || null,
        id_persona: idPersona,
        persona_nombre: nombre,
        persona_apellido: "",
        persona_tipo_doc: tipoDoc,
        persona_identificacion: identificacion,
        persona_cargo: cargo,
        responsable: persona.ultimo_usuario_solicitud || persona.responsable || this.solicitud?.diligenciador || "Sin asignar",
        ultimo_usuario_solicitud: persona.ultimo_usuario_solicitud || this.solicitud?.diligenciador || persona.responsable || null,
        anotaciones: persona.anotaciones || "",
        id_empresa: null,
        ultima_empresa_contratista: contratistaSolicitud,
        ultima_empresa_solicitante: contratistaSolicitud,
        ultima_revision: persona.ultima_revision || null,
        fecha_consulta: persona.fecha_consulta || null,
        total_solicitudes: 1,
        historial: [
          {
            id: 1,
            codigo_radicado: this.solicitud?.codigo || "SOL-ACTUAL",
            nombre_empresa: empresaSolicitud,
            nombre_contratista: contratistaSolicitud,
            usuario_registro: this.solicitud?.diligenciador || null,
            diligenciador: this.solicitud?.diligenciador || null,
            fecha_inicio: this.solicitud?.fecha_inicio || this.solicitud?.fecha_registro,
            fecha_fin: this.solicitud?.fecha_fin || this.solicitud?.fecha_estimada,
            fecha_solicitud: this.solicitud?.fecha_registro || new Date().toISOString()
          }
        ]
      };

      // 2. Consultar antecedentes desde API / backend
      try {
        let url = `${API.antecedentes}/persona/${idPersona}?actualizar_revision=false`;
        let res = await fetch(url);
        let data = null;

        if (res.ok) {
          const resData = await res.json().catch(() => ({}));
          data = resData.data || resData;
        } else if (identificacion) {
          try {
            const resAll = await fetch(`${API.antecedentes}/getAll`);
            if (resAll.ok) {
              const resAllData = await resAll.json();
              const lista = resAllData.data || resAllData.datos || (Array.isArray(resAllData) ? resAllData : []);
              const encontrado = lista.find(a => String(a.persona_identificacion || a.identificacion || "").trim() === identificacion);
              if (encontrado && (encontrado.id_persona || encontrado.id)) {
                const resIndiv = await fetch(`${API.antecedentes}/persona/${encontrado.id_persona || encontrado.id}?actualizar_revision=false`);
                if (resIndiv.ok) {
                  const resIndivData = await resIndiv.json();
                  data = resIndivData.data || resIndivData;
                }
              }
            }
          } catch (e) {}
        }

        // 3. Revisar cache de localStorage
        const localKey = `incarsa_antecedente_${identificacion}`;
        const localSaved = JSON.parse(localStorage.getItem(localKey) || "null");

        if (data && typeof data === 'object') {
          this.detalleHistorial.id = data.id || this.detalleHistorial.id;
          this.detalleHistorial.id_persona = data.id_persona || idPersona;
          if (data.persona_nombre) this.detalleHistorial.persona_nombre = data.persona_nombre;
          if (data.persona_apellido) this.detalleHistorial.persona_apellido = data.persona_apellido;
          if (data.persona_tipo_doc) this.detalleHistorial.persona_tipo_doc = data.persona_tipo_doc;
          if (data.persona_identificacion) this.detalleHistorial.persona_identificacion = String(data.persona_identificacion);
          if (data.persona_cargo) this.detalleHistorial.persona_cargo = data.persona_cargo;
          
          const responsableBackend = (Array.isArray(data.historial) && data.historial.length > 0 ? (data.historial[0].usuario_registro || data.historial[0].diligenciador) : null) || data.ultimo_usuario_solicitud || data.responsable;
          if (responsableBackend) {
            this.detalleHistorial.responsable = responsableBackend;
            this.detalleHistorial.ultimo_usuario_solicitud = responsableBackend;
          }
          if (data.anotaciones) this.detalleHistorial.anotaciones = data.anotaciones;
          const contratistaBackend = data.ultima_empresa_contratista || data.nombre_contratista || (Array.isArray(data.historial) && data.historial.length > 0 ? data.historial[0].nombre_contratista : null);
          const contratistaFinal = contratistaBackend || contratistaSolicitud;
          this.detalleHistorial.ultima_empresa_contratista = contratistaFinal;
          this.detalleHistorial.ultima_empresa_solicitante = contratistaFinal;
          if (data.ultima_revision) this.detalleHistorial.ultima_revision = data.ultima_revision;
          
          this.detalleHistorial.fecha_consulta = (data.fecha_consulta && data.fecha_consulta !== "Pendiente" && data.fecha_consulta !== "No registrada") ? data.fecha_consulta : null;
          if (Array.isArray(data.historial) && data.historial.length > 0) {
            this.detalleHistorial.historial = data.historial;
            this.detalleHistorial.total_solicitudes = data.historial.length;
          }
        } else if (localSaved && localSaved.fecha_consulta && localSaved.fecha_consulta !== "Pendiente" && localSaved.fecha_consulta !== "No registrada") {
          Object.assign(this.detalleHistorial, localSaved);
        }

        persona.estadoVigencia = this.getEstadoVigencia(this.detalleHistorial.fecha_consulta);
        persona.fecha_consulta = this.detalleHistorial.fecha_consulta;
        persona.ultima_revision = this.detalleHistorial.ultima_revision;

      } catch (err) {
        console.warn("Aviso al consultar antecedentes en revisión:", err.message);
      } finally {
        this.cargandoHistorial = false;
      }
    },

    cerrarHistorialModal() {
      this.showHistorialModal = false;
    },

    abrirFormularioAntecedentes(item) {
      if (!this.puedeVerAntecedentes) {
        this.mostrarToast("No tienes permisos para modificar antecedentes.", "warning");
        return;
      }
      this.showHistorialModal = false;
      this.mensajeExitoAntecedente = "";
      this.mensajeErrorAntecedente = "";

      const ahora = new Date();
      const hoyLocal = this.obtenerFechaHoraLocal(ahora);
      const masUnAnio = this.obtenerFechaMasUnAnio(ahora);

      const sesionNombre = this.usuarioSesion?.nombre || this.usuarioSesion?.nombres || "Administrador Sistema";
      const contratistaActual = item.ultima_empresa_contratista || item.nombre_contratista || item.ultima_empresa_solicitante || this.solicitud?.nombre_emContratista || this.solicitud?.contratista || this.solicitud?.empresa_contratista || "Sin contratista asignado";

      this.formAntecedente = {
        id: item.id || null,
        id_persona: item.id_persona,
        persona_nombre: item.persona_nombre || "",
        persona_apellido: item.persona_apellido || "",
        persona_tipo_doc: item.persona_tipo_doc || "CC",
        persona_identificacion: item.persona_identificacion || "",
        persona_cargo: item.persona_cargo || "General",
        responsable: item.responsable && item.responsable !== "Sin asignar" ? item.responsable : sesionNombre,
        anotaciones: item.anotaciones || "",
        id_empresa: item.id_empresa || null,
        ultima_empresa_contratista: contratistaActual,
        ultima_empresa_solicitante: contratistaActual,
        ultima_revision: hoyLocal,
        fecha_consulta: masUnAnio,
        historial: Array.isArray(item.historial) ? item.historial : [],
        total_solicitudes: item.total_solicitudes || 1
      };

      this.showFormModal = true;
    },

    cerrarFormularioAntecedentes() {
      this.showFormModal = false;
      this.mensajeExitoAntecedente = "";
      this.mensajeErrorAntecedente = "";
      if (this.personaSeleccionadaAntecedente) {
        this.showHistorialModal = true;
      }
    },

    async guardarAntecedente() {
      if (!this.formAntecedente.id_persona) return;

      this.guardandoAntecedente = true;
      this.mensajeExitoAntecedente = "";
      this.mensajeErrorAntecedente = "";

      const fechaSoloDate = this.formAntecedente.fecha_consulta ? this.formAntecedente.fecha_consulta.split("T")[0] : null;

      const payload = {
        responsable: this.formAntecedente.responsable ? this.formAntecedente.responsable.trim() : "Administrador Sistema",
        anotaciones: this.formAntecedente.anotaciones ? this.formAntecedente.anotaciones.trim() : null,
        ultima_revision: this.formAntecedente.ultima_revision,
        fecha_consulta: fechaSoloDate
      };

      try {
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
            console.warn("Aviso backend al guardar antecedente:", errorMsg);
          }
        } catch (e) {
          console.warn("Fallo al actualizar backend, persistiendo local:", e);
        }

        // Persistir localmente en cache
        const ident = String(this.formAntecedente.persona_identificacion).trim();
        const localKey = `incarsa_antecedente_${ident}`;
        localStorage.setItem(localKey, JSON.stringify({
          ...this.formAntecedente,
          responsable: payload.responsable,
          anotaciones: payload.anotaciones,
          ultima_revision: payload.ultima_revision,
          fecha_consulta: payload.fecha_consulta
        }));

        // Sincronizar en detalleHistorial
        this.detalleHistorial.responsable = payload.responsable;
        this.detalleHistorial.anotaciones = payload.anotaciones || "";
        this.detalleHistorial.ultima_revision = payload.ultima_revision;
        this.detalleHistorial.fecha_consulta = payload.fecha_consulta;

        // Actualizar la persona en la vista de solicitud
        if (this.personaSeleccionadaAntecedente) {
          this.personaSeleccionadaAntecedente.responsable = payload.responsable;
          this.personaSeleccionadaAntecedente.anotaciones = payload.anotaciones || "";
          this.personaSeleccionadaAntecedente.ultima_revision = payload.ultima_revision;
          this.personaSeleccionadaAntecedente.fecha_consulta = payload.fecha_consulta;
          this.personaSeleccionadaAntecedente.estadoVigencia = this.getEstadoVigencia(payload.fecha_consulta);
        }

        this.mensajeExitoAntecedente = "¡Vigencia renovada exitosamente a +1 año!";
        this.mostrarToast("Vigencia de antecedentes actualizada (+1 año)", "success");

        setTimeout(() => {
          this.showFormModal = false;
          this.showHistorialModal = true;
        }, 1100);

      } catch (err) {
        console.error("Error al guardar antecedentes:", err);
        this.mensajeErrorAntecedente = err.message || "Error al actualizar la vigencia.";
      } finally {
        this.guardandoAntecedente = false;
      }
    },

    // =============================================================
    // GESTIÓN Y AUDITORÍA DE INDUCCIONES (GESCO)
    // =============================================================

    async abrirInduccionModal(persona) {
      if (!this.puedeVerInduccion) {
        this.mostrarToast("No tienes permisos para auditar inducciones.", "warning");
        return;
      }
      this.personaSeleccionadaInduccion = persona;
      this.cargandoInduccion = true;
      this.showInduccionModal = true;
      this.mensajeExitoInduccion = "";
      this.mensajeErrorInduccion = "";

      const idPersona = persona.id_persona || persona.id;
      const contratistaActual = this.solicitud?.nombre_emContratista || this.solicitud?.contratista || this.solicitud?.empresa_contratista || "Sin contratista asignado";

      this.detalleInduccion = {
        id: null,
        id_persona: idPersona,
        persona_nombre: persona.nombre || "Contratista",
        persona_apellido: persona.apellido || "",
        persona_identificacion: persona.identificacion || "—",
        persona_tipo_doc: persona.tipo_doc || "CC",
        persona_cargo: persona.cargo || "Operario",
        responsable: persona.responsable_induccion || "Auditor GESCO",
        anotaciones: persona.anotaciones_induccion || "",
        fecha_induccion: persona.fecha_induccion || null,
        fecha_vigencia: persona.fecha_vigencia_induccion || (persona.fecha_induccion ? this.obtenerFechaMasUnAnio(persona.fecha_induccion) : null),
        ultima_empresa_contratista: contratistaActual,
        ultima_revision: null
      };

      try {
        if (idPersona) {
          const res = await fetch(`${API.inducciones}/persona/${idPersona}?auto_renovar=false`);
          if (res.ok) {
            const data = await res.json();
            if (data) {
              this.detalleInduccion.id = data.id;
              this.detalleInduccion.responsable = data.responsable || this.detalleInduccion.responsable;
              this.detalleInduccion.anotaciones = data.anotaciones || "";
              this.detalleInduccion.fecha_induccion = data.fecha_induccion || this.detalleInduccion.fecha_induccion;
              this.detalleInduccion.fecha_vigencia = data.fecha_vigencia || (data.fecha_induccion ? this.obtenerFechaMasUnAnio(data.fecha_induccion) : this.detalleInduccion.fecha_vigencia);
              this.detalleInduccion.ultima_revision = data.ultima_revision;
              if (data.nombre_empresa) {
                this.detalleInduccion.ultima_empresa_contratista = data.nombre_empresa;
              }
            }
          }
        }
      } catch (err) {
        console.warn("Aviso al consultar inducción:", err);
      } finally {
        this.cargandoInduccion = false;
        persona.fecha_induccion = this.detalleInduccion.fecha_induccion;
        persona.fecha_vigencia_induccion = this.detalleInduccion.fecha_vigencia;
        persona.responsable_induccion = this.detalleInduccion.responsable;
        persona.anotaciones_induccion = this.detalleInduccion.anotaciones;
        persona.estadoVigenciaInduccion = this.getEstadoVigenciaInduccion(this.detalleInduccion.fecha_vigencia);
      }
    },

    cerrarInduccionModal() {
      this.showInduccionModal = false;
    },

    abrirFormularioInduccion(item) {
      if (!this.puedeVerInduccion) {
        this.mostrarToast("No tienes permisos para modificar inducciones.", "warning");
        return;
      }
      this.showInduccionModal = false;
      this.mensajeExitoInduccion = "";
      this.mensajeErrorInduccion = "";

      const ahora = new Date();
      const hoyLocal = this.obtenerFechaHoraLocal(ahora).split(" ")[0];
      
      let fechaInd = hoyLocal;
      if (item.fecha_induccion && item.fecha_induccion !== "None" && item.fecha_induccion !== "null" && item.fecha_induccion !== "—") {
        const limpia = String(item.fecha_induccion).trim().split("T")[0].split(" ")[0];
        if (/^\d{4}-\d{2}-\d{2}$/.test(limpia)) {
          fechaInd = limpia;
        }
      }
      const fechaVig = item.fecha_vigencia && item.fecha_vigencia !== "None" && item.fecha_vigencia !== "null" && item.fecha_vigencia !== "—"
        ? String(item.fecha_vigencia).trim().split("T")[0].split(" ")[0]
        : this.obtenerFechaMasUnAnio(fechaInd);

      const sesionNombre = (this.userDisplayName && this.userDisplayName !== "Usuario Activo")
        ? this.userDisplayName
        : (this.usuarioSesion?.nombre || this.usuarioSesion?.nombres || "Auditor GESCO");

      this.formInduccion = {
        id_persona: item.id_persona,
        persona_nombre: item.persona_nombre || "",
        persona_apellido: item.persona_apellido || "",
        persona_tipo_doc: item.persona_tipo_doc || "CC",
        persona_identificacion: item.persona_identificacion || "",
        persona_cargo: item.persona_cargo || "General",
        responsable: sesionNombre,
        anotaciones: item.anotaciones || "",
        fecha_induccion: fechaInd,
        fecha_vigencia: fechaVig,
        ultima_empresa_contratista: item.ultima_empresa_contratista || "Sin contratista asignado"
      };

      this.showFormInduccionModal = true;

      this.$nextTick(() => {
        if (this.$refs.fechaInduccionRevisionInput) {
          if (this.$refs.fechaInduccionRevisionInput._flatpickr) {
            this.$refs.fechaInduccionRevisionInput._flatpickr.setDate(this.formInduccion.fecha_induccion, true);
          } else {
            this.initFlatpickrFechaInduccionRevision(this.$refs.fechaInduccionRevisionInput);
          }
        }
      });
    },

    initFlatpickrFechaInduccionRevision(el) {
      if (typeof flatpickr === "undefined" || !el) return;
      if (el._flatpickr) el._flatpickr.destroy();
      const self = this;
      flatpickr(el, {
        locale: (typeof flatpickr !== "undefined" && flatpickr.l10ns && flatpickr.l10ns.es) ? flatpickr.l10ns.es : "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d M Y",
        altInputClass: "text-sm font-bold text-[var(--paper-ink)] dark:text-white bg-transparent border-0 p-0 focus:ring-0 cursor-pointer w-full truncate",
        defaultDate: self.formInduccion.fecha_induccion || "today",
        onChange(selectedDates, dateStr) {
          if (dateStr) {
            self.formInduccion.fecha_induccion = dateStr;
            self.formInduccion.fecha_vigencia = self.obtenerFechaMasUnAnio(dateStr);
          }
        }
      });
    },

    cerrarFormularioInduccion() {
      this.showFormInduccionModal = false;
      this.mensajeExitoInduccion = "";
      this.mensajeErrorInduccion = "";
      if (this.personaSeleccionadaInduccion) {
        this.showInduccionModal = true;
      }
    },

    async guardarInduccion() {
      if (!this.formInduccion.id_persona) return;

      this.guardandoInduccion = true;
      this.mensajeExitoInduccion = "";
      this.mensajeErrorInduccion = "";

      const ahora = new Date();
      const hoyLocal = this.obtenerFechaHoraLocal(ahora).split(" ")[0];
      const fechaInd = this.formInduccion.fecha_induccion || hoyLocal;
      const fechaVig = this.obtenerFechaMasUnAnio(fechaInd);
      const sesionNombre = (this.userDisplayName && this.userDisplayName !== "Usuario Activo")
        ? this.userDisplayName
        : (this.usuarioSesion?.nombre || this.usuarioSesion?.nombres || "Auditor GESCO");

      const payload = {
        responsable: this.formInduccion.responsable ? this.formInduccion.responsable.trim() : sesionNombre,
        anotaciones: this.formInduccion.anotaciones ? this.formInduccion.anotaciones.trim() : null,
        fecha_induccion: fechaInd,
        fecha_vigencia: fechaVig
      };

      try {
        const res = await fetch(`${API.inducciones}/persona/${this.formInduccion.id_persona}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || err.mensaje || "Error al actualizar inducción");
        }

        this.mensajeExitoInduccion = "¡Vigencia de inducción renovada exitosamente (+1 año)!";
        this.mostrarToast("Inducción renovada con vigencia de 1 año", "success");

        // Refrescar en memoria de la persona
        if (this.personaSeleccionadaInduccion) {
          this.personaSeleccionadaInduccion.fecha_induccion = fechaInd;
          this.personaSeleccionadaInduccion.fecha_vigencia_induccion = fechaVig;
          this.personaSeleccionadaInduccion.responsable_induccion = payload.responsable;
          this.personaSeleccionadaInduccion.anotaciones_induccion = payload.anotaciones;
          this.personaSeleccionadaInduccion.estadoVigenciaInduccion = this.getEstadoVigenciaInduccion(fechaVig);
        }

        // Actualizar detalleInduccion
        if (this.detalleInduccion) {
          this.detalleInduccion.fecha_induccion = fechaInd;
          this.detalleInduccion.fecha_vigencia = fechaVig;
          this.detalleInduccion.responsable = payload.responsable;
          this.detalleInduccion.anotaciones = payload.anotaciones;
        }

        setTimeout(() => {
          this.cerrarFormularioInduccion();
        }, 1200);

      } catch (e) {
        this.mensajeErrorInduccion = e.message || "No fue posible guardar los cambios de inducción.";
      } finally {
        this.guardandoInduccion = false;
      }
    },

    // =============================================================
    // GESTIÓN Y AUDITORÍA DE SEGURIDAD SOCIAL (SST)
    // =============================================================

    async abrirSeguridadSocialModal(persona) {
      if (!this.puedeVerSeguridadSocial) {
        this.mostrarToast("No tienes permisos para dictaminar seguridad social.", "warning");
        return;
      }
      this.personaSeleccionadaSS = persona;
      const idPersona = persona.id_persona || persona.id;
      const identificacion = String(persona.identificacion || "").trim();
      const tipoDoc = persona.tipo_doc || "CC";
      const cargo = persona.cargo || "Operario";
      const nombre = persona.nombre || "Persona";
      const apellido = persona.apellido || "";

      this.cargandoSeguridadSocial = true;
      this.mensajeExitoSS = "";
      this.mensajeErrorSS = "";
      this.limpiarFiltrosHistorial();
      this.showSeguridadSocialModal = true;

      const contratistaSolicitud = this.solicitud?.nombre_emContratista || this.solicitud?.contratista || this.solicitud?.empresa_contratista || this.solicitud?.nombre_contratista || persona.contratista || "Sin contratista asignado";
      const empresaSolicitud = this.solicitud?.nombre_empresa || this.solicitud?.empresa_solicitante || "INCARSA S.A.S.";

      let usuarioSST = "";
      try {
        const sesion = (typeof getAuthSession === 'function') 
          ? getAuthSession() 
          : JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || '{}');
        const nombres = sesion?.nombres || sesion?.nombre || "";
        const apellidos = sesion?.apellidos || sesion?.apellido || "";
        usuarioSST = `${nombres} ${apellidos}`.trim() || sesion?.usuario || "";
      } catch (e) {}

      const sesionNombre = usuarioSST || (this.userDisplayName && this.userDisplayName !== "Usuario Activo" ? this.userDisplayName : "Evaluador SST");

      // 1. Estado inicial reactivo unificado
      this.formSeguridadSocial = {
        id: null,
        id_persona: idPersona,
        persona_nombre: nombre,
        persona_apellido: apellido,
        persona_tipo_doc: tipoDoc,
        persona_identificacion: identificacion,
        persona_cargo: cargo,
        responsable: persona.responsable_ss || sesionNombre,
        anotaciones: persona.anotaciones_ss || "",
        ultima_empresa_contratista: contratistaSolicitud,
        ultima_revision: persona.ultima_revision_ss || null,
        fecha_vigencia: persona.fecha_vigencia_ss || null,
        historial: [
          {
            id: 1,
            codigo_radicado: this.solicitud?.codigo || "SOL-ACTUAL",
            nombre_empresa: empresaSolicitud,
            nombre_contratista: contratistaSolicitud,
            usuario_registro: this.solicitud?.diligenciador || null,
            diligenciador: this.solicitud?.diligenciador || null,
            fecha_inicio: this.solicitud?.fecha_inicio || this.solicitud?.fecha_registro,
            fecha_fin: this.solicitud?.fecha_fin || this.solicitud?.fecha_estimada,
            fecha_solicitud: this.solicitud?.fecha_registro || new Date().toISOString()
          }
        ]
      };
      this.detalleSeguridadSocial = this.formSeguridadSocial;
      this.formSeguridadSocialRevision = this.formSeguridadSocial;

      // 2. Consultar backend
      try {
        if (idPersona) {
          const res = await fetch(`${API.seguridad_social}/persona/${idPersona}?actualizar_revision=false`);
          if (res.ok) {
            const resData = await res.json().catch(() => ({}));
            const data = resData.data || resData;
            if (data && typeof data === 'object') {
              this.formSeguridadSocial.id = data.id || null;
              if (data.persona_nombre) this.formSeguridadSocial.persona_nombre = data.persona_nombre;
              if (data.persona_apellido) this.formSeguridadSocial.persona_apellido = data.persona_apellido;
              if (data.persona_tipo_doc) this.formSeguridadSocial.persona_tipo_doc = data.persona_tipo_doc;
              if (data.persona_identificacion) this.formSeguridadSocial.persona_identificacion = String(data.persona_identificacion);
              if (data.persona_cargo) this.formSeguridadSocial.persona_cargo = data.persona_cargo;
              if (data.responsable && data.responsable !== "Sin asignar") {
                this.formSeguridadSocial.responsable = data.responsable;
              } else {
                this.formSeguridadSocial.responsable = sesionNombre;
              }
              if (data.ultima_empresa_contratista) {
                this.formSeguridadSocial.ultima_empresa_contratista = data.ultima_empresa_contratista;
              }
              if (data.ultima_revision) {
                this.formSeguridadSocial.ultima_revision = data.ultima_revision;
              }
              const fVigBackend = data.fecha_vigencia || data.fecha_consulta;
              if (fVigBackend && fVigBackend !== "Pendiente" && fVigBackend !== "No registrada") {
                this.formSeguridadSocial.fecha_vigencia = fVigBackend;
              }
              if (data.anotaciones) {
                this.formSeguridadSocial.anotaciones = data.anotaciones;
              }
              if (Array.isArray(data.historial) && data.historial.length > 0) {
                this.formSeguridadSocial.historial = data.historial;
              }
            }
          }
        }

        // Revisar cache localStorage
        const localKeySS = `incarsa_ss_${identificacion}`;
        const localSavedSS = JSON.parse(localStorage.getItem(localKeySS) || "null");
        if (localSavedSS && localSavedSS.fecha_vigencia) {
          this.formSeguridadSocial.fecha_vigencia = localSavedSS.fecha_vigencia;
          this.formSeguridadSocial.responsable = localSavedSS.responsable || this.formSeguridadSocial.responsable;
          this.formSeguridadSocial.anotaciones = localSavedSS.anotaciones || this.formSeguridadSocial.anotaciones;
        }

        persona.fecha_vigencia_ss = this.formSeguridadSocial.fecha_vigencia;
        persona.estadoVigenciaSS = this.getEstadoVigenciaSS(this.formSeguridadSocial.fecha_vigencia);

        // Inicializar o sincronizar Flatpickr
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

      } catch (e) {
        console.warn("Aviso al consultar seguridad social en revisión:", e);
      } finally {
        this.cargandoSeguridadSocial = false;
      }
    },

    cerrarSeguridadSocialModal() {
      this.showSeguridadSocialModal = false;
      this.mensajeExitoSS = "";
      this.mensajeErrorSS = "";
      this.limpiarFiltrosHistorial();
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
        altInputClass: "input-field w-full pl-9 pr-3 py-2 text-xs sm:text-sm rounded-xl border border-[var(--paper-shadow)] cursor-pointer font-bold",
        defaultDate: this.formSeguridadSocial?.fecha_vigencia || null,
        disableMobile: "true",
        allowInput: true,
        placeholder: "Seleccionar fecha de vigencia...",
        onChange: (selectedDates, dateStr) => {
          if (self.formSeguridadSocial) {
            self.formSeguridadSocial.fecha_vigencia = dateStr || null;
          }
        }
      });

      if (this.fpVigenciaModalInstance.altInput) {
        this.fpVigenciaModalInstance.altInput.addEventListener('input', (e) => {
          const val = e.target.value.trim();
          if (/^\d{2}\/\d{2}\/\d{4}$/.test(val)) {
            const [d, m, y] = val.split('/');
            const iso = `${y}-${m}-${d}`;
            if (self.formSeguridadSocial) {
              self.formSeguridadSocial.fecha_vigencia = iso;
            }
          }
        });
      }

      if (this.formSeguridadSocial?.fecha_vigencia) {
        this.fpVigenciaModalInstance.setDate(this.formSeguridadSocial.fecha_vigencia, false);
      }
    },

    async guardarSeguridadSocial() {
      if (!this.formSeguridadSocial || !this.formSeguridadSocial.id_persona) return;

      this.guardandoSeguridadSocial = true;
      this.mensajeExitoSS = "";
      this.mensajeErrorSS = "";

      let usuarioSST = "";
      try {
        const sesion = (typeof getAuthSession === 'function') 
          ? getAuthSession() 
          : JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || '{}');
        const nombres = sesion?.nombres || sesion?.nombre || "";
        const apellidos = sesion?.apellidos || sesion?.apellido || "";
        usuarioSST = `${nombres} ${apellidos}`.trim() || sesion?.usuario || "";
      } catch (e) {}

      const sesionNombre = usuarioSST || (this.userDisplayName && this.userDisplayName !== "Usuario Activo" ? this.userDisplayName : "Evaluador SST");

      const fVigStr = this.formSeguridadSocial.fecha_vigencia
        ? String(this.formSeguridadSocial.fecha_vigencia).split("T")[0].split(" ")[0].trim()
        : null;

      const payload = {
        responsable: sesionNombre,
        anotaciones: this.formSeguridadSocial.anotaciones ? this.formSeguridadSocial.anotaciones.trim() : null,
        fecha_vigencia: fVigStr,
        fecha_consulta: fVigStr,
        ultima_revision: this.obtenerFechaHoraLocal(new Date())
      };

      try {
        const idPers = this.formSeguridadSocial.id_persona;
        const res = await fetch(`${API.seguridad_social}/persona/${idPers}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || err.mensaje || `Error al guardar (HTTP ${res.status})`);
        }

        // Persistir en cache localStorage
        const ident = String(this.formSeguridadSocial.persona_identificacion || "").trim();
        const localKeySS = `incarsa_ss_${ident}`;
        localStorage.setItem(localKeySS, JSON.stringify({
          ...this.formSeguridadSocial,
          ...payload
        }));

        // Actualizar detalle reactivo
        this.formSeguridadSocial.fecha_vigencia = fVigStr;
        this.formSeguridadSocial.responsable = payload.responsable;
        this.formSeguridadSocial.anotaciones = payload.anotaciones || "";
        this.formSeguridadSocial.ultima_revision = payload.ultima_revision;

        // Actualizar persona en la lista
        if (this.personaSeleccionadaSS) {
          this.personaSeleccionadaSS.fecha_vigencia_ss = fVigStr;
          this.personaSeleccionadaSS.responsable_ss = payload.responsable;
          this.personaSeleccionadaSS.anotaciones_ss = payload.anotaciones || "";
          this.personaSeleccionadaSS.estadoVigenciaSS = this.getEstadoVigenciaSS(fVigStr);
        }

        this.mensajeExitoSS = "¡Dictamen de seguridad social actualizado exitosamente!";
        this.mostrarToast("Seguridad social dictaminada y actualizada con éxito", "success");

        setTimeout(() => {
          this.mensajeExitoSS = "";
        }, 3000);

      } catch (err) {
        console.error("Error al dictaminar seguridad social:", err);
        this.mensajeErrorSS = err.message || "Error al actualizar la seguridad social.";
      } finally {
        this.guardandoSeguridadSocial = false;
      }
    },

    // Alias compatibles para el modal unificado
    get guardando() { return this.guardandoSeguridadSocial; },
    set guardando(val) { this.guardandoSeguridadSocial = val; },
    get mensajeExito() { return this.mensajeExitoSS; },
    get mensajeError() { return this.mensajeErrorSS; },
    getEstadoVigencia(fecha) { return this.getEstadoVigenciaSS(fecha); },
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
    async copiarCodigo(codigo) {
      if (!codigo) return;
      try {
        await navigator.clipboard.writeText(codigo);
        this.copiadoFeedback = codigo;
        this.mostrarToast(`Código ${codigo} copiado al portapapeles`, "success");
        setTimeout(() => {
          if (this.copiadoFeedback === codigo) {
            this.copiadoFeedback = null;
          }
        }, 2000);
      } catch (e) {
        console.warn("No se pudo copiar código:", e);
      }
    },

    // =============================================================
    // MODAL DE DISPOSITIVOS Y EQUIPOS (SOLO LECTURA)
    // =============================================================

    abrirModalDispositivos() {
      this.filtroDispositivos = "";
      this.showModalDispositivos = true;
    },

    cerrarModalDispositivos() {
      this.showModalDispositivos = false;
      this.filtroDispositivos = "";
    },

    async copiarSerieDispositivo(serie) {
      if (!serie || serie === '—' || serie === 'S/N') return;
      try {
        await navigator.clipboard.writeText(serie);
        this.dispositivoCopiado = serie;
        this.mostrarToast("Número de serie copiado al portapapeles", "success");
        setTimeout(() => {
          if (this.dispositivoCopiado === serie) {
            this.dispositivoCopiado = null;
          }
        }, 2000);
      } catch (e) {
        console.warn("No se pudo copiar serie:", e);
      }
    },

    get listaDispositivos() {
      const c = this.solicitud?.computos || this.solicitud?.equipos || this.solicitud?.eq_computo || [];
      return Array.isArray(c) ? c : [];
    },

    get totalDispositivos() {
      return this.listaDispositivos.length;
    },

    get dispositivosFiltrados() {
      const q = (this.filtroDispositivos || "").trim().toLowerCase();
      const list = this.listaDispositivos;
      if (!q) return list;
      return list.filter(d => 
        (d.marca || "").toLowerCase().includes(q) ||
        (d.modelo || "").toLowerCase().includes(q) ||
        (d.serie || "").toLowerCase().includes(q)
      );
    }
  };
}
