/**
 * INCARSA - Panel de Control SuperAdmin (RBAC & Mantenimiento 503)
 */

function superAdminPanel() {
  return {
    cargando: true,
    guardandoMantenimiento: false,
    guardandoPermisos: false,
    hayCambiosPendientes: false,
    
    // Modo mantenimiento (General o Selectivo por Módulos)
    mantenimiento: {
      activo: false,
      tipo: 'general', // 'general' o 'modulos'
      modulos: [],     // slugs de módulos en mantenimiento
      mensaje: 'Estamos realizando labores de mantenimiento y optimización en la plataforma. El servicio se reanudará en breve.',
      tiempo: 'Disponible en aproximadamente 30 minutos',
      temporizador_minutos: 30,
      temporizador_fin: null,
      updated_at: null
    },

    listaModulosSistema: [
      { id: 'dashboard', nombre: 'Dashboard y Estadísticas', icono: 'fa-gauge-high', color: 'text-cyan-400' },
      { id: 'solicitudes', nombre: 'Listado de Solicitudes', icono: 'fa-file-invoice', color: 'text-amber-400' },
      { id: 'nueva_solicitud', nombre: 'Nueva Solicitud', icono: 'fa-file-circle-plus', color: 'text-emerald-400' },
      { id: 'usuarios', nombre: 'Listado de Usuarios', icono: 'fa-users', color: 'text-blue-400' },
      { id: 'nuevo_usuario', nombre: 'Nuevo Usuario', icono: 'fa-user-plus', color: 'text-indigo-400' },
      { id: 'correspondencias', nombre: 'Listado de Correspondencia', icono: 'fa-envelope-open-text', color: 'text-amber-400' },
      { id: 'nueva_correspondencia', nombre: 'Nueva Correspondencia', icono: 'fa-paper-plane', color: 'text-emerald-400' },
      { id: 'plantas', nombre: 'Plantas y Zonas', icono: 'fa-building', color: 'text-violet-400' },
      { id: 'contratistas', nombre: 'Empresas Contratistas', icono: 'fa-id-card-clip', color: 'text-orange-400' },
      { id: 'vehiculos', nombre: 'Vehículos y Maquinaria', icono: 'fa-truck-front', color: 'text-teal-400' },
      { id: 'personas', nombre: 'Directorio de Personas', icono: 'fa-person', color: 'text-pink-400' },
      { id: 'procesamiento', nombre: 'Procesamiento de Solicitudes', icono: 'fa-diagram-project', color: 'text-yellow-400' },
      { id: 'antecedentes', nombre: 'Verificación de Antecedentes', icono: 'fa-magnifying-glass-chart', color: 'text-sky-400' },
      { id: 'revision_solicitud', nombre: 'Revisión y Aprobación', icono: 'fa-clipboard-check', color: 'text-emerald-400' }
    ],

    // Gestión de Permisos
    roles: [],
    modulos: [],
    acciones: ['ver', 'crear', 'editar', 'eliminar', 'aprobar'],
    matriz: {},
    rolSeleccionadoId: 1, // Por defecto ADMINISTRADOR
    busquedaModulo: '',

    // 3. Emisión de Mensajes y Comunicados Personalizados
    mensajeForm: {
      destinatarioTipo: 'rol', // 'rol', 'usuarios', 'todos'
      rolesSeleccionados: [],  // array of IDs [4, 5, 7]
      usuariosSeleccionados: [], // array of IDs [1, 2, ...]
      tipo: 'info', // 'info', 'warning', 'error', 'success'
      titulo: '',
      mensaje: '',
      enlace: '',
      archivo: null,
      archivoNombre: '',
      archivoUrl: '',
      archivoTamano: ''
    },
    usuariosSistema: [],
    busquedaUsuarioNotif: '',
    cargandoUsuarios: false,
    enviandoMensaje: false,
    historialDifusion: [],
    cargandoHistorial: false,
    mostrarHistorial: false,

    // 4. Radicación Especial de Correspondencia (Control Total SuperAdmin)
    corrForm: {
      radicado: '',
      fecha_envio: new Date().toISOString().split('T')[0],
      tipo_correspondencia: 'INTERNA',
      asunto: '',
      procedencia: '',
      destino: ''
    },
    guardandoCorrespondencia: false,
    ultimasCorrespondencias: [],
    cargandoCorrespondencias: false,
    filtroBusquedaCorrSuperadmin: '',

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

    get usuariosFiltradosNotif() {
      if (!this.busquedaUsuarioNotif.trim()) return this.usuariosSistema;
      const q = this.busquedaUsuarioNotif.toLowerCase();
      return this.usuariosSistema.filter(u => 
        (u.nombre_completo || '').toLowerCase().includes(q) ||
        (u.correo || '').toLowerCase().includes(q) ||
        (u.rol || '').toLowerCase().includes(q)
      );
    },

    get correspondenciasFiltradasSuperadmin() {
      const q = (this.filtroBusquedaCorrSuperadmin || '').trim().toLowerCase();
      if (!q) return this.ultimasCorrespondencias;
      return this.ultimasCorrespondencias.filter(item => {
        const rad = (item.radicado || '').toLowerCase();
        const asu = (item.asunto || '').toLowerCase();
        const tip = (item.tipo_correspondencia || '').toLowerCase();
        const pro = (item.procedencia || '').toLowerCase();
        const des = (item.destino || '').toLowerCase();
        const fec = (item.fecha_envio || '').toLowerCase();
        return rad.includes(q) || asu.includes(q) || tip.includes(q) || pro.includes(q) || des.includes(q) || fec.includes(q);
      });
    },

    get resumenDestinatarios() {
      if (this.mensajeForm.destinatarioTipo === 'todos') {
        return 'Todos los roles operativos del sistema';
      }
      if (this.mensajeForm.destinatarioTipo === 'rol') {
        const cant = this.mensajeForm.rolesSeleccionados.length;
        if (cant === 0) return 'Ningún rol seleccionado';
        const nombres = this.roles
          .filter(r => this.mensajeForm.rolesSeleccionados.includes(r.id))
          .map(r => r.nombre_rol)
          .join(', ');
        return `${cant} rol(es): ${nombres}`;
      }
      if (this.mensajeForm.destinatarioTipo === 'usuarios') {
        const cant = this.mensajeForm.usuariosSeleccionados.length;
        if (cant === 0) return 'Ningún usuario seleccionado';
        return `${cant} usuario(s) seleccionado(s)`;
      }
      return '';
    },

    get totalModulosMantenimiento() {
      return (this.mantenimiento.modulos || []).length;
    },

    get permisosActivosRolActual() {
      if (this.esRolSuperAdmin) return (this.modulos.length || 0) * (this.acciones.length || 5);
      const rolId = String(this.rolSeleccionadoId);
      const rolData = this.matriz[rolId] || this.matriz[this.rolSeleccionadoId] || {};
      let activos = 0;
      for (const mod of this.modulos) {
        if (rolData[mod]) {
          for (const acc of this.acciones) {
            if (rolData[mod][acc]) activos++;
          }
        }
      }
      return activos;
    },

    get totalPermisosPosibles() {
      return (this.modulos.length || 0) * (this.acciones.length || 5);
    },

    iconoRol(nombreRol) {
      const n = (nombreRol || '').trim().toUpperCase();
      if (n === 'SUPERADMIN') return 'fa-crown';
      if (n === 'ADMINISTRADOR') return 'fa-user-gear';
      if (n === 'VIGILANTE') return 'fa-shield-halved';
      if (n.includes('DOCUMENTAL')) return 'fa-folder-tree';
      if (n === 'SST') return 'fa-helmet-safety';
      if (n === 'GESCO') return 'fa-briefcase';
      if (n === 'SCR') return 'fa-id-badge';
      return 'fa-user-tag';
    },

    colorIconoRol(nombreRol, esActivo) {
      if (esActivo) return 'text-slate-950';
      const n = (nombreRol || '').trim().toUpperCase();
      if (n === 'SUPERADMIN') return 'text-fuchsia-400';
      if (n === 'ADMINISTRADOR') return 'text-sky-400';
      if (n === 'VIGILANTE') return 'text-emerald-400';
      if (n.includes('DOCUMENTAL')) return 'text-purple-400';
      if (n === 'SST') return 'text-amber-400';
      if (n === 'GESCO') return 'text-teal-400';
      if (n === 'SCR') return 'text-rose-400';
      return 'text-slate-400';
    },

    isModuloEnMantenimiento(modId) {
      return (this.mantenimiento.modulos || []).includes(modId);
    },

    toggleModuloMantenimiento(modId) {
      if (!Array.isArray(this.mantenimiento.modulos)) {
        this.mantenimiento.modulos = [];
      }
      const idx = this.mantenimiento.modulos.indexOf(modId);
      if (idx >= 0) {
        this.mantenimiento.modulos.splice(idx, 1);
      } else {
        this.mantenimiento.modulos.push(modId);
      }
      this.mantenimiento.modulos = [...this.mantenimiento.modulos];
    },

    seleccionarTodosModulosMantenimiento(activar) {
      if (activar) {
        this.mantenimiento.modulos = this.listaModulosSistema.map(m => m.id);
      } else {
        this.mantenimiento.modulos = [];
      }
    },

    setTemporizadorPreset(minutos) {
      this.mantenimiento.temporizador_minutos = minutos;
      if (minutos < 60) {
        this.mantenimiento.tiempo = `Disponible en aproximadamente ${minutos} minutos`;
      } else {
        const horas = Math.round((minutos / 60) * 10) / 10;
        this.mantenimiento.tiempo = `Disponible en aproximadamente ${horas} hora${horas > 1 ? 's' : ''}`;
      }
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
        this.cargarMatrizPermisos(),
        this.cargarUsuariosSistema(),
        this.cargarHistorialDifusion(),
        this.cargarUltimasCorrespondencias()
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
          this.mantenimiento.tipo = data.tipo || 'general';
          this.mantenimiento.modulos = Array.isArray(data.modulos) ? data.modulos : [];
          if (data.mensaje) this.mantenimiento.mensaje = data.mensaje;
          if (data.tiempo) this.mantenimiento.tiempo = data.tiempo;
          if (data.temporizador_minutos !== undefined) this.mantenimiento.temporizador_minutos = data.temporizador_minutos;
          if (data.temporizador_fin !== undefined) this.mantenimiento.temporizador_fin = data.temporizador_fin;
          this.mantenimiento.updated_at = data.updated_at;
        }
      } catch (err) {
        console.error('Error cargando estado de mantenimiento:', err);
      }
    },

    async toggleMantenimiento(nuevoEstado) {
      const activar = nuevoEstado !== undefined ? nuevoEstado : !this.mantenimiento.activo;
      const esGeneral = this.mantenimiento.tipo === 'general';
      const cantModulos = (this.mantenimiento.modulos || []).length;

      if (activar && !esGeneral && cantModulos === 0) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Sin módulos seleccionados',
            text: 'Has seleccionado el modo por módulos, pero no has marcado ningún módulo para poner en mantenimiento. Marca al menos un módulo o cambia a modo General.',
            confirmButtonColor: '#f59e0b'
          });
        }
        return;
      }

      const titulo = activar 
        ? (esGeneral ? '¿Activar Mantenimiento GENERAL (HTTP 503)?' : `¿Activar Mantenimiento en ${cantModulos} Módulo(s)?`)
        : '¿Reanudar servicio y desactivar mantenimiento?';

      let textoDetalle = '';
      if (activar) {
        if (esGeneral) {
          textoDetalle = 'Todo el sistema responderá con Error 503 para los usuarios estándar. Tú como SUPERADMIN conservarás acceso pleno.';
        } else {
          const nombres = (this.mantenimiento.modulos || []).map(id => {
            const f = this.listaModulosSistema.find(m => m.id === id);
            return f ? f.nombre : id;
          }).slice(0, 4).join(', ');
          const resto = cantModulos > 4 ? ` y ${cantModulos - 4} más` : '';
          textoDetalle = `Solo los módulos seleccionados (${nombres}${resto}) mostrarán la pantalla 503. El resto del sistema seguirá 100% operativo para todos.`;
        }
      } else {
        textoDetalle = 'Todos los usuarios volverán a tener acceso normal a la plataforma de acuerdo con sus permisos.';
      }

      if (typeof Swal !== 'undefined') {
        const confirmacion = await Swal.fire({
          title: titulo,
          text: textoDetalle,
          icon: activar ? 'warning' : 'question',
          showCancelButton: true,
          confirmButtonText: activar ? 'Sí, aplicar mantenimiento' : 'Sí, reanudar servicio',
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
            tipo: this.mantenimiento.tipo,
            modulos: this.mantenimiento.modulos,
            mensaje: this.mantenimiento.mensaje,
            tiempo: this.mantenimiento.tiempo,
            temporizador_minutos: this.mantenimiento.temporizador_minutos
          })
        });

        const data = await res.json();
        if (res.ok && data.exito) {
          this.mantenimiento.activo = activar;
          if (data.temporizador_fin) this.mantenimiento.temporizador_fin = data.temporizador_fin;

          if (typeof Swal !== 'undefined') {
            Swal.fire({
              icon: 'success',
              title: activar ? 'Modo Mantenimiento Activado' : 'Servicio Reanudado con Éxito',
              text: activar 
                ? (esGeneral ? 'El sistema completo está ahora en mantenimiento (503) para usuarios estándar.' : `Mantenimiento activado en ${cantModulos} módulo(s).`)
                : 'La plataforma está operando con total normalidad.',
              timer: 2800,
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

    async guardarConfiguracionMantenimiento() {
      this.guardandoMantenimiento = true;
      try {
        const res = await fetch('/api/v1/superadmin/mantenimiento', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            activo: this.mantenimiento.activo,
            tipo: this.mantenimiento.tipo,
            modulos: this.mantenimiento.modulos,
            mensaje: this.mantenimiento.mensaje,
            tiempo: this.mantenimiento.tiempo,
            temporizador_minutos: this.mantenimiento.temporizador_minutos
          })
        });

        const data = await res.json();
        if (res.ok && data.exito) {
          if (data.temporizador_fin) this.mantenimiento.temporizador_fin = data.temporizador_fin;
          this.notificar('Configuración de mantenimiento y cronómetro guardada exitosamente.', 'success');
        } else {
          throw new Error(data.detail || 'Error al guardar la configuración');
        }
      } catch (err) {
        console.error('Error guardando config mantenimiento:', err);
        if (typeof Swal !== 'undefined') {
          Swal.fire({ icon: 'error', title: 'Error', text: err.message || 'Error al guardar.' });
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
        correspondencias: 'Listado de Correspondencia',
        nueva_correspondencia: 'Nueva Correspondencia (Formulario)',
        plantas: 'Gestión de Plantas y Zonas',
        contratistas: 'Gestión de Contratistas',
        vehiculos: 'Gestión de Vehículos',
        personas: 'Listado de Personas',
        procesamiento: 'Procesamiento de Solicitudes',
        antecedentes: 'Verificación de Antecedentes',
        revision_solicitud: 'Revisión y Aprobación Detallada',
        dispositivos: 'Consulta de Dispositivos',
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
        correspondencias: 'fa-envelope-open-text text-amber-400',
        nueva_correspondencia: 'fa-paper-plane text-emerald-400',
        plantas: 'fa-building text-violet-400',
        contratistas: 'fa-id-card-clip text-orange-400',
        vehiculos: 'fa-truck-front text-teal-400',
        personas: 'fa-person text-pink-400',
        procesamiento: 'fa-diagram-project text-yellow-400',
        antecedentes: 'fa-magnifying-glass-chart text-sky-400',
        revision_solicitud: 'fa-clipboard-check text-emerald-400',
        dispositivos: 'fa-laptop-code text-purple-400',
        superadmin: 'fa-shield-halved text-rose-400'
      };
      return iconos[mod] || 'fa-folder text-slate-400';
    },

    bgIconoModulo(mod) {
      const bgs = {
        dashboard: 'bg-cyan-500/15 border-cyan-500/30 text-cyan-400 shadow-cyan-500/10',
        solicitudes: 'bg-amber-500/15 border-amber-500/30 text-amber-400 shadow-amber-500/10',
        nueva_solicitud: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400 shadow-emerald-500/10',
        usuarios: 'bg-blue-500/15 border-blue-500/30 text-blue-400 shadow-blue-500/10',
        nuevo_usuario: 'bg-indigo-500/15 border-indigo-500/30 text-indigo-400 shadow-indigo-500/10',
        correspondencias: 'bg-amber-500/15 border-amber-500/30 text-amber-400 shadow-amber-500/10',
        nueva_correspondencia: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400 shadow-emerald-500/10',
        plantas: 'bg-violet-500/15 border-violet-500/30 text-violet-400 shadow-violet-500/10',
        contratistas: 'bg-orange-500/15 border-orange-500/30 text-orange-400 shadow-orange-500/10',
        vehiculos: 'bg-teal-500/15 border-teal-500/30 text-teal-400 shadow-teal-500/10',
        personas: 'bg-pink-500/15 border-pink-500/30 text-pink-400 shadow-pink-500/10',
        procesamiento: 'bg-yellow-500/15 border-yellow-500/30 text-yellow-400 shadow-yellow-500/10',
        antecedentes: 'bg-sky-500/15 border-sky-500/30 text-sky-400 shadow-sky-500/10',
        revision_solicitud: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400 shadow-emerald-500/10',
        dispositivos: 'bg-purple-500/15 border-purple-500/30 text-purple-400 shadow-purple-500/10',
        superadmin: 'bg-rose-500/15 border-rose-500/30 text-rose-400 shadow-rose-500/10'
      };
      return bgs[mod] || 'bg-slate-800 border-slate-700 text-slate-400';
    },

    // -------------------------------------------------------------
    // 3. COMUNICADOS Y MENSAJES PERSONALIZADOS
    // -------------------------------------------------------------
    async cargarUsuariosSistema() {
      this.cargandoUsuarios = true;
      try {
        const res = await fetch('/api/v1/usuarios/getAll');
        if (res.ok) {
          const data = await res.json();
          this.usuariosSistema = Array.isArray(data) ? data : [];
        }
      } catch (err) {
        console.error('Error cargando usuarios para comunicados:', err);
      } finally {
        this.cargandoUsuarios = false;
      }
    },

    async cargarHistorialDifusion() {
      this.cargandoHistorial = true;
      try {
        const res = await fetch('/api/v1/notificaciones/historial-difusion?limit=20');
        if (res.ok) {
          const data = await res.json();
          this.historialDifusion = Array.isArray(data.historial) ? data.historial : [];
        }
      } catch (err) {
        console.error('Error cargando historial de difusión:', err);
      } finally {
        this.cargandoHistorial = false;
      }
    },

    seleccionarTipoMensaje(tipo) {
      this.mensajeForm.tipo = tipo;
    },

    toggleRolNotif(rolId) {
      const idx = this.mensajeForm.rolesSeleccionados.indexOf(rolId);
      if (idx >= 0) {
        this.mensajeForm.rolesSeleccionados.splice(idx, 1);
      } else {
        this.mensajeForm.rolesSeleccionados.push(rolId);
      }
      this.mensajeForm.rolesSeleccionados = [...this.mensajeForm.rolesSeleccionados];
    },

    seleccionarTodosRolesNotif(habilitar) {
      if (habilitar) {
        this.mensajeForm.rolesSeleccionados = this.roles
          .filter(r => !r.is_superadmin && (r.nombre_rol || '').trim().toUpperCase() !== 'SUPERADMIN')
          .map(r => r.id);
      } else {
        this.mensajeForm.rolesSeleccionados = [];
      }
    },

    toggleUsuarioNotif(userId) {
      const idx = this.mensajeForm.usuariosSeleccionados.indexOf(userId);
      if (idx >= 0) {
        this.mensajeForm.usuariosSeleccionados.splice(idx, 1);
      } else {
        this.mensajeForm.usuariosSeleccionados.push(userId);
      }
      this.mensajeForm.usuariosSeleccionados = [...this.mensajeForm.usuariosSeleccionados];
    },

    seleccionarTodosUsuariosNotif(habilitar) {
      if (habilitar) {
        const filtradosIds = this.usuariosFiltradosNotif.map(u => u.id);
        const setIds = new Set([...this.mensajeForm.usuariosSeleccionados, ...filtradosIds]);
        this.mensajeForm.usuariosSeleccionados = Array.from(setIds);
      } else {
        this.mensajeForm.usuariosSeleccionados = [];
      }
    },

    limpiarFormularioMensaje() {
      this.mensajeForm = {
        destinatarioTipo: 'rol',
        rolesSeleccionados: [],
        usuariosSeleccionados: [],
        tipo: 'info',
        titulo: '',
        mensaje: '',
        enlace: '',
        archivo: null,
        archivoNombre: '',
        archivoUrl: '',
        archivoTamano: ''
      };
      this.busquedaUsuarioNotif = '';
      const input = document.getElementById('archivoAdjuntoNotifInput');
      if (input) input.value = '';
    },

    manejarArchivoNotif(event) {
      const file = event.target.files && event.target.files[0];
      if (!file) return;

      const maxBytes = 25 * 1024 * 1024;
      if (file.size > maxBytes) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'error',
            title: 'Archivo demasiado grande',
            text: 'El tamaño máximo permitido para adjuntos es de 25 MB.'
          });
        }
        event.target.value = '';
        return;
      }

      this.mensajeForm.archivo = file;
      this.mensajeForm.archivoNombre = file.name;
      
      // Formatear tamaño legible
      if (file.size < 1024) {
        this.mensajeForm.archivoTamano = file.size + ' B';
      } else if (file.size < 1024 * 1024) {
        this.mensajeForm.archivoTamano = (file.size / 1024).toFixed(1) + ' KB';
      } else {
        this.mensajeForm.archivoTamano = (file.size / (1024 * 1024)).toFixed(1) + ' MB';
      }
    },

    quitarArchivoNotif() {
      this.mensajeForm.archivo = null;
      this.mensajeForm.archivoNombre = '';
      this.mensajeForm.archivoUrl = '';
      this.mensajeForm.archivoTamano = '';
      const input = document.getElementById('archivoAdjuntoNotifInput');
      if (input) input.value = '';
    },

    obtenerIconoArchivo(nombre) {
      if (!nombre) return 'fa-file-lines text-slate-300';
      const ext = (nombre.split('.').pop() || '').toLowerCase();
      if (['pdf'].includes(ext)) return 'fa-file-pdf text-rose-400';
      if (['doc', 'docx'].includes(ext)) return 'fa-file-word text-blue-400';
      if (['xls', 'xlsx', 'csv'].includes(ext)) return 'fa-file-excel text-emerald-400';
      if (['ppt', 'pptx'].includes(ext)) return 'fa-file-powerpoint text-amber-400';
      if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return 'fa-file-zipper text-yellow-400';
      if (['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(ext)) return 'fa-file-image text-purple-400';
      return 'fa-file-lines text-slate-300';
    },

    formatearTextoEnlace(url) {
      if (!url) return '';
      const u = String(url).trim();
      try {
        if (u.startsWith('http://') || u.startsWith('https://')) {
          const parsed = new URL(u);
          const domain = parsed.hostname.replace(/^www\./, '');
          const path = parsed.pathname !== '/' ? parsed.pathname : '';
          return domain + (path.length > 25 ? path.substring(0, 20) + '…' : path);
        }
      } catch (e) {}
      return u;
    },

    formatearTiempoRelativoDifusion(fechaStr) {
      if (!fechaStr) return '';
      try {
        const fecha = new Date(fechaStr.replace(' ', 'T'));
        const ahora = new Date();
        const diffSegundos = Math.floor((ahora - fecha) / 1000);
        if (diffSegundos < 60) return 'Hace un momento';
        const diffMinutos = Math.floor(diffSegundos / 60);
        if (diffMinutos < 60) return `Hace ${diffMinutos} min`;
        const diffHoras = Math.floor(diffMinutos / 60);
        if (diffHoras < 24) return `Hace ${diffHoras} h`;
        const diffDias = Math.floor(diffHoras / 24);
        return `Hace ${diffDias} d`;
      } catch (e) {
        return fechaStr;
      }
    },

    async enviarMensajePersonalizado() {
      const form = this.mensajeForm;
      const tit = (form.titulo || '').trim();
      const msg = (form.mensaje || '').trim();

      if (!tit) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Título requerido',
            text: 'Por favor ingresa un título descriptivo para el comunicado.',
            confirmButtonColor: '#f59e0b'
          });
        }
        return;
      }
      if (!msg) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Mensaje requerido',
            text: 'Por favor redacta el cuerpo o detalle del comunicado.',
            confirmButtonColor: '#f59e0b'
          });
        }
        return;
      }

      if (form.destinatarioTipo === 'rol' && form.rolesSeleccionados.length === 0) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Sin roles seleccionados',
            text: 'Debes seleccionar al menos un rol de destino para emitir el mensaje.',
            confirmButtonColor: '#f59e0b'
          });
        }
        return;
      }

      if (form.destinatarioTipo === 'usuarios' && form.usuariosSeleccionados.length === 0) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Sin usuarios seleccionados',
            text: 'Debes marcar al menos un usuario destinatario para enviar el mensaje.',
            confirmButtonColor: '#f59e0b'
          });
        }
        return;
      }

      const resumen = this.resumenDestinatarios;
      if (typeof Swal !== 'undefined') {
        const docHtml = form.archivo
          ? `<p><strong>Documento:</strong> <span style="color:#10b981"><i class="fa-solid fa-paperclip"></i> ${form.archivoNombre} (${form.archivoTamano})</span></p>`
          : '';
        const confirm = await Swal.fire({
          title: '¿Confirmar emisión de comunicado?',
          html: `
            <div style="text-align:left; font-size:13px; line-height:1.6; margin-top:8px;">
              <p><strong>Destinatarios:</strong> <span style="color:#f59e0b">${resumen}</span></p>
              <p><strong>Tipo:</strong> <span style="text-transform:uppercase; font-family:monospace; background:#1e293b; color:#38bdf8; padding:2px 6px; border-radius:4px;">${form.tipo}</span></p>
              <p><strong>Título:</strong> ${tit}</p>
              ${docHtml}
            </div>
          `,
          icon: 'question',
          showCancelButton: true,
          confirmButtonText: 'Sí, emitir comunicado',
          cancelButtonText: 'Cancelar',
          confirmButtonColor: '#2563eb',
          cancelButtonColor: '#64748b'
        });

        if (!confirm.isConfirmed) return;
      }

      this.enviandoMensaje = true;
      try {
        let archivoUrlSubido = null;
        let archivoNombreSubido = null;

        // Si se adjuntó un archivo, subirlo primero
        if (form.archivo) {
          const formData = new FormData();
          formData.append('file', form.archivo);

          const resUpload = await fetch('/api/v1/notificaciones/subir-adjunto', {
            method: 'POST',
            body: formData
          });

          const dataUpload = await resUpload.json();
          if (!resUpload.ok || !dataUpload.exito) {
            throw new Error(dataUpload.detail || dataUpload.mensaje || 'Error al subir el archivo adjunto.');
          }

          archivoUrlSubido = dataUpload.url_archivo;
          archivoNombreSubido = dataUpload.nombre_archivo;
        }

        const payload = {
          titulo: tit,
          mensaje: msg,
          tipo: form.tipo,
          enlace: form.enlace ? form.enlace.trim() : null,
          archivo_url: archivoUrlSubido,
          archivo_nombre: archivoNombreSubido,
          destinatario_tipo: form.destinatarioTipo,
          roles_ids: form.destinatarioTipo === 'rol' ? form.rolesSeleccionados : [],
          usuarios_ids: form.destinatarioTipo === 'usuarios' ? form.usuariosSeleccionados : []
        };

        const res = await fetch('/api/v1/notificaciones/difusion', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok && data.exito) {
          if (typeof Swal !== 'undefined') {
            Swal.fire({
              icon: 'success',
              title: '¡Comunicado Emitido!',
              text: data.mensaje || 'Las notificaciones fueron entregadas en tiempo real.',
              timer: 3000,
              showConfirmButton: false
            });
          }

          this.limpiarFormularioMensaje();
          await this.cargarHistorialDifusion();
        } else {
          throw new Error(data.detail || data.mensaje || 'No fue posible emitir el comunicado.');
        }
      } catch (err) {
        console.error('Error enviando comunicado:', err);
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'error',
            title: 'Error al emitir',
            text: err.message || 'Error de conexión con el servidor.'
          });
        }
      } finally {
        this.enviandoMensaje = false;
      }
    },

    // -------------------------------------------------------------
    // 4. RADICACIÓN ESPECIAL DE CORRESPONDENCIA (SUPERADMIN)
    // -------------------------------------------------------------
    async cargarUltimasCorrespondencias() {
      this.cargandoCorrespondencias = true;
      try {
        let res = await fetch('/api/v1/correspondencia/getAll');
        if (!res.ok) {
          res = await fetch('/correspondencia/getAll');
        }
        const data = await res.json().catch(() => ({}));
        if (data.exito && Array.isArray(data.data)) {
          // Ordenar de más reciente a más antiguo por id / fecha y mostrar solo las últimas 3
          const lista = [...data.data].sort((a, b) => (b.id || 0) - (a.id || 0));
          this.ultimasCorrespondencias = lista.slice(0, 3);
        }
      } catch (err) {
        console.error('Error al cargar correspondencias:', err);
      } finally {
        this.cargandoCorrespondencias = false;
      }
    },

    initFlatpickrCorrespondencia(el) {
      if (!el || typeof flatpickr === 'undefined') return;
      if (this.fpCorrInstance) {
        try { this.fpCorrInstance.destroy(); } catch (e) {}
      }
      this.fpCorrInstance = flatpickr(el, {
        locale: flatpickr.l10ns?.es || 'es',
        dateFormat: 'Y-m-d',
        altInput: true,
        altFormat: 'd/m/Y',
        altInputClass: 'input-field w-full rounded-xl pl-3.5 pr-10 py-2.5 text-sm bg-slate-900 border border-slate-700 text-white font-medium focus:border-fuchsia-500 focus:ring-2 focus:ring-fuchsia-500/20 cursor-pointer shadow-inner',
        defaultDate: this.corrForm.fecha_envio || new Date(),
        disableMobile: true,
        onChange: (selectedDates, dateStr) => {
          this.corrForm.fecha_envio = dateStr;
        }
      });
    },

    abrirCalendarioCorrespondencia() {
      if (this.fpCorrInstance) {
        this.fpCorrInstance.open();
      }
    },

    limpiarFormularioCorrespondencia() {
      const hoy = new Date().toISOString().split('T')[0];
      this.corrForm = {
        radicado: '',
        fecha_envio: hoy,
        tipo_correspondencia: 'INTERNA',
        asunto: '',
        procedencia: '',
        destino: ''
      };
      if (this.fpCorrInstance) {
        this.fpCorrInstance.setDate(hoy, true);
      }
    },

    copiarTextoAlPortapapeles(texto) {
      if (!texto) return;
      navigator.clipboard.writeText(texto).then(() => {
        if (typeof Swal !== 'undefined') {
          const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 2000,
            timerProgressBar: true
          });
          Toast.fire({
            icon: 'success',
            title: `Copiado: ${texto}`
          });
        }
      }).catch(() => {});
    },

    formatearFechaCorta(fecha) {
      if (!fecha) return '—';
      const f = String(fecha).split('T')[0].trim();
      const partes = f.split('-');
      const mesesCortos = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
      if (partes.length === 3) {
        const dia = String(parseInt(partes[2], 10)).padStart(2, '0');
        const mIdx = parseInt(partes[1], 10) - 1;
        const anio = partes[0];
        const mesNom = mesesCortos[mIdx] || partes[1];
        return `${dia} ${mesNom} ${anio}`;
      }
      return f;
    },

    async registrarCorrespondenciaSuperAdmin() {
      const f = this.corrForm;
      if (!f.tipo_correspondencia || !f.asunto.trim() || !f.procedencia.trim() || !f.destino.trim()) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Campos Incompletos',
            text: 'Por favor diligencia el asunto, procedencia y destino de la correspondencia.',
            confirmButtonColor: '#d946ef'
          });
        }
        return;
      }

      this.guardandoCorrespondencia = true;
      try {
        const payload = {
          tipo_correspondencia: f.tipo_correspondencia,
          asunto: f.asunto.trim(),
          procedencia: f.procedencia.trim(),
          destino: f.destino.trim(),
          fecha_envio: f.fecha_envio || undefined,
          radicado: f.radicado ? f.radicado.trim() : undefined
        };

        let res = await fetch('/api/v1/correspondencia', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok && res.status === 404) {
          res = await fetch('/correspondencia', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        }

        const data = await res.json().catch(() => ({}));

        if (!res.ok || data.exito === false) {
          throw new Error(data.detail || data.mensaje || 'Error al registrar la correspondencia.');
        }

        const radicadoAsignado = data.radicado || ('SCR-' + String(data.id_generado || '').padStart(3, '0'));
        const fechaRaw = f.fecha_envio || (new Date()).toISOString().split('T')[0];
        const fechaAsignada = this.formatearFechaCorta(fechaRaw);

        const esInterna = f.tipo_correspondencia === 'INTERNA';
        const tipoBg = esInterna ? 'rgba(6, 182, 212, 0.16)' : 'rgba(245, 158, 11, 0.16)';
        const tipoColor = esInterna ? '#38bdf8' : '#fbbf24';
        const tipoBorder = esInterna ? 'rgba(56, 189, 248, 0.45)' : 'rgba(251, 191, 36, 0.45)';
        const tipoIcon = esInterna ? 'fa-building' : 'fa-paper-plane';

        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'success',
            title: '¡Correspondencia Radicada!',
            background: '#0f172a',
            color: '#f8fafc',
            html: `
              <div style="text-align: left; padding: 2px 2px; font-size: 0.88rem; line-height: 1.5;">
                <p style="margin-bottom: 8px; font-size: 0.85rem; color: #94a3b8;">La correspondencia fue ingresada al sistema con éxito con permisos SuperAdmin.</p>

                <!-- TICKET DE RADICACIÓN TIPO COMPROBANTE -->
                <div class="superadmin-ticket-card">
                  <div class="superadmin-ticket-notch-left"></div>
                  <div class="superadmin-ticket-notch-right"></div>

                  <!-- Cabecera del Ticket -->
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="display: inline-flex; align-items: center; gap: 5px; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; background: rgba(217, 70, 239, 0.18); color: #f0abfc; border: 1px solid rgba(217, 70, 239, 0.35); padding: 3px 8px; border-radius: 6px;">
                      <i class="fa-solid fa-receipt"></i> TICKET OFICIAL DE RADICACIÓN
                    </span>
                    <span style="font-size: 0.68rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.05em;">
                      NIVEL 6 • MAESTRO
                    </span>
                  </div>

                  <!-- Código / Radicado Principal -->
                  <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 12px;">
                    <div>
                      <div style="font-size: 0.7rem; text-transform: uppercase; font-weight: 700; color: #94a3b8; letter-spacing: 0.06em; margin-bottom: 2px;">CÓDIGO / RADICADO</div>
                      <div style="font-family: monospace; font-size: 1.45rem; font-weight: 900; color: #38bdf8; letter-spacing: 0.06em; text-shadow: 0 0 14px rgba(56, 189, 248, 0.45); line-height: 1.1;">
                        ${radicadoAsignado}
                      </div>
                    </div>
                    <div style="text-align: right;">
                      <span style="display: inline-flex; align-items: center; gap: 4px; padding: 3px 9px; border-radius: 9999px; font-size: 0.72rem; font-weight: 800; background: ${tipoBg}; color: ${tipoColor}; border: 1px solid ${tipoBorder};">
                        <i class="fa-solid ${tipoIcon}" style="font-size: 0.65rem;"></i> ${f.tipo_correspondencia}
                      </span>
                    </div>
                  </div>

                  <!-- Línea divisoria perforada de corte -->
                  <div class="superadmin-ticket-divider"></div>

                  <!-- Metadatos: Fecha Asignada y Asunto -->
                  <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.82rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                      <span style="color: #a855f7; font-weight: 700; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; display: inline-flex; align-items: center; gap: 6px;">
                        <i class="fa-regular fa-calendar-check" style="color: #d946ef;"></i> FECHA ASIGNADA:
                      </span>
                      <strong style="color: #f0abfc; font-family: monospace; font-weight: 800; font-size: 0.95rem; letter-spacing: 0.03em;">
                        ${fechaAsignada}
                      </strong>
                    </div>

                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;">
                      <span style="color: #94a3b8; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; display: inline-flex; align-items: center; gap: 6px; flex-shrink: 0;">
                        <i class="fa-regular fa-file-lines" style="color: #c084fc;"></i> Asunto:
                      </span>
                      <span style="color: #e2e8f0; font-size: 0.8rem; font-weight: 600; text-align: right; max-width: 230px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${f.asunto.trim()}">
                        ${f.asunto.trim()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            `,
            confirmButtonText: 'Aceptar',
            confirmButtonColor: '#d946ef'
          });
        }

        this.limpiarFormularioCorrespondencia();
        await this.cargarUltimasCorrespondencias();
      } catch (err) {
        console.error('Error al registrar correspondencia SuperAdmin:', err);
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'error',
            title: 'Error de Radicación',
            text: err.message || 'No fue posible registrar la correspondencia.',
            confirmButtonColor: '#ef4444'
          });
        }
      } finally {
        this.guardandoCorrespondencia = false;
      }
    }
  };
}

