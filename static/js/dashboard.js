
// ---------------------------------------------------------
// Shell general: sidebar, navbar, dropdown de perfil
// ---------------------------------------------------------
function appShell() {
  return {
    sidebarCollapsed: false,
    sidebarOpenMobile: false,
    profileMenuOpen: false,
    notificationsOpen: false,
    modalTodasNotificacionesOpen: false,
    filtroNotifTab: 'todas',
    busquedaNotif: '',
    notifPage: 1,
    notifPageSize: 8,
    activeRole: "GESTOR DE DOCUMENTACIÓN",
    openModules: { procesamiento: false, formularios: false, tablas: false },
    darkMode: localStorage.getItem('darkMode') === 'true',
    userId: 1,
    roleId: 2,
    notifications: [],
    unreadNotificationsCount: 0,

    tieneRol(...roles) {
      if (typeof window.tieneRol === "function") {
        return window.tieneRol(...roles);
      }
      return false;
    },

    get esAdminOSuperAdmin() {
      return this.tieneRol('ADMINISTRADOR', 'SUPERADMIN');
    },

    puedeModulo(mod) {
      if (this.activeRole === "SUPERADMIN") return true;
      if (typeof window.puedeModulo === "function") {
        return window.puedeModulo(mod);
      }
      return true;
    },

    puedeAccion(mod, acc) {
      if (this.activeRole === "SUPERADMIN") return true;
      if (typeof window.puedeAccion === "function") {
        return window.puedeAccion(mod, acc);
      }
      return true;
    },

    formatearTiempoRelativo(fechaStr) {
      if (typeof formatearTiempoRelativo === "function") {
        return formatearTiempoRelativo(fechaStr);
      }
      return fechaStr || "";
    },

    formatearTextoEnlace(url) {
      if (typeof window.formatearTextoEnlace === "function") {
        return window.formatearTextoEnlace(url);
      }
      return url || "";
    },

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

    init() {
      // Aplicar dark mode guardado
      document.documentElement.classList.toggle('dark', this.darkMode);

      // Restaurar el nombre y rol del usuario desde la sesión si existe
      let sesion = null;
      if (typeof getAuthSession === "function") {
        sesion = getAuthSession();
      } else {
        try {
          sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
        } catch (e) {}
      }

      if (sesion) {
        this.activeRole = sesion.rol || this.activeRole;
        this.userId = sesion.id || this.userId;
        this.roleId = sesion.id_rol || this.roleId;
        this._userName = sesion.nombre || "Usuario";
        this._userInitials = (this._userName.split(" ").map(p => p[0]).join("")).substring(0, 2).toUpperCase();
      }

      // Escuchar apertura remota de modal de notificaciones
      window.addEventListener("open-notificaciones-modal", () => {
        this.abrirModalTodasNotificaciones();
      });

      // Escuchar notificaciones en caliente vía SSE
      window.addEventListener("notificacion-en-caliente", (e) => {
        const notif = e.detail;
        if (notif) {
          const existe = (this.notifications || []).some(n => n.id && notif.id && String(n.id) === String(notif.id));
          if (!existe) {
            this.notifications.unshift(notif);
            this.unreadNotificationsCount = (this.unreadNotificationsCount || 0) + 1;
          }
        }
      });

      window.addEventListener("notificacion-en-caliente-remota", (e) => {
        const notif = e.detail;
        if (notif) {
          const existe = (this.notifications || []).some(n => n.id && notif.id && String(n.id) === String(notif.id));
          if (!existe) {
            this.notifications.unshift(notif);
            this.unreadNotificationsCount = (this.unreadNotificationsCount || 0) + 1;
          }
        }
      });

      window.addEventListener("notificaciones-leidas-sync", (e) => {
        const data = e.detail || {};
        if (data.todas) {
          (this.notifications || []).forEach(n => n.leido = true);
          this.unreadNotificationsCount = 0;
        } else if (data.id_notificacion) {
          const target = (this.notifications || []).find(n => String(n.id) === String(data.id_notificacion));
          if (target && !target.leido) {
            target.leido = true;
            if (this.unreadNotificationsCount > 0) this.unreadNotificationsCount--;
          }
        }
      });

      // Escuchar actualizaciones de notificaciones (al revisar solicitudes en cualquier sección)
      window.addEventListener("notificaciones-actualizadas", () => {
        this.cargarNotificaciones();
      });
      window.addEventListener("storage", (e) => {
        if (e.key === "incarsa_notificaciones_reload" || e.key === "incarsa_notif_reload") {
          this.cargarNotificaciones();
        }
      });

      this.cargarNotificaciones();
      setInterval(() => this.cargarNotificaciones(), 35000);
    },

    async cargarNotificaciones(limit = 50) {
      // Revisar si ya están precargadas desde el splash
      try {
        const preloadedNotifs = sessionStorage.getItem("incarsa_preloaded_notificaciones");
        if (preloadedNotifs) {
          const d = JSON.parse(preloadedNotifs);
          if (d && (d.notificaciones || d.no_leidas !== undefined)) {
            this.notifications = d.notificaciones || [];
            this.unreadNotificationsCount = d.no_leidas || 0;
          }
        }
      } catch (e) {}

      try {
        const notifUrl = (typeof API !== "undefined" && API.notificaciones) 
          ? API.notificaciones 
          : `${window.location.origin}/api/v1/notificaciones`;
        const params = new URLSearchParams();
        if (this.userId) params.append("id_usuario", this.userId);
        if (this.roleId) params.append("id_rol", this.roleId);
        if (limit) params.append("limit", limit);
        const res = await fetch(`${notifUrl}?${params.toString()}`);
        if (res.ok) {
          const data = await res.json();
          this.notifications = data.notificaciones || [];
          this.unreadNotificationsCount = data.no_leidas || 0;
        }
      } catch (err) {
        console.warn("Aviso al cargar notificaciones en dashboard:", err);
      }
    },

    async marcarNotificacionLeida(n) {
      if (!n.leido) {
        try {
          const notifUrl = (typeof API !== "undefined" && API.notificaciones) 
            ? API.notificaciones 
            : `${window.location.origin}/api/v1/notificaciones`;
          await fetch(`${notifUrl}/${n.id}/leer`, { method: "PATCH" });
          n.leido = true;
          if (this.unreadNotificationsCount > 0) {
            this.unreadNotificationsCount--;
          }
        } catch (e) {
          console.warn("Aviso al marcar notificación como leída:", e);
        }
      }
      if (n.enlace) {
        window.location.href = n.enlace;
      }
    },

    esNotifPreaprobada(n) {
      if (!n) return false;
      const enlace = String(n.enlace || "");
      const titulo = String(n.titulo || "");
      return enlace.includes("confirmar=true") || (titulo.toLowerCase().includes("preaprobada") && enlace.includes("/solicitudes/revision/"));
    },

    obtenerCodigoSolicitudDeNotif(n) {
      if (!n || !n.enlace) return null;
      const match = n.enlace.match(/\/solicitudes\/revision\/([^\/?#]+)/);
      if (match && match[1]) return match[1];
      return null;
    },

    async revisarSolicitudNotif(n) {
      if (!n.leido) {
        try {
          const notifUrl = (typeof API !== "undefined" && API.notificaciones) 
            ? API.notificaciones 
            : `${window.location.origin}/api/v1/notificaciones`;
          await fetch(`${notifUrl}/${n.id}/leer`, { method: "PATCH" });
          n.leido = true;
          if (this.unreadNotificationsCount > 0) this.unreadNotificationsCount--;
        } catch (e) {}
      }
      const cod = this.obtenerCodigoSolicitudDeNotif(n);
      if (cod) {
        window.location.href = `/solicitudes/revision/${cod}`;
      } else if (n.enlace) {
        window.location.href = n.enlace;
      }
    },

    async confirmarAprobacionDirectaNotif(n) {
      const cod = this.obtenerCodigoSolicitudDeNotif(n);
      if (!cod) {
        if (n.enlace) window.location.href = n.enlace;
        return;
      }

      const sesion = (typeof getSesionActual === "function") ? getSesionActual() : null;
      const nombreUsuario = sesion?.nombres 
        ? `${sesion.nombres} ${sesion.apellidos || ''}`.trim() 
        : (this.userDisplayName || "Auditor SCR");

      const accionConfirmar = async () => {
        n.aprobando = true;
        try {
          const payload = {
            id_planta: null,
            rol: "SCR",
            decision: "APROBADO",
            observacion: "Aprobación definitiva confirmada directamente desde el panel de notificaciones.",
            id_usuario: this.userId || sesion?.id || null,
            nombre_revisor: nombreUsuario
          };
          const res = await fetch(`${API.solicitudes}/${cod}/dictamen`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
          if (res.ok) {
            n.aprobadoExitoso = true;
            n.leido = true;
            const notifUrl = (typeof API !== "undefined" && API.notificaciones) 
              ? API.notificaciones 
              : `${window.location.origin}/api/v1/notificaciones`;
            fetch(`${notifUrl}/${n.id}/leer`, { method: "PATCH" }).catch(() => {});
            if (this.unreadNotificationsCount > 0) this.unreadNotificationsCount--;

            if (typeof Swal !== 'undefined') {
              Swal.fire({
                icon: 'success',
                title: '¡Solicitud Aprobada!',
                text: `La solicitud #${cod} ha sido aprobada definitivamente con éxito.`,
                timer: 3000,
                showConfirmButton: false
              });
            } else if (typeof Alerta !== 'undefined') {
              Alerta.fire({
                type: 'success',
                title: '¡Solicitud Aprobada!',
                text: `La solicitud #${cod} ha sido aprobada definitivamente.`
              });
            }
          } else {
            const err = await res.json().catch(() => ({}));
            const msg = err.detail || err.mensaje || "Error al aprobar la solicitud.";
            if (typeof Swal !== 'undefined') {
              Swal.fire({ icon: 'error', title: 'Error', text: msg });
            } else {
              alert(`Error al aprobar: ${msg}`);
            }
          }
        } catch (e) {
          console.error("Error al aprobar desde notificación:", e);
          alert("Error de conexión al aprobar la solicitud: " + e.message);
        } finally {
          n.aprobando = false;
        }
      };

      if (typeof Swal !== 'undefined') {
        const result = await Swal.fire({
          title: '¿Confirmar Aprobación Final?',
          html: `<p class="text-sm text-slate-300">¿Deseas dar la <strong>aprobación definitiva</strong> a la solicitud <strong>#${cod}</strong> sin ingresar a la ventana de revisión?</p>`,
          icon: 'question',
          showCancelButton: true,
          confirmButtonColor: '#10b981',
          cancelButtonColor: '#64748b',
          confirmButtonText: '<i class="fa-solid fa-check-double mr-1.5"></i> Sí, Confirmar y Aprobar',
          cancelButtonText: 'Cancelar',
          background: '#0f172a',
          color: '#f8fafc'
        });
        if (result.isConfirmed) {
          await accionConfirmar();
        }
      } else if (typeof Alerta !== 'undefined') {
        const res = await Alerta.fire({
          type: 'question',
          title: '¿Confirmar Aprobación?',
          text: `¿Deseas aprobar definitivamente la solicitud #${cod} sin ingresar a la ventana de revisión?`,
          confirmText: 'Sí, Aprobar',
          cancelText: 'Cancelar',
          showCancel: true
        });
        if (res.isConfirmed) {
          await accionConfirmar();
        }
      } else {
        if (confirm(`¿Deseas confirmar la aprobación definitiva de la solicitud #${cod}?`)) {
          await accionConfirmar();
        }
      }
    },

    async marcarTodasNotificacionesLeidas() {
      try {
        const notifUrl = (typeof API !== "undefined" && API.notificaciones) 
          ? API.notificaciones 
          : `${window.location.origin}/api/v1/notificaciones`;
        await fetch(`${notifUrl}/marcar-todas-leidas`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id_usuario: this.userId, id_rol: this.roleId })
        });
        this.notifications.forEach(n => n.leido = true);
        this.unreadNotificationsCount = 0;
      } catch (e) {
        console.warn("Aviso al marcar todas las notificaciones:", e);
      }
    },

    toggleDarkMode() {
      this.darkMode = !this.darkMode;
      document.documentElement.classList.toggle('dark', this.darkMode);
      localStorage.setItem('darkMode', this.darkMode);
    },

    get userDisplayName() {
      return this._userName || "Laura Gómez";
    },
    get userInitials() {
      return this._userInitials || "LG";
    },

    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
    },
    toggleMobileSidebar() {
      this.sidebarOpenMobile = !this.sidebarOpenMobile;
    },
    closeMobileSidebar() {
      this.sidebarOpenMobile = false;
    },
    toggleModule(name) {
      this.openModules[name] = !this.openModules[name];
    },
    cerrarSesion() {
      if (typeof cerrarSesionUsuario === "function") {
        cerrarSesionUsuario();
      } else {
        try {
          sessionStorage.clear();
          localStorage.removeItem("incarsa_token");
          localStorage.removeItem("incarsa_session");
        } catch (e) {}
        window.location.replace("/login?logout=1");
      }
    }
  };
}

// ---------------------------------------------------------
// Helper: normaliza solicitudes del backend o mock al mismo formato
// ---------------------------------------------------------
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

function normalizarSolicitud(s) {
  if (!s) return {};

  // Formatear plantas como cadena legible
  let cadenaPlanta = "—";
  if (Array.isArray(s.plantas) && s.plantas.length > 0) {
    cadenaPlanta = s.plantas.map(p => (typeof p === "object" ? (p.nombre || p.nombre_planta || p.planta) : p)).filter(Boolean).join(", ");
  } else if (typeof s.planta === "string" && s.planta.trim() !== "") {
    cadenaPlanta = s.planta;
  } else if (typeof s.plantas === "string" && s.plantas.trim() !== "") {
    cadenaPlanta = s.plantas;
  }

  let listaComputos = [];
  if (typeof s.computos === 'string' && s.computos.trim() !== '') {
    listaComputos = s.computos.split('###').map(c => {
      const [id, marca, modelo, serie] = c.split('|||');
      return { id, marca, modelo, serie };
    });
  } else if (Array.isArray(s.computos)) {
    listaComputos = s.computos;
  }

  let listaVehiculos = [];
  if (typeof s.vehiculos === 'string' && s.vehiculos.trim() !== '') {
    listaVehiculos = s.vehiculos.split('###').map(v => {
      const partes = v.split('|||');
      const id = partes[0];
      const tipo = partes[1] || "Vehículo";
      const placa = partes[2] || "—";
      const licencia_doc = partes[3] || "";
      const aut = partes[4];
      const mot = partes[5] || "";
      return {
        id,
        tipo,
        placa,
        licencia_doc,
        licencia: licencia_doc,
        autorizado: aut !== '0' && aut !== 0 && aut !== false && aut !== 'false',
        motivo: mot
      };
    });
  } else if (Array.isArray(s.vehiculos) || Array.isArray(s.vehiculo)) {
    const rawV = Array.isArray(s.vehiculos) ? s.vehiculos : s.vehiculo;
    listaVehiculos = rawV.map(v => ({
      id: v.id || v.id_vehiculo,
      tipo: v.tipo || "Vehículo",
      placa: v.placa || "—",
      conductor: v.conductor || "",
      licencia_doc: v.licencia_doc || v.licencia || "",
      licencia: v.licencia_doc || v.licencia || "",
      autorizado: v.autorizado !== '0' && v.autorizado !== 0 && v.autorizado !== false && v.autorizado !== 'false',
      motivo: v.motivo || v.motivo_rechazo || ""
    }));
  }

  try {
    const storageKeyVeh = `incarsa_solicitud_${s.id}_vehiculos`;
    const localVeh = JSON.parse(localStorage.getItem(storageKeyVeh) || "null");
    if (Array.isArray(localVeh) && localVeh.length > 0) {
      listaVehiculos = listaVehiculos.map(lv => {
        const match = localVeh.find(v => String(v.id) === String(lv.id) || (v.placa && v.placa === lv.placa));
        if (match) {
          return {
            ...lv,
            autorizado: match.autorizado !== '0' && match.autorizado !== 0 && match.autorizado !== false && match.autorizado !== 'false',
            motivo: match.motivo_rechazo || match.motivo || lv.motivo || ""
          };
        }
        return lv;
      });
    }
  } catch (e) {}
  
  let listaPersonas = [];
  if (typeof s.personas === 'string' && s.personas.trim() !== '') {
    if (s.personas.includes('|||') || s.personas.includes('###')) {
      listaPersonas = s.personas.split('###').map(p => {
        const parts = p.split('|||');
        const id = parts[0];
        const ap_nombre = parts[1];
        const tipo_doc = parts[2];
        const identificacion = parts[3];
        const cargo = parts[4];
        const autorizado = parts[5];
        const motivo = parts[6] || "";
        return {
          id,
          ap_nombre,
          nombre: ap_nombre,
          tipo_doc,
          identificacion,
          cargo,
          autorizado: autorizado !== '0' && autorizado !== 0 && autorizado !== false && autorizado !== 'false',
          motivo: motivo || ""
        };
      });
    } else {
      try {
        listaPersonas = JSON.parse(s.personas);
      } catch (e) {
        listaPersonas = [];
      }
    }
  } else if (Array.isArray(s.personas) || Array.isArray(s.ingresantes)) {
    const rawP = Array.isArray(s.personas) ? s.personas : s.ingresantes;
    listaPersonas = rawP.map(p => ({
      id: p.id,
      ap_nombre: p.ap_nombre || `${p.nombre || ''} ${p.apellido || ''}`.trim() || p.nombre || "Contratista",
      nombre: p.nombre || p.ap_nombre || "Contratista",
      tipo_doc: p.tipo_doc || "CC",
      identificacion: p.identificacion || "—",
      cargo: p.cargo || "Operario",
      autorizado: p.autorizado !== '0' && p.autorizado !== 0 && p.autorizado !== false && p.autorizado !== 'false',
      motivo: p.motivo || p.motivo_rechazo || ""
    }));
  }

  try {
    const storageKey = `incarsa_solicitud_${s.id}_personas`;
    const localPersonas = JSON.parse(localStorage.getItem(storageKey) || "null");
    if (Array.isArray(localPersonas) && localPersonas.length > 0) {
      listaPersonas = listaPersonas.map(lp => {
        const match = localPersonas.find(p => String(p.id) === String(lp.id) || (p.identificacion && p.identificacion === lp.identificacion));
        if (match) {
          return {
            ...lp,
            autorizado: match.autorizado !== '0' && match.autorizado !== 0 && match.autorizado !== false && match.autorizado !== 'false',
            motivo: match.motivo_rechazo || match.motivo || lp.motivo || ""
          };
        }
        return lp;
      });
    }
  } catch (e) {}

  let listaRevisiones = [];
  if (Array.isArray(s.revisiones)) {
    listaRevisiones = s.revisiones;
  } else {
    try {
      const storageKeyRev = `incarsa_revisiones_${s.id}`;
      const guardado = JSON.parse(localStorage.getItem(storageKeyRev) || "null");
      if (guardado) {
        if (Array.isArray(guardado.historial)) {
          listaRevisiones = guardado.historial;
        } else if (Array.isArray(guardado)) {
          listaRevisiones = guardado;
        }
      }
    } catch (e) {}
  }

  const nombreEmpresaOrigen = s.nombre_empresa || s.empresa_origen || s.empresaOrigen || "INCARSA";
  const nombreContratista = s.nombre_emContratista || s.empresa_contratista || s.contratista || "—";
  const diligenciadorNombre = s.diligenciador || (typeof s.diligenciado_por === "string" ? s.diligenciado_por : null) || s.diligenciadoPor || "Administrador";
  const codigoVal = s.codigo || s.codigo_radicado || `RAD-${s.id}`;

  return {
    id: s.id,
    codigo: codigoVal,
    codigo_radicado: codigoVal,
    nombre_empresa: nombreEmpresaOrigen,
    nombre_emContratista: nombreContratista,
    planta: cadenaPlanta,
    plantas: cadenaPlanta,
    fecha_ingreso: formatearFechaCorta(s.fecha_ingreso || s.fecha_inicio || s.fechaIngreso),
    fecha_salida: formatearFechaCorta(s.fecha_salida || s.fecha_fin || s.fechaSalida),
    fechaIngreso: formatearFechaCorta(s.fecha_ingreso || s.fecha_inicio || s.fechaIngreso),
    fechaSalida: formatearFechaCorta(s.fecha_salida || s.fecha_fin || s.fechaSalida),
    fecha_creacion: formatearFechaHoraEspanol(s.fecha_creacion),
    estado: (s.estado || "ENVIADO").toUpperCase(),
    diligenciador: diligenciadorNombre,
    observaciones: s.observaciones || s.observacion || "",
    // campos del modal detalle
    empresaOrigen: nombreEmpresaOrigen,
    empresa_origen: nombreEmpresaOrigen,
    contratista: nombreContratista,
    empresa_contratista: nombreContratista,
    riesgo: s.nivel_de_riesgo || s.nivelRiesgo || s.riesgo || "—",
    actividad: s.actividad || "—",
    is_active: s.is_active,
    vehiculos: listaVehiculos || [],
    computos: listaComputos || [],
    personas: listaPersonas || [],
    revisiones: listaRevisiones || []
  };
}

function esSolicitudActiva(s) {
  if (!s) return false;
  if (s.is_active === 0 || s.is_active === false || s.is_active === "0" || s.is_active === "false") {
    return false;
  }
  if (s.is_active === 1 || s.is_active === true || s.is_active === "1" || s.is_active === "true") {
    return true;
  }
  return false;
}

// ---------------------------------------------------------
// Tarjetas contadoras del dashboard
// ---------------------------------------------------------
function dashboardCards() {
  return {
    solicitudesActivas: [],
    solicitudesTodas: [],
    cargando: true,

    async init() {
      // 1. Usar datos precargados desde el splash inmediatamente para cero parpadeo
      try {
        const pre = sessionStorage.getItem("incarsa_preloaded_solicitudes");
        if (pre) {
          const raw = JSON.parse(pre);
          if (Array.isArray(raw) && raw.length > 0) {
            this.solicitudesTodas = raw.map(normalizarSolicitud).filter(Boolean);
            this.solicitudesActivas = this.solicitudesTodas.filter(s => esSolicitudActiva(s));
            this.cargando = false;
          }
        }
      } catch (e) {}

      // 2. Refrescar en background
      try {
        const res = await fetch(`${API.solicitudes}/getall`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const raw = Array.isArray(data) ? data : (data.datos || []);
        this.solicitudesTodas = raw.map(normalizarSolicitud).filter(Boolean);
        this.solicitudesActivas = this.solicitudesTodas.filter(s => esSolicitudActiva(s));
      } catch (error) {
        if (!this.solicitudesTodas || this.solicitudesTodas.length === 0) {
          console.warn("Backend no disponible, usando datos mock:", error.message);
          const mock = (typeof MOCK_SOLICITUDES !== "undefined" ? MOCK_SOLICITUDES : []).map(normalizarSolicitud).filter(Boolean);
          this.solicitudesTodas = mock;
          this.solicitudesActivas = mock.filter(s => esSolicitudActiva(s));
        }
      } finally {
        this.cargando = false;
      }

      // Escuchar eventos en caliente para refrescar contadores automáticamente
      window.addEventListener("solicitud-actualizada-en-caliente", () => this.recargar());
      window.addEventListener("solicitudes-recargar", () => this.recargar());
    },

    async recargar() {
      try {
        const res = await fetch(`${API.solicitudes}/getall`);
        if (res.ok) {
          const data = await res.json();
          const raw = Array.isArray(data) ? data : (data.datos || []);
          this.solicitudesTodas = raw.map(normalizarSolicitud).filter(Boolean);
          this.solicitudesActivas = this.solicitudesTodas.filter(s => esSolicitudActiva(s));
        }
      } catch (e) {}
    },

    get counts() {
      return {
        enviados: this.solicitudesActivas.filter(s => s && s.estado === "ENVIADO").length,
        enRevision: this.solicitudesActivas.filter(s => s && (s.estado === "EN REVISIÓN" || s.estado === "EN REVISION")).length,
        porAprobar: this.solicitudesActivas.filter(s => s && s.estado === "POR APROBAR").length,
        aprobados: this.solicitudesActivas.filter(s => s && s.estado === "APROBADO").length,
        total: this.solicitudesTodas.length
      };
    }
  };
}

// ---------------------------------------------------------
// Tabla de solicitudes: filtro, paginación, modales
// ---------------------------------------------------------
function solicitudesTable() {
  return {
    solicitudes: [],
    search: "",
    pageSize: 5,
    currentPage: 1,
    sortKey: "id",
    sortAsc: true,
    cargando: true,
    permisosVersion: 0,

    // Modal state
    viewModalOpen: false,
    deleteModalOpen: false,
    selected: null,
    pendingDeleteId: null,

    puedeAccion(mod, acc) {
      // Dependencia reactiva para Alpine.js
      const _v = this.permisosVersion;
      if (typeof window.puedeAccion === 'function') {
        return window.puedeAccion(mod, acc);
      }
      return false;
    },

    puedeEditarSolicitud(s) {
      const _v = this.permisosVersion;
      if (typeof window.puedeEditarSolicitud === 'function') {
        return window.puedeEditarSolicitud(s);
      }
      if (!s) return false;
      const sesion = (typeof getAuthSession === 'function') ? getAuthSession() : null;
      const miRol = (sesion?.rol || this.activeRole || '').trim().toUpperCase();
      if (miRol === 'SUPERADMIN') return true;

      if (!this.puedeAccion('dashboard', 'editar') && !this.puedeAccion('solicitudes', 'editar')) return false;
      const est = String(s.estado || '').trim().toUpperCase();
      return est === 'ENVIADO';
    },

    async init() {
      // Escuchar actualizaciones dinámicas de permisos en vivo
      window.addEventListener("permisos-actualizados", () => {
        this.permisosVersion++;
      });

      // Asegurar permisos sincronizados si aún no están cargados
      if (typeof window.recargarMisPermisos === 'function') {
        window.recargarMisPermisos().then(() => {
          this.permisosVersion++;
        });
      }

      // 1. Usar datos precargados desde el splash inmediatamente
      try {
        const pre = sessionStorage.getItem("incarsa_preloaded_solicitudes");
        if (pre) {
          const raw = JSON.parse(pre);
          if (Array.isArray(raw) && raw.length > 0) {
            const normalizadas = raw.map(normalizarSolicitud).filter(Boolean);
            this.solicitudes = normalizadas.filter(s => esSolicitudActiva(s));
            this.cargando = false;
          }
        }
      } catch (e) {}

      // 2. Refrescar en background
      try {
        const res = await fetch(`${API.solicitudes}/getall`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const raw = Array.isArray(data) ? data : (data.datos || []);
        const normalizadas = raw.map(normalizarSolicitud).filter(Boolean);
        this.solicitudes = normalizadas.filter(s => esSolicitudActiva(s));
      } catch (error) {
        if (!this.solicitudes || this.solicitudes.length === 0) {
          console.warn("Backend no disponible, usando datos mock:", error.message);
          const mock = (typeof MOCK_SOLICITUDES !== "undefined" ? MOCK_SOLICITUDES : []).map(normalizarSolicitud).filter(Boolean);
          this.solicitudes = mock.filter(s => esSolicitudActiva(s));
        }
      } finally {
        this.cargando = false;
      }

      // Escuchar eventos en caliente para refrescar la tabla automáticamente
      window.addEventListener("solicitud-actualizada-en-caliente", () => this.recargar());
      window.addEventListener("solicitudes-recargar", () => this.recargar());
    },

    async recargar() {
      try {
        const res = await fetch(`${API.solicitudes}/getall`);
        if (res.ok) {
          const data = await res.json();
          const raw = Array.isArray(data) ? data : (data.datos || []);
          const normalizadas = raw.map(normalizarSolicitud).filter(Boolean);
          this.solicitudes = normalizadas.filter(s => esSolicitudActiva(s));
        }
      } catch (e) {}
    },

    estadoClass(estado) {
      const map = {
        "ENVIADO": "status-enviado",
        "EN REVISIÓN": "status-revision",
        "EN REVISION": "status-revision",
        "DEVUELTO PARA CORRECCIÓN": "status-devuelto",
        "DEVUELTO": "status-devuelto",
        "POR APROBAR": "status-aprobar",
        "APROBADO": "status-aprobado",
        "PRE-APROBADO": "status-aprobado",
        "RECHAZADO": "status-rechazado"
      };
      return map[(estado || "").toUpperCase()] || "status-enviado";
    },

    get filtered() {
      const term = this.search.trim().toLowerCase();
      let rows = this.solicitudes;
      if (term) {
        rows = rows.filter(s =>
          (s.nombre_empresa || "").toLowerCase().includes(term) ||
          (s.nombre_emContratista || "").toLowerCase().includes(term) ||
          (s.planta || "").toLowerCase().includes(term) ||
          (s.fecha_ingreso || "").toLowerCase().includes(term) ||
          (s.fecha_salida || "").toLowerCase().includes(term) ||
          (s.estado || "").toLowerCase().includes(term) ||
          (s.diligenciador || "").toLowerCase().includes(term) ||
          (s.riesgo || "").toLowerCase().includes(term) ||
          (s.codigo || "").toLowerCase().includes(term)
        );
      }
      return rows;
    },

    get totalPages() {
      return Math.max(1, Math.ceil(this.filtered.length / this.pageSize));
    },

    get paginated() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.filtered.slice(start, start + this.pageSize);
    },

    goToPage(n) {
      if (n < 1 || n > this.totalPages) return;
      this.currentPage = n;
    },

    resetPage() {
      this.currentPage = 1;
    },

    async openView(solicitud) {
      this.selected = normalizarSolicitud(solicitud);
      this.viewModalOpen = true;

      try {
        const res = await fetch(`${API.solicitudes}/${solicitud.id}`);
        if (res.ok) {
          const dataLive = await res.json();
          if (dataLive && (dataLive.id || dataLive.codigo)) {
            this.selected = normalizarSolicitud({
              ...solicitud,
              ...dataLive
            });
            const idx = this.solicitudes.findIndex(s => String(s.id) === String(solicitud.id));
            if (idx > -1) {
              this.solicitudes[idx] = { ...this.solicitudes[idx], ...this.selected };
            }
            // Refrescar conteo de notificaciones ya que se marcó como leída
            this.cargarNotificaciones();
            localStorage.setItem("incarsa_notificaciones_reload", Date.now().toString());
          }
        }
      } catch (err) {
        console.warn("Aviso al refrescar solicitud en dashboard:", err);
      }
    },

    closeView() {
      this.viewModalOpen = false;
      this.selected = null;
    },

    editSolicitud(solicitud) {
      const code = (solicitud && (solicitud.codigo || solicitud.id)) || '';
      window.location.href = `/solicitudes/editar/${code}`;
    },

    confirmDelete(solicitud) {
      this.pendingDeleteId = solicitud.id;
      this.deleteModalOpen = true;
    },

    cancelDelete() {
      this.pendingDeleteId = null;
      this.deleteModalOpen = false;
    },

    executeDelete() {
      this.solicitudes = this.solicitudes.filter(s => s.id !== this.pendingDeleteId);
      this.deleteModalOpen = false;
      this.pendingDeleteId = null;
      if (this.currentPage > this.totalPages) this.currentPage = this.totalPages;
    }
  };
}

// ---------------------------------------------------------
// Sección de usuarios: pestañas por rol + modal de detalle
// ---------------------------------------------------------
function usersSection() {
  return {
    roles: ["SST", "GESCO", "SCR", "GESTIÓN DOCUMENTAL"],
    usuarios: [],
    solicitudes: [],
    activeTab: "SST",
    modalOpen: false,
    selectedUser: null,
    cargando: true,

    tieneRol(...roles) {
      if (typeof window.tieneRol === "function") {
        return window.tieneRol(...roles);
      }
      return false;
    },

    get esAdminOSuperAdmin() {
      return this.tieneRol('ADMINISTRADOR', 'SUPERADMIN');
    },

    async init() {
      // Restringir exclusivamente a ADMINISTRADOR y SUPERADMIN
      if (!this.esAdminOSuperAdmin) {
        this.cargando = false;
        return;
      }

      // 1. Usar datos precargados desde el splash
      try {
        const preUsers = sessionStorage.getItem("incarsa_preloaded_usuarios");
        if (preUsers) {
          const uRaw = JSON.parse(preUsers);
          if (Array.isArray(uRaw) && uRaw.length > 0) {
            this.usuarios = uRaw;
            this.cargando = false;
          }
        }
        const preSols = sessionStorage.getItem("incarsa_preloaded_solicitudes");
        if (preSols) {
          const sRaw = JSON.parse(preSols);
          if (Array.isArray(sRaw) && sRaw.length > 0) {
            this.solicitudes = sRaw.map(normalizarSolicitud);
          }
        }
      } catch (e) {}

      // 2. Refrescar usuarios desde backend
      try {
        const response = await fetch(`${API.usuarios}/getall`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        this.usuarios = Array.isArray(data) ? data : (data.datos || []);
      } catch (error) {
        if (!this.usuarios || this.usuarios.length === 0) {
          console.warn("Backend no disponible, usando datos mock de usuarios:", error.message);
        }
      } finally {
        this.cargando = false;
      }

      // Cargar solicitudes activas para la sección de gestores
      try {
        const res = await fetch(`${API.solicitudes}/getall?active=true`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const raw = Array.isArray(data) ? data : (data.datos_solicitudes || data.datos || []);
        this.solicitudes = raw.map(normalizarSolicitud);
      } catch {
        if (!this.solicitudes || this.solicitudes.length === 0) {
          const mock = typeof MOCK_SOLICITUDES !== "undefined" ? MOCK_SOLICITUDES : [];
          this.solicitudes = mock.map(normalizarSolicitud);
        }
      }
    },

    get usuariosFiltrados() {
      const normalizar = (txt) =>
        (txt || "")
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .trim();

      const tabActiva = normalizar(this.activeTab);

      return this.usuarios.filter(u => {
        const rolUsuario = normalizar(u.rol || u.nombre_rol || "");

        if (!rolUsuario) {
          // Fallback por id_rol si no hay string de rol
          const rolesIdMap = { 2: "gestor de documentacion", 3: "sst", 4: "gesco", 5: "scr" };
          return normalizar(rolesIdMap[u.id_rol] || "") === tabActiva;
        }

        return rolUsuario === tabActiva;
      });
    },

    getNombreCompleto(user) {
      if (user.nombre_completo) return user.nombre_completo;
      return `${user.nombres || ""} ${user.apellidos || ""}`.trim();
    },

    getIniciales(val) {
      const nombre = typeof val === "object" && val !== null ? this.getNombreCompleto(val) : val;
      if (!nombre || typeof nombre !== "string") return "";
      const partes = nombre.trim().split(/\s+/);
      if (partes.length === 1) return partes[0].substring(0, 2).toUpperCase();
      return (partes[0][0] + partes[1][0]).toUpperCase();
    },

    solicitudesDe(nombreCompleto) {
      return this.solicitudes.filter(
        s => (s.diligenciador || "").toLowerCase() === (nombreCompleto || "").toLowerCase()
      );
    },

    openUser(user) {
      this.selectedUser = user;
      this.modalOpen = true;
    },

    closeUser() {
      this.modalOpen = false;
      this.selectedUser = null;
    }
  };
}

// ---------------------------------------------------------
// Gráficos: torta de solicitudes por mes y usuarios por rol
// ---------------------------------------------------------
let chartMonthsInstance = null;
let chartRolesInstance = null;

function getChartThemeConfig() {
  const isDark = document.documentElement.classList.contains('dark') || localStorage.getItem('darkMode') === 'true';
  
  // Paleta neón luminosa y armoniosa para modo oscuro
  const darkPalette = [
    "#00f0ff", // Cian Neón Eléctrico (INCARSA)
    "#c084fc", // Púrpura / Violeta Neón (MILPA)
    "#00ff9d", // Verde Esmeralda Neón (UNIMINAS)
    "#ffb700", // Ámbar / Oro Neón (CARBOINSA)
    "#ff2a55", // Carmesí / Rojo Neón
    "#38bdf8", // Azul Cielo Neón
    "#f43f5e", // Rosa Neón
    "#a855f7"  // Púrpura Eléctrico
  ];

  // Paleta corporativa sólida para modo claro
  const lightPalette = [
    "#109ea9ff", // Azul Teal Corporativo
    "#a24ff0ff", // Púrpura
    "#16c857ff", // Verde Esmeralda
    "#f18811ff", // Ámbar
    "#e72626ff", // Rojo Carmesí
    "#0791d6ff", // Azul Cielo
    "#f97316"  // Naranja
  ];

  return {
    isDark,
    palette: isDark ? darkPalette : lightPalette,
    borderColor: isDark ? "#1e1e1e" : "#ffffff",
    borderWidth: 2.5,
    legendColor: isDark ? "#cbd5e1" : "#475569",
    tooltipBg: isDark ? "rgba(18, 18, 22, 0.95)" : "#0f172a",
    tooltipBorder: isDark ? "rgba(255, 255, 255, 0.15)" : "#334155",
    tooltipTitle: "#ffffff",
    tooltipBody: isDark ? "#cbd5e1" : "#f1f5f9"
  };
}

function syncDashboardChartsTheme() {
  const cfg = getChartThemeConfig();
  [chartMonthsInstance, chartRolesInstance].forEach(chart => {
    if (chart) {
      chart.data.datasets.forEach(ds => {
        ds.backgroundColor = cfg.palette;
        ds.borderColor = cfg.borderColor;
        ds.borderWidth = cfg.borderWidth;
      });
      if (chart.options.plugins) {
        if (chart.options.plugins.legend && chart.options.plugins.legend.labels) {
          chart.options.plugins.legend.labels.color = cfg.legendColor;
        }
        if (chart.options.plugins.tooltip) {
          chart.options.plugins.tooltip.backgroundColor = cfg.tooltipBg;
          chart.options.plugins.tooltip.borderColor = cfg.tooltipBorder;
          chart.options.plugins.tooltip.titleColor = cfg.tooltipTitle;
          chart.options.plugins.tooltip.bodyColor = cfg.tooltipBody;
        }
      }
      chart.update();
    }
  });
}

function initDashboardCharts() {
  const esAdminOSuper = (typeof window.tieneRol === "function") 
    ? window.tieneRol('ADMINISTRADOR', 'SUPERADMIN') 
    : false;

  // Si el usuario no es Administrador ni SuperAdmin, no cargar ni renderizar las gráficas
  if (!esAdminOSuper) {
    return;
  }

  const cfg = getChartThemeConfig();

  async function graficoMeses() {
    try {
      const MonthCount = await fetch(`${API.solicitudes}/fechasCount`);
      if (!MonthCount.ok) throw new Error("Error HTTP: " + MonthCount.status);

      const dataF = await MonthCount.json();
      const mes = dataF.map(df => df.month);
      const total = dataF.map(df => df.total);

      const monthCtx = document.getElementById("chartMonths");
      if (monthCtx && dataF.length > 0) {
        if (chartMonthsInstance) {
          chartMonthsInstance.destroy();
        }
        chartMonthsInstance = new Chart(monthCtx, {
          type: "pie",
          data: {
            labels: mes,
            datasets: [{
              data: total,
              backgroundColor: cfg.palette,
              borderColor: cfg.borderColor,
              borderWidth: cfg.borderWidth
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
              animateScale: true,
              animateRotate: true,
              duration: 1200,
              easing: 'easeInOutQuad',
            },
            hover: {
              animationDuration: 250
            },
            plugins: {
              legend: { 
                position: "bottom", 
                labels: { 
                  boxWidth: 12, 
                  font: { size: 11.5, weight: '600' },
                  color: cfg.legendColor,
                  padding: 14
                } 
              },
              tooltip: {
                backgroundColor: cfg.tooltipBg,
                borderColor: cfg.tooltipBorder,
                borderWidth: 1,
                titleColor: cfg.tooltipTitle,
                bodyColor: cfg.tooltipBody,
                padding: 10,
                cornerRadius: 8
              }
            }
          }
        });
      }
    } catch (error) {
      console.error('❌ Error al cargar la gráfica de meses:', error);
    }
  }

  async function graficoRoles() {
    try {
      const Count = await fetch(`${API.usuarios}/usuarios/conteo-por-rol`);
      if (!Count.ok) throw new Error("Error HTTP: " + Count.status);

      const rawDatas = await Count.json();
      const datas = Array.isArray(rawDatas)
        ? rawDatas.filter(dat => String(dat.rol || '').trim().toUpperCase() !== 'SUPERADMIN')
        : [];
      const ticket = datas.map(dat => dat.rol);
      const value = datas.map(dat => dat.total);

      const rolesCtx = document.getElementById("chartRoles");
      if (rolesCtx && datas.length > 0) {
        if (chartRolesInstance) {
          chartRolesInstance.destroy();
        }
        chartRolesInstance = new Chart(rolesCtx, {
          type: "pie",
          data: {
            labels: ticket,
            datasets: [{
              data: value,
              backgroundColor: cfg.palette,
              borderColor: cfg.borderColor,
              borderWidth: cfg.borderWidth
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
              animateScale: true,
              animateRotate: true,
              duration: 1200,
              easing: 'easeInOutQuad',
            },
            hover: {
              animationDuration: 250
            },
            plugins: {
              legend: { 
                position: "bottom", 
                labels: { 
                  boxWidth: 12, 
                  font: { size: 11.5, weight: '600' },
                  color: cfg.legendColor,
                  padding: 14
                } 
              },
              tooltip: {
                backgroundColor: cfg.tooltipBg,
                borderColor: cfg.tooltipBorder,
                borderWidth: 1,
                titleColor: cfg.tooltipTitle,
                bodyColor: cfg.tooltipBody,
                padding: 10,
                cornerRadius: 8
              }
            }
          }
        });
      }
    } catch (error) {
      console.error('❌ Error al cargar la gráfica de roles:', error);
    }
  }

  graficoMeses();
  graficoRoles();

  // Escuchar cambios de tema en el elemento raíz <html> para actualización reactiva en tiempo real
  if (!window._chartThemeObserverAttached) {
    window._chartThemeObserverAttached = true;
    const observer = new MutationObserver(mutations => {
      for (const mutation of mutations) {
        if (mutation.attributeName === 'class') {
          syncDashboardChartsTheme();
          break;
        }
      }
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
  }
}

document.addEventListener("DOMContentLoaded", initDashboardCharts);

