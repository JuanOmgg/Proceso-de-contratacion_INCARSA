/**
 * INCARSA - Panel de Control SuperAdmin (RBAC & Mantenimiento 503)
 */

function superAdminPanel() {
  return {
    cargando: true,
    guardandoMantenimiento: false,
    guardandoPermisos: false,
    hayCambiosPendientes: false,
    
    // Modo mantenimiento
    mantenimiento: {
      activo: false,
      mensaje: 'Estamos realizando labores de mantenimiento y optimización en la plataforma. El servicio se reanudará en breve.',
      tiempo: 'Disponible en aproximadamente 30 minutos',
      updated_at: null
    },

    // Gestión de Permisos
    roles: [],
    modulos: [],
    acciones: ['ver', 'crear', 'editar', 'eliminar', 'aprobar'],
    matriz: {},
    rolSeleccionadoId: 1, // Por defecto ADMINISTRADOR
    busquedaModulo: '',

    get rolActual() {
      return this.roles.find(r => r.id === this.rolSeleccionadoId) || null;
    },

    get esRolSuperAdmin() {
      const r = this.rolActual;
      return !!(r && (r.is_superadmin || (r.nombre_rol || '').trim().toUpperCase() === 'SUPERADMIN'));
    },

    get modulosFiltrados() {
      if (!this.busquedaModulo.trim()) return this.modulos;
      const q = this.busquedaModulo.toLowerCase();
      return this.modulos.filter(m => {
        const nombreHumano = this.formatoModulo(m).toLowerCase();
        return m.toLowerCase().includes(q) || nombreHumano.includes(q);
      });
    },

    async init() {
      // Verificar acceso exclusivo
      const sesion = (typeof getAuthSession === 'function') ? getAuthSession() : null;
      const miRol = (sesion?.rol || '').trim().toUpperCase();
      
      if (miRol !== 'SUPERADMIN') {
        if (typeof Swal !== 'undefined') {
          await Swal.fire({
            icon: 'error',
            title: 'Acceso Denegado',
            text: 'Esta sección es de uso exclusivo para la cuenta Maestro SUPERADMIN.',
            confirmButtonColor: '#ea580c'
          });
        }
        window.location.replace('/dashboard');
        return;
      }

      await Promise.all([
        this.cargarEstadoMantenimiento(),
        this.cargarMatrizPermisos()
      ]);

      this.cargando = false;
    },

    // -------------------------------------------------------------
    // 1. MODO MANTENIMIENTO
    // -------------------------------------------------------------
    async cargarEstadoMantenimiento() {
      try {
        const res = await fetch('/api/v1/superadmin/mantenimiento');
        if (res.ok) {
          const data = await res.json();
          this.mantenimiento.activo = !!data.activo;
          if (data.mensaje) this.mantenimiento.mensaje = data.mensaje;
          if (data.tiempo) this.mantenimiento.tiempo = data.tiempo;
          this.mantenimiento.updated_at = data.updated_at;
        }
      } catch (err) {
        console.error('Error cargando estado de mantenimiento:', err);
      }
    },

    async toggleMantenimiento(nuevoEstado) {
      const activar = nuevoEstado !== undefined ? nuevoEstado : !this.mantenimiento.activo;
      const titulo = activar ? '¿Activar Modo Mantenimiento (HTTP 503)?' : '¿Reanudar servicio y desactivar mantenimiento?';
      const texto = activar 
        ? 'Todos los usuarios que no sean SUPERADMIN verán la pantalla de mantenimiento (503) y no podrán interactuar con el sistema.'
        : 'Todos los usuarios volverán a tener acceso normal de acuerdo con sus roles y permisos.';

      if (typeof Swal !== 'undefined') {
        const confirmacion = await Swal.fire({
          title: titulo,
          text: texto,
          icon: activar ? 'warning' : 'question',
          showCancelButton: true,
          confirmButtonText: activar ? 'Sí, activar mantenimiento' : 'Sí, reanudar servicio',
          cancelButtonText: 'Cancelar',
          confirmButtonColor: activar ? '#dc2626' : '#16a34a',
          cancelButtonColor: '#64748b'
        });

        if (!confirmacion.isConfirmed) {
          return;
        }
      }

      this.guardandoMantenimiento = true;
      try {
        const res = await fetch('/api/v1/superadmin/mantenimiento', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            activo: activar,
            mensaje: this.mantenimiento.mensaje,
            tiempo: this.mantenimiento.tiempo
          })
        });

        const data = await res.json();
        if (res.ok && data.exito) {
          this.mantenimiento.activo = activar;
          if (typeof Swal !== 'undefined') {
            Swal.fire({
              icon: 'success',
              title: activar ? 'Modo Mantenimiento Activado' : 'Servicio Reanudado con Éxito',
              text: activar ? 'El sistema ahora responde con código HTTP 503 para usuarios estándar.' : 'El sistema está operando con normalidad.',
              timer: 2500,
              showConfirmButton: false
            });
          }
        } else {
          throw new Error(data.detail || 'No fue posible actualizar el modo de mantenimiento');
        }
      } catch (err) {
        console.error('Error guardando mantenimiento:', err);
        if (typeof Swal !== 'undefined') {
          Swal.fire({ icon: 'error', title: 'Error', text: err.message || 'Error de conexión.' });
        }
      } finally {
        this.guardandoMantenimiento = false;
      }
    },

    // -------------------------------------------------------------
    // 2. MATRIZ DE PERMISOS
    // -------------------------------------------------------------
    async cargarMatrizPermisos() {
      try {
        const res = await fetch('/api/v1/superadmin/permisos');
        if (res.ok) {
          const data = await res.json();
          this.roles = data.roles || [];
          this.modulos = data.modulos || [];
          this.matriz = data.matriz || {};

          // Si el rol seleccionado no existe en roles, elegir el primero
          if (this.roles.length > 0 && !this.roles.some(r => r.id === this.rolSeleccionadoId)) {
            this.rolSeleccionadoId = this.roles[0].id;
          }
        }
      } catch (err) {
        console.error('Error cargando matriz de permisos:', err);
      }
    },

    async seleccionarRol(idRol) {
      if (this.rolSeleccionadoId === idRol) return;

      // Si hay cambios pendientes en el rol actual, confirmar antes de cambiar
      if (this.hayCambiosPendientes && !this.esRolSuperAdmin) {
        if (typeof Swal !== 'undefined') {
          const res = await Swal.fire({
            title: '¿Guardar cambios pendientes?',
            text: `Tienes cambios sin guardar para el rol ${this.rolActual?.nombre_rol || ''}. ¿Deseas guardarlos antes de cambiar de rol?`,
            icon: 'warning',
            showDenyButton: true,
            showCancelButton: true,
            confirmButtonText: 'Guardar y cambiar',
            denyButtonText: 'Descartar cambios',
            cancelButtonText: 'Permanecer aquí',
            confirmButtonColor: '#f59e0b',
            denyButtonColor: '#ef4444',
            cancelButtonColor: '#64748b'
          });

          if (res.isConfirmed) {
            await this.guardarPermisosRol();
          } else if (!res.isDenied) {
            return; // Cancelado, no cambia de rol
          }
        }
      }

      this.rolSeleccionadoId = idRol;
      this.hayCambiosPendientes = false;
    },

    getPermiso(modulo, accion) {
      if (this.esRolSuperAdmin) return true;

      const rolId = String(this.rolSeleccionadoId);
      const rolData = this.matriz[rolId] || this.matriz[this.rolSeleccionadoId] || {};
      if (!rolData[modulo]) return false;
      return !!rolData[modulo][accion];
    },

    togglePermiso(modulo, accion) {
      if (this.esRolSuperAdmin) {
        this.notificar('Los permisos de SUPERADMIN son irrestrictos por seguridad.', 'info');
        return;
      }

      const rolId = String(this.rolSeleccionadoId);
      if (!this.matriz[rolId]) this.matriz[rolId] = {};
      if (!this.matriz[rolId][modulo]) {
        this.matriz[rolId][modulo] = { ver: false, crear: false, editar: false, eliminar: false, aprobar: false };
      }
      
      const valorActual = !!this.matriz[rolId][modulo][accion];
      const nuevoValor = !valorActual;

      // Clonar para asegurar reactividad profunda en Alpine
      const modObj = { ...this.matriz[rolId][modulo], [accion]: nuevoValor };

      // Si se desactiva "ver", desactivar automáticamente las demás acciones dependientes
      if (accion === 'ver' && !nuevoValor) {
        modObj.crear = false;
        modObj.editar = false;
        modObj.eliminar = false;
        modObj.aprobar = false;
      }
      // Si se activa cualquier acción operativa, asegurar que "ver" esté activo
      if (accion !== 'ver' && nuevoValor) {
        modObj.ver = true;
      }

      this.matriz[rolId][modulo] = modObj;
      this.matriz = { ...this.matriz };
      this.hayCambiosPendientes = true;
    },

    marcarTodosModulo(modulo, habilitar) {
      if (this.esRolSuperAdmin) {
        this.notificar('Los permisos de SUPERADMIN no admiten modificaciones.', 'info');
        return;
      }

      const rolId = String(this.rolSeleccionadoId);
      if (!this.matriz[rolId]) this.matriz[rolId] = {};

      const nuevoModulo = {
        ver: !!habilitar,
        crear: !!habilitar,
        editar: !!habilitar,
        eliminar: !!habilitar,
        aprobar: !!habilitar
      };

      this.matriz[rolId][modulo] = nuevoModulo;
      this.matriz = { ...this.matriz };
      this.hayCambiosPendientes = true;

      const nom = this.formatoModulo(modulo);
      this.notificar(
        `${nom}: Todas las acciones ${habilitar ? 'HABILITADAS' : 'BLOQUEADAS'}`,
        habilitar ? 'success' : 'warning'
      );
    },

    marcarTodosRol(habilitar) {
      if (this.esRolSuperAdmin) {
        this.notificar('Los permisos de SUPERADMIN no admiten modificaciones.', 'info');
        return;
      }

      const rolId = String(this.rolSeleccionadoId);
      if (!this.matriz[rolId]) this.matriz[rolId] = {};

      const nuevoRolObj = {};
      this.modulos.forEach(mod => {
        nuevoRolObj[mod] = {
          ver: !!habilitar,
          crear: !!habilitar,
          editar: !!habilitar,
          eliminar: !!habilitar,
          aprobar: !!habilitar
        };
      });

      this.matriz[rolId] = nuevoRolObj;
      this.matriz = { ...this.matriz };
      this.hayCambiosPendientes = true;

      const nombreRol = this.rolActual ? this.rolActual.nombre_rol : 'Rol';
      this.notificar(
        `${nombreRol}: Todos los módulos ${habilitar ? 'HABILITADOS' : 'BLOQUEADOS'}`,
        habilitar ? 'success' : 'warning'
      );
    },

    async guardarPermisosRol() {
      const rol = this.rolActual;
      if (!rol) return;

      if (this.esRolSuperAdmin) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'info',
            title: 'Acceso Irrestricto',
            text: 'El rol SUPERADMIN posee control maestro permanente. Sus permisos no requieren ser guardados.',
            confirmButtonColor: '#f59e0b'
          });
        }
        return;
      }

      this.guardandoPermisos = true;
      const permisosArray = [];
      const rolId = String(rol.id);
      const datosRol = this.matriz[rolId] || this.matriz[rol.id] || {};

      this.modulos.forEach(modulo => {
        const accionesModulo = datosRol[modulo] || {};
        this.acciones.forEach(accion => {
          permisosArray.push({
            modulo: modulo,
            accion: accion,
            permitido: !!accionesModulo[accion]
          });
        });
      });

      try {
        const res = await fetch(`/api/v1/superadmin/permisos/${rol.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ permisos: permisosArray })
        });

        const data = await res.json();
        if (res.ok && data.exito) {
          this.hayCambiosPendientes = false;

          if (typeof Swal !== 'undefined') {
            Swal.fire({
              icon: 'success',
              title: '¡Permisos Guardados al 100%!',
              html: `La matriz de permisos para <strong>${rol.nombre_rol}</strong> se sincronizó en base de datos correctamente.`,
              timer: 2200,
              showConfirmButton: false,
              background: '#0f172a',
              color: '#f8fafc'
            });
          }

          // Si el usuario actual tiene este rol, refrescar sus permisos locales en tiempo real
          const sesion = (typeof getAuthSession === 'function') ? getAuthSession() : null;
          if (sesion && sesion.id_rol === rol.id && typeof window.recargarMisPermisos === 'function') {
            await window.recargarMisPermisos();
          }
        } else {
          throw new Error(data.detail || 'Error al guardar permisos.');
        }
      } catch (err) {
        console.error('Error guardando permisos:', err);
        if (typeof Swal !== 'undefined') {
          Swal.fire({ icon: 'error', title: 'Error', text: err.message || 'No se pudo guardar la configuración.' });
        }
      } finally {
        this.guardandoPermisos = false;
      }
    },

    notificar(mensaje, tipo = 'info') {
      if (typeof Swal !== 'undefined') {
        const Toast = Swal.mixin({
          toast: true,
          position: 'top-end',
          showConfirmButton: false,
          timer: 2000,
          timerProgressBar: true,
          background: '#1e293b',
          color: '#f8fafc'
        });
        Toast.fire({
          icon: tipo,
          title: mensaje
        });
      } else {
        console.log(`[NOTIFICACIÓN] ${mensaje}`);
      }
    },

    formatoModulo(mod) {
      const mapa = {
        dashboard: 'Dashboard / Estadísticas',
        solicitudes: 'Listado de Solicitudes',
        nueva_solicitud: 'Nueva Solicitud (Formulario)',
        usuarios: 'Listado de Usuarios',
        nuevo_usuario: 'Nuevo Usuario (Formulario)',
        plantas: 'Gestión de Plantas y Zonas',
        contratistas: 'Gestión de Contratistas',
        vehiculos: 'Gestión de Vehículos',
        personas: 'Listado de Personas',
        procesamiento: 'Procesamiento de Solicitudes',
        antecedentes: 'Verificación de Antecedentes',
        revision_solicitud: 'Revisión y Aprobación Detallada',
        superadmin: 'Panel Maestro SuperAdmin'
      };
      return mapa[mod] || mod.replace('_', ' ').toUpperCase();
    },

    iconoModulo(mod) {
      const iconos = {
        dashboard: 'fa-gauge-high text-cyan-400',
        solicitudes: 'fa-file-invoice text-amber-400',
        nueva_solicitud: 'fa-file-circle-plus text-emerald-400',
        usuarios: 'fa-users text-blue-400',
        nuevo_usuario: 'fa-user-plus text-indigo-400',
        plantas: 'fa-building text-violet-400',
        contratistas: 'fa-id-card-clip text-orange-400',
        vehiculos: 'fa-truck-front text-teal-400',
        personas: 'fa-person text-pink-400',
        procesamiento: 'fa-diagram-project text-yellow-400',
        antecedentes: 'fa-magnifying-glass-chart text-sky-400',
        revision_solicitud: 'fa-clipboard-check text-emerald-400',
        superadmin: 'fa-shield-halved text-rose-400'
      };
      return iconos[mod] || 'fa-folder text-slate-400';
    }
  };
}
