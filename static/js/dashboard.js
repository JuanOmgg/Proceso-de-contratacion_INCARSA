/**
 * dashboard.js — Lógica de Tablas, Filtros y Modales de Solicitudes y Usuarios
 * (La gestión del Shell general y notificaciones se encuentra centralizada en /static/js/app-shell.js)
 */


// Helpers centralizados: normalizarSolicitud, generarCodigoAlfanumerico y formatearFechaCorta
// se encuentran definidos y expuestos globalmente en /static/js/config.js


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

function esSolicitudParaGestionDoc(s, sesion) {
  if (!sesion && typeof getAuthSession === 'function') {
    sesion = getAuthSession();
  }
  if (!sesion) return true;

  const rolTexto = String(sesion.rol || sesion.nombre_rol || "").toUpperCase();
  const rolId = Number(sesion.id_rol || 0);
  const esGestionDoc = rolTexto.includes("SOLICITANTE") || rolId === 5;

  if (!esGestionDoc) return true;

  const myId = Number(sesion.id || 0);
  const solDiligenciadoPor = Number(s.diligenciado_por || s.id_diligenciador || 0);

  if (myId && solDiligenciadoPor && myId === solDiligenciadoPor) {
    return true;
  }

  // Coincidencia secundaria por nombre del diligenciador por si el id no viniese enlazado
  const nombreUsuario = String(sesion.nombre || sesion.nombre_completo || `${sesion.nombres || ''} ${sesion.apellidos || ''}`).trim().toLowerCase();
  const diligenciadorSol = String(s.diligenciador || "").trim().toLowerCase();
  if (nombreUsuario && diligenciadorSol && (nombreUsuario.includes(diligenciadorSol) || diligenciadorSol.includes(nombreUsuario))) {
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
      const sesion = (typeof getAuthSession === 'function') ? getAuthSession() : null;
      // 1. Usar datos precargados desde el splash inmediatamente para cero parpadeo
      try {
        const pre = sessionStorage.getItem("incarsa_preloaded_solicitudes");
        if (pre) {
          const raw = JSON.parse(pre);
          if (Array.isArray(raw) && raw.length > 0) {
            this.solicitudesTodas = raw.map(normalizarSolicitud).filter(Boolean).filter(s => esSolicitudParaGestionDoc(s, sesion));
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
        this.solicitudesTodas = raw.map(normalizarSolicitud).filter(Boolean).filter(s => esSolicitudParaGestionDoc(s, sesion));
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
        const sesion = (typeof getAuthSession === 'function') ? getAuthSession() : null;
        const res = await fetch(`${API.solicitudes}/getall`);
        if (res.ok) {
          const data = await res.json();
          const raw = Array.isArray(data) ? data : (data.datos || []);
          this.solicitudesTodas = raw.map(normalizarSolicitud).filter(Boolean).filter(s => esSolicitudParaGestionDoc(s, sesion));
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
    showDeleteModal: false,
    qrModalOpen: false,
    copiadoToast: false,
    selected: null,
    selectedQr: null,
    pendingDeleteId: null,
    solicitudAEliminar: null,

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

      const sesion = (typeof getAuthSession === 'function') ? getAuthSession() : null;
      // 1. Usar datos precargados desde el splash inmediatamente
      try {
        const pre = sessionStorage.getItem("incarsa_preloaded_solicitudes");
        if (pre) {
          const raw = JSON.parse(pre);
          if (Array.isArray(raw) && raw.length > 0) {
            const normalizadas = raw.map(normalizarSolicitud).filter(Boolean);
            this.solicitudes = normalizadas.filter(s => esSolicitudActiva(s) && esSolicitudParaGestionDoc(s, sesion));
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
        this.solicitudes = normalizadas.filter(s => esSolicitudActiva(s) && esSolicitudParaGestionDoc(s, sesion));
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
        const sesion = (typeof getAuthSession === 'function') ? getAuthSession() : null;
        const res = await fetch(`${API.solicitudes}/getall`);
        if (res.ok) {
          const data = await res.json();
          const raw = Array.isArray(data) ? data : (data.datos || []);
          const normalizadas = raw.map(normalizarSolicitud).filter(Boolean);
          this.solicitudes = normalizadas.filter(s => esSolicitudActiva(s) && esSolicitudParaGestionDoc(s, sesion));
        }
      } catch (e) {}
    },

    estadoClass(estado) {
      return (typeof window.estadoClass === 'function') ? window.estadoClass(estado) : 'status-enviado';
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

    copiarTexto(texto) {
      if (!texto) return;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(texto).then(() => {
          this.copiadoToast = true;
          setTimeout(() => { this.copiadoToast = false; }, 2000);
        }).catch(() => {});
      } else {
        const input = document.createElement('textarea');
        input.value = texto;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        this.copiadoToast = true;
        setTimeout(() => { this.copiadoToast = false; }, 2000);
      }
    },

    openQrModal(solicitud) {
      if (!solicitud) return;
      this.selectedQr = solicitud;
      this.qrModalOpen = true;
    },

    cerrarQrModal() {
      this.qrModalOpen = false;
      this.selectedQr = null;
    },

    descargarQr() {
      if (!this.selectedQr) return;
      const codigo = this.selectedQr.codigo || ('RAD-' + this.selectedQr.id);
      const a = document.createElement('a');
      a.href = `/api/v1/solicitudes/${encodeURIComponent(codigo)}/qr`;
      a.download = `QR-${codigo}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    },

    async copiarEnlaceQr() {
      if (!this.selectedQr) return;
      const codigo = this.selectedQr.codigo || ('RAD-' + this.selectedQr.id);
      const url = `${window.location.origin}/verificar/${encodeURIComponent(codigo)}`;
      try {
        await navigator.clipboard.writeText(url);
        this.copiadoToast = true;
        setTimeout(() => (this.copiadoToast = false), 2500);
      } catch (e) {
        const ta = document.createElement('textarea');
        ta.value = url;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        this.copiadoToast = true;
        setTimeout(() => (this.copiadoToast = false), 2500);
      }
    },

    editSolicitud(solicitud) {
      const code = (solicitud && (solicitud.codigo || solicitud.id)) || '';
      window.location.href = `/solicitudes/editar/${code}`;
    },

    confirmDelete(solicitud) {
      this.pendingDeleteId = solicitud?.id || null;
      this.solicitudAEliminar = solicitud;
      this.deleteModalOpen = true;
      this.showDeleteModal = true;
    },

    confirmarEliminar(solicitud) {
      this.confirmDelete(solicitud);
    },

    cancelDelete() {
      this.pendingDeleteId = null;
      this.solicitudAEliminar = null;
      this.deleteModalOpen = false;
      this.showDeleteModal = false;
    },

    cancelarEliminar() {
      this.cancelDelete();
    },

    async executeDelete() {
      if (!this.pendingDeleteId && !this.solicitudAEliminar) return;
      const id = this.pendingDeleteId || this.solicitudAEliminar?.id;
      this.solicitudes = this.solicitudes.filter(s => s.id !== id);
      this.deleteModalOpen = false;
      this.showDeleteModal = false;
      this.pendingDeleteId = null;
      this.solicitudAEliminar = null;
      if (this.currentPage > this.totalPages) this.currentPage = Math.max(1, this.totalPages);
      try {
        await fetch(`${API.solicitudes}/${id}`, { method: "DELETE" });
      } catch (e) {
        console.warn("No se pudo eliminar en backend:", e);
      }
    },

    eliminarSolicitud() {
      return this.executeDelete();
    }
  };
}

// ---------------------------------------------------------
// Sección de usuarios: pestañas por rol + modal de detalle
// ---------------------------------------------------------
function usersSection() {
  return {
    roles: ["SST", "GESCO", "SCR", "SOLICITANTE"],
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



