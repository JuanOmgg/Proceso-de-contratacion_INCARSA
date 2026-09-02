const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

const API_BASE_URL = isLocal ? "http://127.0.0.1:8000" : "PONER_SERVIDOR_PRODUCCION";

const API = {
    base: API_BASE_URL,
    solicitudes: `${API_BASE_URL}/api/v1/solicitudes`,
    empresas: `${API_BASE_URL}/api/v1/empresas`,
    usuarios: `${API_BASE_URL}/api/v1/usuarios`,
    plantas: `${API_BASE_URL}/planta`,
    roles: `${API_BASE_URL}/roles`,
    personas: `${API_BASE_URL}/api/v1/personas`,
    antecedentes: `${API_BASE_URL}/api/v1/antecedentes`,
    vehiculos: `${API_BASE_URL}/api/v1/vehiculos`,
    contratistas: `${API_BASE_URL}/emp_contratista`,
    auth: `${API_BASE_URL}/api/v1/auth`,
    notificaciones: `${API_BASE_URL}/api/v1/notificaciones`
};

// Utilidad para formatear tiempos relativos amigables
function formatearTiempoRelativo(fechaStr) {
    if (!fechaStr) return "";
    try {
        const fecha = new Date(String(fechaStr).replace(" ", "T"));
        const ahora = new Date();
        const diffSegundos = Math.floor((ahora - fecha) / 1000);
        if (diffSegundos < 60) return "Hace un momento";
        const diffMinutos = Math.floor(diffSegundos / 60);
        if (diffMinutos < 60) return `Hace ${diffMinutos} min`;
        const diffHoras = Math.floor(diffMinutos / 60);
        if (diffHoras < 24) return `Hace ${diffHoras} h`;
        const diffDias = Math.floor(diffHoras / 24);
        if (diffDias === 1) return "Ayer";
        if (diffDias < 7) return `Hace ${diffDias} d`;
        return fecha.toLocaleDateString("es-CO", { day: "numeric", month: "short" });
    } catch (e) {
        return fechaStr;
    }
}

// ============================================================================
// Shell global de navegación y sesión de usuario para todas las vistas
// ============================================================================
function appShellStub() {
    let sesion = null;
    try {
        sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
    } catch (e) {}

    const nombreUsuario = sesion ? (sesion.nombre || sesion.nombres || `${sesion.nombres || ''} ${sesion.apellidos || ''}`.trim() || "Usuario") : "Administrador Sistema";
    const iniciales = nombreUsuario.split(" ").filter(Boolean).map(p => p[0]).join("").substring(0, 2).toUpperCase() || "AD";
    const userId = sesion?.id || 1;
    const roleId = sesion?.id_rol || 2;

    return {
        sidebarCollapsed: false,
        sidebarOpenMobile: false,
        notificationsOpen: false,
        userId: userId,
        roleId: roleId,
        activeRole: sesion?.rol || "ADMINISTRADOR",
        openModules: { formularios: false, tablas: true, procesamiento: false },
        notifications: [],
        unreadNotificationsCount: 0,
        userDisplayName: nombreUsuario,
        userInitials: iniciales,
        darkMode: localStorage.getItem('darkMode') === 'true',

        formatearTiempoRelativo: formatearTiempoRelativo,

        init() {
            // Aplicar el modo oscuro guardado al cargar la página
            document.documentElement.classList.toggle('dark', this.darkMode);
            this.cargarNotificaciones();
            // Polling periódico cada 35 segundos
            setInterval(() => this.cargarNotificaciones(), 35000);
        },

        async cargarNotificaciones() {
            try {
                const params = new URLSearchParams();
                if (this.userId) params.append("id_usuario", this.userId);
                if (this.roleId) params.append("id_rol", this.roleId);
                const res = await fetch(`${API.notificaciones}?${params.toString()}`);
                if (res.ok) {
                    const data = await res.json();
                    this.notifications = data.notificaciones || [];
                    this.unreadNotificationsCount = data.no_leidas || 0;
                }
            } catch (err) {
                console.warn("Aviso al cargar notificaciones:", err);
            }
        },

        async marcarNotificacionLeida(n) {
            if (!n.leido) {
                try {
                    await fetch(`${API.notificaciones}/${n.id}/leer`, { method: "PATCH" });
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
                await fetch(`${API.notificaciones}/marcar-todas-leidas`, {
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

        toggleSidebar() {
            this.sidebarCollapsed = !this.sidebarCollapsed;
        },

        toggleMobileSidebar() {
            this.sidebarOpenMobile = !this.sidebarOpenMobile;
        },

        closeMobileSidebar() {
            this.sidebarOpenMobile = false;
        }
    };
}

/* =========================================================
   Alerta — mini librería de alertas propia (sin dependencias)
   API: Alerta.fire({ type, title, text, confirmText, cancelText, showCancel })
   Devuelve una Promise<{ isConfirmed: boolean }>
   ========================================================= */
const Alerta = (() => {

  const ICONS = {
    success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>',
    error:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"/></svg>',
    warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4M12 17h.01M10.3 3.9L1.8 18a1 1 0 0 0 .9 1.5h18.6a1 1 0 0 0 .9-1.5L13.7 3.9a1 1 0 0 0-1.7 0Z"/></svg>',
    info:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16v-4M12 8h.01"/><circle cx="12" cy="12" r="9.5"/></svg>'
  };

  function fire({
    type = 'info',
    title = '',
    text = '',
    confirmText = 'Aceptar',
    cancelText = 'Cancelar',
    showCancel = false
  } = {}) {
    return new Promise((resolve) => {
      const overlay = document.createElement('div');
      overlay.className = 'al-overlay';

      overlay.innerHTML = `
        <div class="al-card ${type}">
          <div class="al-stamp">${ICONS[type] || ICONS.info}</div>
          <h2 class="al-title"></h2>
          <p class="al-text"></p>
          <div class="al-actions">
            ${showCancel ? `<button class="al-btn al-btn-cancel">${cancelText}</button>` : ''}
            <button class="al-btn al-btn-confirm">${confirmText}</button>
          </div>
          <div class="al-serrated"></div>
        </div>
      `;

      // set text content safely (avoids HTML injection from dynamic strings)
      overlay.querySelector('.al-title').textContent = title;
      overlay.querySelector('.al-text').textContent = text;

      document.body.appendChild(overlay);
      requestAnimationFrame(() => overlay.classList.add('show'));

      function close(result) {
        overlay.classList.remove('show');
        setTimeout(() => overlay.remove(), 180);
        resolve(result);
      }

      overlay.querySelector('.al-btn-confirm').addEventListener('click', () => close({ isConfirmed: true }));
      const cancelBtn = overlay.querySelector('.al-btn-cancel');
      if (cancelBtn) cancelBtn.addEventListener('click', () => close({ isConfirmed: false }));

      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close({ isConfirmed: false });
      });
      document.addEventListener('keydown', function esc(e) {
        if (e.key === 'Escape') { close({ isConfirmed: false }); document.removeEventListener('keydown', esc); }
      });
    });
  }

  return { fire };
})();

async function confirmDemo() {
  const { isConfirmed } = await Alerta.fire({
    type: 'warning',
    title: '¿Eliminar el archivo?',
    text: 'Esta acción es permanente y no se puede deshacer.',
    showCancel: true,
    confirmText: 'Sí, eliminar',
    cancelText: 'Cancelar'
  });
  Alerta.fire({
    type: isConfirmed ? 'success' : 'info',
    title: isConfirmed ? 'Eliminado' : 'Cancelado',
    text: isConfirmed ? 'El archivo fue eliminado.' : 'No se realizó ningún cambio.'
  });
}