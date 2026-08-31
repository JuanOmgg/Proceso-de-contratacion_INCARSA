const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

const API_BASE_URL = isLocal ? "http://127.0.0.1:8000" : "PONER_SERVIDOR_PRODUCCION";

const API = {
    base: API_BASE_URL,
    solicitudes: `${API_BASE_URL}/api/v1/solicitudes`,
    empresas: `${API_BASE_URL}/api/v1/empresas`,
    usuarios: `${API_BASE_URL}/usuarios`,
    plantas: `${API_BASE_URL}/planta`,
    roles: `${API_BASE_URL}/roles`,
    personas: `${API_BASE_URL}/personas`,
    antecedentes: `${API_BASE_URL}/antecedentes`,
    vehiculos: `${API_BASE_URL}/api/v1/vehiculos`,
    contratistas: `${API_BASE_URL}/emp_contratista`,
    auth: `${API_BASE_URL}/api/v1/auth`
};

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

    return {
        sidebarCollapsed: false,
        sidebarOpenMobile: false,
        notificationsOpen: false,
        activeRole: sesion?.rol || "ADMINISTRADOR",
        openModules: { formularios: false, tablas: true, procesamiento: false },
        notifications: [
            { id: 1, texto: "Sistema actualizado correctamente", tiempo: "Hace un momento" }
        ],
        userDisplayName: nombreUsuario,
        userInitials: iniciales,
        darkMode: localStorage.getItem('darkMode') === 'true',

        init() {
            // Aplicar el modo oscuro guardado al cargar la página
            document.documentElement.classList.toggle('dark', this.darkMode);
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