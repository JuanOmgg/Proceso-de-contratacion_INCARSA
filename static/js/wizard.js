/**
 * ============================================================================
 * wizard.js — Lógica y Estado del Formulario por Pasos (Alpine.js)
 * ============================================================================
 * Este archivo gestiona todo el ciclo de vida del formulario de solicitudes:
 * 1. Control del Stepper (Paso 1 a 4: navegación, validaciones y guardado).
 * 2. Carga asíncrona de catálogos desde el backend FastAPI (Empresas y Contratistas).
 * 3. Modo Edición (carga datos desde URL `?edit=ID` o API del backend).
 * 4. Integración del calendario Flatpickr para fechas de ingreso y salida.
 * 5. Búsqueda y registro modal de Empresas Contratistas y Personas.
 * 6. Gestión dinámica de tablas de Vehículos y Equipos de cómputo.
 * 7. Envío final (simulación o conexión POST/PUT al backend).
 */

function solicitudWizard() {
  return {
    // ========================================================================
    // 1. ESTADO GENERAL DEL STEPPER
    // ========================================================================
    currentStep: 1, // Paso activo actual (1: Datos, 2: Personas, 3: Vehículos/Equipos, 4: Revisión)
    steps: ["Datos generales", "Personas", "Vehículos y equipos", "Revisión"],
    errors: {}, // Objeto con los mensajes de error por campo { contratista: "...", fechaIngreso: "..." }
    submitting: false, // Indicador de carga al hacer clic en "Enviar solicitud"
    submitted: false, // Bandera que se activa tras completar el envío con éxito
    cargando: true, // Indicador de carga inicial de catálogos

    // ========================================================================
    // 2. MODO EDICIÓN
    // ========================================================================
    isEdit: false, // True si se ingresó con el parámetro ?edit=SOL-XXXX
    editId: null, // ID de la solicitud que se está editando
    solicitudDevuelta: false, // True si la solicitud fue devuelta por SCR para corrección única
    motivoDevolucion: "", // Motivo o inconsistencias descritas por SCR
    tokenEdicion: null, // Token de acceso único provisto por la notificación

    // ========================================================================
    // 3. CATÁLOGOS Y ARRAYS DE DATOS ACTIVOS
    // ========================================================================
    empresas: [], // Lista de empresas destino (cargadas desde la API o fallback)
    empresasContratistas: [], // Lista de contratistas disponibles para autocompletar
    personas: [], // Personas agregadas a la solicitud actual
    personasRegistradas: [], // Catálogo de personas disponibles
    vehiculos: [], // Vehículos agregados a la solicitud actual
    vehiculosRegistrados: [], // Catálogo de vehículos disponibles
    equipos: [], // Equipos de cómputo agregados a la solicitud actual

    // Fallbacks locales (se usan automáticamente si el backend no responde)
    empresasDisponibles: [
      { id: "emp-incarsa", nombre: "INCARSA", plantas: ["Planta Norte", "Planta Sur", "Planta Cartagena"] },
      { id: "emp-transcol", nombre: "Transportes Colombia S.A.S.", plantas: ["Planta Barranquilla", "Planta Cartagena"] },
      { id: "emp-logimax", nombre: "LogiMax", plantas: ["Planta Medellín", "Planta Sur"] }
    ],
    empresasContratistasDisponibles: [
      { id: "ec-1", nombre: "Andes Ingeniería S.A.S.", observacion: "Mantenimiento general" },
      { id: "ec-2", nombre: "Electro Montajes del Caribe", observacion: "Electricidad" },
      { id: "ec-3", nombre: "Servicios Logísticos del Oriente", observacion: "Transporte y carga" },
      { id: "ec-4", nombre: "Grupo Constructor del Sur", observacion: "Obras civiles" }
    ],
    personasRegistradas: [
      { id: 1, nombres: "Carlos Ramírez Ortiz", tipoDoc: "CC", numDoc: "1032456789", cargo: "Técnico eléctrico", documento: "cc_carlos_ramirez.pdf" },
      { id: 2, nombres: "María Fernanda Suárez", tipoDoc: "CC", numDoc: "1098765432", cargo: "Ingeniera de mantenimiento", documento: "cc_maria_suarez.pdf" },
      { id: 3, nombres: "Jhonatan Andrés Pérez", tipoDoc: "CE", numDoc: "8801234", cargo: "Operario", documento: "ce_jhonatan_perez.pdf" }
    ],

    // Opciones para selectores y chips
    nivelesRiesgo: ["Bajo", "Medio", "Alto"],
    tiposDocPersona: ["CC", "CE", "PAS", "PPT"],
    tiposDocAdjuntoPersona: [
      "ARL",
      "Cédula de Ciudadanía",
      "Certificado de Alturas",
      "Examen Médico Ocupacional",
      "Certificado de Espacios Confinados",
      "EPS / Seguridad Social",
      "Hoja de Vida / Certificación",
      "Soporte de GESCO",
      "Otro documento"
    ],
    tiposVehiculo: ["Camioneta", "Camión", "Automóvil", "Motocicleta", "Volqueta", "Maquinaria", "Otro"],
    tiposDocAdjuntoVehiculo: [
      "SOAT",
      "Revisión Tecnomecánica",
      "Tarjeta de Propiedad",
      "Póliza Contractual / Extracontractual",
      "Tarjeta de Operación",
      "Certificado de Emisión de Gases",
      "Otro documento"
    ],

    // ========================================================================
    // MODAL DE VISUALIZACIÓN DE DOCUMENTOS (PERSONAS Y VEHÍCULOS)
    // ========================================================================
    modalDocsOpen: false,
    modalDocsTitle: "",
    modalDocsSubtitle: "",
    modalDocsIcon: "fa-folder-open",
    modalDocsList: [],

    abrirModalDocsPersona(p) {
      this.modalDocsTitle = p.nombres || "Documentos de la persona";
      this.modalDocsSubtitle = `${p.tipoDoc || 'CC'} ${p.numDoc || ''} · ${p.cargo || 'Sin cargo'}`.trim();
      this.modalDocsIcon = "fa-user";

      let docs = [];
      if (Array.isArray(p.documentos) && p.documentos.length > 0) {
        docs = p.documentos.map(d => {
          const nombre = d.nombre_archivo || d.nom_documento || d.nombre || "Archivo adjunto";
          return {
            tipo: d.tipo_doc || d.tipo || "Documento",
            nombre: nombre,
            url: d.url_acceso || (nombre ? `/uploads/documentos/${nombre}` : null)
          };
        });
      } else if (p.documento) {
        docs.push({
          tipo: "Documento de Identidad",
          nombre: p.documento,
          url: `/uploads/documentos/${p.documento}`
        });
      }
      this.modalDocsList = docs;
      this.modalDocsOpen = true;
    },

    abrirModalDocsVehiculo(v) {
      this.modalDocsTitle = `Vehículo ${v.placa || ''} (${v.tipo || 'Vehículo'})`;
      this.modalDocsSubtitle = v.conductor ? `Conductor: ${v.conductor}` : 'Documentación vehicular';
      this.modalDocsIcon = "fa-truck";

      let docs = [];
      if (v.licencia_doc) {
        docs.push({
          tipo: "Licencia de Conducción",
          nombre: v.licencia_doc,
          url: `/uploads/documentos/vehiculos/${v.licencia_doc}`
        });
      }
      if (Array.isArray(v.documentos)) {
        v.documentos.forEach(d => {
          const nom = d.nombre_archivo || d.nom_documento;
          if (nom) {
            docs.push({
              tipo: d.tipo_doc || "Documento Vehicular",
              nombre: nom,
              url: d.url_acceso || `/uploads/documentos/vehiculos/${nom}`
            });
          }
        });
      }
      this.modalDocsList = docs;
      this.modalDocsOpen = true;
    },

    cerrarModalDocs() {
      this.modalDocsOpen = false;
      this.modalDocsList = [];
    },

    /**
     * Retorna las clases visuales de Tailwind según el nivel de riesgo seleccionado.
     */
    getRiesgoBadgeClass(nivel) {
      switch (nivel) {
        case "Bajo":
          return "bg-green-500 text-white border-green-400 hover:bg-green-600";
        case "Medio":
          return "bg-yellow-500 text-white border-yellow-400 hover:bg-yellow-600";
        case "Alto":
          return "bg-red-500 text-white border-red-400 hover:bg-red-600";
        default:
          return "bg-slate-100 text-white hover:bg-gray-400";
      }
    },

    // ========================================================================
    // 4. MODELO PRINCIPAL DEL FORMULARIO (Paso 1)
    // ========================================================================
    form: {
      contratista: "", // Nombre de la empresa contratista seleccionada
      empresas: [], // IDs de empresas destino seleccionadas (ej: ["emp-incarsa"])
      plantasPorEmpresa: {}, // Mapeo de plantas por empresa { "emp-incarsa": ["Planta Norte"] }
      fechaIngreso: "", // Fecha de inicio en formato YYYY-MM-DD
      fechaSalida: "", // Fecha de finalización en formato YYYY-MM-DD
      nivelRiesgo: "", // "Bajo" | "Medio" | "Alto"
      actividad: "", // Descripción detallada de las labores a ejecutar
      diligenciadoPor: "Juan Prieto", // Nombre del usuario autenticado
      estado: "ENVIADO", // Estado editable por SUPERADMIN en modo edición
      codigo: "" // Código de radicado en modo edición
    },
    aceptaVeracidad: false, // Checkbox de confirmación y veracidad en el Paso 4

    // ========================================================================
    // 5. ESTADO DE BÚSQUEDA Y MODALES
    // ========================================================================

    // Modal / Búsqueda de Personas
    personaSearchQuery: "", // Texto escrito en el buscador de personas
    showPersonaModal: false, // Visibilidad del modal para crear/editar persona
    guardandoPersona: false, // Spinner durante la llamada POST/PUT al backend
    isEditingPersona: false, // Indica si el modal está en modo edición
    editingPersonaId: null, // ID de la persona que se está editando en la BD
    editingPersonaOldDoc: "", // Documento previo de la persona en edición
    editingPersonaIndex: -1, // Índice en this.personas si ya está en la solicitud
    nuevaPersona: {
      nombres: "",
      apellidos: "",
      tipoDoc: "CC",
      numDoc: "",
      cargo: "",
      observacion: "",
      documentos: [
        { tipo_doc: "ARL", nombre_archivo: "" }
      ]
    },
    personaModalErrors: {}, // Errores de validación dentro del modal de personas

    // Modal / Búsqueda de Empresas Contratistas
    contratistaSearchQuery: "", // Texto escrito en el buscador de contratistas
    showContratistaModal: false, // Visibilidad del modal para registrar nueva empresa
    guardandoEmpresa: false, // Spinner durante la llamada POST al backend
    nuevaEmpresa: { nombre: "", observacion: "" },
    nuevaEmpresaErrors: {}, // Errores de validación dentro del modal de empresas

    // Modal / Búsqueda de Vehículos
    vehiculoSearchQuery: "", // Texto escrito en el buscador de vehículos
    showVehiculoModal: false, // Visibilidad del modal para registrar nuevo vehículo
    guardandoVehiculo: false, // Spinner durante la llamada POST al backend
    isEditingVehiculo: false, // Indica si el modal de vehículos está en modo edición
    editingVehiculoId: null, // ID del vehículo en la BD si existe
    editingVehiculoOldPlaca: "", // Placa previa del vehículo en edición
    editingVehiculoIndex: -1, // Índice en this.vehiculos si ya está en la solicitud
    nuevoVehiculo: {
      tipo: "Camioneta",
      placa: "",
      conductor: "",
      licencia_doc: "",
      licencia_url: null,
      documentos: [
        { tipo_doc: "SOAT", nombre_archivo: "" }
      ]
    },
    vehiculoModalErrors: {}, // Errores de validación del modal de vehículos

    plantas: [], // Lista de plantas cargadas desde la API

    // ========================================================================
    // 6. INICIALIZACIÓN (Lifecycle Hook de Alpine)
    // ========================================================================
    async init() {
      // Validar permisos RBAC de creación y edición
      const isEditar = window.location.pathname.includes("editar") || new URLSearchParams(window.location.search).has("edit") || new URLSearchParams(window.location.search).has("codigo");
      const miSesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
      const esSuper = (miSesion?.rol || "").trim().toUpperCase() === "SUPERADMIN";

      if (!esSuper) {
        if (isEditar && !window.puedeAccion('solicitudes', 'editar')) {
          console.warn("Acceso denegado: No tienes permiso para editar solicitudes.");
          window.location.replace("/solicitudes");
          return;
        }
        if (!isEditar && (!window.puedeAccion('solicitudes', 'crear') || !window.puedeModulo('nueva_solicitud'))) {
          console.warn("Acceso denegado: No tienes permiso para crear solicitudes.");
          window.location.replace("/solicitudes");
          return;
        }
      }

      // 1. Cargar empresas, plantas, contratistas, personas y vehículos desde FastAPI
      await Promise.allSettled([
        this.cargarEmpresas(),
        this.cargarPlantas(),
        this.cargarEmpresasContratistas(),
        this.cargarPersonas(),
        this.cargarVehiculos()
      ]);

      // Escuchar eventos globales de sincronización de vehículos
      window.addEventListener("vehiculos-actualizados", () => {
        this.cargarVehiculos();
      });

      // 2. Verificar si es modo edición
      await this.inicializarModoEdicion();
    },

    solicitudOriginal: null,

    estadoClass(estado) {
      const map = {
        "ENVIADO": "status-enviado",
        "EN REVISIÓN": "status-revision",
        "EN REVISION": "status-revision",
        "DEVUELTO PARA CORRECCIÓN": "status-devuelto",
        "DEVUELTO": "status-devuelto",
        "POR APROBAR": "status-aprobar",
        "APROBADO": "status-aprobado",
        "PRE-APROBADO": "status-aprobado",
        "RECHAZADO": "status-rechazado"
      };
      return map[(estado || "").toUpperCase()] || "status-enviado";
    },

    get esSuperAdmin() {
      const miSesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
      return (miSesion?.rol || "").trim().toUpperCase() === "SUPERADMIN";
    },

    /**
     * Si la URL incluye ?edit=ID, busca la solicitud en la API o localStorage y precarga el formulario
     */
    async inicializarModoEdicion() {
      const params = new URLSearchParams(window.location.search);
      let editParam = params.get("codigo") || params.get("edit");

      // Extraer de la ruta si viene como /solicitudes/editar/{codigo}
      if (!editParam) {
        const segs = window.location.pathname.split("/").filter(Boolean);
        const idxEditar = segs.indexOf("editar");
        if (idxEditar !== -1 && segs[idxEditar + 1]) {
          editParam = decodeURIComponent(segs[idxEditar + 1]);
        }
      }

      if (!editParam) return;

      this.isEdit = true;
      this.editId = editParam;
      console.log("🔍 [MODO EDICIÓN] Iniciando carga de solicitud ID/Código:", editParam);

      let found = null;

      // 1. Intentar buscar por endpoint individual directo (soporta ID y código RAD-XXXX)
      try {
        const res = await fetch(`${API.solicitudes}/${editParam}`);
        if (res.ok) {
          const data = await res.json();
          found = data.datos || data.data || data;
        }
      } catch (e) {
        console.warn("Consulta directa por código falló, buscando en listado completo:", e);
      }

      // 2. Cargar todas las solicitudes del backend (getall) para encontrarla
      if (!found) {
        try {
          const res = await fetch(`${API.solicitudes}/getall`);
          if (res.ok) {
            const data = await res.json();
            const lista = Array.isArray(data) ? data : (data.datos || data.data || []);
            found = lista.find(s => 
              String(s.codigo || "").toLowerCase() === String(editParam).toLowerCase() ||
              String(s.id || "").toLowerCase() === String(editParam).toLowerCase() ||
              (s.id_generado && String(s.id_generado).toLowerCase() === String(editParam).toLowerCase())
            );
          }
        } catch (e) {
          console.warn("No se pudo buscar en getall:", e);
        }
      }

      // 3. Buscar en localStorage
      if (!found) {
        try {
          const guardadas = JSON.parse(localStorage.getItem("incarsa_solicitudes_creadas") || "[]");
          found = guardadas.find(s => String(s.id).toLowerCase() === String(editParam).toLowerCase());
        } catch (e) {}
      }


      if (found) {
        const miSesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
        const miRol = (miSesion?.rol || "").trim().toUpperCase();
        const esSuper = (miRol === "SUPERADMIN");
        const estadoSol = String(found.estado || "").trim().toUpperCase();
        const tokenParam = params.get("token");

        // Caso: Solicitud devuelta por SCR para corrección única
        if (estadoSol === "DEVUELTO PARA CORRECCIÓN") {
          if (!tokenParam && !esSuper) {
            console.warn(`Acceso restringido: La solicitud ${editParam} fue devuelta para corrección única y requiere token de la notificación.`);
            if (typeof Swal !== "undefined") {
              await Swal.fire({
                icon: "warning",
                title: "Edición Única Restringida",
                text: "Esta solicitud fue devuelta por SCR para corrección. Solo puedes ingresar a editarla a través del enlace de la notificación.",
                confirmButtonColor: "#f59e0b"
              });
            } else if (typeof alert === "function") {
              alert("Esta solicitud fue devuelta por SCR para corrección. Solo puedes ingresar a editarla a través del enlace de la notificación.");
            }
            window.location.replace("/solicitudes");
            return;
          }

          if (tokenParam) {
            try {
              const targetId = found.id || editParam;
              const resToken = await fetch(`${API.solicitudes}/${targetId}/validar-token-edicion?token=${encodeURIComponent(tokenParam)}`);
              if (!resToken.ok) {
                const errData = await resToken.json().catch(() => ({}));
                const msgError = errData.detail || "El enlace de edición única no es válido o ya fue utilizado previamente.";
                if (typeof Swal !== "undefined") {
                  await Swal.fire({
                    icon: "error",
                    title: "Acceso denegado",
                    text: msgError,
                    confirmButtonColor: "#ef4444"
                  });
                } else if (typeof alert === "function") {
                  alert(msgError);
                }
                window.location.replace("/solicitudes");
                return;
              }
              const dataToken = await resToken.json();
              this.tokenEdicion = tokenParam;
              this.solicitudDevuelta = true;
              this.motivoDevolucion = dataToken.motivo_devolucion || found.motivo_devolucion || "";
            } catch (errToken) {
              console.error("Error al validar token de edición única:", errToken);
              if (typeof alert === "function") {
                alert("Error de conexión al verificar el enlace de edición única.");
              }
              window.location.replace("/solicitudes");
              return;
            }
          }
        } else if (!esSuper && estadoSol !== "ENVIADO") {
          // Si NO es SuperAdmin y no es DEVUELTO, solo puede editar en estado 'ENVIADO'
          console.warn(`Acceso restringido: La solicitud ${editParam} está en estado '${estadoSol}'. Solo puede ser editada en estado 'ENVIADO', o por un usuario SUPERADMIN.`);
          if (typeof alert === "function") {
            alert(`La solicitud se encuentra en estado "${estadoSol}". Solo puede ser editada mientras esté en estado "ENVIADO", o por un usuario SUPERADMIN.`);
          }
          window.location.replace("/solicitudes");
          return;
        }

        console.log("✅ [MODO EDICIÓN] Solicitud encontrada para editar:", found);
        this.solicitudOriginal = found;
        this.cargarDatosEnFormulario(found);
      } else {
        console.warn(`❌ [MODO EDICIÓN] No se encontró ninguna solicitud con ID ${editParam}`);
      }
    },

    cargarDatosEnFormulario(found) {
      // 1. Contratista
      let contratistaNombre = found.nombre_emContratista || found.empresa_contratista || found.contratista || "";
      if (typeof contratistaNombre === 'number' || (!isNaN(parseInt(contratistaNombre)) && String(contratistaNombre).length <= 4)) {
        const ec = this.empresasContratistas.find(c => String(c.id) === String(contratistaNombre));
        if (ec) contratistaNombre = ec.nombre || ec.N_empresa || contratistaNombre;
      }
      this.form.contratista = String(contratistaNombre);

      // 2 & 3. Resolver Empresas y Plantas asociadas
      this.form.empresas = [];
      this.form.plantasPorEmpresa = {};

      // Obtener lista cruda de plantas de la solicitud
      let listaPlantasRaw = [];
      if (Array.isArray(found.plantas)) {
        listaPlantasRaw = found.plantas;
      } else if (Array.isArray(found.plantas_ids)) {
        listaPlantasRaw = found.plantas_ids;
      } else if (typeof found.planta === 'string' && found.planta.trim() !== '' && found.planta !== '—') {
        listaPlantasRaw = found.planta.split(',').map(p => p.trim()).filter(Boolean);
      }

      // Si found tiene plantasPorEmpresa preconfigurado
      if (found.plantasPorEmpresa && typeof found.plantasPorEmpresa === 'object') {
        Object.keys(found.plantasPorEmpresa).forEach(empKey => {
          const empIdStr = String(empKey);
          if (!this.form.empresas.includes(empIdStr)) this.form.empresas.push(empIdStr);
          this.form.plantasPorEmpresa[empIdStr] = Array.isArray(found.plantasPorEmpresa[empKey])
            ? [...found.plantasPorEmpresa[empKey]]
            : [];
        });
      }

      // Identificar empresas desde empresa_origen / nombre_empresa
      const empOrigenVal = String(found.empresa_origen || found.nombre_empresa || found.empresaOrigen || "").trim();
      if (empOrigenVal && empOrigenVal !== '—') {
        const empEncontrada = this.empresas.find(e => 
          String(e.id) === empOrigenVal ||
          (e.nombre && (
            e.nombre.toLowerCase() === empOrigenVal.toLowerCase() ||
            e.nombre.toLowerCase().includes(empOrigenVal.toLowerCase()) ||
            empOrigenVal.toLowerCase().includes(e.nombre.toLowerCase())
          ))
        );
        if (empEncontrada) {
          const empIdStr = String(empEncontrada.id);
          if (!this.form.empresas.includes(empIdStr)) {
            this.form.empresas.push(empIdStr);
          }
          if (!this.form.plantasPorEmpresa[empIdStr]) {
            this.form.plantasPorEmpresa[empIdStr] = [];
          }
        }
      }

      // Procesar cada planta para asignarla a su empresa correspondiente
      for (const pRaw of listaPlantasRaw) {
        let pId = null;
        let pNombre = "";

        if (typeof pRaw === 'object' && pRaw !== null) {
          pId = pRaw.id ? String(pRaw.id) : null;
          pNombre = pRaw.nombre || pRaw.nombre_planta || (pId ? `Planta #${pId}` : "");
        } else if (typeof pRaw === 'number' || (!isNaN(parseInt(pRaw)) && String(pRaw).length <= 4)) {
          pId = String(pRaw);
          const matchP = this.plantas.find(pl => String(pl.id) === pId);
          pNombre = matchP ? (matchP.nombre || matchP.nombre_planta) : `Planta #${pId}`;
        } else {
          pNombre = String(pRaw).trim();
        }

        if (!pNombre) continue;

        // Encontrar a qué empresa pertenece esta planta
        let empresaDePlanta = null;

        // A) Buscar en this.plantas por ID o nombre
        const plantaCatalogo = this.plantas.find(pl => 
          (pId && String(pl.id) === pId) || 
          (pl.nombre && pl.nombre.trim().toLowerCase() === pNombre.toLowerCase())
        );

        if (plantaCatalogo && plantaCatalogo.id_empresa) {
          empresaDePlanta = this.empresas.find(e => String(e.id) === String(plantaCatalogo.id_empresa));
        }

        // B) Si no se encontró por catálogo, buscar coincidencia por nombre de empresa dentro del nombre de la planta
        if (!empresaDePlanta) {
          empresaDePlanta = this.empresas.find(e => {
            const nomEmp = (e.nombre || e.N_empresa || "").toLowerCase().replace(/s\.a\.s\.?/gi, "").trim();
            return nomEmp && pNombre.toLowerCase().includes(nomEmp);
          });
        }

        // C) Si aún no se encuentra, asociarla a la primera empresa seleccionada
        if (!empresaDePlanta && this.form.empresas.length > 0) {
          empresaDePlanta = this.empresas.find(e => String(e.id) === this.form.empresas[0]);
        }

        if (empresaDePlanta) {
          const empIdStr = String(empresaDePlanta.id);
          if (!this.form.empresas.includes(empIdStr)) {
            this.form.empresas.push(empIdStr);
          }
          if (!this.form.plantasPorEmpresa[empIdStr]) {
            this.form.plantasPorEmpresa[empIdStr] = [];
          }
          if (!this.form.plantasPorEmpresa[empIdStr].includes(pNombre)) {
            this.form.plantasPorEmpresa[empIdStr].push(pNombre);
          }
        }
      }

      // Si no hay empresas seleccionadas pero hay disponibles, seleccionar la primera por defecto
      if (this.form.empresas.length === 0 && this.empresas.length > 0) {
        const defaultEmpId = String(this.empresas[0].id);
        this.form.empresas.push(defaultEmpId);
        this.form.plantasPorEmpresa[defaultEmpId] = [];
      }

      // 4. Fechas, riesgo, actividad y diligenciador
      this.form.fechaIngreso = found.fecha_ingreso || found.fecha_inicio || found.fechaIngreso || "";
      this.form.fechaSalida = found.fecha_salida || found.fecha_fin || found.fechaSalida || "";
      this.form.nivelRiesgo = found.nivel_de_riesgo || found.nivelRiesgo || found.riesgo || "Bajo";
      this.form.actividad = found.actividad || "";
      this.form.diligenciadoPor = found.diligenciador || (found.diligenciado_por ? `Usuario #${found.diligenciado_por}` : "") || found.diligenciadoPor || "—";
      this.form.estado = (found.estado || "ENVIADO").toUpperCase();
      this.form.codigo = found.codigo || found.codigo_radicado || "";

      // 5. Personas
      let listaPersonas = [];
      if (Array.isArray(found.ingresantes) && found.ingresantes.length > 0) {
        listaPersonas = found.ingresantes;
      } else if (Array.isArray(found.personas) && found.personas.length > 0) {
        listaPersonas = found.personas;
      } else if (typeof found.personas === 'string' && found.personas.trim() !== '') {
        if (found.personas.includes('|||') || found.personas.includes('###')) {
          listaPersonas = found.personas.split('###').map(p => {
            const [id, ap_nombre, tipo_doc, identificacion, cargo] = p.split('|||');
            return { id, nombres: ap_nombre, tipoDoc: tipo_doc || 'CC', numDoc: identificacion, cargo: cargo || 'Personal' };
          });
        } else {
          try { listaPersonas = JSON.parse(found.personas); } catch (e) {}
        }
      }

      this.personas = listaPersonas.map((p, idx) => ({
        id: p.id || (idx + 1),
        item: idx + 1,
        nombres: p.nombres || p.nombre_completo || `${p.nombre || ''} ${p.apellido || ''}`.trim() || p.ap_nombre || 'Personal',
        tipoDoc: p.tipoDoc || p.tipo_doc || 'CC',
        numDoc: p.numDoc || p.num_doc || p.identificacion || '',
        cargo: p.cargo || 'Técnico',
        documento: p.documento || p.documento_doc || (p.documentos && p.documentos[0]?.nombre_archivo) || null,
        documentos: Array.isArray(p.documentos) && p.documentos.length > 0
          ? p.documentos
          : (p.documento ? [{ tipo_doc: 'Cédula', nombre_archivo: p.documento }] : []),
        _existingDoc: p.documento || null
      }));

      // 6. Vehículos
      let listaVehiculos = [];
      if (typeof found.vehiculos === 'string' && found.vehiculos.trim() !== '') {
        if (found.vehiculos.includes('|||') || found.vehiculos.includes('###')) {
          listaVehiculos = found.vehiculos.split('###').map(v => {
            const [id, placa, marca, modelo, serie] = v.split('|||');
            return { id, placa, marca, modelo, tipo: 'Camioneta', conductor: '' };
          });
        } else {
          try { listaVehiculos = JSON.parse(found.vehiculos); } catch (e) {}
        }
      } else if (Array.isArray(found.vehiculos)) {
        listaVehiculos = found.vehiculos;
      } else if (Array.isArray(found.vehiculo)) {
        listaVehiculos = found.vehiculo;
      }

      this.vehiculos = listaVehiculos.map(v => ({
        id: v.id,
        tipo: v.tipo || "Camioneta",
        placa: (v.placa || "").toUpperCase().trim(),
        conductor: v.conductor || "",
        licencia_doc: v.licencia_doc || v.licencia || "",
        documentos: Array.isArray(v.documentos) && v.documentos.length > 0
          ? v.documentos.map(d => ({
              tipo_doc: d.tipo_doc || d.tipo || "SOAT",
              nombre_archivo: d.nombre_archivo || d.nom_documento || d.nombre || ""
            }))
          : [{ tipo_doc: "SOAT", nombre_archivo: "" }]
      }));

      // 7. Equipos de cómputo
      let listaComputos = [];
      if (typeof found.computos === 'string' && found.computos.trim() !== '') {
        listaComputos = found.computos.split('###').map(c => {
          const [id, marca, modelo, serie] = c.split('|||');
          return { id, marca, modelo, serie };
        });
      } else if (Array.isArray(found.computos)) {
        listaComputos = found.computos;
      } else if (Array.isArray(found.equipos)) {
        listaComputos = found.equipos;
      } else if (Array.isArray(found.eq_computo)) {
        listaComputos = found.eq_computo;
      }

      this.equipos = listaComputos.map(e => ({
        id: e.id,
        marca: e.marca || "",
        modelo: e.modelo || "",
        serie: e.serie || ""
      }));

      this.aceptaVeracidad = true;
      this.errors = {}; // Limpiar cualquier error previo

      // 8. Sincronizar fechas con Flatpickr (con timeout para asegurar DOM montado)
      setTimeout(() => {
        if (this.fpIngresoInstance && this.form.fechaIngreso) {
          this.fpIngresoInstance.setDate(this.form.fechaIngreso, true);
        }
        if (this.fpSalidaInstance && this.form.fechaSalida) {
          this.fpSalidaInstance.setDate(this.form.fechaSalida, true);
        }
      }, 150);
    },

    async cargarEmpresas() {
      try {
        let res = await fetch(`${API.empresas}/getall`);
        if (!res.ok) {
          res = await fetch(`${API.empresas}/`);
        }
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        this.empresas = Array.isArray(data) ? data : (data.datos || []);
        console.log("✅ Empresas cargadas:", this.empresas);
      } catch (error) {
        console.warn("❌ Backend no disponible para empresas, usando fallback:", error.message);
        this.empresas = Array.isArray(this.empresasDisponibles) ? this.empresasDisponibles : [];
      } finally {
        this.cargando = false;
      }
    },

    async cargarPlantas() {
      try {
        const res = await fetch(`${API.plantas}/getall`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        this.plantas = Array.isArray(data) ? data : (data.datos || []);
        console.log("✅ Plantas cargadas:", this.plantas);
      } catch (err) {
        console.warn("Backend no disponible para plantas:", err.message);
        this.plantas = [];
      }
    },

    async cargarEmpresasContratistas() {
      try {
        let responseEC = await fetch(`${API.contratistas}/getall`);
        if (!responseEC.ok) {
          responseEC = await fetch(`${API.contratistas}/`);
        }
        if (!responseEC.ok) throw new Error(`HTTP ${responseEC.status}`);
        const data = await responseEC.json();
        this.empresasContratistas = Array.isArray(data) ? data : (data.data || data.datos || []);
        console.log("✅ Empresas contratistas cargadas:", this.empresasContratistas);
      } catch (error) {
        console.warn("❌ Backend no disponible para empresas contratistas, usando fallback:", error.message);
        this.empresasContratistas = Array.isArray(this.empresasContratistasDisponibles)
          ? this.empresasContratistasDisponibles
          : [];
      }
    },

    /**
     * Consume la API de personas registradas (GET /personas/getAll)
     */
    async cargarPersonas() {
      try {
        const res = await fetch(`${API.personas}/getAll`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const lista = data.datos_person || data.datos || (Array.isArray(data) ? data : []);
        if (Array.isArray(lista) && lista.length > 0) {
          this.personasRegistradas = lista.map(p => ({
            id: p.id,
            nombres: p.nombres || `${p.nombre || ""} ${p.apellido || ""}`.trim(),
            nombre: p.nombre,
            apellido: p.apellido,
            tipoDoc: p.tipo_doc || p.tipoDoc || "CC",
            numDoc: p.identificacion || p.numDoc,
            cargo: p.cargo || "Personal",
            observacion: p.observacion || "",
            documento: p.documento_doc || p.documento || null,
            documentos: Array.isArray(p.documentos) && p.documentos.length > 0
              ? p.documentos
              : (p.documento_doc || p.documento ? [{ tipo_doc: "Cédula", nombre_archivo: p.documento_doc || p.documento }] : [])
          }));
          console.log("✅ Personas cargadas desde la BD:", this.personasRegistradas);
        }
      } catch (error) {
        console.warn("❌ Backend no disponible para personas:", error.message);
      }
    },

    /**
     * Consume la API de vehículos registrados (GET /vehiculo/getAll)
     */
    async cargarVehiculos() {
      try {
        const res = await fetch(`${API.vehiculos}/getAll`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const lista = data.datos_vehi || data.datos || (Array.isArray(data) ? data : []);
        if (Array.isArray(lista) && lista.length > 0) {
          this.vehiculosRegistrados = lista.map(v => ({
            id: v.id,
            tipo: v.tipo || "Camioneta",
            placa: (v.placa || "").toUpperCase().trim(),
            conductor: v.conductor || "",
            licencia_doc: v.licencia_doc || v.licencia || "",
            documentos: Array.isArray(v.documentos) ? v.documentos : (Array.isArray(v.documentos_ids) ? v.documentos_ids : [])
          }));
          console.log("✅ Vehículos cargados desde la BD:", this.vehiculosRegistrados);
        }
      } catch (error) {
        console.warn("❌ Backend no disponible para vehículos:", error.message);
      }
    },



    // ========================================================================
    // 7. CALENDARIO FLATPICKR
    // ========================================================================
    fpIngresoInstance: null,
    fpSalidaInstance: null,

    /**
     * Inicializa Flatpickr en un input de fecha y sincroniza el rango (fechaSalida >= fechaIngreso)
     * @param {HTMLElement} el - Elemento input DOM
     * @param {string} field - Nombre del campo ('fechaIngreso' o 'fechaSalida')
     */
    initFlatpickr(el, field) {
      if (typeof flatpickr === "undefined") return;
      const initialValue = this.form[field] || "";
      const isIngreso = field === "fechaIngreso";

      const fpInstance = flatpickr(el, {
        locale: flatpickr.l10ns?.es || "es",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        altInputClass: el.className,
        defaultDate: initialValue || null,
        disableMobile: "true",
        onChange: (selectedDates, dateStr) => {
          this.form[field] = dateStr;
          if (this.errors[field]) delete this.errors[field];

          // Bloquea fechas de salida anteriores a la fecha de ingreso
          if (isIngreso && this.fpSalidaInstance) {
            this.fpSalidaInstance.set("minDate", dateStr);
            if (this.form.fechaSalida && this.form.fechaSalida < dateStr) {
              this.form.fechaSalida = dateStr;
              this.fpSalidaInstance.setDate(dateStr, false);
            }
          }
        }
      });

      if (isIngreso) {
        this.fpIngresoInstance = fpInstance;
      } else {
        this.fpSalidaInstance = fpInstance;
        if (this.form.fechaIngreso) {
          fpInstance.set("minDate", this.form.fechaIngreso);
        }
      }

      if (this.form[field]) {
        fpInstance.setDate(this.form[field], false);
      }
    },

    // ========================================================================
    // 8. SELECCIÓN DE EMPRESAS Y PLANTAS (Paso 1)
    // ========================================================================

    /**
     * Activa o desactiva una empresa destino. Al deseleccionar, limpia sus plantas elegidas.
     */
    toggleEmpresa(empresaId) {
      const sId = String(empresaId);
      const idx = this.form.empresas.findIndex(id => String(id) === sId);
      if (idx > -1) {
        this.form.empresas.splice(idx, 1);
        delete this.form.plantasPorEmpresa[sId];
        delete this.form.plantasPorEmpresa[empresaId];
      } else {
        this.form.empresas.push(sId);
        if (!this.form.plantasPorEmpresa[sId]) {
          this.form.plantasPorEmpresa[sId] = [];
        }
      }
      if (this.errors.empresas) delete this.errors.empresas;
      if (this.errors.plantas) delete this.errors.plantas;
    },

    isEmpresaSelected(empresaId) {
      const sId = String(empresaId);
      return this.form.empresas.some(id => String(id) === sId);
    },

    empresaNombre(empresaId) {
      const empresa = this.empresas.find(e => String(e.id) === String(empresaId));
      return empresa ? (empresa.nombre || empresa.N_empresa) : `Empresa #${empresaId}`;
    },

    plantasDeEmpresa(empresaId) {
      const empresa = this.empresas.find(e => String(e.id) === String(empresaId));
      const empNombre = empresa ? (empresa.nombre || empresa.N_empresa || "") : "";

      if (empresa && Array.isArray(empresa.plantas) && empresa.plantas.length > 0) {
        return empresa.plantas;
      }
      
      const dePlantasApi = this.plantas.filter(p => 
        String(p.id_empresa) === String(empresaId) ||
        (empNombre && p.N_empresa && (
          p.N_empresa.toLowerCase() === empNombre.toLowerCase() ||
          p.N_empresa.toLowerCase().includes(empNombre.toLowerCase()) ||
          empNombre.toLowerCase().includes(p.N_empresa.toLowerCase())
        ))
      );
      if (dePlantasApi.length > 0) return dePlantasApi;

      // Fallback si la empresa tiene plantas anidadas en su objeto
      const empMatch = (this.empresasDisponibles || []).find(e => 
        String(e.id) === String(empresaId) || 
        (empNombre && e.nombre && e.nombre.toLowerCase() === empNombre.toLowerCase())
      );
      if (empMatch && Array.isArray(empMatch.plantas)) {
        return empMatch.plantas;
      }

      return [];
    },

    /**
     * Selecciona o deselecciona una planta específica de una empresa
     */
    togglePlanta(empresaId, planta) {
      const sId = String(empresaId);
      if (!this.form.plantasPorEmpresa[sId]) {
        this.form.plantasPorEmpresa[sId] = [];
      }
      const arr = this.form.plantasPorEmpresa[sId];
      const plantaNombre = typeof planta === 'object' ? (planta.nombre || planta.nombre_planta || String(planta.id)) : String(planta);

      const idx = arr.findIndex(p => {
        const pStr = typeof p === 'object' ? (p.nombre || p.nombre_planta || String(p.id)) : String(p);
        return pStr.trim().toLowerCase() === plantaNombre.trim().toLowerCase();
      });

      if (idx > -1) {
        arr.splice(idx, 1);
      } else {
        arr.push(plantaNombre);
      }
      if (this.errors.plantas) delete this.errors.plantas;
    },

    isPlantaSelected(empresaId, planta) {
      const sId = String(empresaId);
      const arr = this.form.plantasPorEmpresa[sId] || this.form.plantasPorEmpresa[empresaId] || [];
      const plantaNombre = typeof planta === 'object' ? (planta.nombre || planta.nombre_planta || String(planta.id)) : String(planta);
      const plantaId = typeof planta === 'object' ? String(planta.id || '') : '';

      return arr.some(p => {
        const pStr = typeof p === 'object' ? (p.nombre || p.nombre_planta || String(p.id)) : String(p);
        const pIdStr = typeof p === 'object' ? String(p.id || '') : (typeof p === 'number' ? String(p) : '');
        
        return (
          pStr.trim().toLowerCase() === plantaNombre.trim().toLowerCase() ||
          (plantaId && (pStr === plantaId || pIdStr === plantaId)) ||
          pStr.includes(plantaNombre) || plantaNombre.includes(pStr)
        );
      });
    },

    // ========================================================================
    // 9. BÚSQUEDA Y CREACIÓN DE EMPRESAS CONTRATISTAS
    // ========================================================================

    /**
     * Verifica si una empresa contratista ya está seleccionada actualmente
     */
    contratistaYaSeleccionada(empresa) {
      if (!this.form.contratista) return false;
      const nombreEmpresa = String(empresa?.nombre || empresa?.N_empresa || empresa || "");
      const contratistaActual = String(this.form.contratista || "");
      return Boolean(contratistaActual && (
        nombreEmpresa.toLowerCase() === contratistaActual.toLowerCase() ||
        String(empresa?.id || "") === contratistaActual
      ));
    },

    /**
     * Filtra empresas contratistas en tiempo real según el texto escrito en `contratistaSearchQuery`
     */
    contratistasFiltrados() {
      const q = String(this.contratistaSearchQuery || "").toLowerCase().trim();
      if (!q) return [];
      return this.empresasContratistas
        .filter(empresa => {
          const nombre = String(empresa?.nombre || empresa?.N_empresa || empresa || "");
          return nombre.toLowerCase().includes(q);
        })
        .slice(0, 6);
    },

    /**
     * Selecciona una empresa contratista desde los resultados de búsqueda
     */
    agregarContratistaDesdeBusqueda(empresa) {
      if (this.contratistaYaSeleccionada(empresa)) return;
      const nombre = empresa?.nombre || empresa?.N_empresa || empresa;
      this.form.contratista = nombre;
      this.contratistaSearchQuery = "";
      if (this.errors.contratista) delete this.errors.contratista;
    },

    /**
     * Quita la empresa contratista seleccionada
     */
    removeContratista() {
      this.form.contratista = "";
      if (this.errors.contratista) delete this.errors.contratista;
    },

    openContratistaModal() {
      this.showContratistaModal = true;
      this.nuevaEmpresa = { nombre: "", observacion: "" };
      this.nuevaEmpresaErrors = {};
    },

    closeContratistaModal() {
      this.showContratistaModal = false;
      this.nuevaEmpresa = { nombre: "", observacion: "" };
      this.nuevaEmpresaErrors = {};
    },

    /**
     * Guarda una nueva empresa contratista en la base de datos (POST /emp_contratista)
     */
    async guardarNuevaEmpresa() {
      const nombre = String(this.nuevaEmpresa?.nombre || "").trim();
      const observacion = String(this.nuevaEmpresa?.observacion || "").trim();
      this.nuevaEmpresaErrors = {};

      if (!nombre) {
        this.nuevaEmpresaErrors.nombre = "Ingresa el nombre de la empresa.";
        return;
      }

      this.guardandoEmpresa = true;

      try {
        const response = await fetch(API.contratistas, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            nombre: nombre,
            observacion: observacion
          })
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `Error HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log("✅ Empresa contratista guardada en BD:", data);

        const nueva = {
          id: data.empcont_id || `ec-${Date.now()}`,
          nombre: nombre,
          observacion: observacion
        };

        this.empresasContratistas.unshift(nueva);
        this.form.contratista = nombre;
        this.contratistaSearchQuery = "";
        if (this.errors.contratista) delete this.errors.contratista;
        this.closeContratistaModal();

      } catch (error) {
        console.warn("⚠️ No se pudo guardar en backend, usando guardado local:", error.message);
        const fallback = {
          id: `ec-${Date.now()}`,
          nombre: nombre,
          observacion: observacion
        };
        this.empresasContratistas.unshift(fallback);
        this.form.contratista = nombre;
        this.contratistaSearchQuery = "";
        if (this.errors.contratista) delete this.errors.contratista;
        this.closeContratistaModal();
      } finally {
        this.guardandoEmpresa = false;
      }
    },

    // ========================================================================
    // 10. BÚSQUEDA Y CREACIÓN DE PERSONAS (Paso 2)
    // ========================================================================

    /**
     * Verifica si una persona ya fue agregada a la solicitud actual mediante su documento
     */
    personaYaAgregada(numDoc) {
      return this.personas.some(p => String(p.numDoc || p.identificacion) === String(numDoc));
    },

    /**
     * Filtra el catálogo de personas por nombre o número de documento
     */
    personasFiltradas() {
      const q = String(this.personaSearchQuery || "").trim().toLowerCase();
      if (!q) return [];
      return this.personasRegistradas
        .filter(p => (p.nombres || "").toLowerCase().includes(q) || String(p.numDoc || p.identificacion || "").toLowerCase().includes(q))
        .slice(0, 6);
    },

    /**
     * Añade una persona del catálogo a la lista activa de la solicitud
     */
    agregarPersonaDesdeBusqueda(persona) {
      const doc = persona.numDoc || persona.identificacion;
      if (this.personaYaAgregada(doc)) return;
      this.personas.push({
        id: persona.id,
        item: this.personas.length + 1,
        nombres: persona.nombres || `${persona.nombre || ""} ${persona.apellido || ""}`.trim(),
        tipoDoc: persona.tipoDoc || persona.tipo_doc || "CC",
        numDoc: doc,
        cargo: persona.cargo || "Personal",
        observacion: persona.observacion || "",
        documentos: Array.isArray(persona.documentos) && persona.documentos.length > 0
          ? persona.documentos
          : (persona.documento ? [{ tipo_doc: "Cédula de ciudadanía", nombre_archivo: persona.documento }] : [])
      });
      this.personaSearchQuery = "";
      if (this.errors.personas) delete this.errors.personas;
    },

    /**
     * Elimina una persona de la solicitud actual y renumera los ítems
     */
    removePersona(idx) {
      this.personas.splice(idx, 1);
      this.personas.forEach((p, i) => (p.item = i + 1));
    },

    openPersonaModal() {
      this.isEditingPersona = false;
      this.editingPersonaId = null;
      this.editingPersonaOldDoc = "";
      this.editingPersonaIndex = -1;
      this.nuevaPersona = {
        nombres: "",
        apellidos: "",
        tipoDoc: "CC",
        numDoc: "",
        cargo: "",
        observacion: "",
        documentos: [
          { tipo_doc: "ARL", nombre_archivo: "" }
        ]
      };
      this.personaModalErrors = {};
      this.showPersonaModal = true;
    },

    /**
     * Abre el modal de persona pre-llenando sus datos para edición
     */
    async openEditPersonaModal(persona, idx = -1) {
      this.isEditingPersona = true;
      this.editingPersonaId = persona.id || null;
      this.editingPersonaOldDoc = String(persona.numDoc || persona.identificacion || "").trim();
      this.editingPersonaIndex = idx !== -1 ? idx : this.personas.findIndex(p => String(p.numDoc || p.identificacion || "").trim() === this.editingPersonaOldDoc);

      let nombres = (persona.nombre || "").trim();
      let apellidos = (persona.apellido || "").trim();
      if (!nombres && !apellidos && persona.nombres) {
        const parts = persona.nombres.trim().split(" ");
        if (parts.length > 2) {
          nombres = parts.slice(0, 2).join(" ");
          apellidos = parts.slice(2).join(" ");
        } else if (parts.length === 2) {
          nombres = parts[0];
          apellidos = parts[1];
        } else {
          nombres = parts[0];
          apellidos = "";
        }
      }

      let docs = [];
      if (Array.isArray(persona.documentos) && persona.documentos.length > 0) {
        docs = persona.documentos.map(d => ({
          id: d.id || null,
          tipo_doc: d.tipo_doc || d.tipo || "ARL",
          nombre_archivo: d.nombre_archivo || d.nom_documento || d.nombre || "",
          url_documento: d.url_acceso || (d.nombre_archivo ? `/uploads/documentos/${d.nombre_archivo}` : null),
          nombre_original: d.nombre_original || d.nombre_archivo || ""
        }));
      } else if (persona.documento) {
        docs.push({
          tipo_doc: "Cédula de Ciudadanía",
          nombre_archivo: persona.documento,
          url_documento: `/uploads/documentos/${persona.documento}`,
          nombre_original: persona.documento
        });
      }

      if (docs.length === 0) {
        docs = [{ tipo_doc: "ARL", nombre_archivo: "" }];
      }

      this.nuevaPersona = {
        nombres: nombres,
        apellidos: apellidos,
        tipoDoc: persona.tipoDoc || persona.tipo_doc || "CC",
        numDoc: String(persona.numDoc || persona.identificacion || ""),
        cargo: persona.cargo || "",
        observacion: persona.observacion || "",
        documentos: docs
      };
      this.personaModalErrors = {};
      this.showPersonaModal = true;

      // Si la persona tiene ID numérico en la BD, consultar para tener la versión fresca de documentos
      if (persona.id && !isNaN(parseInt(persona.id))) {
        try {
          const res = await fetch(`${API.personas}/${persona.id}`);
          if (res.ok) {
            const data = await res.json();
            const pDb = data.persona || data.datos || data;
            if (pDb && Array.isArray(pDb.documentos) && pDb.documentos.length > 0) {
              this.nuevaPersona.documentos = pDb.documentos.map(d => ({
                id: d.id || null,
                tipo_doc: d.tipo_doc || "ARL",
                nombre_archivo: d.nombre_archivo || "",
                url_documento: d.url_acceso || (d.nombre_archivo ? `/uploads/documentos/${d.nombre_archivo}` : null),
                nombre_original: d.nombre_archivo || ""
              }));
              if (pDb.nombre && !this.nuevaPersona.nombres) this.nuevaPersona.nombres = pDb.nombre;
              if (pDb.apellido && !this.nuevaPersona.apellidos) this.nuevaPersona.apellidos = pDb.apellido;
            }
          }
        } catch (e) {
          console.warn("No se pudo obtener el detalle fresco de la persona:", e.message);
        }
      }
    },

    closePersonaModal() {
      this.showPersonaModal = false;
      this.isEditingPersona = false;
      this.editingPersonaId = null;
      this.editingPersonaOldDoc = "";
      this.editingPersonaIndex = -1;
      this.nuevaPersona = {
        nombres: "",
        apellidos: "",
        tipoDoc: "CC",
        numDoc: "",
        cargo: "",
        observacion: "",
        documentos: [
          { tipo_doc: "ARL", nombre_archivo: "" }
        ]
      };
      this.personaModalErrors = {};
    },

    /**
     * Sube físicamente un archivo al servidor FastAPI (POST /api/v1/solicitudes/subir-documento/)
     * Incluye validación de tamaño, extensión y manejo de alertas SweetAlert2.
     */
    async uploadArchivo(file, tipoDocumento = "general") {
      if (!file) return null;

      const MAX_SIZE_MB = 10;
      const MAX_BYTES = MAX_SIZE_MB * 1024 * 1024;
      const extension = (file.name.split('.').pop() || '').toLowerCase().trim();
      const formatosPermitidos = ['pdf', 'png', 'jpg', 'jpeg'];

      // 1. Validación Frontend: Archivo vacío
      if (file.size === 0) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Archivo vacío',
            text: 'El archivo seleccionado está vacío (0 bytes) y no se puede procesar.',
            confirmButtonColor: '#f59e0b',
            confirmButtonText: 'Entendido'
          });
        } else {
          alert('El archivo seleccionado está vacío (0 bytes).');
        }
        return null;
      }

      // 2. Validación Frontend: Extensión permitida
      if (!formatosPermitidos.includes(extension)) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'error',
            title: 'Formato no permitido',
            html: `La extensión <b>.${extension}</b> no está permitida.<br>Solo se admiten documentos en formato <b>PDF, PNG o JPG</b>.`,
            confirmButtonColor: '#ef4444',
            confirmButtonText: 'Entendido'
          });
        } else {
          alert(`Formato .${extension} no permitido. Solo se admiten PDF, PNG o JPG.`);
        }
        return null;
      }

      // 3. Validación Frontend: Tamaño máximo (10 MB)
      if (file.size > MAX_BYTES) {
        const tamanoMB = (file.size / (1024 * 1024)).toFixed(2);
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Tamaño excedido',
            html: `El archivo pesa <b>${tamanoMB} MB</b> y supera el límite de <b>${MAX_SIZE_MB} MB</b>.<br>Por favor comprímelo o sube un documento más liviano.`,
            confirmButtonColor: '#f59e0b',
            confirmButtonText: 'Entendido'
          });
        } else {
          alert(`El archivo pesa ${tamanoMB} MB y supera el límite de ${MAX_SIZE_MB} MB.`);
        }
        return null;
      }

      // 4. Envío al backend
      const formData = new FormData();
      formData.append("file", file);
      formData.append("tipo_documento", tipoDocumento);

      try {
        const res = await fetch(`${API.solicitudes}/subir-documento/`, {
          method: "POST",
          body: formData
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          const detalle = err.detail || `Error al procesar el archivo (Código ${res.status})`;

          if (typeof Swal !== 'undefined') {
            Swal.fire({
              icon: 'error',
              title: 'Archivo rechazado por el servidor',
              text: detalle,
              confirmButtonColor: '#ef4444',
              confirmButtonText: 'Aceptar'
            });
          } else {
            alert(detalle);
          }
          return null;
        }

        const data = await res.json();
        console.log("📁 [FILE UPLOAD SEGURO] Archivo subido con éxito:", data);

        // Notificación flotante sutil de éxito
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'success',
            title: 'Documento cargado correctamente',
            showConfirmButton: false,
            timer: 2500,
            timerProgressBar: true
          });
        }

        return {
          nombre_archivo: data.nombre_archivo,
          url_documento: data.url_documento,
          nombre_original: data.nombre_original || file.name
        };
      } catch (error) {
        console.error("❌ Error al subir archivo:", error);
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'error',
            title: 'Error de conexión',
            text: 'No fue posible comunicarse con el servidor para subir el documento.',
            confirmButtonColor: '#ef4444',
            confirmButtonText: 'Cerrar'
          });
        }
        return null;
      }
    },

    /**
     * Agrega una nueva fila de documento a la persona en el modal (1 a N)
     */
    addDocumentoPersona() {
      this.nuevaPersona.documentos.push({
        tipo_doc: "Seguridad Social / ARL",
        nombre_archivo: ""
      });
    },

    /**
     * Elimina una fila de documento en el modal de persona
     */
    removeDocumentoPersona(idx) {
      if (this.nuevaPersona.documentos.length > 1) {
        this.nuevaPersona.documentos.splice(idx, 1);
      } else {
        this.nuevaPersona.documentos[0].nombre_archivo = "";
      }
    },

    /**
     * Captura y sube el archivo seleccionado para el documento de persona
     */
    async handleDocumentoPersonaFile(event, idx) {
      const file = event.target.files[0];
      if (file && this.nuevaPersona.documentos[idx]) {
        const tipo = this.nuevaPersona.documentos[idx].tipo_doc || "cedula";
        const uploaded = await this.uploadArchivo(file, tipo);
        if (uploaded) {
          this.nuevaPersona.documentos[idx].nombre_archivo = uploaded.nombre_archivo;
          this.nuevaPersona.documentos[idx].url_documento = uploaded.url_documento;
          this.nuevaPersona.documentos[idx].nombre_original = uploaded.nombre_original;
        } else {
          // Si falló la validación, limpiar el input para que pueda seleccionar otro
          event.target.value = "";
          this.nuevaPersona.documentos[idx].nombre_archivo = "";
          this.nuevaPersona.documentos[idx].url_documento = null;
        }
      }
    },

    /**
     * Valida los campos obligatorios del modal de persona
     */
    validateNuevaPersona() {
      this.personaModalErrors = {};
      const nombres = String(this.nuevaPersona.nombres || "").trim();
      const apellidos = String(this.nuevaPersona.apellidos || "").trim();
      const numDoc = String(this.nuevaPersona.numDoc || "").trim();
      const cargo = String(this.nuevaPersona.cargo || "").trim();

      if (!apellidos) this.personaModalErrors.apellidos = "Ingresa los apellidos.";
      if (!nombres) this.personaModalErrors.nombres = "Ingresa los nombres.";
      if (!numDoc) this.personaModalErrors.numDoc = "Ingresa el número de documento.";
      if (!cargo) this.personaModalErrors.cargo = "Ingresa el cargo.";

      // Al editar, ignorar el chequeo de duplicados contra sí mismo
      const esDuplicado = this.personas.some((p, idx) => {
        const docP = String(p.numDoc || p.identificacion || "").trim();
        if (docP !== numDoc) return false;
        if (this.isEditingPersona) {
          if (this.editingPersonaIndex !== -1 && idx === this.editingPersonaIndex) return false;
          if (this.editingPersonaId && p.id && String(p.id) === String(this.editingPersonaId)) return false;
          if (this.editingPersonaOldDoc && docP === this.editingPersonaOldDoc) return false;
        }
        return true;
      });

      if (numDoc && esDuplicado) {
        this.personaModalErrors.numDoc = "Ya existe una persona registrada en la solicitud con ese número de documento.";
      }
      return Object.keys(this.personaModalErrors).length === 0;
    },

    /**
     * Guarda la persona en el backend (POST /personas/create o PUT /personas/{id}),
     * la sincroniza con el catálogo y la actualiza en la solicitud activa
     */
    async guardarNuevaPersona() {
      if (!this.validateNuevaPersona()) return;

      const nombres = String(this.nuevaPersona.nombres || "").trim();
      const apellidos = String(this.nuevaPersona.apellidos || "").trim();
      const nombreCompleto = `${nombres} ${apellidos}`.trim();
      const tipoDoc = this.nuevaPersona.tipoDoc || "CC";
      const numDoc = String(this.nuevaPersona.numDoc || "").trim();
      const cargo = String(this.nuevaPersona.cargo || "").trim();
      const observacion = String(this.nuevaPersona.observacion || "").trim();

      // Filtra y estructura los documentos válidos adjuntados
      const docsValidos = (this.nuevaPersona.documentos || [])
        .filter(d => d.nombre_archivo && d.nombre_archivo.trim())
        .map(d => ({
          id: d.id || null,
          tipo_doc: d.tipo_doc,
          nombre_archivo: d.nombre_archivo.trim(),
          url_acceso: d.url_documento || `/uploads/documentos/${d.nombre_archivo.trim()}`
        }));

      this.guardandoPersona = true;

      if (this.isEditingPersona) {
        // ==================== MODO EDICIÓN ====================
        const personaActualizada = {
          id: this.editingPersonaId,
          nombres: nombreCompleto,
          nombre: nombres,
          apellido: apellidos,
          tipoDoc: tipoDoc,
          numDoc: numDoc,
          identificacion: numDoc,
          cargo: cargo,
          observacion: observacion,
          documentos: docsValidos
        };

        try {
          if (this.editingPersonaId && !isNaN(parseInt(this.editingPersonaId))) {
            const response = await fetch(`${API.personas}/${this.editingPersonaId}`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                nombre: nombres,
                apellido: apellidos,
                tipo_doc: tipoDoc,
                identificacion: numDoc,
                cargo: cargo,
                observacion: observacion,
                documentos_ids: docsValidos.map(d => ({ tipo_doc: d.tipo_doc, nombre_archivo: d.nombre_archivo }))
              })
            });

            if (!response.ok) {
              const errData = await response.json().catch(() => ({}));
              throw new Error(errData.detail || errData.mensaje || `HTTP ${response.status}`);
            }
            console.log("✅ Persona actualizada exitosamente en BD");
          }
        } catch (error) {
          console.warn("⚠️ No se pudo actualizar en backend, aplicando cambios localmente:", error.message);
        } finally {
          // 1. Actualizar en el catálogo de personas registradas
          const idxCat = this.personasRegistradas.findIndex(p =>
            (this.editingPersonaId && p.id && String(p.id) === String(this.editingPersonaId)) ||
            String(p.numDoc || p.identificacion || "").trim() === this.editingPersonaOldDoc
          );
          if (idxCat !== -1) {
            this.personasRegistradas[idxCat] = {
              ...this.personasRegistradas[idxCat],
              id: this.editingPersonaId || this.personasRegistradas[idxCat].id,
              nombres: nombreCompleto,
              nombre: nombres,
              apellido: apellidos,
              tipoDoc: tipoDoc,
              numDoc: numDoc,
              identificacion: numDoc,
              cargo: cargo,
              observacion: observacion,
              documentos: docsValidos
            };
          }

          // 2. Actualizar en la lista activa de la solicitud (this.personas)
          let idxSol = this.editingPersonaIndex;
          if (idxSol === -1 || idxSol >= this.personas.length) {
            idxSol = this.personas.findIndex(p =>
              (this.editingPersonaId && p.id && String(p.id) === String(this.editingPersonaId)) ||
              String(p.numDoc || p.identificacion || "").trim() === this.editingPersonaOldDoc
            );
          }
          if (idxSol !== -1) {
            personaActualizada.item = this.personas[idxSol].item || (idxSol + 1);
            this.personas[idxSol] = { ...this.personas[idxSol], ...personaActualizada };
          } else {
            personaActualizada.item = this.personas.length + 1;
            this.personas.push(personaActualizada);
          }

          // 3. Sincronizar conductor de vehículos si estaba asignada
          if (this.editingPersonaOldDoc) {
            this.vehiculos.forEach(v => {
              if (v.conductor && (v.conductor === this.editingPersonaOldDoc || v.conductor.includes(this.editingPersonaOldDoc))) {
                v.conductor = `${nombreCompleto} (${numDoc})`;
              }
            });
          }

          if (typeof Swal !== 'undefined') {
            Swal.fire({
              toast: true,
              position: 'top-end',
              icon: 'success',
              title: 'Persona actualizada correctamente',
              showConfirmButton: false,
              timer: 2500,
              timerProgressBar: true
            });
          }

          if (this.errors.personas) delete this.errors.personas;
          this.guardandoPersona = false;
          this.closePersonaModal();
        }
      } else {
        // ==================== MODO CREACIÓN ====================
        const personaNueva = {
          item: this.personas.length + 1,
          nombres: nombreCompleto,
          nombre: nombres,
          apellido: apellidos,
          tipoDoc: tipoDoc,
          numDoc: numDoc,
          cargo: cargo,
          observacion: observacion,
          documentos: docsValidos
        };

        try {
          const response = await fetch(`${API.personas}/create`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              nombre: nombres,
              apellido: apellidos,
              tipo_doc: tipoDoc,
              identificacion: numDoc,
              cargo: cargo,
              observacion: observacion,
              documentos_ids: docsValidos.map(d => ({ tipo_doc: d.tipo_doc, nombre_archivo: d.nombre_archivo }))
            })
          });

          if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || errData.mensaje || `HTTP ${response.status}`);
          }

          const data = await response.json();
          console.log("✅ Persona guardada exitosamente en BD:", data);
          const nuevoId = data.persona || data.id || data.person_id || (data.datos && data.datos.id);
          if (nuevoId && !isNaN(parseInt(nuevoId))) {
            personaNueva.id = parseInt(nuevoId);
          }
        } catch (error) {
          console.warn("⚠️ No se pudo guardar en backend, guardando localmente:", error.message);
          personaNueva.id = `per-${Date.now()}`;
        } finally {
          // 1. Agregar al catálogo de búsqueda
          if (!this.personasRegistradas.some(p => String(p.numDoc || p.identificacion) === numDoc)) {
            this.personasRegistradas.unshift({
              id: personaNueva.id,
              nombres: nombreCompleto,
              nombre: nombres,
              apellido: apellidos,
              tipoDoc: tipoDoc,
              numDoc: numDoc,
              cargo: cargo,
              observacion: observacion,
              documentos: docsValidos
            });
          }

          // 2. Agregar directamente a la lista activa de la solicitud
          if (!this.personaYaAgregada(numDoc)) {
            this.personas.push(personaNueva);
          }

          if (this.errors.personas) delete this.errors.personas;
          this.personaSearchQuery = "";
          this.guardandoPersona = false;
          this.closePersonaModal();
        }
      }
    },

    // ========================================================================
    // 11. VEHÍCULOS Y EQUIPOS (Paso 3)
    // ========================================================================
    vehiculoYaAgregado(placa) {
      if (!placa) return false;
      const cleanPlaca = String(placa).toUpperCase().trim();
      return this.vehiculos.some(v => (v.placa || "").toUpperCase().trim() === cleanPlaca);
    },

    vehiculosFiltrados() {
      const q = String(this.vehiculoSearchQuery || "").trim().toLowerCase();
      if (!q) return [];
      return this.vehiculosRegistrados
        .filter(v => 
          (v.placa || "").toLowerCase().includes(q) ||
          (v.tipo || "").toLowerCase().includes(q) ||
          (v.conductor || "").toLowerCase().includes(q)
        )
        .slice(0, 6);
    },

    agregarVehiculoDesdeBusqueda(vehiculo) {
      const placa = (vehiculo.placa || "").toUpperCase().trim();
      if (this.vehiculoYaAgregado(placa)) return;
      this.vehiculos.push({
        id: vehiculo.id,
        tipo: vehiculo.tipo || "Camioneta",
        placa: placa,
        conductor: vehiculo.conductor || "",
        licencia_doc: vehiculo.licencia_doc || "",
        documentos: Array.isArray(vehiculo.documentos) && vehiculo.documentos.length > 0
          ? vehiculo.documentos.map(d => ({
              tipo_doc: d.tipo_doc || d.tipo || "SOAT",
              nombre_archivo: d.nombre_archivo || d.nom_documento || ""
            }))
          : []
      });
      this.vehiculoSearchQuery = "";
    },

    openVehiculoModal() {
      this.isEditingVehiculo = false;
      this.editingVehiculoId = null;
      this.editingVehiculoOldPlaca = "";
      this.editingVehiculoIndex = -1;
      this.nuevoVehiculo = {
        tipo: "Camioneta",
        placa: "",
        conductor: "",
        licencia_doc: "",
        licencia_url: null,
        documentos: [
          { tipo_doc: "SOAT", nombre_archivo: "" }
        ]
      };
      this.vehiculoModalErrors = {};
      this.showVehiculoModal = true;
    },

    /**
     * Abre el modal de vehículo pre-llenando sus datos para edición
     */
    openEditVehiculoModal(vehiculo, idx = -1) {
      this.isEditingVehiculo = true;
      this.editingVehiculoId = vehiculo.id || null;
      this.editingVehiculoOldPlaca = String(vehiculo.placa || "").toUpperCase().trim();
      this.editingVehiculoIndex = idx !== -1 ? idx : this.vehiculos.findIndex(v => String(v.placa || "").toUpperCase().trim() === this.editingVehiculoOldPlaca);

      let docs = [];
      if (Array.isArray(vehiculo.documentos) && vehiculo.documentos.length > 0) {
        docs = vehiculo.documentos.map(d => ({
          id: d.id || null,
          tipo_doc: d.tipo_doc || d.tipo || "SOAT",
          nombre_archivo: d.nombre_archivo || d.nom_documento || "",
          url_documento: d.url_documento || d.url_acceso || (d.nombre_archivo ? `/uploads/documentos/${d.nombre_archivo}` : null)
        }));
      } else {
        docs = [{ tipo_doc: "SOAT", nombre_archivo: "" }];
      }

      this.nuevoVehiculo = {
        tipo: vehiculo.tipo || "Camioneta",
        placa: String(vehiculo.placa || "").toUpperCase().trim(),
        conductor: vehiculo.conductor || "",
        licencia_doc: vehiculo.licencia_doc || vehiculo.licencia || "",
        licencia_url: vehiculo.licencia_url || null,
        documentos: docs
      };
      this.vehiculoModalErrors = {};
      this.showVehiculoModal = true;
    },

    closeVehiculoModal() {
      this.showVehiculoModal = false;
      this.isEditingVehiculo = false;
      this.editingVehiculoId = null;
      this.editingVehiculoOldPlaca = "";
      this.editingVehiculoIndex = -1;
      this.nuevoVehiculo = {
        tipo: "Camioneta",
        placa: "",
        conductor: "",
        licencia_doc: "",
        licencia_url: null,
        documentos: [
          { tipo_doc: "SOAT", nombre_archivo: "" }
        ]
      };
      this.vehiculoModalErrors = {};
    },

    addDocumentoNuevoVehiculo() {
      this.nuevoVehiculo.documentos.push({
        tipo_doc: "Revisión Tecnomecánica",
        nombre_archivo: ""
      });
    },

    removeDocumentoNuevoVehiculo(idx) {
      if (this.nuevoVehiculo.documentos.length > 1) {
        this.nuevoVehiculo.documentos.splice(idx, 1);
      } else {
        this.nuevoVehiculo.documentos[0].nombre_archivo = "";
      }
    },

    async handleDocumentoNuevoVehiculoFile(event, idx) {
      const file = event.target.files[0];
      if (file && this.nuevoVehiculo.documentos[idx]) {
        const tipo = this.nuevoVehiculo.documentos[idx].tipo_doc || "soat";
        const uploaded = await this.uploadArchivo(file, tipo);
        if (uploaded) {
          this.nuevoVehiculo.documentos[idx].nombre_archivo = uploaded.nombre_archivo;
          this.nuevoVehiculo.documentos[idx].url_documento = uploaded.url_documento;
          this.nuevoVehiculo.documentos[idx].nombre_original = uploaded.nombre_original;
        } else {
          event.target.value = "";
          this.nuevoVehiculo.documentos[idx].nombre_archivo = "";
          this.nuevoVehiculo.documentos[idx].url_documento = null;
        }
      }
    },

    async handleLicenciaNuevoVehiculoFile(event) {
      const file = event.target.files[0];
      if (file) {
        const uploaded = await this.uploadArchivo(file, "licencia");
        if (uploaded) {
          this.nuevoVehiculo.licencia_doc = uploaded.nombre_archivo;
          this.nuevoVehiculo.licencia_url = uploaded.url_documento;
        } else {
          event.target.value = "";
          this.nuevoVehiculo.licencia_doc = "";
          this.nuevoVehiculo.licencia_url = null;
        }
      }
    },

    removeLicenciaNuevoVehiculo() {
      this.nuevoVehiculo.licencia_doc = "";
      this.nuevoVehiculo.licencia_url = null;
    },

    async handleLicenciaVehiculoFile(event, vIdx) {
      const file = event.target.files[0];
      if (file && this.vehiculos[vIdx]) {
        const uploaded = await this.uploadArchivo(file, "licencia");
        if (uploaded) {
          this.vehiculos[vIdx].licencia_doc = uploaded.nombre_archivo;
          this.vehiculos[vIdx].licencia_url = uploaded.url_documento;
        } else {
          event.target.value = "";
          this.vehiculos[vIdx].licencia_doc = "";
          this.vehiculos[vIdx].licencia_url = null;
        }
      }
    },

    removeLicenciaVehiculo(vIdx) {
      if (this.vehiculos[vIdx]) {
        this.vehiculos[vIdx].licencia_doc = "";
        this.vehiculos[vIdx].licencia_url = null;
      }
    },

    validateNuevoVehiculo() {
      this.vehiculoModalErrors = {};
      const placa = String(this.nuevoVehiculo.placa || "").toUpperCase().trim();
      const tipo = String(this.nuevoVehiculo.tipo || "").trim();

      if (!placa) {
        this.vehiculoModalErrors.placa = "Ingresa la placa del vehículo.";
      }
      if (!tipo) {
        this.vehiculoModalErrors.tipo = "Selecciona el tipo de vehículo.";
      }

      const esDuplicado = this.vehiculos.some((v, idx) => {
        const pPlaca = String(v.placa || "").toUpperCase().trim();
        if (pPlaca !== placa) return false;
        if (this.isEditingVehiculo) {
          if (this.editingVehiculoIndex !== -1 && idx === this.editingVehiculoIndex) return false;
          if (this.editingVehiculoId && v.id && String(v.id) === String(this.editingVehiculoId)) return false;
          if (this.editingVehiculoOldPlaca && pPlaca === this.editingVehiculoOldPlaca) return false;
        }
        return true;
      });

      if (placa && esDuplicado) {
        this.vehiculoModalErrors.placa = "Ya agregaste un vehículo con esta placa a la solicitud.";
      }
      return Object.keys(this.vehiculoModalErrors).length === 0;
    },

    async guardarNuevoVehiculo() {
      if (!this.validateNuevoVehiculo()) return;

      const placa = String(this.nuevoVehiculo.placa || "").toUpperCase().trim();
      const tipo = this.nuevoVehiculo.tipo || "Camioneta";
      const conductor = String(this.nuevoVehiculo.conductor || "").trim();
      const licencia_doc = String(this.nuevoVehiculo.licencia_doc || "").trim();

      const docsValidos = (this.nuevoVehiculo.documentos || [])
        .filter(d => d.nombre_archivo && d.nombre_archivo.trim())
        .map(d => ({
          tipo_doc: d.tipo_doc,
          nom_documento: d.nombre_archivo.trim(),
          nombre_archivo: d.nombre_archivo.trim()
        }));

      this.guardandoVehiculo = true;

      if (this.isEditingVehiculo) {
        // ==================== MODO EDICIÓN ====================
        const vehiculoActualizado = {
          id: this.editingVehiculoId,
          tipo: tipo,
          placa: placa,
          conductor: conductor,
          licencia_doc: licencia_doc,
          licencia_url: this.nuevoVehiculo.licencia_url || null,
          documentos: docsValidos
        };

        try {
          if (this.editingVehiculoId && !isNaN(parseInt(this.editingVehiculoId))) {
            const response = await fetch(`${API.vehiculos}/${this.editingVehiculoId}`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                tipo: tipo,
                placa: placa,
                conductor: conductor,
                licencia_doc: licencia_doc,
                licencia_url: this.nuevoVehiculo.licencia_url || null,
                documentos: docsValidos
              })
            });

            if (!response.ok) {
              const errData = await response.json().catch(() => ({}));
              throw new Error(errData.detail || errData.mensaje || `HTTP ${response.status}`);
            }
            console.log("✅ Vehículo actualizado exitosamente en BD");
          }
        } catch (error) {
          console.warn("⚠️ No se pudo actualizar vehículo en el backend:", error.message);
        }

        // 1. Actualizar en this.vehiculos (lista de la solicitud activa)
        if (this.editingVehiculoIndex !== -1 && this.vehiculos[this.editingVehiculoIndex]) {
          this.vehiculos[this.editingVehiculoIndex] = {
            ...this.vehiculos[this.editingVehiculoIndex],
            ...vehiculoActualizado
          };
        } else {
          const idxEncontrado = this.vehiculos.findIndex(v => String(v.placa || "").toUpperCase().trim() === this.editingVehiculoOldPlaca || (this.editingVehiculoId && String(v.id) === String(this.editingVehiculoId)));
          if (idxEncontrado !== -1) {
            this.vehiculos[idxEncontrado] = {
              ...this.vehiculos[idxEncontrado],
              ...vehiculoActualizado
            };
          }
        }

        // 2. Actualizar en el catálogo de búsqueda
        const regIdx = this.vehiculosRegistrados.findIndex(v => String(v.placa || "").toUpperCase().trim() === this.editingVehiculoOldPlaca || (this.editingVehiculoId && String(v.id) === String(this.editingVehiculoId)));
        if (regIdx !== -1) {
          this.vehiculosRegistrados[regIdx] = {
            ...this.vehiculosRegistrados[regIdx],
            ...vehiculoActualizado
          };
        }

        this.guardandoVehiculo = false;
        this.closeVehiculoModal();
        return;
      }

      const vehiculoNuevo = {
        tipo: tipo,
        placa: placa,
        conductor: conductor,
        licencia_doc: licencia_doc,
        documentos: docsValidos
      };

      try {
        const response = await fetch(`${API.vehiculos}/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tipo: tipo,
            placa: placa,
            documentos: docsValidos,
            conductor: conductor,
            licencia_doc: licencia_doc
          })
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || errData.mensaje || `HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log("✅ Vehículo guardado exitosamente en BD:", data);
        if (data.id) vehiculoNuevo.id = data.id;
      } catch (error) {
        console.warn("⚠️ No se pudo guardar en backend el vehículo, agregando localmente:", error.message);
        vehiculoNuevo.id = `veh-${Date.now()}`;
      } finally {
        // 1. Agregar al catálogo de búsqueda
        if (!this.vehiculosRegistrados.some(v => (v.placa || "").toUpperCase().trim() === placa)) {
          this.vehiculosRegistrados.unshift({
            id: vehiculoNuevo.id,
            tipo: tipo,
            placa: placa,
            conductor: conductor,
            licencia_doc: licencia_doc,
            documentos: docsValidos
          });
        }

        // 2. Agregar a la solicitud activa
        if (!this.vehiculoYaAgregado(placa)) {
          this.vehiculos.push(vehiculoNuevo);
        }

        this.vehiculoSearchQuery = "";
        this.guardandoVehiculo = false;
        this.closeVehiculoModal();
      }
    },

    removeVehiculo(idx) {
      this.vehiculos.splice(idx, 1);
    },

    addEquipo() {
      this.equipos.push({ marca: "", modelo: "", serie: "" });
    },
    removeEquipo(idx) {
      this.equipos.splice(idx, 1);
    },

    // ========================================================================
    // 12. VALIDACIONES POR PASO
    // ========================================================================
    validateStep(step) {
      this.errors = {};

      // Validación Paso 1: Datos Generales
      if (step === 1) {
        if (!this.form.contratista.trim()) this.errors.contratista = "Ingresa el contratista.";
        if (this.form.empresas.length === 0) {
          this.errors.empresas = "Selecciona al menos una empresa.";
        } else {
          const empresaSinPlantas = this.form.empresas.some(
            id => (this.form.plantasPorEmpresa[id] || []).length === 0
          );
          if (empresaSinPlantas) this.errors.plantas = "Selecciona al menos una planta para cada empresa elegida.";
        }
        if (!this.form.fechaIngreso) this.errors.fechaIngreso = "Selecciona la fecha de ingreso.";
        if (!this.form.fechaSalida) this.errors.fechaSalida = "Selecciona la fecha de salida.";
        if (this.form.fechaIngreso && this.form.fechaSalida && this.form.fechaSalida < this.form.fechaIngreso) {
          this.errors.fechaSalida = "La fecha de salida no puede ser anterior al ingreso.";
        }
        if (!this.form.nivelRiesgo) this.errors.nivelRiesgo = "Selecciona el nivel de riesgo.";
        if (!this.form.actividad.trim()) this.errors.actividad = "Describe la actividad a realizar.";
      }

      // Validación Paso 2: Al menos una persona agregada
      if (step === 2) {
        if (this.personas.length === 0) {
          this.errors.personas = "Busca y agrega al menos una persona, o registra una nueva.";
        }
      }

      // Validación Paso 4: Confirmación de veracidad
      if (step === 4) {
        if (!this.aceptaVeracidad) this.errors.veracidad = "Debes confirmar que la información es veraz.";
      }

      return Object.keys(this.errors).length === 0;
    },

    // ========================================================================
    // 13. CONTROL DE NAVEGACIÓN ENTRE PASOS
    // ========================================================================
    nextStep() {
      if (!this.validateStep(this.currentStep)) return;
      if (this.currentStep < this.steps.length) this.currentStep++;
      window.scrollTo({ top: 0, behavior: "smooth" });
    },

    prevStep() {
      if (this.currentStep > 1) this.currentStep--;
      window.scrollTo({ top: 0, behavior: "smooth" });
    },

    goToStep(n) {
      // Solo se permite retroceder haciendo clic en el stepper, no saltar hacia adelante
      if (n < this.currentStep) this.currentStep = n;
    },

    stepStatus(n) {
      if (n < this.currentStep) return "is-complete";
      if (n === this.currentStep) return "is-current";
      return "";
    },

    // ========================================================================
    // 14. ENVÍO FINAL DEL FORMULARIO
    // ========================================================================
    nextSolicitudId() {
      const year = new Date().getFullYear();
      return `SOL-${year}-0001`;
    },

    /**
     * Envía la solicitud al endpoint FastAPI (POST /api/v1/solicitudes/)
     */
    async submitForm() {
      if (!this.validateStep(4)) return;
      this.submitting = true;

      // 1. Resolver IDs para Backend
      // ID de Empresa Origen
      let empresaOrigenId = 1;
      if (this.form.empresas.length > 0) {
        const empEncontrada = this.empresas.find(e => String(e.id) === String(this.form.empresas[0]));
        empresaOrigenId = empEncontrada && !isNaN(parseInt(empEncontrada.id)) ? parseInt(empEncontrada.id) : (parseInt(this.form.empresas[0]) || 1);
      }

      // ID de Empresa Contratista
      let contratistaId = 1;
      const contEncontrado = this.empresasContratistas.find(c =>
        String(c.nombre || c.N_empresa || "").toLowerCase() === String(this.form.contratista || "").toLowerCase() ||
        String(c.id) === String(this.form.contratista)
      );
      if (contEncontrado && !isNaN(parseInt(contEncontrado.id))) {
        contratistaId = parseInt(contEncontrado.id);
      }

      // IDs de Plantas seleccionadas
      const plantasIds = [];
      for (const empId of this.form.empresas) {
        const empresaObj = this.empresas.find(e => String(e.id) === String(empId));
        const plantasSeleccionadas = this.form.plantasPorEmpresa[empId] || [];
        for (const pSel of plantasSeleccionadas) {
          if (empresaObj && Array.isArray(empresaObj.plantas)) {
            const match = empresaObj.plantas.find(p =>
              (typeof p === "object" && (p.nombre === pSel || String(p.id) === String(pSel))) ||
              (typeof p === "string" && p === pSel)
            );
            if (match && typeof match === "object" && match.id && !isNaN(parseInt(match.id))) {
              plantasIds.push(parseInt(match.id));
              continue;
            }
          }
          if (!isNaN(parseInt(pSel))) {
            plantasIds.push(parseInt(pSel));
          } else {
            plantasIds.push(1);
          }
        }
      }

      // IDs de Personas garantizados
      const personasIds = [];
      for (const p of this.personas) {
        let pId = parseInt(p.id);
        if (!isNaN(pId) && pId > 0) {
          personasIds.push(pId);
        } else if (p.numDoc || p.identificacion) {
          const doc = String(p.numDoc || p.identificacion).trim();
          const match = this.personasRegistradas.find(pr => String(pr.numDoc || pr.identificacion).trim() === doc);
          if (match && !isNaN(parseInt(match.id)) && parseInt(match.id) > 0) {
            p.id = parseInt(match.id);
            personasIds.push(parseInt(match.id));
          }
        }
      }

      // Estructura de personas para payload de backend
      const personasPayload = this.personas.map(p => ({
        id: parseInt(p.id) || undefined,
        id_persona: parseInt(p.id) || undefined,
        nombre: p.nombres || p.nombre || "Personal",
        identificacion: p.numDoc || p.identificacion || "",
        tipo_doc: p.tipoDoc || p.tipo_doc || "CC",
        cargo: p.cargo || "Personal",
        autorizado: true,
        motivo: null
      }));

      // Usuario autenticado (Diligenciador únicamente para nueva solicitud)
      const sesion = JSON.parse(sessionStorage.getItem("incarsa_session") || "null");
      const diligenciadorId = (sesion && sesion.id && !isNaN(parseInt(sesion.id))) ? parseInt(sesion.id) : 1;

      // Vehículos estructurados con licencia y documentos
      const vehiculosPayload = this.vehiculos.map(v => ({
        id: v.id || undefined,
        tipo: v.tipo || "Camioneta",
        placa: (v.placa || "").toUpperCase().trim(),
        conductor: v.conductor || "",
        licencia_doc: v.licencia_doc || "",
        documentos: (v.documentos || [])
          .filter(d => d.nombre_archivo && d.nombre_archivo.trim())
          .map(d => ({
            id: d.id || undefined,
            tipo_doc: d.tipo_doc || "soat",
            nom_documento: d.nombre_archivo.trim(),
            nombre_archivo: d.nombre_archivo.trim()
          }))
      }));

      // Equipos de Cómputo
      const equiposPayload = (this.equipos || [])
        .filter(e => (e.marca && e.marca.trim()) || (e.modelo && e.modelo.trim()) || (e.serie && e.serie.trim()))
        .map(e => ({
          marca: (e.marca || "").trim() || "Genérica",
          modelo: (e.modelo || "").trim() || "General",
          serie: (e.serie || "").trim() || "S/N"
        }));

      // Payload para la API
      const payloadApi = {
        codigo_radicado: this.form.codigo || undefined,
        observaciones: this.form.observaciones || undefined,
        estado: (this.isEdit && this.esSuperAdmin) ? (this.form.estado || this.solicitudOriginal?.estado || "ENVIADO") : undefined,
        empresa_origen: empresaOrigenId,
        diligenciado_por: this.isEdit ? undefined : diligenciadorId,
        nivel_de_riesgo: this.form.nivelRiesgo || "Bajo",
        tipo_personal: "Contratista",
        empresa_contratista: contratistaId,
        plantas_ids: plantasIds.length ? plantasIds : [1],
        personas_ids: personasIds,
        personas: personasPayload,
        fecha_inicio: this.form.fechaIngreso,
        fecha_fin: this.form.fechaSalida,
        actividad: this.form.actividad,
        is_active: true,
        vehiculo: vehiculosPayload,
        vehiculos: vehiculosPayload,
        eq_computo: equiposPayload,
        equipos: equiposPayload,
        token_edicion: this.tokenEdicion || undefined
      };

      // ========================================================================
      // MODO EDICIÓN (PATCH)
      // ========================================================================
      if (this.isEdit && this.editId) {
        try {
          console.log(`📤 [PATCH] Actualizando solicitud ${this.editId} en FastAPI:`, payloadApi);
          
          const response = await fetch(`${API.solicitudes}/${this.editId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payloadApi)
          });

          if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || errData.mensaje || `HTTP ${response.status}`);
          }

          // Actualizar en localStorage si existe allí
          try {
            const guardadas = JSON.parse(localStorage.getItem("incarsa_solicitudes_creadas") || "[]");
            const idx = guardadas.findIndex(s => String(s.id) === String(this.editId));
            const solicitudActualizada = {
              id: this.editId,
              estado: this.solicitudDevuelta ? "POR APROBAR" : (this.form.estado || this.solicitudOriginal?.estado || "ENVIADO"),
              contratista: this.form.contratista,
              empresaOrigen: this.empresaNombre(this.form.empresas[0]),
              plantas: plantasIds,
              fechaIngreso: this.form.fechaIngreso,
              fechaSalida: this.form.fechaSalida,
              nivelRiesgo: this.form.nivelRiesgo,
              actividad: this.form.actividad,
              diligenciadoPor: this.form.diligenciadoPor,
              diligenciado_por: this.solicitudOriginal?.diligenciado_por || this.solicitudOriginal?.id_diligenciador,
              personas: this.personas,
              vehiculos: this.vehiculos,
              equipos: this.equipos
            };
            if (idx > -1) {
              guardadas[idx] = solicitudActualizada;
            } else {
              guardadas.unshift(solicitudActualizada);
            }
            localStorage.setItem("incarsa_solicitudes_creadas", JSON.stringify(guardadas));
          } catch (e) {}

          // Sincronizar almacenamiento local de revisiones según nuevo estado
          try {
            const storageKeyRev = `incarsa_revisiones_${this.editId}`;
            const nuevoEstado = this.solicitudDevuelta ? "POR APROBAR" : String(this.form.estado || "").trim().toUpperCase();
            if (["EN REVISIÓN", "EN REVISION", "ENVIADO"].includes(nuevoEstado)) {
              localStorage.removeItem(storageKeyRev);
            } else if (nuevoEstado === "POR APROBAR") {
              const dataRev = JSON.parse(localStorage.getItem(storageKeyRev) || "null");
              if (dataRev) {
                if (Array.isArray(dataRev)) {
                  const filtradas = dataRev.filter(r => String(r.rol || "").toUpperCase() !== "SCR");
                  localStorage.setItem(storageKeyRev, JSON.stringify(filtradas));
                } else if (Array.isArray(dataRev.historial)) {
                  dataRev.historial = dataRev.historial.filter(r => String(r.rol || "").toUpperCase() !== "SCR");
                  if (dataRev.roles) delete dataRev.roles["SCR"];
                  localStorage.setItem(storageKeyRev, JSON.stringify(dataRev));
                }
              }
            }
          } catch (e) {}

          this.submitted = true;
          setTimeout(() => {
            window.location.href = "/solicitudes";
          }, 1200);

        } catch (error) {
          console.warn("⚠️ Backend no respondió a la actualización, guardando localmente:", error.message);
          
          try {
            const guardadas = JSON.parse(localStorage.getItem("incarsa_solicitudes_creadas") || "[]");
            const idx = guardadas.findIndex(s => String(s.id) === String(this.editId));
            const solicitudActualizada = {
              id: this.editId,
              estado: this.form.estado || this.solicitudOriginal?.estado || "ENVIADO",
              contratista: this.form.contratista,
              empresaOrigen: this.empresaNombre(this.form.empresas[0]),
              plantas: plantasIds,
              fechaIngreso: this.form.fechaIngreso,
              fechaSalida: this.form.fechaSalida,
              nivelRiesgo: this.form.nivelRiesgo,
              actividad: this.form.actividad,
              diligenciadoPor: this.form.diligenciadoPor,
              personas: this.personas,
              vehiculos: this.vehiculos,
              equipos: this.equipos
            };
            if (idx > -1) {
              guardadas[idx] = solicitudActualizada;
            } else {
              guardadas.unshift(solicitudActualizada);
            }
            localStorage.setItem("incarsa_solicitudes_creadas", JSON.stringify(guardadas));
          } catch (e) {}

          try {
            const storageKeyRev = `incarsa_revisiones_${this.editId}`;
            const nuevoEstado = String(this.form.estado || "").trim().toUpperCase();
            if (["EN REVISIÓN", "EN REVISION", "ENVIADO"].includes(nuevoEstado)) {
              localStorage.removeItem(storageKeyRev);
            } else if (nuevoEstado === "POR APROBAR") {
              const dataRev = JSON.parse(localStorage.getItem(storageKeyRev) || "null");
              if (dataRev) {
                if (Array.isArray(dataRev)) {
                  const filtradas = dataRev.filter(r => String(r.rol || "").toUpperCase() !== "SCR");
                  localStorage.setItem(storageKeyRev, JSON.stringify(filtradas));
                } else if (Array.isArray(dataRev.historial)) {
                  dataRev.historial = dataRev.historial.filter(r => String(r.rol || "").toUpperCase() !== "SCR");
                  if (dataRev.roles) delete dataRev.roles["SCR"];
                  localStorage.setItem(storageKeyRev, JSON.stringify(dataRev));
                }
              }
            }
          } catch (e) {}

          this.submitted = true;
          setTimeout(() => {
            window.location.href = "/solicitudes";
          }, 1200);
        } finally {
          this.submitting = false;
        }
        return;
      }

      // ========================================================================
      // MODO CREACIÓN (POST)
      // ========================================================================
      try {
        console.log("📤 [POST] Enviando solicitud a FastAPI:", payloadApi);
        const response = await fetch(`${API.solicitudes}/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payloadApi)
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || errData.mensaje || `HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log("✅ Solicitud guardada exitosamente en BD:", data);

        const nuevaSolicitud = {
          id: data.id || (data.ids_generados && data.ids_generados.length ? `SOL-${new Date().getFullYear()}-${String(data.ids_generados[0]).padStart(4, "0")}` : (data.id_generado ? `SOL-${new Date().getFullYear()}-${String(data.id_generado).padStart(4, "0")}` : this.nextSolicitudId())),
          estado: "ENVIADO",
          contratista: this.form.contratista,
          empresaOrigen: this.empresaNombre(this.form.empresas[0]),
          plantas: plantasIds,
          fechaIngreso: this.form.fechaIngreso,
          fechaSalida: this.form.fechaSalida,
          nivelRiesgo: this.form.nivelRiesgo,
          actividad: this.form.actividad,
          diligenciadoPor: this.form.diligenciadoPor,
          personas: this.personas,
          vehiculos: this.vehiculos,
          equipos: this.equipos
        };

        // Guardar en localStorage para visibilidad inmediata en el dashboard
        try {
          const guardadas = JSON.parse(localStorage.getItem("incarsa_solicitudes_creadas") || "[]");
          guardadas.unshift(nuevaSolicitud);
          localStorage.setItem("incarsa_solicitudes_creadas", JSON.stringify(guardadas));
        } catch (e) {
          console.warn("No se pudo guardar en localStorage:", e);
        }

        this.submitted = true;
        setTimeout(() => {
          window.location.href = "/solicitudes";
        }, 1200);

      } catch (error) {
        console.warn("⚠️ Backend no respondió o dio error, usando guardado local:", error.message);

        const fallbackSolicitud = {
          id: this.nextSolicitudId(),
          estado: "ENVIADO",
          contratista: this.form.contratista,
          empresaOrigen: this.empresaNombre(this.form.empresas[0]),
          plantas: plantasIds,
          fechaIngreso: this.form.fechaIngreso,
          fechaSalida: this.form.fechaSalida,
          nivelRiesgo: this.form.nivelRiesgo,
          actividad: this.form.actividad,
          diligenciadoPor: this.form.diligenciadoPor,
          personas: this.personas,
          vehiculos: this.vehiculos,
          equipos: this.equipos
        };

        // Guardar en localStorage para persistencia offline
        try {
          const guardadas = JSON.parse(localStorage.getItem("incarsa_solicitudes_creadas") || "[]");
          guardadas.unshift(fallbackSolicitud);
          localStorage.setItem("incarsa_solicitudes_creadas", JSON.stringify(guardadas));
        } catch (e) {
          console.warn("No se pudo guardar en localStorage fallback:", e);
        }

        this.submitted = true;
        setTimeout(() => {
          window.location.href = "/solicitudes";
        }, 1200);

      } finally {
        this.submitting = false;
      }
    }
  };
}
