/**
 * permisos.js — Sistema Global de Control de Acceso Basado en Roles (RBAC) y Permisos Dinámicos (INCARSA)
 * 
 * Gestiona:
 * - Validación de roles activos (`window.tieneRol`).
 * - Caché y recarga en caliente de matriz de permisos por usuario (`window.recargarMisPermisos`).
 * - Comprobación granular de acceso a módulos (`window.puedeModulo`).
 * - Comprobación granular de permisos de acción: ver, crear, editar, eliminar, aprobar (`window.puedeAccion`).
 * - Regla de negocio para edición condicional de solicitudes (`window.puedeEditarSolicitud`).
 */

(function () {
  'use strict';

  /**
   * Valida si el usuario activo posee alguno de los roles solicitados.
   * El rol 'SUPERADMIN' tiene bypass total automático.
   */
  function tieneRol(...roles) {
    let sesion = null;
    if (typeof getAuthSession === 'function') {
      sesion = getAuthSession();
    } else {
      try {
        sesion = JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || 'null');
      } catch (e) {}
    }

    const miRol = (sesion?.rol || 'ADMINISTRADOR').trim().toUpperCase();

    // SuperAdmin tiene acceso total automático
    if (miRol === 'SUPERADMIN') {
      return true;
    }

    const listaRoles = roles.flat().filter(Boolean).map(r => String(r).trim().toUpperCase());
    return listaRoles.includes(miRol);
  }
  window.tieneRol = tieneRol;

  /**
   * Permisos dinámicos cacheados en memoria / storage
   */
  window.permisosActivos = (function () {
    try {
      return JSON.parse(sessionStorage.getItem('incarsa_permisos') || localStorage.getItem('incarsa_permisos') || 'null');
    } catch (e) {
      return null;
    }
  })();

  /**
   * Consulta al endpoint de permisos del backend para refrescar la matriz en caliente
   */
  async function recargarMisPermisos() {
    try {
      const token = (typeof getAuthToken === 'function') ? getAuthToken() : null;
      if (!token) return {};

      const res = await fetch('/api/v1/roles/mis-permisos');
      if (res.ok) {
        const data = await res.json();
        if (data && data.permisos) {
          sessionStorage.setItem('incarsa_permisos', JSON.stringify(data.permisos));
          localStorage.setItem('incarsa_permisos', JSON.stringify(data.permisos));
          window.permisosActivos = data.permisos;
          window.dispatchEvent(new CustomEvent('permisos-actualizados', { detail: data.permisos }));
          return data.permisos;
        }
      }
    } catch (e) {
      console.warn('Aviso cargando permisos dinámicos:', e);
    }
    return {};
  }
  window.recargarMisPermisos = recargarMisPermisos;

  /**
   * Verifica si el usuario activo tiene permiso para ver/acceder a un módulo específico
   */
  function puedeModulo(modulo) {
    let sesion = null;
    if (typeof getAuthSession === 'function') {
      sesion = getAuthSession();
    } else {
      try {
        sesion = JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || 'null');
      } catch (e) {}
    }

    const miRol = (sesion?.rol || '').trim().toUpperCase();
    if (miRol === 'SUPERADMIN') return true;

    try {
      const permisos = window.permisosActivos || JSON.parse(sessionStorage.getItem('incarsa_permisos') || localStorage.getItem('incarsa_permisos') || 'null');
      const modKey = (modulo === 'seguridadsocial') ? 'seguridad_social' : modulo;
      if (permisos && permisos[modKey] && permisos[modKey].ver !== undefined) {
        return !!permisos[modKey].ver;
      }
    } catch (e) {}

    // Fallbacks de compatibilidad por rol si no se ha cargado la matriz
    const fallbacks = {
      'dashboard': true,
      'solicitudes': true,
      'nueva_solicitud': ['ADMINISTRADOR', 'GESTION DOCUMENTAL', 'SST', 'GESCO', 'SCR'].includes(miRol),
      'usuarios': ['ADMINISTRADOR'].includes(miRol),
      'nuevo_usuario': ['ADMINISTRADOR', 'SCR'].includes(miRol),
      'plantas': ['ADMINISTRADOR', 'SCR'].includes(miRol),
      'contratistas': ['ADMINISTRADOR', 'SCR', 'GESTION DOCUMENTAL'].includes(miRol),
      'vehiculos': ['ADMINISTRADOR', 'SCR', 'GESTION DOCUMENTAL'].includes(miRol),
      'dispositivos': ['ADMINISTRADOR', 'SCR', 'GESTION DOCUMENTAL', 'SST', 'GESCO'].includes(miRol),
      'personas': true,
      'procesamiento': ['ADMINISTRADOR', 'SST', 'GESCO', 'SCR', 'GESTION DOCUMENTAL'].includes(miRol),
      'antecedentes': ['ADMINISTRADOR', 'SCR'].includes(miRol),
      'seguridad_social': ['ADMINISTRADOR', 'SST'].includes(miRol),
      'inducciones': ['ADMINISTRADOR', 'GESCO', 'SCR', 'SST'].includes(miRol),
      'correspondencias': true,
      'nueva_correspondencia': true,
      'superadmin': miRol === 'SUPERADMIN'
    };

    return fallbacks[modulo] !== undefined ? fallbacks[modulo] : true;
  }
  window.puedeModulo = puedeModulo;

  /**
   * Verifica si el usuario activo puede ejecutar una acción (ver, crear, editar, eliminar, aprobar) en un módulo
   */
  function puedeAccion(modulo, accion) {
    let sesion = null;
    if (typeof getAuthSession === 'function') {
      sesion = getAuthSession();
    } else {
      try {
        sesion = JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || 'null');
      } catch (e) {}
    }

    const miRol = (sesion?.rol || '').trim().toUpperCase();
    if (miRol === 'SUPERADMIN') return true;

    try {
      const permisos = window.permisosActivos || JSON.parse(sessionStorage.getItem('incarsa_permisos') || localStorage.getItem('incarsa_permisos') || 'null');
      const modKey = (modulo === 'seguridadsocial') ? 'seguridad_social' : modulo;
      if (permisos && permisos[modKey] && permisos[modKey][accion] !== undefined) {
        return !!permisos[modKey][accion];
      }
    } catch (e) {}

    // Por defecto el administrador y SST tienen permiso de acción en seguridad social
    if (miRol === 'ADMINISTRADOR') return true;
    if (miRol === 'SST' && (modulo === 'seguridad_social' || modulo === 'seguridadsocial')) return true;
    return false;
  }
  window.puedeAccion = puedeAccion;

  /**
   * Regla de negocio: Determina si una solicitud puede ser editada por el usuario
   * - SuperAdmin siempre puede editar
   * - Los demás usuarios requieren permiso y que la solicitud esté en estado 'ENVIADO'
   */
  function puedeEditarSolicitud(solicitud) {
    if (!solicitud) return false;
    let sesion = null;
    if (typeof getAuthSession === 'function') {
      sesion = getAuthSession();
    } else {
      try {
        sesion = JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || 'null');
      } catch (e) {}
    }

    const miRol = (sesion?.rol || '').trim().toUpperCase();
    if (miRol === 'SUPERADMIN') return true;

    if (!puedeAccion('solicitudes', 'editar') && !puedeAccion('dashboard', 'editar')) {
      return false;
    }

    const est = String(solicitud.estado || '').trim().toUpperCase();
    return est === 'ENVIADO' || est === 'PRE-ENVIADO';
  }

  function puedeGenerarFormularioTemporal() {
    let sesion = null;
    if (typeof getAuthSession === 'function') {
      sesion = getAuthSession();
    } else {
      try {
        sesion = JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || 'null');
      } catch (e) {}
    }
    if (!sesion) return true;
    const idRol = parseInt(sesion.id_rol || sesion.rol_id, 10);
    const rolNom = String(sesion.rol || sesion.nombre_rol || '').toUpperCase();
    return idRol === 5 || idRol === 1 || idRol === 2 ||
           rolNom.includes('SOLICITANTE') ||
           rolNom.includes('GESTION DOCUMENTAL') ||
           rolNom.includes('GESTIÓN DOCUMENTAL') ||
           rolNom.includes('ADMIN');
  }
  window.puedeGenerarFormularioTemporal = puedeGenerarFormularioTemporal;
  window.puedeEditarSolicitud = puedeEditarSolicitud;

  /**
   * Guardián de navegación síncrono.
   * Valida si el usuario está autenticado y si tiene autorización (RBAC) para la ruta actual.
   * Redirige a /login o /403 si el acceso no es permitido.
   */
  function validarRutaActual() {
    try {
      const token = (typeof getAuthToken === 'function') 
        ? getAuthToken() 
        : (sessionStorage.getItem('incarsa_token') || localStorage.getItem('incarsa_token'));
      
      const path = (window.location.pathname || '').toLowerCase();
      
      // Rutas universales / libres de validación
      if (
        path === '/' ||
        path === '/dashboard' ||
        path.includes('/revision') ||
        path.includes('/login') ||
        path.includes('/403') ||
        path.includes('/404') ||
        path.includes('/500') ||
        path.includes('/503') ||
        path.includes('/splash-loading') ||
        path.includes('/cargando') ||
        path.includes('/formulario-temporal') ||
        path.includes('/autorizacion-datos')
      ) {
        return true;
      }

      // Si no hay token de autenticación, redirigir a login
      if (!token) {
        window.location.replace('/login');
        return false;
      }

      // Si es SuperAdmin, acceso total irrestricto
      if (tieneRol('SUPERADMIN')) {
        return true;
      }

      let denegado = false;

      // Rutas del Formulario de Usuarios (crear / editar)
      const esFormularioUsuario = 
        path === '/usuarios/nuevo' || 
        path === '/usuarios/nueva' || 
        path.startsWith('/usuarios/editar') || 
        path.includes('formulario-usuarios') || 
        path.includes('usuario-formulario');

      const esListadoUsuarios = !esFormularioUsuario && (path === '/usuarios' || path.startsWith('/usuarios/'));
      const esNuevaSolicitud = path === '/solicitudes/nueva' || path.includes('formulario-solicitudes') || path.includes('solicitudes-formulario');
      const esProcesamiento = path === '/procesamiento' || path.startsWith('/procesamiento/');
      const esAntecedentes = path === '/antecedentes' || path.startsWith('/antecedentes/');
      const esSuperAdmin = path === '/superadmin' || path.startsWith('/superadmin/');

      function checkRuta() {
        if (esFormularioUsuario) {
          return puedeModulo('nuevo_usuario') || puedeModulo('usuarios');
        }
        if (esListadoUsuarios) {
          return puedeModulo('usuarios');
        }
        if (esNuevaSolicitud) {
          return puedeModulo('nueva_solicitud');
        }
        if (esProcesamiento) {
          return puedeModulo('procesamiento');
        }
        if (esAntecedentes) {
          return puedeModulo('antecedentes');
        }
        if (esSuperAdmin) {
          return puedeModulo('superadmin');
        }
        return true;
      }

      if (!checkRuta()) {
        denegado = true;
      }

      if (denegado) {
        // Antes de redirigir a 403, intentamos refrescar permisos del backend
        // para evitar falsos positivos por caché local o cambios recientes en la matriz
        recargarMisPermisos().then(permisosFrescos => {
          if (permisosFrescos && Object.keys(permisosFrescos).length > 0) {
            if (checkRuta()) {
              // Permiso concedido tras refresco, no redirigir a 403
              return;
            }
          }
          console.warn('⛔ [RBAC] Acceso denegado a la ruta ' + path + ' para el usuario actual.');
          window.location.replace('/403');
        }).catch(() => {
          console.warn('⛔ [RBAC] Acceso denegado a la ruta ' + path + ' para el usuario actual.');
          window.location.replace('/403');
        });
        return false;
      }

      return true;
    } catch (e) {
      console.warn('Error en guardián de permisos:', e);
      return true;
    }
  }
  window.validarRutaActual = validarRutaActual;

  // Ejecución inmediata del guardián al cargarse el script para evitar FOUC
  validarRutaActual();

  // Auto-sincronizar permisos frescos si el usuario tiene sesión activa
  document.addEventListener('DOMContentLoaded', () => {
    const token = (typeof getAuthToken === 'function') ? getAuthToken() : null;
    if (token) {
      recargarMisPermisos();
    }
  });

})();
