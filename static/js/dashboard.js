
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
    notifications: [
      { id: 1, texto: "SOL-2026-0145 pasó a Por Aprobar", tiempo: "Hace 12 min" },
      { id: 2, texto: "SOL-2026-0146 fue rechazada por SCR", tiempo: "Hace 1 h" },
      { id: 3, texto: "Nuevo usuario SST registrado", tiempo: "Hace 3 h" }
    ],

    init() {
      // Aplicar dark mode guardado
      document.documentElement.classList.toggle('dark', this.darkMode);

      // Restaurar el nombre y rol del usuario desde la sesión si existe
      const sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || "null");
      if (sesion) {
        this.activeRole = sesion.rol || this.activeRole;
        this._userName = sesion.nombre || "Laura Gómez";
        this._userInitials = (this._userName.split(" ").map(p => p[0]).join("")).substring(0, 2).toUpperCase();
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
      window.location.href = `solicitudes-formulario.html?edit=${solicitud.id}`;
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
function initDashboardCharts() {

  const inkPalette = [
    "#f52f60ff", // Neon Pink / Magenta
    "#ca4820ff", // Electric Orange
    "#f7c940ff", // Vivid Amber / Yellow
    "#02f07dff", // Bright Lime Green
    "#00B0FF", // Electric Sky Blue
    "#7C4DFF", // Vivid Purple / Indigo
    "#FF1744", // Crimson Red
    "#044e57ff", // Cyan / Aqua
    "#abe206ff", // Bright Acid Green
    "#D500F9", // Neon Purple
    "#FF9100", // Bright Coral / Gold
    "#536cfaff"
  ];

  const Rols = ["#3B82F6", "#06c283ff", "#F59E0B", "#e8fc75ff", "#FF1744"]

  async function graficoMeses() {

    try {
      const MonthCount = await fetch(`${API.solicitudes}/fechasCount`);

      if (!MonthCount.ok) {
        throw new Error("Error HTTP: " + MonthCount.status);
      }

      dataF = await MonthCount.json();

      const mes = dataF.map(df => df.month);
      const total = dataF.map(df => df.total);

      const monthCtx = document.getElementById("chartMonths");

      if (monthCtx && dataF.length > 0) {
        new Chart(monthCtx, {
          type: "pie",
          data: {
            labels: mes,
            datasets: [{
              data: total,
              backgroundColor: Rols,
              borderColor: "#ffffff",
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
              animateScale: true,
              animateRotate: true,
              duration: 2000,
              easing: 'easeInOutQuad',
            },
            hover: {
              animationDuration: 300
            },

            plugins: {
              legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 11 } } }
            }
          }

        });
      }
    } catch (error) {
      console.error('❌ Error al cargar la gráfica de meses:', error);
    }
  }
  graficoMeses();

  async function graficoRoles() {

    try {
      const Count = await fetch(`${API.usuarios}/usuarios/conteo-por-rol`);

      if (!Count.ok) {
        throw new Error("Error HTTP: " + Count.status);
      }

      const datas = await Count.json();

      const ticket = datas.map(dat => dat.rol);
      const value = datas.map(dat => dat.total);

      const rolesCtx = document.getElementById("chartRoles");

      if (rolesCtx && datas.length > 0) {
        new Chart(rolesCtx, {
          type: "pie",
          data: {
            labels: ticket,
            datasets: [{
              data: value,
              backgroundColor: Rols,
              borderColor: "#ffffff",
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
              animateScale: true,
              animateRotate: true,
              duration: 2000,
              easing: 'easeInOutQuad',
            },

            hover: {
              animationDuration: 300
            },

            plugins: {
              legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 11 } } }
            }
          }
        });
      }
    } catch (error) {
      console.error('❌ Error al cargar la gráfica de roles:', error);
    }
  }
  graficoRoles();
}


document.addEventListener("DOMContentLoaded", initDashboardCharts);
