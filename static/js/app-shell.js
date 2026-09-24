/**
 * app-shell.js — Componente Global del Shell de la Aplicación (INCARSA)
 * 
 * Centraliza la lógica transversal del Layout para todas las páginas del sistema:
 * - Control del Sidebar (colapsado en desktop y drawer en móviles).
 * - Menús de perfil, datos del usuario activo y cierre de sesión.
 * - Conmutador reactivo de Tema Oscuro (Dark / Light Mode).
 * - Sistema integral de Notificaciones en el Topbar y Modal Completo:
 *     - Listado, búsqueda, filtros por categoría (todas, no leídas, info, alertas).
 *     - Paginación dinámica y sincronización SSE en tiempo real.
 *     - Marcado de lectura individual o masivo.
 *     - Acciones directas de pre-aprobación y revisión de expedientes.
 * - Verificación de permisos y roles del usuario activo.
 * - Alertas y advertencias de estado de mantenimiento.
 * 
 * Expone:
 *   window.appShell()
 *   window.appShellStub() (alias para compatibilidad total con plantillas existentes)
 */

(function () {
  'use strict';

  function appShell() {
    let sesion = null;
    if (typeof getAuthSession === 'function') {
      sesion = getAuthSession();
    } else {
      try {
        sesion = JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || 'null');
      } catch (e) {}
    }

    const nombreUsuario = sesion
      ? (sesion.nombre || sesion.nombres || `${sesion.nombres || ''} ${sesion.apellidos || ''}`.trim() || 'Usuario')
      : 'Administrador Sistema';

    const iniciales = nombreUsuario
      .split(' ')
      .filter(Boolean)
      .map(p => p[0])
      .join('')
      .substring(0, 2)
      .toUpperCase() || 'AD';

    const userId = sesion?.id || 1;
    const roleId = sesion?.id_rol || 2;
    const rolNombre = sesion?.rol || 'ADMINISTRADOR';

    // Sincronización de atributos de rol para estilos exclusivos
    if (String(rolNombre || '').trim().toUpperCase() === 'SUPERADMIN') {
      document.documentElement.setAttribute('data-role', 'SUPERADMIN');
      document.documentElement.classList.add('role-superadmin');
    } else {
      document.documentElement.removeAttribute('data-role');
      document.documentElement.classList.remove('role-superadmin');
    }

    return {
      // ----------------------------------------------------------------------
      // 1. ESTADO DE NAVEGACIÓN Y SIDEBAR
      // ----------------------------------------------------------------------
      sidebarCollapsed: false,
      sidebarOpenMobile: false,
      profileMenuOpen: false,
      openModules: { formularios: false, tablas: true, procesamiento: false },

      // ----------------------------------------------------------------------
      // 2. SESIÓN Y PERFIL DEL USUARIO
      // ----------------------------------------------------------------------
      userId: userId,
      roleId: roleId,
      activeRole: rolNombre,
      _userName: nombreUsuario,
      _userInitials: iniciales,

      get userDisplayName() {
        return this._userName;
      },

      get userInitials() {
        return this._userInitials;
      },

      // ----------------------------------------------------------------------
      // 3. TEMA OSCURO / CLARO
      // ----------------------------------------------------------------------
      darkMode: localStorage.getItem('darkMode') === 'true',

      toggleDarkMode() {
        this.darkMode = !this.darkMode;
        document.documentElement.classList.toggle('dark', this.darkMode);
        localStorage.setItem('darkMode', this.darkMode);
      },

      // ----------------------------------------------------------------------
      // 4. NOTIFICACIONES
      // ----------------------------------------------------------------------
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
        // Revisar precarga de splash en sessionStorage
        try {
          const preloadedNotifs = sessionStorage.getItem('incarsa_preloaded_notificaciones');
          if (preloadedNotifs) {
            const d = JSON.parse(preloadedNotifs);
            if (d && (d.notificaciones || d.no_leidas !== undefined)) {
              this.notifications = d.notificaciones || [];
              this.unreadNotificationsCount = d.no_leidas || 0;
            }
          }
        } catch (e) {}

        try {
          const notifUrl = (typeof API !== 'undefined' && API.notificaciones)
            ? API.notificaciones
            : `${window.location.origin}/api/v1/notificaciones`;
          const params = new URLSearchParams();
          if (this.userId) params.append('id_usuario', this.userId);
          if (this.roleId) params.append('id_rol', this.roleId);
          if (limit) params.append('limit', limit);

          const res = await fetch(`${notifUrl}?${params.toString()}`);
          if (res.ok) {
            const data = await res.json();
            const notifs = data.notificaciones || [];
            if (window._solicitudesConfirmadasDirectas && window._solicitudesConfirmadasDirectas.size > 0) {
              notifs.forEach(n => {
                const c = window.obtenerCodigoSolicitudDeNotif ? window.obtenerCodigoSolicitudDeNotif(n) : null;
                if (c && window._solicitudesConfirmadasDirectas.has(c)) {
                  n.aprobadoExitoso = true;
                  n.leido = true;
                }
              });
            }
            this.notifications = notifs;
            this.unreadNotificationsCount = data.no_leidas || 0;
          }
        } catch (err) {
          console.warn('Aviso al cargar notificaciones en shell:', err);
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

      async marcarTodasNotificacionesLeidas() {
        try {
          const notifUrl = (typeof API !== 'undefined' && API.notificaciones)
            ? API.notificaciones
            : `${window.location.origin}/api/v1/notificaciones`;
          await fetch(`${notifUrl}/marcar-todas-leidas`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_usuario: this.userId, id_rol: this.roleId })
          });
          (this.notifications || []).forEach(n => n.leido = true);
          this.unreadNotificationsCount = 0;
        } catch (e) {
          console.warn('Aviso al marcar todas las notificaciones:', e);
        }
      },

      // ----------------------------------------------------------------------
      // 5. PERMISOS Y ROLES
      // ----------------------------------------------------------------------
      tieneRol(...roles) {
        if (typeof window.tieneRol === 'function') {
          return window.tieneRol(...roles);
        }
        return false;
      },

      get esAdminOSuperAdmin() {
        return this.tieneRol('ADMINISTRADOR', 'SUPERADMIN');
      },

      puedeModulo(mod) {
        if (this.activeRole === 'SUPERADMIN') return true;
        if (typeof window.puedeModulo === 'function') {
          return window.puedeModulo(mod);
        }
        return true;
      },

      puedeAccion(mod, acc) {
        if (this.activeRole === 'SUPERADMIN') return true;
        if (typeof window.puedeAccion === 'function') {
          return window.puedeAccion(mod, acc);
        }
        return true;
      },

      // ----------------------------------------------------------------------
      // 6. MANTENIMIENTO Y FORMATOS
      // ----------------------------------------------------------------------
      get estadoMantenimiento() {
        return (typeof Alpine !== 'undefined' && Alpine.store && Alpine.store('mantenimiento'))
          ? Alpine.store('mantenimiento')
          : window.estadoMantenimiento;
      },

      isModuloMantenimiento(mod) {
        if (typeof window.isModuloMantenimiento === 'function') {
          return window.isModuloMantenimiento(mod);
        }
        return false;
      },

      advertirModuloMantenimiento(nombreModulo) {
        if (typeof window.advertirModuloMantenimiento === 'function') {
          window.advertirModuloMantenimiento(nombreModulo);
        }
      },

      formatearTiempoRelativo(fechaStr) {
        if (typeof window.formatearTiempoRelativo === 'function') {
          return window.formatearTiempoRelativo(fechaStr);
        }
        return fechaStr || '';
      },

      formatearTextoEnlace(url) {
        if (typeof window.formatearTextoEnlace === 'function') {
          return window.formatearTextoEnlace(url);
        }
        return url || '';
      },

      // ----------------------------------------------------------------------
      // 7. CONTROL DE ELEMENTOS DEL LAYOUT
      // ----------------------------------------------------------------------
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
        if (this.openModules[name] !== undefined) {
          this.openModules[name] = !this.openModules[name];
        }
      },

      cerrarSesion() {
        if (typeof cerrarSesionUsuario === 'function') {
          cerrarSesionUsuario();
        } else {
          try {
            sessionStorage.clear();
            localStorage.removeItem('incarsa_token');
            localStorage.removeItem('incarsa_session');
          } catch (e) {}
          window.location.replace('/login?logout=1');
        }
      },

      // ----------------------------------------------------------------------
      // 8. INICIALIZACIÓN Y EVENT LISTENERS
      // ----------------------------------------------------------------------
      init() {
        // Aplicar dark mode guardado
        document.documentElement.classList.toggle('dark', this.darkMode);

        // Actualizar sesión actual
        let currentSesion = null;
        if (typeof getAuthSession === 'function') {
          currentSesion = getAuthSession();
        } else {
          try {
            currentSesion = JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || 'null');
          } catch (e) {}
        }

        if (currentSesion) {
          this.activeRole = currentSesion.rol || this.activeRole;
          this.userId = currentSesion.id || this.userId;
          this.roleId = currentSesion.id_rol || this.roleId;
          this._userName = currentSesion.nombre || currentSesion.nombres || this._userName;
          this._userInitials = this._userName
            .split(' ')
            .filter(Boolean)
            .map(p => p[0])
            .join('')
            .substring(0, 2)
            .toUpperCase() || 'AD';
        }

        // Cargar notificaciones iniciales
        this.cargarNotificaciones();

        // Polling cada 35 segundos
        setInterval(() => this.cargarNotificaciones(), 35000);

        // Escuchar apertura remota de modal de notificaciones
        window.addEventListener('open-notificaciones-modal', () => {
          this.abrirModalTodasNotificaciones();
        });

        // Escuchar notificaciones en caliente vía SSE
        window.addEventListener('notificacion-en-caliente', (e) => {
          const notif = e.detail;
          if (notif) {
            const existe = (this.notifications || []).some(n => n.id && notif.id && String(n.id) === String(notif.id));
            if (!existe) {
              this.notifications.unshift(notif);
              this.unreadNotificationsCount = (this.unreadNotificationsCount || 0) + 1;
            }
          }
        });

        window.addEventListener('notificacion-en-caliente-remota', (e) => {
          const notif = e.detail;
          if (notif) {
            const existe = (this.notifications || []).some(n => n.id && notif.id && String(n.id) === String(notif.id));
            if (!existe) {
              this.notifications.unshift(notif);
              this.unreadNotificationsCount = (this.unreadNotificationsCount || 0) + 1;
            }
          }
        });

        window.addEventListener('notificaciones-leidas-sync', (e) => {
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

        // Escuchar actualizaciones de notificaciones externas
        window.addEventListener('notificaciones-actualizadas', () => {
          this.cargarNotificaciones();
        });

        window.addEventListener('storage', (e) => {
          if (e.key === 'incarsa_notificaciones_reload' || e.key === 'incarsa_notif_reload') {
            this.cargarNotificaciones();
          }
        });
      }
    };
  }

  // Exponer globalmente ambos identificadores para compatibilidad absoluta
  window.appShell = appShell;
  window.appShellStub = appShell;

  /* =========================================================
     SENTINEL DE CONECTIVIDAD DE RED (Offline / Online Status)
     ========================================================= */
  (function initNetworkSentinel() {
    function createBanner() {
      let el = document.getElementById('incarsa-network-banner');
      if (el) return el;
      el = document.createElement('div');
      el.id = 'incarsa-network-banner';
      el.className = 'network-status-banner';
      el.innerHTML = `
        <div class="network-status-content">
          <i class="network-status-icon fa-solid fa-wifi"></i>
          <span class="network-status-text"></span>
        </div>
      `;
      document.body.appendChild(el);
      return el;
    }

    function showOffline() {
      const banner = createBanner();
      banner.classList.remove('is-online', 'slide-up');
      banner.classList.add('is-offline', 'slide-down');
      
      const icon = banner.querySelector('.network-status-icon');
      const text = banner.querySelector('.network-status-text');
      if (icon) icon.className = 'network-status-icon fa-solid fa-plane-slash';
      if (text) text.textContent = 'Sin conexión a la red. Las acciones pendientes se sincronizarán al reconectar.';
      
      if (typeof window.showToast === 'function') {
        window.showToast('Sin conexión a la red de INCARSA', 'warning', 4000);
      }
    }

    function showOnline() {
      const banner = document.getElementById('incarsa-network-banner');
      if (!banner) return;
      
      banner.classList.remove('is-offline');
      banner.classList.add('is-online');
      
      const icon = banner.querySelector('.network-status-icon');
      const text = banner.querySelector('.network-status-text');
      if (icon) icon.className = 'network-status-icon fa-solid fa-wifi';
      if (text) text.textContent = 'Conexión restablecida con el servidor de INCARSA.';
      
      if (typeof window.showToast === 'function') {
        window.showToast('Conexión a internet restablecida', 'success', 3000);
      }

      // Disparar evento para que otras vistas recarguen datos frescos si lo requieren
      window.dispatchEvent(new CustomEvent('red-restablecida'));

      setTimeout(() => {
        banner.classList.remove('slide-down');
        banner.classList.add('slide-up');
      }, 3000);
    }

    window.addEventListener('offline', showOffline);
    window.addEventListener('online', showOnline);

    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', showOffline);
      } else {
        showOffline();
      }
    }
  })();

})();
