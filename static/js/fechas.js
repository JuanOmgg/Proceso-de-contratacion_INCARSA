
/**
 * INCARSA - Sistema de Gestión de Solicitudes y Contratistas
 * fechas.js - Módulo Centralizado y Unificado de Manejo y Formateo de Fechas
 * 
 * Expone utilidades globales en `window` y en el espacio de nombres `window.Fechas`.
 * Compatible de forma nativa con Alpine.js, Jinja2 y Flatpickr.
 */

(function () {
  'use strict';

  const MESES_CORTOS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
  const MESES_LARGOS = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
  ];

  /**
   * Parsea de forma segura cualquier string de fecha o Date a un objeto Date local,
   * evitando el bug clásico de desfase de un día por conversión UTC en JavaScript.
   */
  function parsearFechaLocal(fechaStr) {
    if (!fechaStr || fechaStr === '—' || fechaStr === '-' || fechaStr === 'None' || fechaStr === 'null' || fechaStr === 'Pendiente' || fechaStr === 'No registrada') {
      return null;
    }
    if (fechaStr instanceof Date) {
      return isNaN(fechaStr.getTime()) ? null : fechaStr;
    }

    try {
      const raw = String(fechaStr).trim();

      // Formato YYYY-MM-DD o YYYY-MM-DD HH:MM:SS o con T
      const matchIso = raw.match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?/);
      if (matchIso) {
        const y = parseInt(matchIso[1], 10);
        const m = parseInt(matchIso[2], 10) - 1;
        const d = parseInt(matchIso[3], 10);
        const hh = matchIso[4] !== undefined ? parseInt(matchIso[4], 10) : 0;
        const mm = matchIso[5] !== undefined ? parseInt(matchIso[5], 10) : 0;
        const ss = matchIso[6] !== undefined ? parseInt(matchIso[6], 10) : 0;
        return new Date(y, m, d, hh, mm, ss);
      }

      // Formato DD/MM/YYYY o DD-MM-YYYY
      const matchLatam = raw.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?/);
      if (matchLatam) {
        const d = parseInt(matchLatam[1], 10);
        const m = parseInt(matchLatam[2], 10) - 1;
        const y = parseInt(matchLatam[3], 10);
        const hh = matchLatam[4] !== undefined ? parseInt(matchLatam[4], 10) : 0;
        const mm = matchLatam[5] !== undefined ? parseInt(matchLatam[5], 10) : 0;
        const ss = matchLatam[6] !== undefined ? parseInt(matchLatam[6], 10) : 0;
        return new Date(y, m, d, hh, mm, ss);
      }

      // Formato español texto: "29 Sep 2026" o "29 septiembre 2026"
      const matchEsp = raw.match(/^(\d{1,2})\s+([a-zA-ZáéíóúñÁÉÍÓÚÑ]{3,12})\s+(\d{4})(?:[,\s]+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM)?)?/i);
      if (matchEsp) {
        const d = parseInt(matchEsp[1], 10);
        const mesTexto = matchEsp[2].toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').slice(0, 3);
        const mesesMap = { ene: 0, feb: 1, mar: 2, abr: 3, may: 4, jun: 5, jul: 6, ago: 7, sep: 8, oct: 9, nov: 10, dic: 11 };
        const m = mesesMap[mesTexto] !== undefined ? mesesMap[mesTexto] : -1;
        const y = parseInt(matchEsp[3], 10);
        if (m !== -1) {
          let hh = matchEsp[4] !== undefined ? parseInt(matchEsp[4], 10) : 0;
          const mm = matchEsp[5] !== undefined ? parseInt(matchEsp[5], 10) : 0;
          const ss = matchEsp[6] !== undefined ? parseInt(matchEsp[6], 10) : 0;
          const ampm = (matchEsp[7] || '').toUpperCase();
          if (ampm === 'PM' && hh < 12) hh += 12;
          if (ampm === 'AM' && hh === 12) hh = 0;
          return new Date(y, m, d, hh, mm, ss);
        }
      }

      // Fallback genérico de Date
      const dGen = new Date(raw);
      return isNaN(dGen.getTime()) ? null : dGen;
    } catch (e) {
      return null;
    }
  }

  /**
   * Formatea una fecha con hora en formato español amigable de 12 horas con AM/PM.
   * Ej: "2026-09-24 10:10:00" -> "24 Sep 2026, 10:10 AM"
   * Si no tiene hora: "24 Sep 2026"
   */
  function formatearFechaHora(fechaStr) {
    if (!fechaStr || fechaStr === '—' || fechaStr === '-' || fechaStr === 'None' || fechaStr === 'null') {
      return '—';
    }

    const d = parsearFechaLocal(fechaStr);
    if (!d) return String(fechaStr);

    const dia = String(d.getDate()).padStart(2, '0');
    const mes = MESES_CORTOS[d.getMonth()] || '';
    const anio = d.getFullYear();

    const raw = String(fechaStr).trim();
    const tieneHora = /[ T]\d{1,2}:\d{2}/.test(raw);

    if (tieneHora) {
      let hh = d.getHours();
      const mm = String(d.getMinutes()).padStart(2, '0');
      const ampm = hh >= 12 ? 'PM' : 'AM';
      hh = hh % 12 || 12;
      return `${dia} ${mes} ${anio}, ${String(hh).padStart(2, '0')}:${mm} ${ampm}`;
    }

    return `${dia} ${mes} ${anio}`;
  }

  /**
   * Formato corto para tablas y listados.
   * Ej: "2026-09-24" -> "24 Sep 2026"
   */
  function formatearFechaCorta(fechaStr) {
    if (!fechaStr || fechaStr === '—' || fechaStr === '-' || fechaStr === 'None' || fechaStr === 'null' || fechaStr === 'undefined') {
      return '—';
    }

    const d = parsearFechaLocal(fechaStr);
    if (!d) {
      const limpia = String(fechaStr).split('T')[0].split(',')[0].split(' ')[0].trim();
      return (limpia && limpia !== 'null' && limpia !== 'undefined') ? limpia : '—';
    }

    const dia = String(d.getDate()).padStart(2, '0');
    const mes = MESES_CORTOS[d.getMonth()] || '';
    const anio = d.getFullYear();
    return `${dia} ${mes} ${anio}`;
  }

  /**
   * Formato numérico tradicional latinoamericano DD/MM/YYYY.
   * Ej: "2026-09-24" -> "24/09/2026"
   */
  function formatearSoloFecha(fechaStr) {
    if (!fechaStr || fechaStr === '—' || fechaStr === '-' || fechaStr === 'None' || fechaStr === 'null') {
      return '—';
    }

    const d = parsearFechaLocal(fechaStr);
    if (!d) return String(fechaStr);

    const dia = String(d.getDate()).padStart(2, '0');
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const anio = d.getFullYear();
    return `${dia}/${mes}/${anio}`;
  }

  /**
   * Formateador genérico con opción de incluir hora o no.
   */
  function formatearFecha(fechaStr, incluirHora = false) {
    if (!fechaStr || fechaStr === '—' || fechaStr === '-' || fechaStr === 'None' || fechaStr === 'null' || fechaStr === 'Pendiente' || fechaStr === 'No registrada') {
      return incluirHora ? 'No registrada' : 'Pendiente';
    }
    return incluirHora ? formatearFechaHora(fechaStr) : formatearFechaCorta(fechaStr);
  }

  /**
   * Formatea un rango de fechas de ingreso y salida.
   * Ej: "24 Sep 2026 → 28 Sep 2026"
   */
  function formatearRangoFechas(fechaInicio, fechaFin) {
    const f1 = formatearFechaCorta(fechaInicio);
    const f2 = formatearFechaCorta(fechaFin);
    const v1 = f1 && f1 !== '—';
    const v2 = f2 && f2 !== '—';

    if (v1 && v2) return `${f1} → ${f2}`;
    if (v1) return `Desde ${f1}`;
    if (v2) return `Hasta ${f2}`;
    return '—';
  }

  /**
   * Formatea un rango de fechas con tags HTML para renderizar con flecha estilizada.
   */
  function formatearRangoFechasHtml(fechaInicio, fechaFin) {
    const f1 = formatearFechaCorta(fechaInicio);
    const f2 = formatearFechaCorta(fechaFin);
    const v1 = f1 && f1 !== '—';
    const v2 = f2 && f2 !== '—';

    if (v1 && v2) {
      return `<span class="font-medium text-slate-700 dark:text-slate-200">${f1}</span><span class="text-slate-400 dark:text-slate-500 mx-1.5 font-normal">→</span><span class="font-medium text-slate-700 dark:text-slate-200">${f2}</span>`;
    }
    if (v1) {
      return `<span class="text-slate-400 dark:text-slate-500">Desde</span> <span class="font-medium text-slate-700 dark:text-slate-200">${f1}</span>`;
    }
    if (v2) {
      return `<span class="text-slate-400 dark:text-slate-500">Hasta</span> <span class="font-medium text-slate-700 dark:text-slate-200">${f2}</span>`;
    }
    return `<span class="text-slate-400 dark:text-slate-500">Por definir</span>`;
  }

  /**
   * Tiempos relativos amigables para el centro de notificaciones y feed en vivo.
   * Ej: "Hace un momento", "Hace 15 min", "Hace 2 h", "Ayer", "Hace 4 d"
   */
  function formatearTiempoRelativo(fechaStr) {
    if (!fechaStr) return '';
    const fecha = parsearFechaLocal(fechaStr);
    if (!fecha) return String(fechaStr || '');

    const ahora = new Date();
    const diffSegundos = Math.floor((ahora.getTime() - fecha.getTime()) / 1000);

    if (diffSegundos < 60) return 'Hace un momento';
    const diffMinutos = Math.floor(diffSegundos / 60);
    if (diffMinutos < 60) return `Hace ${diffMinutos} min`;
    const diffHoras = Math.floor(diffMinutos / 60);
    if (diffHoras < 24) return `Hace ${diffHoras} h`;
    const diffDias = Math.floor(diffHoras / 24);
    if (diffDias === 1) return 'Ayer';
    if (diffDias < 7) return `Hace ${diffDias} d`;

    const dia = fecha.getDate();
    const mes = MESES_CORTOS[fecha.getMonth()] || '';
    return `${dia} ${mes}`;
  }

  /**
   * Semáforo unificado de Vigencia (SST, Antecedentes, Inducciones).
   * Calcula días restantes contra la medianoche de hoy y genera los metadatos visuales.
   */
  function getEstadoVigencia(fechaVigenciaStr) {
    if (!fechaVigenciaStr || fechaVigenciaStr === 'None' || fechaVigenciaStr === 'null' || fechaVigenciaStr === 'Pendiente' || fechaVigenciaStr === 'No registrada' || fechaVigenciaStr === '—') {
      return {
        estado: 'sin_revision',
        etiqueta: 'Sin revisión',
        textoDias: 'Sin revisión',
        icono: 'fa-solid fa-circle-question',
        badgeClass: 'bg-slate-500/20 text-slate-700 dark:text-slate-100 border-slate-400/40 vigencia-badge-neon is-sin-revision',
        dotClass: 'bg-slate-400',
        dias: null
      };
    }

    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);

    const fechaLimite = parsearFechaLocal(fechaVigenciaStr);
    if (!fechaLimite || isNaN(fechaLimite.getTime())) {
      return {
        estado: 'sin_revision',
        etiqueta: 'Fecha inválida',
        textoDias: 'Fecha inválida',
        icono: 'fa-solid fa-circle-question',
        badgeClass: 'bg-slate-500/20 text-slate-700 dark:text-slate-100 border-slate-400/40 vigencia-badge-neon is-sin-revision',
        dotClass: 'bg-slate-400',
        dias: null
      };
    }
    fechaLimite.setHours(0, 0, 0, 0);

    const diffMs = fechaLimite.getTime() - hoy.getTime();
    const diffDias = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    if (diffDias < 0) {
      const diasVencidos = Math.abs(diffDias);
      return {
        estado: 'vencido',
        etiqueta: `Vencido (${diasVencidos}d)`,
        textoDias: `Vencido hace ${diasVencidos} ${diasVencidos === 1 ? 'día' : 'días'}`,
        icono: 'fa-solid fa-circle-xmark',
        badgeClass: 'bg-red-500/20 text-red-700 dark:text-red-200 border-red-400/40 vigencia-badge-neon is-vencido',
        dotClass: 'bg-red-500',
        dias: diffDias
      };
    } else if (diffDias === 0) {
      return {
        estado: 'por_vencer',
        etiqueta: 'Vence hoy',
        textoDias: 'Vence hoy',
        icono: 'fa-solid fa-triangle-exclamation',
        badgeClass: 'bg-amber-500/20 text-amber-700 dark:text-amber-200 border-amber-400/40 vigencia-badge-neon is-por-vencer',
        dotClass: 'bg-amber-500',
        dias: 0
      };
    } else if (diffDias <= 30) {
      return {
        estado: 'por_vencer',
        etiqueta: `Por vencer (${diffDias}d)`,
        textoDias: `${diffDias} ${diffDias === 1 ? 'día restante' : 'días restantes'}`,
        icono: 'fa-solid fa-triangle-exclamation',
        badgeClass: 'bg-amber-500/20 text-amber-700 dark:text-amber-200 border-amber-400/40 vigencia-badge-neon is-por-vencer',
        dotClass: 'bg-amber-500',
        dias: diffDias
      };
    } else {
      return {
        estado: 'vigente',
        etiqueta: `Vigente (${diffDias}d)`,
        textoDias: `${diffDias} días restantes`,
        icono: 'fa-solid fa-circle-check',
        badgeClass: 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-200 border-emerald-400/40 vigencia-badge-neon is-vigente',
        dotClass: 'bg-emerald-500',
        dias: diffDias
      };
    }
  }

  /**
   * Calcula exactamente 1 año después de una fecha base (ISO YYYY-MM-DD).
   * Utilizado en el módulo de Inducciones.
   */
  function obtenerFechaMasUnAnio(fechaBase) {
    const d = fechaBase ? (parsearFechaLocal(fechaBase) || new Date()) : new Date();
    d.setFullYear(d.getFullYear() + 1);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  /**
   * Recorta una URL larga para mostrarla en notificaciones sin romper el layout.
   */
  function formatearTextoEnlace(url) {
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
  }

  // Objeto Namespace Unificado
  const Fechas = {
    parsear: parsearFechaLocal,
    parsearFechaLocal: parsearFechaLocal,
    formatearFechaHora: formatearFechaHora,
    formatearFechaHoraEspanol: formatearFechaHora,
    formatearCorta: formatearFechaCorta,
    formatearFechaCorta: formatearFechaCorta,
    formatearSoloFecha: formatearSoloFecha,
    formatearFecha: formatearFecha,
    formatearRango: formatearRangoFechas,
    formatearRangoFechas: formatearRangoFechas,
    formatearRangoFechasHtml: formatearRangoFechasHtml,
    tiempoRelativo: formatearTiempoRelativo,
    formatearTiempoRelativo: formatearTiempoRelativo,
    formatearTextoEnlace: formatearTextoEnlace,
    getEstadoVigencia: getEstadoVigencia,
    getEstadoVigenciaSS: getEstadoVigencia,
    getEstadoVigenciaInduccion: getEstadoVigencia,
    obtenerFechaMasUnAnio: obtenerFechaMasUnAnio
  };

  // Exposición en Window: como Namespace y como funciones globales para Alpine.js
  window.Fechas = Fechas;
  window.parsearFechaLocal = parsearFechaLocal;
  window.formatearFechaHora = formatearFechaHora;
  window.formatearFechaHoraEspanol = formatearFechaHora;
  window.formatearFechaCorta = formatearFechaCorta;
  window.formatearSoloFecha = formatearSoloFecha;
  window.formatearFecha = formatearFecha;
  window.formatearRangoFechas = formatearRangoFechas;
  window.formatearRangoFechasHtml = formatearRangoFechasHtml;
  window.formatearTiempoRelativo = formatearTiempoRelativo;
  window.formatearTextoEnlace = formatearTextoEnlace;
  window.getEstadoVigencia = getEstadoVigencia;
  window.getEstadoVigenciaSS = getEstadoVigencia;
  window.getEstadoVigenciaInduccion = getEstadoVigencia;
  window.obtenerFechaMasUnAnio = obtenerFechaMasUnAnio;

})();
