/**
 * alertas.js — Sistema Global de Alertas y Notificaciones Toast (INCARSA)
 * 
 * Proporciona:
 * 1. Alerta: Componente visual de diálogo/modal ticket (sin dependencias externas).
 *    - Alerta.fire({ type, title, text, confirmText, cancelText, showCancel })
 *    - Alerta.success(title, text)
 *    - Alerta.error(title, text)
 *    - Alerta.warning(title, text)
 *    - Alerta.info(title, text)
 *    - Alerta.confirm(title, text, confirmText, cancelText)
 * 
 * 2. window.showToast: Notificaciones rápidas tipo toast con SweetAlert2 o fallback visual.
 */

(function () {
  'use strict';

  /* =========================================================
     Iconos SVG vectoriales optimizados
     ========================================================= */
  const ICONS = {
    success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>',
    error:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"/></svg>',
    warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4M12 17h.01M10.3 3.9L1.8 18a1 1 0 0 0 .9 1.5h18.6a1 1 0 0 0 .9-1.5L13.7 3.9a1 1 0 0 0-1.7 0Z"/></svg>',
    info:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16v-4M12 8h.01"/><circle cx="12" cy="12" r="9.5"/></svg>'
  };

  /* =========================================================
     Alerta Core
     ========================================================= */
  const Alerta = {
    fire({
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

        // Inserción segura de texto para evitar inyecciones XSS
        const titleEl = overlay.querySelector('.al-title');
        const textEl = overlay.querySelector('.al-text');
        if (titleEl) titleEl.textContent = title;
        if (textEl) textEl.textContent = text;

        document.body.appendChild(overlay);
        requestAnimationFrame(() => overlay.classList.add('show'));

        let resolved = false;
        function close(result) {
          if (resolved) return;
          resolved = true;
          overlay.classList.remove('show');
          document.removeEventListener('keydown', handleEsc);
          setTimeout(() => {
            if (overlay.parentNode) {
              overlay.parentNode.removeChild(overlay);
            }
          }, 200);
          resolve(result);
        }

        function handleEsc(e) {
          if (e.key === 'Escape') {
            close({ isConfirmed: false });
          }
        }

        const confirmBtn = overlay.querySelector('.al-btn-confirm');
        if (confirmBtn) {
          confirmBtn.addEventListener('click', () => close({ isConfirmed: true }));
          confirmBtn.focus();
        }

        const cancelBtn = overlay.querySelector('.al-btn-cancel');
        if (cancelBtn) {
          cancelBtn.addEventListener('click', () => close({ isConfirmed: false }));
        }

        overlay.addEventListener('click', (e) => {
          if (e.target === overlay) {
            close({ isConfirmed: false });
          }
        });

        document.addEventListener('keydown', handleEsc);
      });
    },

    // Métodos abreviados
    success(title = 'Operación Exitosa', text = '') {
      return this.fire({ type: 'success', title, text });
    },

    error(title = 'Error', text = '') {
      return this.fire({ type: 'error', title, text });
    },

    warning(title = 'Advertencia', text = '') {
      return this.fire({ type: 'warning', title, text });
    },

    info(title = 'Información', text = '') {
      return this.fire({ type: 'info', title, text });
    },

    confirm(title = '¿Está seguro?', text = '', confirmText = 'Aceptar', cancelText = 'Cancelar') {
      return this.fire({
        type: 'warning',
        title,
        text,
        showCancel: true,
        confirmText,
        cancelText
      });
    }
  };

  /* =========================================================
     Toast Notifications (SweetAlert2 o Fallback nativo)
     ========================================================= */
  window.showToast = function (message, icon = 'info', duration = 3000) {
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        toast: true,
        position: 'top-end',
        icon: icon,
        title: message,
        showConfirmButton: false,
        timer: duration,
        timerProgressBar: true,
        customClass: {
          popup: 'colored-toast'
        }
      });
    } else {
      // Fallback si Swal no está cargado
      console.log(`[TOAST ${String(icon).toUpperCase()}] ${message}`);
      let toastContainer = document.getElementById('incarsa-toast-container');
      if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'incarsa-toast-container';
        toastContainer.style.position = 'fixed';
        toastContainer.style.top = '1.5rem';
        toastContainer.style.right = '1.5rem';
        toastContainer.style.zIndex = '999999';
        toastContainer.style.display = 'flex';
        toastContainer.style.flexDirection = 'column';
        toastContainer.style.gap = '0.5rem';
        document.body.appendChild(toastContainer);
      }

      const toast = document.createElement('div');
      toast.style.background = icon === 'error' ? '#EF4444' : icon === 'success' ? '#10B981' : icon === 'warning' ? '#F59E0B' : '#3B82F6';
      toast.style.color = '#FFFFFF';
      toast.style.padding = '0.75rem 1.25rem';
      toast.style.borderRadius = '0.5rem';
      toast.style.fontSize = '0.875rem';
      toast.style.boxShadow = '0 10px 15px -3px rgba(0,0,0,0.2)';
      toast.style.fontWeight = '500';
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      toast.style.transition = 'all 0.2s ease-out';
      toast.textContent = message;

      toastContainer.appendChild(toast);
      requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
      });

      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(() => toast.remove(), 200);
      }, duration);
    }
  };

  // Demo helper
  window.confirmDemo = async function () {
    const { isConfirmed } = await Alerta.confirm(
      '¿Eliminar el archivo?',
      'Esta acción es permanente y no se puede deshacer.',
      'Sí, eliminar',
      'Cancelar'
    );
    if (isConfirmed) {
      Alerta.success('Eliminado', 'El archivo fue eliminado.');
    } else {
      Alerta.info('Cancelado', 'No se realizó ningún cambio.');
    }
  };

  // Exponer globalmente
  window.Alerta = Alerta;

})();
