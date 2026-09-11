/**
 * INCARSA - Sistema de Gestión de Solicitudes
 * revision-solicitud.js - Lógica para la Vista Dedicada de Revisión y Dictamen de Roles
 */

function formatearFechaHoraEspanol(fechaStr) {
  if (!fechaStr || fechaStr === '—' || fechaStr === '-') return '—';
  try {
    const str = String(fechaStr).trim();
    const partes = str.replace('T', ' ').split(' ');
    const fPartes = partes[0].split('-');
    if (fPartes.length === 3) {
      const anio = fPartes[0];
      const mesIdx = parseInt(fPartes[1], 10) - 1;
      const dia = fPartes[2].padStart(2, '0');
      const meses = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
      const mesNombre = meses[mesIdx] || fPartes[1];

      if (partes[1]) {
        const hPartes = partes[1].split(':');
        let h = parseInt(hPartes[0], 10);
        const m = (hPartes[1] || '00').padStart(2, '0');
        const ampm = h >= 12 ? 'PM' : 'AM';
        h = h % 12;
        h = h ? h : 12;
        const horaFinal = `${String(h).padStart(2, '0')}:${m} ${ampm}`;
        return `${dia} ${mesNombre} ${anio}, ${horaFinal}`;
      }
      return `${dia} ${mesNombre} ${anio}`;
    }
    return fechaStr;
  } catch (e) {
    return fechaStr;
  }
}

function formatearFechaCorta(fechaStr) {
  if (!fechaStr || fechaStr === '—' || fechaStr === '-') return '—';
  try {
    const str = String(fechaStr).trim().split('T')[0].split(' ')[0];
    const fPartes = str.split('-');
    if (fPartes.length === 3) {
      const anio = fPartes[0];
      const mesIdx = parseInt(fPartes[1], 10) - 1;
      const dia = fPartes[2].padStart(2, '0');
      const meses = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
      const mesNombre = meses[mesIdx] || fPartes[1];
      return `${dia} ${mesNombre} ${anio}`;
    }
    return fechaStr;
  } catch (e) {
    return fechaStr;
  }
}

function revisionSolicitudApp() {
  return {
    solicitudId: null,
    solicitud: null,
    cargando: true,
    guardando: false,
    error: null,

    // Sidebar estado responsive
    sidebarCollapsed: false,
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

    // Sesión y Rol actual
    usuarioSesion: null,
    rolActual: "SST", // 'SST' | 'GESCO' | 'SCR' | 'Administrador' | 'Gestion documental'
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

    /**
     * Determina si el usuario actual tiene permisos para ver y auditar antecedentes en revisión.
     * Habilitado exclusivamente para SCR y roles superiores (ADMINISTRADOR y SUPERADMIN).
     */
    get puedeVerAntecedentes() {
      const rolActualNorm = String(this.rolActual || "").trim().toUpperCase();
      const rolSesionNorm = String(this.usuarioSesion?.rol || this.usuarioSesion?.nombre_rol || "").trim().toUpperCase();
      const idRol = Number(this.usuarioSesion?.id_rol || 0);

      // Si el rol activo (simulado o real) es un rol operativo sin atribución de antecedentes
      const rolesExcluidos = ["SST", "GESCO", "GESTION DOCUMENTAL", "GESTIÓN DOCUMENTAL", "VIGILANTE", "COORDINADOR"];
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
      if (!this.detalleHistorial || !Array.isArray(this.detalleHistorial.historial)) return [];
      let list = [...this.detalleHistorial.historial];

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

      // 2. Obtener sesión de usuario
      try {
        const sesion = JSON.parse(
          sessionStorage.getItem("incarsa_session") ||
          localStorage.getItem("incarsa_session") ||
          "null"
        );
        if (sesion) {
          this.usuarioSesion = sesion;
          const mapaRoles = { 1: "Administrador", 2: "Superadmin", 3: "Vigilante", 4: "Coordinador", 5: "Gestion documental", 6: "SST", 7: "GESCO", 8: "SCR" };
          const rol = sesion.rol || sesion.nombre_rol || mapaRoles[sesion.id_rol] || "Gestion documental";
          this.rolActual = rol;
          this.rolNombre = rol;
        }
      } catch (e) {
        console.warn("No se pudo parsear sesión:", e);
      }

      if (!this.solicitudId) {
        this.error = "No se especificó un ID de solicitud válido.";
        this.cargando = false;
        return;
      }

      await this.cargarSolicitud();

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

        // Preseleccionar planta para dictamen
        if (this.misPlantasDictaminables && this.misPlantasDictaminables.length > 0) {
          this.plantaSeleccionadaDictamen = this.misPlantasDictaminables[0].id;
        }

        // Si es SCR o SuperAdmin y la solicitud está en estados previos a 'POR APROBAR', preseleccionar 'preaprobar'
        if ((this.rolActual === "SCR" || this.esSuperAdmin) && this.solicitud.estado !== "POR APROBAR") {
          this.dictamenForm.decision = "preaprobar";
        } else {
          this.dictamenForm.decision = "aprobar";
        }

        // Cargar vigencias de antecedentes de cada ingresante (exclusivo para SCR y roles superiores)
        if (this.puedeVerAntecedentes) {
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

      // Cargar autorizaciones individuales de vehículos persistidas en localStorage
      try {
        const storageKeyVeh = `incarsa_solicitud_${s.id}_vehiculos`;
        const vehiculosGuardados = JSON.parse(localStorage.getItem(storageKeyVeh) || "null");
        if (Array.isArray(vehiculosGuardados) && vehiculosGuardados.length > 0) {
          listaVehiculos = listaVehiculos.map(v => {
            const match = vehiculosGuardados.find(vg => String(vg.id) === String(v.id) || (vg.placa && vg.placa === v.placa));
            if (match) {
              const autGuardado = match.autorizado !== false && match.autorizado !== 0 && match.autorizado !== '0' && match.autorizado !== 'false';
              return {
                ...v,
                autorizado: autGuardado,
                motivo_rechazo: match.motivo_rechazo || v.motivo_rechazo || ""
              };
            }
            return v;
          });
        }
      } catch (e) {}

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
            motivo_rechazo: p.motivo_rechazo || "",
            fecha_consulta: (p.fecha_consulta && p.fecha_consulta !== "None" && p.fecha_consulta !== "null" && p.fecha_consulta !== "Pendiente" && p.fecha_consulta !== "No registrada") ? p.fecha_consulta : null,
            ultima_revision: (p.ultima_revision && p.ultima_revision !== "None" && p.ultima_revision !== "null" && p.ultima_revision !== "No registrada") ? p.ultima_revision : null,
            responsable: p.responsable || null,
            anotaciones: p.anotaciones || "",
            documentos: Array.isArray(p.documentos) && p.documentos.length > 0 ? p.documentos : [
              { tipo_doc: "cedula", nombre_archivo: `Cedula_${p.identificacion || 'doc'}.pdf` },
              { tipo_doc: "arl", nombre_archivo: `ARL_${p.identificacion || 'doc'}.pdf` },
              { tipo_doc: "examen_medico", nombre_archivo: `Examen_${p.identificacion || 'doc'}.pdf` },
              { tipo_doc: "induccion", nombre_archivo: `Induccion_${p.identificacion || 'doc'}.pdf` }
            ]
          };
        });
      }

      // Cargar autorizaciones individuales previas persistidas en localStorage
      try {
        const storageKey = `incarsa_solicitud_${s.id}_personas`;
        const personasGuardadas = JSON.parse(localStorage.getItem(storageKey) || "null");
        if (Array.isArray(personasGuardadas) && personasGuardadas.length > 0) {
          listaPersonas = listaPersonas.map(p => {
            const match = personasGuardadas.find(pg => String(pg.id) === String(p.id) || (pg.identificacion && pg.identificacion === p.identificacion));
            if (match) {
              const autGuardado = match.autorizado !== false && match.autorizado !== 0 && match.autorizado !== '0' && match.autorizado !== 'false';
              return {
                ...p,
                autorizado: autGuardado,
                motivo_rechazo: match.motivo_rechazo || p.motivo_rechazo || ""
              };
            }
            return p;
          });
        }
      } catch (e) {}

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
      // Si la solicitud ya está en estado final APROBADO o RECHAZADO para roles operativos
      if (estado === "APROBADO" || estado === "RECHAZADO") {
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
      // SCR y roles superiores (SuperAdmin, Administrador) SIEMPRE pueden autorizar
      if (this.esScrOSuperior) {
        return true;
      }
      // Regla de negocio: Si la persona fue enviada/guardada sin autorización previamente en BD,
      // los demás roles NO pueden volver a autorizarla.
      if (persona && persona.denegadaEnBd) {
        return false;
      }
      return true;
    },

    puedeAutorizarVehiculo(vehiculo) {
      if (!this.puedeEditarAutorizacion) return false;
      if (this.esScrOSuperior) {
        return true;
      }
      if (vehiculo && vehiculo.denegadoEnBd) {
        return false;
      }
      return true;
    },

    setAutorizacionPersona(persona, estaAutorizado, motivo = "") {
      if (!this.puedeEditarAutorizacion) {
        this.mostrarToast("No puedes modificar la autorización: ya has emitido dictamen o la solicitud ya fue procesada.", "info");
        return;
      }
      if (estaAutorizado && !this.puedeAutorizarPersona(persona)) {
        this.mostrarToast("No puedes autorizar a este ingresante: fue denegado en una revisión previa. Solo SCR o superiores en modo de edición de revisión pueden reautorizarlo.", "warning");
        return;
      }
      persona.autorizado = estaAutorizado;
      if (!estaAutorizado && motivo) {
        persona.motivo_rechazo = motivo;
      } else if (estaAutorizado) {
        persona.motivo_rechazo = "";
      }
      this.persistirPersonasEnStorage();
      const nombre = persona.nombre || "Ingresante";
      this.mostrarToast(
        estaAutorizado ? `✅ ${nombre} ha sido autorizado` : `⛔ Acceso denegado a ${nombre}`,
        estaAutorizado ? "success" : "info"
      );
    },

    toggleAutorizacionPersona(persona) {
      if (!this.puedeEditarAutorizacion) return;
      if (!persona.autorizado && !this.puedeAutorizarPersona(persona)) {
        this.mostrarToast("No puedes autorizar a este ingresante: fue denegado en una revisión previa. Solo SCR o superior en edición pueden reautorizarlo.", "warning");
        return;
      }
      this.setAutorizacionPersona(persona, !persona.autorizado);
    },

    autorizarTodasPersonas() {
      if (!this.puedeEditarAutorizacion) {
        this.mostrarToast("No puedes modificar autorizaciones: ya has emitido tu dictamen.", "info");
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
      this.persistirPersonasEnStorage();
      if (omitidas > 0) {
        this.mostrarToast(`Se autorizaron los ingresantes disponibles (${omitidas} ingresante(s) se mantuvieron denegados por revisión previa).`, "info");
      } else {
        this.mostrarToast("Todas las personas de la solicitud han sido autorizadas", "success");
      }
    },

    denegarTodasPersonas() {
      if (!this.puedeEditarAutorizacion) {
        this.mostrarToast("No puedes modificar autorizaciones: ya has emitido tu dictamen.", "info");
        return;
      }
      if (!this.solicitud?.personas || this.solicitud.personas.length === 0) return;
      this.solicitud.personas.forEach(p => {
        p.autorizado = false;
      });
      this.persistirPersonasEnStorage();
      this.mostrarToast("Todas las personas han sido marcadas como No Autorizadas", "info");
    },

    async persistirPersonasEnStorage() {
      if (!this.puedeEditarAutorizacion) return;
      try {
        const storageKey = `incarsa_solicitud_${this.solicitudId}_personas`;
        localStorage.setItem(storageKey, JSON.stringify(this.solicitud.personas));

        const locales = JSON.parse(localStorage.getItem("incarsa_solicitudes") || "[]");
        const idx = locales.findIndex(s => String(s.id) === String(this.solicitudId));
        if (idx > -1) {
          locales[idx].personas = this.solicitud.personas;
          localStorage.setItem("incarsa_solicitudes", JSON.stringify(locales));
        }
      } catch (e) {
        console.warn("No se pudo guardar personas en storage:", e);
      }
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
      if (this.misPlantasDictaminables.length > 0) {
        this.plantaSeleccionadaDictamen = this.misPlantasDictaminables[0].id;
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
            fecha: revSst?.fecha_revision ? new Date(revSst.fecha_revision).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : '',
            observacion: revSst?.observacion || '',
            motivoRechazo: revSst?.motivo_rechazo || ''
          },
          gesco: {
            aprobado: gescoAprobado,
            rechazado: gescoRechazado,
            revisor: revGesco?.nombre_revisor || '',
            fecha: revGesco?.fecha_revision ? new Date(revGesco.fecha_revision).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : '',
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
        fecha: revScr?.fecha_revision ? new Date(revScr.fecha_revision).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : '',
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
          fecha: r.fecha_revision ? new Date(r.fecha_revision).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : ''
        };
      });
    },

    get totalPlantasCompletadas() {
      return this.matrizRevisionesPorPlanta.filter(p => p.completa).length;
    },

    get misPlantasDictaminables() {
      const todas = this.plantasSolicitud;
      const esAdmin = this.rolActual === 'Administrador' || this.rolActual === 'SCR' || 
                      (this.usuarioSesion && (Number(this.usuarioSesion.id_rol) === 1 || String(this.usuarioSesion.rol).toUpperCase().includes("ADMIN")));
      if (esAdmin) {
        return todas;
      }
      const misIds = (this.usuarioSesion?.plantas_ids || []).map(Number);
      if (misIds.length === 0) return todas;
      const filtradas = todas.filter(p => misIds.includes(p.id));
      return filtradas.length > 0 ? filtradas : todas;
    },

    get miPlantaYaFirmada() {
      if (this.rolActual !== 'SST' && this.rolActual !== 'GESCO') return false;
      let pid = Number(this.plantaSeleccionadaDictamen);
      if (!pid && this.misPlantasDictaminables.length > 0) {
        pid = Number(this.misPlantasDictaminables[0].id);
      } else if (!pid && this.plantasSolicitud.length > 0) {
        pid = Number(this.plantasSolicitud[0].id);
      }
      const rolKey = this.rolActual.toLowerCase();
      if (!pid) {
        return this.matrizRevisionesPorPlanta.some(item => Boolean(item[rolKey]?.aprobado || item[rolKey]?.rechazado));
      }
      const item = this.matrizRevisionesPorPlanta.find(p => p.id === pid);
      if (!item) return false;
      return Boolean(item[rolKey]?.aprobado || item[rolKey]?.rechazado);
    },

    get tienePlantaAsignadaParaSolicitud() {
      if (this.rolActual !== "SST" && this.rolActual !== "GESCO") {
        return true;
      }

      // Si el rol es simulado por un Administrador o no tiene restricciones, permitir
      const sesion = this.usuarioSesion;
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
     * Carga una revisión existente (SST, GESCO o SCR) en el formulario de dictamen para que SCR/Admin puedan editarla
     */
    cargarRevisionParaEdicion(rol, id_planta = null, plantaNombre = "") {
      if (!this.esScrOSuperior) {
        this.mostrarToast("Solo SCR y roles superiores pueden editar revisiones.", "warning");
        return;
      }

      const rolUpper = String(rol).toUpperCase();
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
      this.dictamenForm = {
        decision: (this.rolActual === "SCR" || this.esSuperAdmin) && this.solicitud?.estado !== "POR APROBAR" ? "preaprobar" : "aprobar",
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
      const idPlantaDictamen = this.editandoRevision 
        ? this.editandoRevision.id_planta 
        : ((this.rolActual === "SST" || this.rolActual === "GESCO") ? Number(this.plantaSeleccionadaDictamen) : null);

      // Asegurar selección de planta
      if (!this.editandoRevision && (this.rolActual === "SST" || this.rolActual === "GESCO") && !this.plantaSeleccionadaDictamen) {
        if (this.misPlantasDictaminables.length > 0) {
          this.plantaSeleccionadaDictamen = this.misPlantasDictaminables[0].id;
        } else if (this.plantasSolicitud.length > 0) {
          this.plantaSeleccionadaDictamen = this.plantasSolicitud[0].id;
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
      const nombreUsuario = this.usuarioSesion?.nombres 
        ? `${this.usuarioSesion.nombres} ${this.usuarioSesion.apellidos || ''}`.trim() 
        : `Auditor (${this.rolActual})`;

      try {
        let decisionBackend = "APROBADO";
        if (decision === "rechazar") decisionBackend = "RECHAZADO";
        else if (decision === "devolver") decisionBackend = "DEVUELTO";
        else if (decision === "preaprobar") decisionBackend = "PREAPROBADO";

        const payloadDictamen = {
          id_planta: idPlantaDictamen,
          rol: rolDictamen,
          decision: decisionBackend,
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
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payloadDictamen)
        });

        if (res.ok) {
          const dataRes = await res.json();
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
            const mensajeToast = decision === "preaprobar"
              ? `Solicitud PRE-APROBADA por SCR. Redirigiendo a Procesamiento...`
              : (decision === "devolver"
                  ? `Solicitud devuelta a Gestión Documental. Redirigiendo a Procesamiento...`
                  : (decision === "rechazar"
                      ? `Solicitud rechazada. Redirigiendo a Procesamiento...`
                      : `Dictamen registrado exitosamente (${dataRes.nuevo_estado}). Redirigiendo a Procesamiento...`));
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
          rol: this.rolActual || "SCR",
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
        nombreArchivo: nom
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
      if (this.puedeVerAntecedentes && this.solicitud?.personas?.length > 0) {
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
    // GESTIÓN Y AUDITORÍA DE ANTECEDENTES (HISTORIAL Y RENOVACIÓN)
    // =============================================================

    async cargarVigenciasPersonas() {
      if (!this.solicitud || !Array.isArray(this.solicitud.personas)) return;
      
      const tareas = this.solicitud.personas.map(async (p) => {
        const idPersona = p.id_persona || p.id;
        const ident = String(p.identificacion || "").trim();

        // 1. Ver si está en localStorage (solo si fue guardado recientemente con fecha válida)
        const localKey = `incarsa_antecedente_${ident}`;
        const localSaved = JSON.parse(localStorage.getItem(localKey) || "null");
        if (localSaved && localSaved.fecha_consulta && localSaved.fecha_consulta !== "Pendiente" && localSaved.fecha_consulta !== "No registrada") {
          p.fecha_consulta = localSaved.fecha_consulta;
          p.ultima_revision = localSaved.ultima_revision;
          p.responsable = localSaved.responsable;
          p.anotaciones = localSaved.anotaciones;
          p.estadoVigencia = this.getEstadoVigencia(localSaved.fecha_consulta);
          return;
        }

        // 2. Si ya tiene fecha_consulta válida en el objeto
        if (p.fecha_consulta && p.fecha_consulta !== "None" && p.fecha_consulta !== "null" && p.fecha_consulta !== "Pendiente" && p.fecha_consulta !== "No registrada") {
          p.estadoVigencia = this.getEstadoVigencia(p.fecha_consulta);
          return;
        }

        // 3. Consultar backend si existe registro previo
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
                return;
              }
            }
          }
        } catch (e) {}

        // Fallback por defecto si no tiene registro previo de revisión: Sin revisión
        p.estadoVigencia = this.getEstadoVigencia(null);
      });

      await Promise.all(tareas);
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
    }
  };
}
