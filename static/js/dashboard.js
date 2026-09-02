
// ---------------------------------------------------------
// Shell general: sidebar, navbar, dropdown de perfil
// ---------------------------------------------------------
function appShell() {
  return {
    sidebarCollapsed: false,
    sidebarOpenMobile: false,
    profileMenuOpen: false,
    notificationsOpen: false,
    activeRole: "GESTOR DE DOCUMENTACIÓN",
    openModules: { procesamiento: false, formularios: false, tablas: false },
    darkMode: localStorage.getItem('darkMode') === 'true',
    userId: 1,
    roleId: 2,
    notifications: [],
    unreadNotificationsCount: 0,

    formatearTiempoRelativo(fechaStr) {
      if (typeof formatearTiempoRelativo === "function") {
        return formatearTiempoRelativo(fechaStr);
      }
      return fechaStr || "";
    },

    init() {
      // Aplicar dark mode guardado
      document.documentElement.classList.toggle('dark', this.darkMode);

      // Restaurar el nombre y rol del usuario desde la sesión si existe
      const sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || "null");
      if (sesion) {
        this.activeRole = sesion.rol || this.activeRole;
        this.userId = sesion.id || this.userId;
        this.roleId = sesion.id_rol || this.roleId;
        this._userName = sesion.nombre || "Laura Gómez";
        this._userInitials = (this._userName.split(" ").map(p => p[0]).join("")).substring(0, 2).toUpperCase();
      }

      this.cargarNotificaciones();
      setInterval(() => this.cargarNotificaciones(), 35000);
    },

    async cargarNotificaciones() {
      try {
        const notifUrl = (typeof API !== "undefined" && API.notificaciones) 
          ? API.notificaciones 
          : "http://127.0.0.1:8000/api/v1/notificaciones";
        const params = new URLSearchParams();
        if (this.userId) params.append("id_usuario", this.userId);
        if (this.roleId) params.append("id_rol", this.roleId);
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
            : "http://127.0.0.1:8000/api/v1/notificaciones";
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

    async marcarTodasNotificacionesLeidas() {
      try {
        const notifUrl = (typeof API !== "undefined" && API.notificaciones) 
          ? API.notificaciones 
          : "http://127.0.0.1:8000/api/v1/notificaciones";
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
      const [id, placa, marca, modelo, serie] = v.split('|||');
      return { id, placa, marca, modelo, serie };
    });
  } else if (Array.isArray(s.vehiculos)) {
    listaVehiculos = s.vehiculos;
  }
  
  let listaPersonas = [];
  if (typeof s.personas === 'string') {
    try {
      listaPersonas = JSON.parse(s.personas);
    } catch (e) {
      listaPersonas = [];
    }
  } else if (Array.isArray(s.personas)) {
    listaPersonas = s.personas;
  }

  const nombreEmpresaOrigen = s.nombre_empresa || s.empresa_origen || s.empresaOrigen || "INCARSA";
  const nombreContratista = s.nombre_emContratista || s.empresa_contratista || s.contratista || "—";
  const diligenciadorNombre = s.diligenciador || s.diligenciadoPor || "Administrador";
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
    personas: listaPersonas
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
      try {
        const res = await fetch(`${API.solicitudes}/getall`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const raw = Array.isArray(data) ? data : (data.datos || []);
        this.solicitudesTodas = raw.map(normalizarSolicitud).filter(Boolean);
        this.solicitudesActivas = this.solicitudesTodas.filter(s => esSolicitudActiva(s));
      } catch (error) {
        console.warn("Backend no disponible, usando datos mock:", error.message);
        const mock = (typeof MOCK_SOLICITUDES !== "undefined" ? MOCK_SOLICITUDES : []).map(normalizarSolicitud).filter(Boolean);
        this.solicitudesTodas = mock;
        this.solicitudesActivas = mock.filter(s => esSolicitudActiva(s));
      } finally {
        this.cargando = false;
      }
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

    // Modal state
    viewModalOpen: false,
    deleteModalOpen: false,
    selected: null,
    pendingDeleteId: null,

    async init() {
      try {
        const res = await fetch(`${API.solicitudes}/getall`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const raw = Array.isArray(data) ? data : (data.datos || []);
        const normalizadas = raw.map(normalizarSolicitud).filter(Boolean);
        // En el dashboard se muestran exclusivamente las solicitudes activas
        this.solicitudes = normalizadas.filter(s => esSolicitudActiva(s));
      } catch (error) {
        console.warn("Backend no disponible, usando datos mock:", error.message);
        const mock = (typeof MOCK_SOLICITUDES !== "undefined" ? MOCK_SOLICITUDES : []).map(normalizarSolicitud).filter(Boolean);
        this.solicitudes = mock.filter(s => esSolicitudActiva(s));
      } finally {
        this.cargando = false;
      }
    },

    estadoClass(estado) {
      const map = {
        "ENVIADO": "status-enviado",
        "EN REVISIÓN": "status-revision",
        "EN REVISION": "status-revision",
        "POR APROBAR": "status-aprobar",
        "APROBADO": "status-aprobado",
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
      this.selected = solicitud;
      this.viewModalOpen = true;

      try {
        const res = await fetch(`${API.solicitudes}/${solicitud.id}`);
        if (res.ok) {
          const dataLive = await res.json();
          if (dataLive && (dataLive.id || dataLive.codigo)) {
            let listaPersonas = dataLive.ingresantes || dataLive.personas || solicitud.personas || [];
            try {
              const storageKey = `incarsa_solicitud_${solicitud.id}_personas`;
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

            this.selected = {
              ...solicitud,
              ...dataLive,
              fecha_ingreso: formatearFechaCorta(dataLive.fecha_ingreso || dataLive.fecha_inicio || solicitud.fecha_ingreso),
              fecha_salida: formatearFechaCorta(dataLive.fecha_salida || dataLive.fecha_fin || solicitud.fecha_salida),
              fechaIngreso: formatearFechaCorta(dataLive.fecha_ingreso || dataLive.fecha_inicio || solicitud.fechaIngreso),
              fechaSalida: formatearFechaCorta(dataLive.fecha_salida || dataLive.fecha_fin || solicitud.fechaSalida),
              fecha_creacion: formatearFechaHoraEspanol(dataLive.fecha_creacion || solicitud.fecha_creacion),
              estado: (dataLive.estado || solicitud.estado || "ENVIADO").toUpperCase(),
              codigo: dataLive.codigo || solicitud.codigo,
              observaciones: dataLive.observaciones || solicitud.observaciones,
              personas: listaPersonas
            };
            const idx = this.solicitudes.findIndex(s => String(s.id) === String(solicitud.id));
            if (idx > -1) {
              this.solicitudes[idx] = { ...this.solicitudes[idx], ...this.selected };
            }
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

    async init() {
      try {
        const response = await fetch(`${API.usuarios}/getall`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        this.usuarios = Array.isArray(data) ? data : (data.datos || []);
      } catch (error) {
        console.warn("Backend no disponible, usando datos mock de usuarios:", error.message);
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
        const mock = typeof MOCK_SOLICITUDES !== "undefined" ? MOCK_SOLICITUDES : [];
        this.solicitudes = mock.map(normalizarSolicitud);
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

      const datas = await Count.json();
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

