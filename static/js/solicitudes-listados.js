function formatearFechaHoraEspanol(fechaStr) {
    if (window.Fechas && typeof window.Fechas.formatearFechaHora === 'function') {
        return window.Fechas.formatearFechaHora(fechaStr);
    }
    return fechaStr || '—';
}

function formatearFechaCorta(fechaStr) {
    if (window.Fechas && typeof window.Fechas.formatearCorta === 'function') {
        return window.Fechas.formatearCorta(fechaStr);
    }
    if (!fechaStr || fechaStr === '—' || fechaStr === 'null' || fechaStr === 'None') return '—';
    return String(fechaStr).split('T')[0].split(' ')[0];
}

function esInactivaVencida(s) {
    if (!s) return false;
    const esInactiva = (s.is_active === 0 || s.is_active === false || s.is_active === "0");
    if (!esInactiva) return false;

    const fFinRaw = s.fecha_salida || s.fecha_fin || s.fechaSalida;
    if (!fFinRaw) return false;

    let fechaFinDate = null;
    if (fFinRaw instanceof Date) {
        fechaFinDate = new Date(fFinRaw.getTime());
    } else if (typeof fFinRaw === "string" && fFinRaw.trim()) {
        const limpia = fFinRaw.trim().split("T")[0].split(" ")[0].replace(/\//g, "-");
        const partes = limpia.split("-");
        if (partes.length === 3) {
            if (partes[0].length === 4) {
                fechaFinDate = new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
            } else if (partes[2].length === 4) {
                fechaFinDate = new Date(Number(partes[2]), Number(partes[1]) - 1, Number(partes[0]));
            }
        }
    }

    if (!fechaFinDate || isNaN(fechaFinDate.getTime())) return false;

    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    fechaFinDate.setHours(0, 0, 0, 0);

    return fechaFinDate.getTime() < hoy.getTime();
}

function generarCodigoAlfanumerico(id) {
    if (!id) return "INC-X9B1";
    // Si ya viene formateado como código alfanumérico largo
    if (typeof id === 'string' && id.startsWith("SOL-") && id.length > 10) {
        return id;
    }
    const str = String(id);
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash |= 0;
    }
    const chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ";
    let code = "";
    let n = Math.abs(hash);
    for (let i = 0; i < 4; i++) {
        code += chars[n % chars.length];
        n = Math.floor(n / chars.length) + (i + 1) * 11;
    }
    return `RAD-${code}${String(id).padStart(2, '0')}`;
}

function normalizarSolicitud(s) {
    if (!s) return {};

    let cadenaPlanta = "—";
    if (Array.isArray(s.plantas) && s.plantas.length > 0) {
        cadenaPlanta = s.plantas.map(p => (typeof p === "object" ? (p.nombre || p.nombre_planta || p.planta) : p)).filter(Boolean).join(", ");
    } else if (typeof s.planta === "string" && s.planta.trim() !== "") {
        cadenaPlanta = s.planta;
    } else if (typeof s.plantas === "string" && s.plantas.trim() !== "") {
        cadenaPlanta = s.plantas;
    }

    // Cargar observaciones guardadas localmente si no vienen en la API
    let observacionesGuardadas = {};
    try {
        observacionesGuardadas = JSON.parse(localStorage.getItem("incarsa_observaciones_solicitudes") || "{}");
    } catch (e) {}

    const observacionVal = s.observacion || s.observaciones || observacionesGuardadas[s.id] || "";
    const codigoVal = s.codigo || s.codigo_radicado || generarCodigoAlfanumerico(s.id);

    let listaComputos = [];
    if (typeof s.computos === 'string' && s.computos.trim() !== '') {
        listaComputos = s.computos.split('###').map(c => {
            const [id, marca, modelo, serie] = c.split('|||');
            return { id, marca, modelo, serie };
        });
    } else if (Array.isArray(s.computos)) {
        listaComputos = s.computos;
    }

    let listaVehiculos = [];
    if (typeof s.vehiculos === 'string' && s.vehiculos.trim() !== '') {
        listaVehiculos = s.vehiculos.split('###').map(v => {
            const partes = v.split('|||');
            const id = partes[0];
            const tipo = partes[1] || "Vehículo";
            const placa = partes[2] || "—";
            const licencia_doc = partes[3] || "";
            const aut = partes[4];
            const mot = partes[5] || "";
            return {
                id,
                tipo,
                placa,
                licencia_doc,
                licencia: licencia_doc,
                autorizado: aut !== '0' && aut !== 0 && aut !== false && aut !== 'false',
                motivo: mot
            };
        });
    } else if (Array.isArray(s.vehiculos) || Array.isArray(s.vehiculo)) {
        const rawV = Array.isArray(s.vehiculos) ? s.vehiculos : s.vehiculo;
        listaVehiculos = rawV.map(v => ({
            id: v.id || v.id_vehiculo,
            tipo: v.tipo || "Vehículo",
            placa: v.placa || "—",
            conductor: v.conductor || "",
            licencia_doc: v.licencia_doc || v.licencia || "",
            licencia: v.licencia_doc || v.licencia || "",
            autorizado: v.autorizado !== '0' && v.autorizado !== 0 && v.autorizado !== false && v.autorizado !== 'false',
            motivo: v.motivo || v.motivo_rechazo || ""
        }));
    }

    try {
        const storageKeyVeh = `incarsa_solicitud_${s.id}_vehiculos`;
        const localVeh = JSON.parse(localStorage.getItem(storageKeyVeh) || "null");
        if (Array.isArray(localVeh) && localVeh.length > 0) {
            listaVehiculos = listaVehiculos.map(lv => {
                const match = localVeh.find(v => String(v.id) === String(lv.id) || (v.placa && v.placa === lv.placa));
                if (match) {
                    return {
                        ...lv,
                        autorizado: match.autorizado !== '0' && match.autorizado !== 0 && match.autorizado !== false && match.autorizado !== 'false',
                        motivo: match.motivo_rechazo || match.motivo || lv.motivo || ""
                    };
                }
                return lv;
            });
        }
    } catch (e) {}

    let listaRevisiones = [];
    if (Array.isArray(s.revisiones)) {
        listaRevisiones = s.revisiones;
    } else {
        try {
            const storageKeyRev = `incarsa_revisiones_${s.id}`;
            const guardado = JSON.parse(localStorage.getItem(storageKeyRev) || "null");
            if (guardado) {
                if (Array.isArray(guardado.historial)) {
                    listaRevisiones = guardado.historial;
                } else if (Array.isArray(guardado)) {
                    listaRevisiones = guardado;
                }
            }
        } catch (e) {}
    }

    let listaPersonas = [];
    if (typeof s.personas === 'string' && s.personas.trim() !== '') {
        if (s.personas.includes('|||') || s.personas.includes('###')) {
            listaPersonas = s.personas.split('###').map(p => {
                const parts = p.split('|||');
                const id = parts[0];
                const ap_nombre = parts[1];
                const tipo_doc = parts[2];
                const identificacion = parts[3];
                const cargo = parts[4];
                const autorizado = parts[5];
                const motivo = parts[6] || "";
                return {
                    id,
                    ap_nombre,
                    nombre: ap_nombre,
                    tipo_doc,
                    identificacion,
                    cargo,
                    autorizado: autorizado !== '0' && autorizado !== 0 && autorizado !== false && autorizado !== 'false',
                    motivo: motivo || ""
                };
            });
        } else {
            try {
                listaPersonas = JSON.parse(s.personas);
            } catch (e) {
                listaPersonas = [];
            }
        }
    } else if (Array.isArray(s.personas) || Array.isArray(s.ingresantes)) {
        const rawP = Array.isArray(s.personas) ? s.personas : s.ingresantes;
        listaPersonas = rawP.map(p => ({
            id: p.id,
            ap_nombre: p.ap_nombre || `${p.nombre || ''} ${p.apellido || ''}`.trim() || p.nombre || "Contratista",
            nombre: p.nombre || p.ap_nombre || "Contratista",
            tipo_doc: p.tipo_doc || "CC",
            identificacion: p.identificacion || "—",
            cargo: p.cargo || "Operario",
            autorizado: p.autorizado !== '0' && p.autorizado !== 0 && p.autorizado !== false && p.autorizado !== 'false',
            motivo: p.motivo || p.motivo_rechazo || ""
        }));
    }

    try {
        const storageKey = `incarsa_solicitud_${s.id}_personas`;
        const localPersonas = JSON.parse(localStorage.getItem(storageKey) || "null");
        if (Array.isArray(localPersonas) && localPersonas.length > 0) {
            listaPersonas = listaPersonas.map(lp => {
                const match = localPersonas.find(p => String(p.id) === String(lp.id) || (p.identificacion && p.identificacion === lp.identificacion));
                if (match) {
                    return {
                        ...lp,
                        autorizado: match.autorizado !== '0' && match.autorizado !== 0 && match.autorizado !== false && match.autorizado !== 'false',
                        motivo: match.motivo_rechazo || match.motivo || lp.motivo || ""
                    };
                }
                return lp;
            });
        }
    } catch (e) {}

    const nombreEmpresaOrigen = s.nombre_empresa || s.empresa_origen || s.empresaOrigen || "INCARSA";
    const nombreContratista = s.nombre_emContratista || s.empresa_contratista || s.contratista || "—";
    const diligenciadorNombre = s.diligenciador || (typeof s.diligenciado_por === "string" ? s.diligenciado_por : null) || s.diligenciadoPor || "Administrador";

    return {
        id: s.id,
        codigo: codigoVal,
        observaciones: observacionVal,
        observacion: observacionVal,
        nombre_empresa: nombreEmpresaOrigen,
        nombre_emContratista: nombreContratista,
        empresaOrigen: nombreEmpresaOrigen,
        empresa_origen: nombreEmpresaOrigen,
        contratista: nombreContratista,
        empresa_contratista: nombreContratista,
        planta: cadenaPlanta,
        plantas: cadenaPlanta,
        plantas_ids: Array.isArray(s.plantas) ? s.plantas.map(p => typeof p === 'object' ? Number(p.id) : Number(p)).filter(Boolean) : (s.plantas_ids ? String(s.plantas_ids).replace(/[\[\]]/g, "").split(",").map(x => parseInt(x.trim(), 10)).filter(n => !isNaN(n)) : []),
        fecha_ingreso: formatearFechaCorta(s.fecha_ingreso || s.fecha_inicio || s.fechaIngreso),
        fecha_salida: formatearFechaCorta(s.fecha_salida || s.fecha_fin || s.fechaSalida),
        fechaIngreso: formatearFechaCorta(s.fecha_ingreso || s.fecha_inicio || s.fechaIngreso),
        fechaSalida: formatearFechaCorta(s.fecha_salida || s.fecha_fin || s.fechaSalida),
        fecha_creacion_raw: s.fecha_creacion,
        fecha_creacion: formatearFechaHoraEspanol(s.fecha_creacion),
        fecha_registro: formatearFechaCorta(s.fecha_registro || s.fecha_creacion || s.created_at),
        estado: (s.estado || "ENVIADO").toUpperCase(),
        riesgo: s.nivel_de_riesgo || s.nivelRiesgo || s.riesgo || "—",
        actividad: s.actividad || "—",
        diligenciador: diligenciadorNombre,
        diligenciado_por: (s.diligenciado_por !== undefined && s.diligenciado_por !== null && !isNaN(Number(s.diligenciado_por))) ? Number(s.diligenciado_por) : (s.id_diligenciador ? Number(s.id_diligenciador) : null),
        is_active: s.is_active,
        vehiculos: listaVehiculos,
        computos: listaComputos,
        personas: listaPersonas,
        revisiones: listaRevisiones
    };
}


function solicitudesCards() {
    return {
        solActivas: 0,
        solInactivas: 0,
        cargando: true,

        init() {
            window.addEventListener("solicitudes-updated", (e) => {
                const list = e.detail || [];
                this.actualizarConteo(list);
            });
            this.cargarInicial();
        },

        get esAdmin() {
            let sesion = null;
            try {
                sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
            } catch (e) {}
            const rolTexto = String((sesion && (sesion.rol || sesion.nombre_rol)) || "").toUpperCase();
            const rolId = Number(sesion ? (sesion.id_rol || sesion.rol_id) : 0);
            return rolId === 1 || rolId === 2 || rolTexto.includes("ADMIN");
        },

        actualizarConteo(lista) {
            let filtrada = lista;
            let sesion = null;
            try {
                sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
            } catch (e) {}
            const rolTexto = String((sesion && (sesion.rol || sesion.nombre_rol)) || "").toUpperCase();
            const rolId = Number(sesion ? sesion.id_rol : 0);
            const esAdminUser = rolId === 1 || rolId === 2 || rolTexto.includes("ADMIN");

            // Si el usuario no es admin ni superadmin, omitir solicitudes inactivas por vencimiento
            if (!esAdminUser) {
                filtrada = filtrada.filter(s => !esInactivaVencida(s));
            }

            const esSstGesco = rolTexto.includes("SST") || rolTexto.includes("GESCO") || rolId === 6 || rolId === 7;
            if (esSstGesco) {
                const misPlantas = (sesion && sesion.plantas_ids ? sesion.plantas_ids : []).map(Number);
                if (!misPlantas || misPlantas.length === 0) {
                    filtrada = [];
                } else {
                    filtrada = filtrada.filter(s => {
                        const pIds = Array.isArray(s.plantas_ids) ? s.plantas_ids.map(Number) : (s.plantas_ids ? String(s.plantas_ids).split(",").map(Number).filter(Boolean) : []);
                        return pIds.some(pid => misPlantas.includes(pid));
                    });
                }
            }
            this.solActivas = filtrada.filter(s => s.is_active === 1 || s.is_active === true || s.is_active === "1").length;
            this.solInactivas = filtrada.filter(s => s.is_active === 0 || s.is_active === false || s.is_active === "0").length;
            this.cargando = false;
        },

        async cargarInicial() {
            this.cargando = true;
            try {
                let sesion = null;
                try {
                    sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
                } catch (e) {}

                let url = `${API.solicitudes}/getall`;
                const rolTextoInicial = String((sesion && (sesion.rol || sesion.nombre_rol)) || "").toUpperCase();
                const rolIdInicial = Number(sesion ? sesion.id_rol : 0);
                const esSstGescoInicial = rolTextoInicial.includes("SST") || rolTextoInicial.includes("GESCO") || rolIdInicial === 6 || rolIdInicial === 7;
                if (sesion && sesion.id && esSstGescoInicial) {
                    url += `?id_usuario=${sesion.id}`;
                }

                const response = await fetch(url);
                if (!response.ok) throw new Error(`Error ${response.status}`);
                const data = await response.json();
                const solicitud = Array.isArray(data) ? data : (data.datos || []);
                this.actualizarConteo(solicitud);
            } catch (error) {
                console.error("Error al cargar tarjetas de solicitudes:", error);
                this.solActivas = 0;
                this.solInactivas = 0;
            } finally {
                this.cargando = false;
            }
        },

        get totalSolicitudes() {
            return this.solActivas + this.solInactivas;
        }
    };
}

function solicitudesTable() {
    return {
        // Datos
        solicitudes: [],
        empresas: [],

        search: "",
        filtroEmpresa: "",
        filtroEstado: "todos",

        pageSize: 5,
        currentPage: 1,
        cargando: true,

        // Modal Detalle
        viewModalOpen: false,
        selected: null,

        // Modal QR de Acceso
        qrModalOpen: false,
        selectedQr: null,

        // Modal Observaciones
        observacionesModalOpen: false,
        solicitudObservacion: null,
        textoObservacion: "",
        guardandoObservacion: false,

        // Toast de copiado
        copiadoToast: false,

        // Catálogos
        contratistas: [],

        // Modal Selector de Tipo de Formulario (Directo vs Externo)
        modalTipoSolicitudOpen: false,

        // Modal Formulario Temporal para Terceros (Estilo Ticket)
        modalTokenOpen: false,
        modalTokenTab: "crear",
        tokenModoTiempo: "rapido", // 'rapido' o 'exacto'
        tokenDuracion: "24",
        tokenFechaPersonalizada: "",
        tokenContratistaId: "",
        tokenContratistaSearch: "",
        tokenBuscadorAbierto: false,
        tokenGeneradoUrl: "",
        tokenInfoGenerado: null,
        tokenCopiado: false,
        tokensHistorial: [],
        cargandoTokens: false,

        // Modal eliminación
        showDeleteModal: false,
        solicitudAEliminar: null,

        // Reactividad de permisos RBAC
        permisosVersion: 0,
        puedeAccion(mod, acc) {
            const _v = this.permisosVersion;
            return window.puedeAccion(mod, acc);
        },
        puedeModulo(mod) {
            const _v = this.permisosVersion;
            return window.puedeModulo(mod);
        },
        puedeEditarSolicitud(s) {
            const _v = this.permisosVersion;
            if (typeof window.puedeEditarSolicitud === "function") {
                return window.puedeEditarSolicitud(s);
            }
            if (!s) return false;
            const sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
            const miRol = (sesion?.rol || this.activeRole || "").trim().toUpperCase();
            if (miRol === "SUPERADMIN") return true;

            if (!this.puedeAccion("solicitudes", "editar")) return false;
            const est = String(s.estado || "").trim().toUpperCase();
            return est === "ENVIADO" || est === "PRE-ENVIADO";
        },

        async init() {
            window.addEventListener("permisos-actualizados", () => {
                this.permisosVersion++;
            });

            // Recarga automática en caliente ante dictámenes o radicaciones
            window.addEventListener("solicitudes-recargar", () => this.getSolicitudes());
            window.addEventListener("solicitud-actualizada-en-caliente", () => this.getSolicitudes());

            // Abrir modal de token si es disparado por un evento personalizado (ej: sidebar)
            window.addEventListener("abrir-modal-token-formulario", () => {
                this.abrirModalToken();
            });

            // Abrir modal selector o token si viene en los query params de URL (?modal=token-terceros o ?modal=selector)
            try {
                const params = new URLSearchParams(window.location.search);
                if (params.get("modal") === "token-terceros") {
                    this.abrirModalToken();
                    window.history.replaceState({}, document.title, window.location.pathname);
                } else if (params.get("modal") === "selector") {
                    this.modalTipoSolicitudOpen = true;
                    window.history.replaceState({}, document.title, window.location.pathname);
                }

                // Filtrar automáticamente si viene desde una notificación de solicitud PRE-ENVIADA
                const estParam = params.get("estado") || params.get("filtro");
                if (estParam && (estParam.toLowerCase() === "pre-enviado" || estParam.toLowerCase() === "pre_enviado")) {
                    this.filtroEstado = "pre-enviado";
                }
                const codParam = params.get("codigo") || params.get("search");
                if (codParam) {
                    this.search = codParam.trim();
                }
            } catch (e) {}

            await Promise.allSettled([
                this.getEmpresas(),
                this.getContratistas(),
                this.getSolicitudes()
            ]);

            this.$watch("search", () => (this.currentPage = 1));
            this.$watch("filtroEmpresa", () => (this.currentPage = 1));
            this.$watch("filtroEstado", () => (this.currentPage = 1));
        },

        notificarCambio() {
            window.dispatchEvent(new CustomEvent("solicitudes-updated", { detail: this.solicitudes }));
        },

        async getSolicitudes() {
            this.cargando = true;
            try {
                let sesion = null;
                try {
                    sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
                } catch (e) {}

                let url = `${API.solicitudes}/getall`;
                const rolTexto = String((sesion && (sesion.rol || sesion.nombre_rol)) || "").toUpperCase();
                const rolId = Number(sesion ? sesion.id_rol : 0);
                const esSstGesco = rolTexto.includes("SST") || rolTexto.includes("GESCO") || rolId === 6 || rolId === 7;
                if (sesion && sesion.id && esSstGesco) {
                    url += `?id_usuario=${sesion.id}`;
                }
                const esGestionDoc = rolTexto.includes("GESTION DOCUMENTAL") || rolTexto.includes("GESTIÓN DOCUMENTAL") || rolTexto.includes("SOLICITANTE") || rolId === 5;
                if (sesion && sesion.id && esGestionDoc) {
                    url += `${url.includes('?') ? '&' : '?'}diligenciado_por=${sesion.id}`;
                }

                const response = await fetch(url);
                if (!response.ok) throw new Error(`Error ${response.status}`);
                const data = await response.json();
                const lista = Array.isArray(data) ? data : (data.datos || []);
                this.solicitudes = lista.map(s => normalizarSolicitud(s));
                this.notificarCambio();
            } catch (error) {
                console.error("Error al cargar solicitudes:", error);
                this.solicitudes = [];
            } finally {
                this.cargando = false;
            }
        },

        async getEmpresas() {
            try {
                const response = await fetch(`${API.empresas}/getall`);
                if (!response.ok) throw new Error(`Error ${response.status}`);
                const data = await response.json();
                this.empresas = Array.isArray(data) ? data : (data.datos || []);
            } catch (error) {
                console.error("Error al cargar empresas:", error);
                this.empresas = [];
            }
        },

        async getContratistas() {
            try {
                const token = (typeof getAuthToken === "function") ? getAuthToken() : null;
                const headers = token ? { "Authorization": `Bearer ${token}` } : {};
                let response = await fetch(`${API.contratistas}/getall`, { headers });
                if (!response.ok) {
                    response = await fetch(`${API.contratistas}/`, { headers });
                }
                if (response.ok) {
                    const data = await response.json();
                    this.contratistas = Array.isArray(data) ? data : (data.data || data.datos || []);
                }
            } catch (error) {
                console.warn("Error al cargar empresas contratistas:", error);
                this.contratistas = [];
            }
        },

        get esAdmin() {
            const u = this.sesionUsuario;
            if (!u) return false;
            const idRol = parseInt(u.id_rol || u.rol_id, 10);
            const rolNom = String(u.rol || u.nombre_rol || "").toUpperCase();
            return idRol === 1 || idRol === 2 || rolNom.includes("ADMIN");
        },

        get solicitudFiltrados() {
            const text = this.search.trim().toLowerCase();
            const esAdminUser = this.esAdmin;

            return this.solicitudes.filter(s => {
                // Si el usuario no es admin ni superadmin, no enlistar solicitudes inactivas por vencimiento
                if (!esAdminUser && esInactivaVencida(s)) {
                    return false;
                }
                const idNum = s.id != null ? String(s.id).trim() : "";
                const idPad = idNum ? idNum.padStart(4, "0") : "";
                const radCode = idNum ? `rad-${idPad}` : "";
                const radShort = idNum ? `rad-${idNum}` : "";
                const textClean = text.replace(/[\s\-_]/g, "");

                const matchCodigo = !text ||
                    (s.codigo || "").toLowerCase().includes(text) ||
                    radCode.includes(text) ||
                    radShort.includes(text) ||
                    idNum.includes(text) ||
                    idPad.includes(text) ||
                    (textClean && radCode.replace(/[\s\-_]/g, "").includes(textClean));

                // Búsqueda en múltiples campos incluyendo código, fecha de registro y observaciones
                const matchTexto = matchCodigo ||
                    (s.fecha_registro || "").toLowerCase().includes(text) ||
                    (s.observaciones || "").toLowerCase().includes(text) ||
                    (s.nombre_empresa || "").toLowerCase().includes(text) ||
                    (s.nombre_emContratista || "").toLowerCase().includes(text) ||
                    (s.diligenciador || "").toLowerCase().includes(text) ||
                    (s.actividad || "").toLowerCase().includes(text) ||
                    (s.planta || "").toLowerCase().includes(text) ||
                    (s.estado || "").toLowerCase().includes(text);

                // Filtro por empresa seleccionada
                const matchEmpresa = !this.filtroEmpresa || 
                    (s.nombre_empresa || "").toLowerCase() === this.filtroEmpresa.toLowerCase();

                // Filtro por estado activo/inactivo/pre-enviado
                const esActivo = (s.is_active === 1 || s.is_active === true || s.is_active === "1");
                const matchEstado =
                    this.filtroEstado === "todos" ||
                    (this.filtroEstado === "activos" && esActivo) ||
                    (this.filtroEstado === "inactivos" && !esActivo) ||
                    (this.filtroEstado === "pre-enviado" && (s.estado || "").toUpperCase() === "PRE-ENVIADO");

                // Filtro estricto de plantas para SST / GESCO: solo ver solicitudes con plantas relacionadas
                if (this.esRolConPlantas) {
                    const misPlantas = this.plantasUsuario;
                    if (!misPlantas || misPlantas.length === 0) return false;
                    if (!Array.isArray(s.plantas_ids) || s.plantas_ids.length === 0) return false;
                    const coincide = s.plantas_ids.some(pid => misPlantas.includes(Number(pid)));
                    if (!coincide) return false;
                }

                return matchTexto && matchEmpresa && matchEstado;
            });
        },

        get puedeGenerarFormularioTemporal() {
            const u = this.sesionUsuario;
            if (!u) return true;
            const idRol = parseInt(u.id_rol || u.rol_id, 10);
            const rolNom = String(u.rol || u.nombre_rol || "").toUpperCase();
            return idRol === 5 || idRol === 1 || idRol === 2 ||
                   rolNom.includes("SOLICITANTE") ||
                   rolNom.includes("GESTION DOCUMENTAL") ||
                   rolNom.includes("GESTIÓN DOCUMENTAL") ||
                   rolNom.includes("ADMIN");
        },

        puedeAprobarPreEnvio(s) {
            if (!s || (s.estado || "").toUpperCase() !== "PRE-ENVIADO") return false;
            const u = this.sesionUsuario;
            if (!u) return true;
            const idRol = parseInt(u.id_rol || u.rol_id, 10);
            const rolNom = String(u.rol || u.nombre_rol || "").toUpperCase();
            if (idRol === 1 || idRol === 2 || rolNom.includes("ADMIN")) return true;
            return (idRol === 5 || rolNom.includes("SOLICITANTE") || rolNom.includes("GESTION DOCUMENTAL") || rolNom.includes("GESTIÓN DOCUMENTAL"));
        },

        get sesionUsuario() {
            try {
                return JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
            } catch (e) {
                return null;
            }
        },

        get esRolConPlantas() {
            const sesion = this.sesionUsuario;
            if (!sesion) return false;
            const rolTexto = String(sesion.rol || sesion.nombre_rol || "").trim().toUpperCase();
            if (rolTexto === "SST" || rolTexto === "GESCO") return true;
            const rolId = Number(sesion.id_rol);
            // ÚNICAMENTE SST (ID 6) y GESCO (ID 7) filtran por plantas
            return rolId === 6 || rolId === 7;
        },

        get plantasUsuario() {
            const sesion = this.sesionUsuario;
            if (!sesion) return [];
            return (sesion.plantas_ids || []).map(Number);
        },

        get plantasUsuarioNombres() {
            const sesion = this.sesionUsuario;
            if (!sesion || !sesion.plantas || sesion.plantas.length === 0) return "";
            return sesion.plantas.map(p => typeof p === 'object' ? p.nombre : p).join(", ");
        },

        get totalPaginas() {
            return Math.max(1, Math.ceil(this.solicitudFiltrados.length / this.pageSize));
        },

        get solicitudesPagina() {
            const start = (this.currentPage - 1) * this.pageSize;
            return this.solicitudFiltrados.slice(start, start + this.pageSize);
        },

        get rangoMostrado() {
            if (this.solicitudFiltrados.length === 0) return "0 de 0";
            const start = (this.currentPage - 1) * this.pageSize + 1;
            const end = Math.min(this.currentPage * this.pageSize, this.solicitudFiltrados.length);
            return `${start}–${end} de ${this.solicitudFiltrados.length}`;
        },

        // ---------------------------------------------------
        // Acciones sobre registros
        // ---------------------------------------------------
        async toggleActivo(solicitud) {
            const nuevoEstado = !(solicitud.is_active === 1 || solicitud.is_active === true || solicitud.is_active === "1");
            solicitud.is_active = nuevoEstado;
            const idx = this.solicitudes.findIndex(s => s.id === solicitud.id);
            if (idx > -1) this.solicitudes[idx].is_active = nuevoEstado;

            this.notificarCambio();

            try {
                const res = await fetch(`${API.solicitudes}/${solicitud.id}`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ is_active: nuevoEstado })
                });
                if (!res.ok) {
                    console.warn(`Error al actualizar estado de solicitud en backend (HTTP ${res.status})`);
                }
            } catch (err) {
                console.error("Error en PATCH de solicitud:", err);
            }
        },

        // ---------------------------------------------------
        // Gestión de Observaciones
        // ---------------------------------------------------
        openObservacionModal(solicitud) {
            this.solicitudObservacion = solicitud;
            this.textoObservacion = solicitud.observaciones || solicitud.observacion || "";
            this.observacionesModalOpen = true;
        },

        closeObservacionModal() {
            this.observacionesModalOpen = false;
            this.solicitudObservacion = null;
            this.textoObservacion = "";
        },

        async guardarObservacion() {
            if (!this.solicitudObservacion) return;
            this.guardandoObservacion = true;

            const nuevaObs = this.textoObservacion.trim();
            const solId = this.solicitudObservacion.id;

            // 1. Actualizar en el objeto de la lista en memoria
            this.solicitudObservacion.observaciones = nuevaObs;
            this.solicitudObservacion.observacion = nuevaObs;

            const idx = this.solicitudes.findIndex(s => String(s.id) === String(solId));
            if (idx > -1) {
                this.solicitudes[idx].observaciones = nuevaObs;
                this.solicitudes[idx].observacion = nuevaObs;
            }

            // 2. Persistir en localStorage
            try {
                const guardadas = JSON.parse(localStorage.getItem("incarsa_observaciones_solicitudes") || "{}");
                guardadas[solId] = nuevaObs;
                localStorage.setItem("incarsa_observaciones_solicitudes", JSON.stringify(guardadas));
            } catch (e) {}

            // 3. Intentar persistir en FastAPI Backend
            try {
                await fetch(`${API.solicitudes}/${solId}`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ observacion: nuevaObs, observaciones: nuevaObs })
                });
            } catch (e) {
                console.warn("No se pudo guardar observación en backend, guardada localmente:", e);
            } finally {
                this.guardandoObservacion = false;
                this.closeObservacionModal();
            }
        },

        copiarTexto(texto) {
            if (!texto) return;
            navigator.clipboard.writeText(texto).then(() => {
                this.copiadoToast = true;
                setTimeout(() => { this.copiadoToast = false; }, 2000);
            }).catch(() => {});
        },

        async openView(solicitud) {
            this.selected = normalizarSolicitud(solicitud);
            this.viewModalOpen = true;

            try {
                const res = await fetch(`${API.solicitudes}/${solicitud.id}`);
                if (res.ok) {
                    const dataLive = await res.json();
                    if (dataLive && (dataLive.id || dataLive.codigo)) {
                        this.selected = normalizarSolicitud({
                            ...solicitud,
                            ...dataLive
                        });
                        const idx = this.solicitudes.findIndex(s => String(s.id) === String(solicitud.id));
                        if (idx > -1) {
                            this.solicitudes[idx] = this.selected;
                            this.notificarCambio();
                        }
                        window.dispatchEvent(new CustomEvent("notificaciones-actualizadas"));
                        localStorage.setItem("incarsa_notificaciones_reload", Date.now().toString());
                    }
                }
            } catch (err) {
                console.warn("Aviso al refrescar detalle de solicitud:", err);
            }
        },

        closeView() {
            this.viewModalOpen = false;
            this.selected = null;
        },

        openQrModal(solicitud) {
            if (!solicitud) return;
            this.selectedQr = solicitud;
            this.qrModalOpen = true;
        },

        cerrarQrModal() {
            this.qrModalOpen = false;
            this.selectedQr = null;
        },

        descargarQr() {
            if (!this.selectedQr) return;
            const codigo = this.selectedQr.codigo || ('RAD-' + this.selectedQr.id);
            const a = document.createElement('a');
            a.href = `/api/v1/solicitudes/${encodeURIComponent(codigo)}/qr`;
            a.download = `QR-${codigo}.png`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        },

        async copiarEnlaceQr() {
            if (!this.selectedQr) return;
            const codigo = this.selectedQr.codigo || ('RAD-' + this.selectedQr.id);
            const url = `${window.location.origin}/verificar/${encodeURIComponent(codigo)}`;
            try {
                await navigator.clipboard.writeText(url);
                this.copiadoToast = true;
                setTimeout(() => (this.copiadoToast = false), 2500);
            } catch (e) {
                const ta = document.createElement('textarea');
                ta.value = url;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
                this.copiadoToast = true;
                setTimeout(() => (this.copiadoToast = false), 2500);
            }
        },

        // ============================================================
        // MÉTODOS PARA FORMULARIOS TEMPORALES CON TOKEN (DELEGA A MODAL GLOBAL)
        // ============================================================
        abrirModalToken(tab = "crear") {
            window.dispatchEvent(new CustomEvent("open-token-formulario-modal", { detail: { tab } }));
        },

        async aprobarPreEnvio(solicitud) {
            const cod = solicitud.codigo || ("RAD-" + solicitud.id);
            let confirmacion = false;
            if (typeof Swal !== "undefined") {
                const res = await Swal.fire({
                    title: "¿Aprobar y Enviar solicitud?",
                    html: `La solicitud <strong>${cod}</strong> pasará de <span class="text-purple-400 font-bold">PRE-ENVIADO</span> a <span class="text-emerald-400 font-bold">ENVIADO</span> y se notificará a los evaluadores (SST, GESCO, SCR) para iniciar la revisión.`,
                    icon: "question",
                    showCancelButton: true,
                    confirmButtonColor: "#10b981",
                    cancelButtonColor: "#64748b",
                    confirmButtonText: "Sí, Aprobar y Enviar",
                    cancelButtonText: "Cancelar"
                });
                confirmacion = res.isConfirmed;
            } else {
                confirmacion = confirm(`¿Deseas autorizar y enviar la solicitud ${cod} para su revisión oficial?`);
            }

            if (!confirmacion) return;

            try {
                const res = await fetch(`${API.solicitudes}/${solicitud.id}/aprobar-envio`, {
                    method: "POST"
                });
                const data = await res.json();
                if (!res.ok || !data.exito) {
                    throw new Error(data.detail || data.mensaje || "Error al aprobar el envío");
                }

                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "success",
                        title: "¡Solicitud Enviada!",
                        text: `La solicitud ${cod} ha sido aprobada y enviada exitosamente al proceso de revisión.`,
                        timer: 2500,
                        showConfirmButton: false
                    });
                } else {
                    alert(`¡Solicitud ${cod} enviada exitosamente!`);
                }

                await this.getSolicitudes();
            } catch (e) {
                if (typeof Swal !== "undefined") {
                    Swal.fire({ icon: "error", title: "Error al aprobar", text: e.message });
                } else {
                    alert("Error: " + e.message);
                }
            }
        },

        estadoClass(estado) {
            const e = (estado || "").toUpperCase();
            if (e === "ENVIADO") return "status-enviado";
            if (e.includes("DEVUELTO") || e.includes("CORRECCI")) return "status-devuelto";
            if (e.includes("REVISION")) return "status-revision";
            if (e === "POR APROBAR") return "status-aprobar";
            if (e === "APROBADO" || e === "PRE-APROBADO") return "status-aprobado";
            if (e === "RECHAZADO") return "status-rechazado";
            return "status-enviado";
        },

        confirmarEliminar(solicitud) {
            this.solicitudAEliminar = solicitud;
            this.showDeleteModal = true;
        },

        cancelarEliminar() {
            this.solicitudAEliminar = null;
            this.showDeleteModal = false;
        },

        async eliminarSolicitud() {
            if (!this.solicitudAEliminar) return;
            const id = this.solicitudAEliminar.id;
            try {
                await fetch(`${API.solicitudes}/${id}`, { method: "DELETE" });
            } catch (e) {
                console.warn("No se pudo eliminar en backend:", e);
            }
            this.solicitudes = this.solicitudes.filter(s => s.id !== id);
            this.notificarCambio();
            this.cancelarEliminar();
            if (this.currentPage > this.totalPaginas) this.currentPage = this.totalPaginas;
        },

        // ---------------------------------------------------
        // Paginación y Filtros
        // ---------------------------------------------------
        resetPage() {
            this.currentPage = 1;
        },
        goToPage(n) {
            if (n >= 1 && n <= this.totalPaginas) this.currentPage = n;
        },
        prevPage() {
            this.goToPage(this.currentPage - 1);
        },
        nextPage() {
            this.goToPage(this.currentPage + 1);
        },

        limpiarFiltros() {
            this.filtroEmpresa = "";
            this.filtroEstado = "todos";
            this.search = "";
            this.currentPage = 1;
        }
    };
}