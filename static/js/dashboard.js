/**
 * dashboard.js — Lógica de Tablas, Filtros y Modales de Solicitudes y Usuarios
 * (La gestión del Shell general y notificaciones se encuentra centralizada en /static/js/app-shell.js)
 */


// ---------------------------------------------------------
// Helper: normaliza solicitudes del backend al formato estándar
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
        console.warn("Aviso al consultar solicitudes para contadores:", error.message);
        if (!this.solicitudesTodas) this.solicitudesTodas = [];
        if (!this.solicitudesActivas) this.solicitudesActivas = [];
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
        console.warn("Aviso al consultar solicitudes activas de la tabla:", error.message);
        if (!this.solicitudes) this.solicitudes = [];
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
        console.warn("Aviso al consultar usuarios del sistema:", error.message);
        if (!this.usuarios) this.usuarios = [];
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
      } catch (e) {
        if (!this.solicitudes) this.solicitudes = [];
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



