/**
 * mantenimiento.js — Sistema Global de Mantenimiento y Bloqueo Temporal (INCARSA)
 * 
 * Gestiona:
 * - Estado global reactivo de mantenimiento (`window.estadoMantenimiento`).
 * - Verificación de módulos en mantenimiento (`window.isModuloMantenimiento`).
 * - Consulta periódica (polling) al backend `/api/v1/sistema/mantenimiento`.
 * - Tienda reactiva Alpine (`$store.mantenimiento`).
 * - Componente Alpine `modalTimerCountdown()` para cuenta regresiva visual en modales 503.
 * - Notificación/modal informativo de módulo bloqueado (`window.advertirModuloMantenimiento`).
 */

(function () {
  'use strict';

  // ============================================================================
  // Estado global reactivo
  // ============================================================================
  window.estadoMantenimiento = {
    activo: false,
    tipo: 'general',
    modulos: [],
    mensaje: '',
    tiempo: '',
    temporizador_minutos: 30,
    temporizador_fin: null
  };

  /**
   * Verifica si un módulo específico se encuentra en mantenimiento.
   * Superadmin siempre tiene acceso (devuelve false).
   */
  window.isModuloMantenimiento = function (mod) {
    let sesion = null;
    if (typeof getAuthSession === 'function') {
      sesion = getAuthSession();
    } else {
      try {
        sesion = JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || 'null');
      } catch (e) {}
    }

    const miRol = (sesion?.rol || '').trim().toUpperCase();
    if (miRol === 'SUPERADMIN') return false;

    const est = (typeof Alpine !== 'undefined' && Alpine.store && Alpine.store('mantenimiento'))
      ? Alpine.store('mantenimiento')
      : window.estadoMantenimiento;

    if (!est || !est.activo) return false;
    if (est.tipo === 'general') return true;
    if (est.tipo === 'modulos') {
      return (est.modulos || []).includes(mod);
    }
    return false;
  };

  /**
   * Consulta el estado de mantenimiento en el backend y actualiza Alpine store y eventos
   */
  async function cargarEstadoMantenimientoGlobal() {
    try {
      const res = await fetch('/api/v1/sistema/mantenimiento');
      if (res.ok) {
        const data = await res.json();
        const nuevoEstado = {
          activo: !!data.activo,
          tipo: data.tipo || 'general',
          modulos: Array.isArray(data.modulos) ? data.modulos : [],
          mensaje: data.mensaje || '',
          tiempo: data.tiempo || '',
          temporizador_minutos: data.temporizador_minutos || 30,
          temporizador_fin: data.temporizador_fin || null
        };
        Object.assign(window.estadoMantenimiento, nuevoEstado);

        if (typeof Alpine !== 'undefined' && Alpine.store && Alpine.store('mantenimiento')) {
          const store = Alpine.store('mantenimiento');
          store.activo = nuevoEstado.activo;
          store.tipo = nuevoEstado.tipo;
          store.modulos = nuevoEstado.modulos;
          store.mensaje = nuevoEstado.mensaje;
          store.tiempo = nuevoEstado.tiempo;
          store.temporizador_minutos = nuevoEstado.temporizador_minutos;
          store.temporizador_fin = nuevoEstado.temporizador_fin;
        }

        window.dispatchEvent(new CustomEvent('mantenimiento-actualizado', { detail: nuevoEstado }));
      }
    } catch (e) {
      console.warn('Aviso cargando estado de mantenimiento global:', e);
    }
  }
  window.cargarEstadoMantenimientoGlobal = cargarEstadoMantenimientoGlobal;

  /**
   * Modal amigable de advertencia cuando se intenta acceder a un módulo bloqueado
   */
  window.advertirModuloMantenimiento = function (nombreModulo) {
    const est = (typeof Alpine !== 'undefined' && Alpine.store && Alpine.store('mantenimiento'))
      ? Alpine.store('mantenimiento')
      : window.estadoMantenimiento;

    const mensaje = est?.mensaje || 'Estamos realizando labores de optimización y mantenimiento programado.';
    const tiempo = est?.tiempo || 'Disponible en breve';

    if (typeof Swal !== 'undefined') {
      Swal.fire({
        icon: 'warning',
        title: 'Módulo en Mantenimiento',
        html: `<div class="text-left space-y-2">
            <p class="font-bold text-amber-400 text-sm">${nombreModulo}</p>
            <p class="text-xs sm:text-sm text-slate-300 leading-relaxed">${mensaje}</p>
            <div class="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 mt-2 flex items-center gap-2">
                <i class="fa-regular fa-clock"></i>
                <span><strong>Tiempo estimado:</strong> ${tiempo}</span>
            </div>
        </div>`,
        confirmButtonText: 'Entendido',
        customClass: {
          popup: 'swal-mantenimiento-modal'
        }
      });
    } else if (typeof Alerta !== 'undefined' && Alerta.warning) {
      Alerta.warning('Módulo en Mantenimiento', `${nombreModulo}: ${mensaje} (Tiempo estimado: ${tiempo})`);
    } else {
      alert(`Módulo en Mantenimiento: ${nombreModulo}\n${mensaje}\nTiempo estimado: ${tiempo}`);
    }
  };

  /**
   * Componente Alpine: Temporizador Visual para Modales en Mantenimiento (503)
   */
  function modalTimerCountdown() {
    return {
      hours: '00',
      minutes: '00',
      seconds: '00',
      timerId: null,
      init() {
        this.tick();
        this.timerId = setInterval(() => this.tick(), 1000);
      },
      destroy() {
        if (this.timerId) clearInterval(this.timerId);
      },
      tick() {
        let target = null;
        const est = (typeof Alpine !== 'undefined' && Alpine.store && Alpine.store('mantenimiento'))
          ? Alpine.store('mantenimiento')
          : window.estadoMantenimiento;

        if (est && est.temporizador_fin) {
          target = Number(est.temporizador_fin);
        }

        if (!target || isNaN(target)) {
          try {
            const saved = JSON.parse(sessionStorage.getItem('incarsa_503_active_timer') || 'null');
            if (saved && saved.target) {
              target = Number(saved.target);
            }
          } catch (e) {}
        }

        if (!target || isNaN(target)) {
          const mins = (est && est.temporizador_minutos) ? Number(est.temporizador_minutos) : 30;
          target = Date.now() + (mins * 60 * 1000);
        }

        const diff = target - Date.now();
        if (diff <= 0) {
          this.hours = '00';
          this.minutes = '00';
          this.seconds = '00';
          return;
        }

        const h = Math.floor(diff / (1000 * 60 * 60));
        const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const s = Math.floor((diff % (1000 * 60)) / 1000);

        this.hours = String(h).padStart(2, '0');
        this.minutes = String(m).padStart(2, '0');
        this.seconds = String(s).padStart(2, '0');
      }
    };
  }
  window.modalTimerCountdown = modalTimerCountdown;

  /**
   * Registrar Alpine store tan pronto Alpine se inicialice
   */
  function registrarAlpineStore() {
    if (typeof Alpine !== 'undefined' && Alpine.store) {
      if (!Alpine.store('mantenimiento')) {
        Alpine.store('mantenimiento', {
          activo: window.estadoMantenimiento.activo,
          tipo: window.estadoMantenimiento.tipo,
          modulos: window.estadoMantenimiento.modulos,
          mensaje: window.estadoMantenimiento.mensaje,
          tiempo: window.estadoMantenimiento.tiempo,
          temporizador_minutos: window.estadoMantenimiento.temporizador_minutos,
          temporizador_fin: window.estadoMantenimiento.temporizador_fin,

          isModuloMantenimiento(mod) {
            return window.isModuloMantenimiento(mod);
          },

          async cargar() {
            await window.cargarEstadoMantenimientoGlobal();
          }
        });
      }
    }
  }

  document.addEventListener('alpine:init', () => {
    registrarAlpineStore();
    window.cargarEstadoMantenimientoGlobal();
  });

  // Si Alpine ya estaba inicializado al cargar este script
  if (window.Alpine && window.Alpine.store) {
    registrarAlpineStore();
  }

  // Carga inicial inmediata y polling cada 30 segundos
  cargarEstadoMantenimientoGlobal();
  setInterval(() => {
    cargarEstadoMantenimientoGlobal();
  }, 30000);

})();
