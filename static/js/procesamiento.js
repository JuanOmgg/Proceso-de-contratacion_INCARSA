/**
 * procesamiento.js
 * Componente Alpine.js del módulo de Procesamiento (trazabilidad).
 * Muestra una tarjeta por solicitud con un timeline de progreso simple:
 * Enviado → En revisión → Por aprobar → Aprobado/Rechazado.
 */

function procesamientoBoard() {
  return {
    search: "",
    filtroEstado: "TODOS",
    filtroActivo: "todos", // "todos" | "activos" | "inactivos"
    userRole: "",

    // Roles autorizados para filtrar entre activos, inactivos o ver todos
    rolesPermitidosInactivos: [
      "ADMIN",
      "ADMINISTRADOR",
      "SUPERADMIN",
      "DIRECTOR",
      "GERENTE",
      "SST",
      "GESCO",
      "SCR",
      "GESTION DOCUMENTAL"
    ],

    get puedeVerInactivos() {
      // Todos los roles con acceso al módulo pueden visualizar y alternar entre activos, inactivos y todos
      return true;
    },

    estadosFiltro: [
      "TODOS", 
      "ENVIADO", 
      "EN REVISIÓN", 
      "POR APROBAR", 
      "APROBADO", 
      "RECHAZADO"
    ],

  estadoEstilos(estado){
    const est = (estado || '').trim().toUpperCase();
    if (est === 'ENVIADO') return 'status-enviado';
    if (est.includes('DEVUELTO') || est.includes('CORRECCI')) return 'status-devuelto';
    if (est.includes('REVISI')) return 'status-revision';
    if (est.includes('APROBAR') || est === 'POR APROBAR') return 'status-aprobar';
    if (est === 'APROBADO') return 'status-aprobado';
    if (est === 'RECHAZADO') return 'status-rechazado';
    return 'status-enviado';
  },

  chipClass(estado) {
    const est = (estado || '').trim().toUpperCase();
    const isActive = this.filtroEstado === estado;
    
    let base = 'chip-neon-todos';
    if (est === 'ENVIADO') base = 'chip-neon-enviado';
    else if (est.includes('REVISI')) base = 'chip-neon-revision';
    else if (est.includes('APROBAR') || est === 'POR APROBAR') base = 'chip-neon-aprobar';
    else if (est === 'APROBADO') base = 'chip-neon-aprobado';
    else if (est === 'RECHAZADO') base = 'chip-neon-rechazado';

    return `${base} ${isActive ? 'is-active scale-105' : 'is-idle'}`;
  },

    // Paginación
    pageSize: 6,
    currentPage: 1,

    // Etapas del flujo de aprobación
    getEtapas(solicitud) {
      const estado = (solicitud.estado || '').toUpperCase();
      return [
        { name: "Enviado", idx: 0 },
        { name: "En revisión", idx: 1 },
        { name: "Por aprobar", idx: 2 },
        { name: estado === "RECHAZADO" ? "Rechazado" : "Aprobado", idx: 3 }
      ];
    },

    getColorEstado(estado) {
      const config = {
        'ENVIADO':     { bg: 'bg-cyan-500', text: 'text-cyan-600', ring: 'ring-cyan-100', line: 'bg-cyan-500' },
        'EN REVISIÓN': { bg: 'bg-purple-500', text: 'text-purple-600', ring: 'ring-purple-100', line: 'bg-purple-500' },
        'POR APROBAR': { bg: 'bg-amber-500', text: 'text-amber-600', ring: 'ring-amber-100', line: 'bg-amber-500' },
        'APROBADO':    { bg: 'bg-emerald-500', text: 'text-emerald-600', ring: 'ring-emerald-100', line: 'bg-emerald-500' },
        'RECHAZADO':   { bg: 'bg-rose-500', text: 'text-rose-600', ring: 'ring-rose-100', line: 'bg-rose-500' }
      };
      return config[estado] || { bg: 'bg-blue-500', text: 'text-blue-600', ring: 'ring-blue-100', line: 'bg-blue-500' };
    },

    nodeStatus(solicitud, idx) {
      const estado = (solicitud.estado || '').toUpperCase();
      
      // Si la solicitud está APROBADA, todos los pasos están completados
      if (estado === 'APROBADO') {
        return 'is-complete';
      }

      // Si fue RECHAZADA, identificar en qué paso exacto ocurrió el rechazo
      if (estado === 'RECHAZADO') {
        const etapaRechazo = String(solicitud.etapa_rechazo || solicitud.fase_rechazo || solicitud.rechazado_en || '').toUpperCase();
        
        // Determinar índice del paso donde se rechazó (0: Enviado, 1: En revisión, 2: Por aprobar, 3: Final/SCR)
        let pasoRechazo = 3;
        if (etapaRechazo.includes('REVIS') || etapaRechazo === 'SST' || etapaRechazo === 'GESCO' || etapaRechazo === '1') {
          pasoRechazo = 1; // Rechazado por SST o GESCO
        } else if (etapaRechazo.includes('APROB') || etapaRechazo === 'SCR' || etapaRechazo === '2') {
          pasoRechazo = 2; // Rechazado en fase de aprobación
        }

        if (idx < pasoRechazo) return 'is-complete';
        if (idx === pasoRechazo) return 'is-rejected';
        return ''; // Pasos posteriores quedan inactivos
      }

      const mapaPasos = {
        'ENVIADO': 0,
        'EN REVISIÓN': 1,
        'POR APROBAR': 2
      };

      const pasoActual = mapaPasos[estado] ?? 0;

      if (idx < pasoActual) return 'is-complete';
      if (idx === pasoActual) return 'is-current';
      return ''; // paso pendiente
    },

    stepClasses(solicitud, idx) {
      const status = this.nodeStatus(solicitud, idx);
      const faseClass = `step-fase-${idx}`;

      if (status === 'is-complete') {
        return `${faseClass} step-node-complete text-white border-transparent`;
      }
      if (status === 'is-rejected') {
        return `${faseClass} step-node-rejected text-white border-transparent`;
      }
      if (status === 'is-current') {
        return `${faseClass} step-node-current is-active text-white border-transparent scale-105`;
      }
      // Pendiente
      return `${faseClass} step-node-pending bg-white text-gray-400 border-2 border-gray-200`;
    },

    labelClasses(solicitud, idx) {
      const status = this.nodeStatus(solicitud, idx);
      const faseClass = `step-label-fase-${idx}`;

      if (status === 'is-complete') {
        return `${faseClass} step-label-complete font-semibold`;
      }
      if (status === 'is-rejected') {
        return `${faseClass} step-label-rejected font-bold`;
      }
      if (status === 'is-current') {
        return `${faseClass} step-label-current is-active font-bold`;
      }
      return `${faseClass} step-label-pending text-gray-400`;
    },

    connectorClasses(solicitud, idx) {
      const estado = (solicitud.estado || '').toUpperCase();
      const conClass = `step-con-${idx}`;

      if (estado === 'APROBADO') {
        return `${conClass} step-connector-complete is-complete`;
      }
      if (estado === 'RECHAZADO') {
        const etapaRechazo = String(solicitud.etapa_rechazo || solicitud.fase_rechazo || solicitud.rechazado_en || '').toUpperCase();
        let pasoRechazo = 3;
        if (etapaRechazo.includes('REVIS') || etapaRechazo === 'SST' || etapaRechazo === 'GESCO' || etapaRechazo === '1') {
          pasoRechazo = 1;
        } else if (etapaRechazo.includes('APROB') || etapaRechazo === 'SCR' || etapaRechazo === '2') {
          pasoRechazo = 2;
        }

        if (idx < pasoRechazo - 1) return `${conClass} step-connector-complete is-complete`;
        if (idx === pasoRechazo - 1) return `${conClass} step-connector-rejected is-rejected`;
        return `${conClass} step-connector-pending is-pending`;
      }
      const mapaPasos = {
        'ENVIADO': 0,
        'EN REVISIÓN': 1,
        'POR APROBAR': 2
      };
      const pasoActual = mapaPasos[estado] ?? 0;
      if (idx < pasoActual) {
        return `${conClass} step-connector-complete is-complete`;
      }
      return `${conClass} step-connector-pending is-pending`;
    },

    solicitudes: [],

    get filtered() {
      let rows = this.solicitudes;

      // 1. Filtro para Gestión Documental: solo consultar solicitudes que haya diligenciado él mismo
      const rolTextoProc = String((this.usuarioSesion && (this.usuarioSesion.rol || this.usuarioSesion.nombre_rol)) || "").toUpperCase();
      const rolIdProc = Number(this.usuarioSesion ? this.usuarioSesion.id_rol : 0);
      const esGestionDoc = rolTextoProc.includes("GESTION DOCUMENTAL") || rolTextoProc.includes("GESTIÓN DOCUMENTAL") || rolIdProc === 5;
      if (esGestionDoc) {
        const myId = Number(this.userId || (this.usuarioSesion && this.usuarioSesion.id) || 0);
        rows = rows.filter(s => Number(s.diligenciado_por) === myId);
      }

      // 2. Filtro para SST y GESCO: únicamente solicitudes vinculadas a sus plantas asignadas
      const esSstGesco = rolTextoProc.includes("SST") || rolTextoProc.includes("GESCO") || rolIdProc === 6 || rolIdProc === 7;
      if (esSstGesco) {
        const misPlantas = (this.usuarioSesion && this.usuarioSesion.plantas_ids ? this.usuarioSesion.plantas_ids : []).map(Number);
        if (!misPlantas || misPlantas.length === 0) {
          return [];
        }
        rows = rows.filter(s => {
          let pIds = [];
          if (Array.isArray(s.plantas_ids)) {
            pIds = s.plantas_ids.map(Number);
          } else if (s.plantas_ids) {
            pIds = String(s.plantas_ids).replace(/[\[\]]/g, "").split(",").map(x => parseInt(x.trim(), 10)).filter(n => !isNaN(n));
          }
          return pIds.some(pid => misPlantas.includes(pid));
        });
      }

      // Filtro por activo / inactivo / todos
      if (this.filtroActivo === "activos") {
        rows = rows.filter(s => s.is_active === 1 || s.is_active === true || s.is_active === "1" || s.is_active === undefined);
      } else if (this.filtroActivo === "inactivos") {
        rows = rows.filter(s => s.is_active === 0 || s.is_active === false || s.is_active === "0");
      }

      // Filtro por estado de flujo
      if (this.filtroEstado !== "TODOS") {
        rows = rows.filter(s => (s.estado || '').toUpperCase() === this.filtroEstado);
      }

      const term = this.search.trim().toLowerCase();
      if (term) {
        const termClean = term.replace(/[\s\-_]/g, "");
        rows = rows.filter(s => {
          const idNum = s.id != null ? String(s.id).trim() : "";
          const idPad = idNum ? idNum.padStart(4, "0") : "";
          const radCode = idNum ? `rad-${idPad}` : "";
          const radShort = idNum ? `rad-${idNum}` : "";
          const codigoCustom = String(s.codigo || s.codigo_solicitud || s.radicado || s.codigo_radicado || "").toLowerCase().trim();

          const codigos = [
            idNum.toLowerCase(),
            idPad.toLowerCase(),
            radCode.toLowerCase(),
            radShort.toLowerCase(),
            codigoCustom,
            codigoCustom.replace(/[\s\-_]/g, ""),
            radCode.replace(/[\s\-_]/g, ""),
            radShort.replace(/[\s\-_]/g, "")
          ];

          const coincideCodigo = codigos.some(c => c && (c.includes(term) || (termClean && c.includes(termClean))));

          const contratistaStr = String(s.nombre_emContratista || s.contratista || s.empresa_contratista || "").toLowerCase();
          const plantaStr = (Array.isArray(s.planta) ? s.planta.join(", ") : String(s.planta || s.plantas || "")).toLowerCase();
          const empresaOrigenStr = String(s.empresa_origen || s.empresa || s.nombre_empresa || "").toLowerCase();
          const diligenciadorStr = String(s.diligenciador || s.diligenciadoPor || s.usuario_creador || "").toLowerCase();
          const estadoStr = String(s.estado || "").toLowerCase();
          const obsStr = String(s.observaciones || s.observacion || "").toLowerCase();

          return (
            coincideCodigo ||
            contratistaStr.includes(term) ||
            plantaStr.includes(term) ||
            empresaOrigenStr.includes(term) ||
            diligenciadorStr.includes(term) ||
            estadoStr.includes(term) ||
            obsStr.includes(term)
          );
        });
      }
      return rows;
    },

    usuarioSesion: null,
    userId: null,

    async init(){
      try {
        let sesion = null;
        if (typeof getAuthSession === "function") {
          sesion = getAuthSession();
        } else {
          sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
        }
        if (sesion) {
          this.usuarioSesion = sesion;
          this.userId = sesion.id;
          this.userRole = sesion.rol || "";
        }
      } catch (e) {
        console.warn("No se pudo leer la sesión:", e);
      }

      // Si el rol no tiene permiso para ver inactivos, forzar estrictamente 'activos'
      if (!this.puedeVerInactivos) {
        this.filtroActivo = "activos";
      }

      await this.getSolicitudes();
    },

    getEstadoRevisionUsuario(solicitud) {
      if (!solicitud) return 'pendiente';

      const revs = Array.isArray(solicitud.revisiones) ? solicitud.revisiones : [];
      const sesion = this.usuarioSesion || {};
      const userId = Number(this.userId || sesion.id || 0);
      const userRol = String(this.userRole || sesion.rol || "").trim().toUpperCase();
      const userPlantasIds = Array.isArray(sesion.plantas_ids) ? sesion.plantas_ids.map(Number) : [];

      // 1. Verificación directa por ID del usuario que emitió el dictamen
      if (userId && revs.length > 0) {
        const revUsuario = revs.find(r => Number(r.id_usuario) === userId);
        if (revUsuario) {
          return revUsuario.decision === 'RECHAZADO' ? 'rechazado' : 'aprobado';
        }
      }

      // 2. Verificación por Rol técnico calificador (SST, GESCO, SCR):
      if (['SST', 'GESCO', 'SCR'].includes(userRol) && revs.length > 0) {
        // Filtrar revisiones registradas por el rol del usuario
        const revsRol = revs.filter(r => String(r.rol || "").trim().toUpperCase() === userRol);
        if (revsRol.length > 0) {
          // Si el usuario tiene plantas asignadas (SST / GESCO), verificar si su planta fue calificada
          if (userPlantasIds.length > 0) {
            const revPlanta = revsRol.find(r => !r.id_planta || userPlantasIds.includes(Number(r.id_planta)));
            if (revPlanta) {
              return revPlanta.decision === 'RECHAZADO' ? 'rechazado' : 'aprobado';
            }
          } else {
            // Si es SCR o no tiene filtro de plantas específico
            const dictamenRol = revsRol[0];
            return dictamenRol.decision === 'RECHAZADO' ? 'rechazado' : 'aprobado';
          }
        }
      }

      // 3. Si el usuario actual no ha calificado la solicitud, permanece estrictamente en "Pendiente"
      return 'pendiente';
    },

    getBotonRevisionTexto(solicitud) {
      const estado = this.getEstadoRevisionUsuario(solicitud);
      if (estado === 'aprobado') return 'Visto bueno otorgado';
      if (estado === 'rechazado') return 'Rechazado';
      return 'Revisar expediente';
    },

    getBotonRevisionClase(solicitud) {
      const estado = this.getEstadoRevisionUsuario(solicitud);
      if (estado === 'aprobado') {
        return 'btn-visto-bueno-listo';
      }
      if (estado === 'rechazado') {
        return 'btn-visto-bueno-rechazado';
      }
      if (estado === 'parcial') {
        return 'btn-visto-bueno-parcial';
      }
      return 'btn-signal';
    },

    getBotonRevisionIcono(solicitud) {
      const estado = this.getEstadoRevisionUsuario(solicitud);
      if (estado === 'aprobado') return 'fa-solid fa-circle-check';
      if (estado === 'rechazado') return 'fa-solid fa-circle-xmark';
      if (estado === 'parcial') return 'fa-solid fa-clock-rotate-left';
      return 'fa-solid fa-clipboard-check';
    },

    async getSolicitudes(){
      try {
        let sesion = null;
        try {
          sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
        } catch (e) {}

        let url = `${API.solicitudes}/getall`;
        const rolTextoProc = String((sesion && (sesion.rol || sesion.nombre_rol)) || "").toUpperCase();
        const rolIdProc = Number(sesion ? sesion.id_rol : 0);
        const esSstGescoProc = rolTextoProc.includes("SST") || rolTextoProc.includes("GESCO") || rolIdProc === 6 || rolIdProc === 7;
        const esGestionDoc = rolTextoProc.includes("GESTION DOCUMENTAL") || rolTextoProc.includes("GESTIÓN DOCUMENTAL") || rolIdProc === 5;

        if (sesion && sesion.id) {
          if (esSstGescoProc) {
            url += `?id_usuario=${sesion.id}`;
          } else if (esGestionDoc) {
            url += `?diligenciado_por=${sesion.id}`;
          }
        }

        const response = await fetch(url);
        if(!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        this.solicitudes = Array.isArray(data) ? data : (data.datos || data.data || []);
      } catch (error) {
        console.warn("Aviso al consultar solicitudes en procesamiento:", error);
        if (!this.solicitudes) this.solicitudes = [];
      }
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
      if (this.currentPage > this.totalPages) this.currentPage = this.totalPages;
    },

    estadoClass(estado) {
      const map = {
        "ENVIADO": "status-enviado",
        "EN REVISIÓN": "status-revision",
        "POR APROBAR": "status-aprobar",
        "APROBADO": "status-aprobado",
        "RECHAZADO": "status-rechazado"
      };
      return map[estado] || "status-enviado";
    },

    // Índice de la etapa actual dentro del flujo (0-3).
    stageIndex(estado) {
      const map = {
        "ENVIADO": 0,
        "EN REVISIÓN": 1,
        "POR APROBAR": 2,
        "APROBADO": 3,
        "RECHAZADO": 3
      };
      return map[estado] ?? 0;
    },

    esRechazado(estado) {
      return estado === "RECHAZADO";
    }
  };
}
