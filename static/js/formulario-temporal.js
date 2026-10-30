/**
 * Formulario Temporal para Terceros - PSI INCARSA S.A.S.
 * Manejo de formulario Alpine.js con wizard de 4 pasos, carga de archivos,
 * gestión de personas, vehículos, cómputos y envío de solicitud PRE-ENVIADA.
 */

function formatearFechaHora(fechaStr) {
  if (!fechaStr || fechaStr === '—' || fechaStr === '-') return 'Enlace activo';
  try {
    const str = String(fechaStr).trim();
    const partes = str.replace('T', ' ').split(' ');
    const fPartes = partes[0].split('-');
    if (fPartes.length === 3) {
      const anio = fPartes[0];
      const mesIdx = parseInt(fPartes[1], 10) - 1;
      const dia = fPartes[2].padStart(2, '0');
      const meses = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
      const mesNombre = meses[mesIdx] || fPartes[1];

      if (partes[1]) {
        const hPartes = partes[1].split(':');
        let h = parseInt(hPartes[0], 10);
        const m = (hPartes[1] || '00').padStart(2, '0');
        const ampm = h >= 12 ? 'PM' : 'AM';
        h = h % 12;
        h = h ? h : 12;
        const horaFinal = `${String(h).padStart(2, '0')}:${m} ${ampm}`;
        return `${dia} ${mesNombre} ${anio}, ${horaFinal}`;
      }
      return `${dia} ${mesNombre} ${anio}`;
    }
    return fechaStr;
  } catch (e) {
    return fechaStr;
  }
}

function formatearFechaLarga(fechaStr) {
  if (!fechaStr || fechaStr === '—' || fechaStr === '-') return 'Por definir';
  try {
    const str = String(fechaStr).trim();
    const partes = str.split('-');
    if (partes.length === 3) {
      const dia = partes[2].padStart(2, '0');
      const mesIdx = parseInt(partes[1], 10) - 1;
      const anio = partes[0];
      const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
      const mesNombre = meses[mesIdx] || partes[1];
      return `${dia} de ${mesNombre}, ${anio}`;
    }
    return fechaStr;
  } catch (e) {
    return fechaStr;
  }
}

function formularioTemporal(tokenInicial) {
  return {
    token: tokenInicial || '',
    cargando: true,
    tokenValido: false,
    mensajeError: '',
    metadata: {},
    formatearFechaHora(f) { return formatearFechaHora(f); },
    formatearFechaLarga(f) { return formatearFechaLarga(f); },
    catalogos: { empresas: [], contratistas: [], personas: [], vehiculos: [] },
    paso: 1,
    aceptoTerminos: false,
    aceptoTratamientoDatos: false,
    enviando: false,
    solicitudExitosa: false,
    codigoGenerado: '',

    // ========================================================================
    // AVISO OBLIGATORIO DE TIEMPO DE RESPUESTA (48 HORAS)
    // ========================================================================
    mostrarAviso48h: true,
    get debeMostrarAviso48h() {
      return Boolean(this.mostrarAviso48h && this.tokenValido && !this.cargando && !this.solicitudExitosa);
    },
    confirmarAviso48h() {
      this.mostrarAviso48h = false;
    },

    fpIngreso: null,
    fpSalida: null,

    form: {
      empresa_contratista: '',
      tipo_personal: 'Contratista',
      nivel_riesgo: 'MEDIO',
      plantas: [],
      fecha_ingreso: '',
      fecha_salida: '',
      actividad: ''
    },

    personas: [],
    vehiculos: [],
    equipos: [],

    // Tipos y opciones
    tiposContratista: ['Contratista', 'Proveedor', 'Visita'],
    tiposDocPersona: ['CC', 'CE', 'PAS', 'PPT'],
    tiposDocAdjuntoPersona: [
      'ARL',
      'Cédula de Ciudadanía',
      'Certificado de Alturas',
      'Examen Médico Ocupacional',
      'Certificado de Espacios Confinados',
      'EPS / Seguridad Social',
      'Hoja de Vida / Certificación',
      'Inducción corporativa',
      'Planilla seguridad social',
      'Autorización tratamiento de datos',
      'Otro documento'
    ],
    tiposVehiculo: ['Camioneta', 'Camión', 'Automóvil', 'Motocicleta', 'Volqueta', 'Maquinaria', 'Otro'],
    tiposDocAdjuntoVehiculo: [
      'SOAT',
      'Revisión Tecnomecánica',
      'Tarjeta de Propiedad',
      'Póliza Contractual / Extracontractual',
      'Tarjeta de Operación',
      'Certificado de Emisión de Gases',
      'Otro documento'
    ],

    // Búsqueda y Modal Persona
    personaSearchQuery: '',
    showPersonaModal: false,
    isEditingPersona: false,
    guardandoPersona: false,
    editingPersonaIndex: -1,
    nuevaPersona: {
      id: null,
      nombres: '',
      apellidos: '',
      tipoDoc: 'CC',
      numDoc: '',
      cargo: '',
      correo: '',
      observacion: '',
      documentos: [
        { tipo_doc: 'ARL', tipo_doc_otro: '', nombre_archivo: '', vigencia: '', url_documento: '' }
      ]
    },
    personaModalErrors: {},

    // Búsqueda y Modal Vehículo
    vehiculoSearchQuery: '',
    showVehiculoModal: false,
    isEditingVehiculo: false,
    guardandoVehiculo: false,
    editingVehiculoIndex: -1,
    nuevoVehiculo: {
      id: null,
      tipo: 'Camioneta',
      placa: '',
      conductor: '',
      id_persona: null,
      licencia_doc: '',
      documentos: [
        { tipo_doc: 'SOAT', tipo_doc_otro: '', nombre_archivo: '', url_documento: '' }
      ]
    },
    vehiculoModalErrors: {},

    // Modal Visor de Documentos
    modalDocsOpen: false,
    modalDocsTitle: '',
    modalDocsSubtitle: '',
    modalDocsIcon: 'fa-folder-open',
    modalDocsList: [],

    async init() {
      if (!this.token || this.token === 'formulario-temporal') {
        const parts = window.location.pathname.split('/').filter(Boolean);
        const lastPart = parts[parts.length - 1] || '';
        this.token = (lastPart !== 'formulario-temporal') ? lastPart : '';
      }
      if (this.token) {
        await this.validarToken();
      } else {
        this.cargando = false;
        this.tokenValido = false;
        this.mensajeError = 'No se proporcionó un token de acceso válido para el formulario.';
      }
      if (this.tokenValido) {
        this.initFlatpickrs();
      }
    },

    initFlatpickrs() {
      this.$nextTick(() => {
        if (this.$refs.fechaIngresoInput) {
          if (this.fpIngreso) this.fpIngreso.destroy();
          this.fpIngreso = flatpickr(this.$refs.fechaIngresoInput, {
            locale: 'es',
            dateFormat: 'Y-m-d',
            altInput: true,
            altFormat: 'j \\de F, Y',
            altInputClass: 'w-full bg-[#18181c] border border-zinc-700 rounded-xl input-with-icon-left pr-4 py-3 text-sm text-white placeholder-zinc-500 focus:border-[var(--role-primary)] focus:ring-1 focus:ring-[var(--role-primary)] cursor-pointer shadow-sm',
            disableMobile: "true",
            minDate: 'today',
            defaultDate: this.form.fecha_ingreso || null,
            onChange: (selectedDates, dateStr) => {
              this.form.fecha_ingreso = dateStr;
              if (this.fpSalida) {
                this.fpSalida.set('minDate', dateStr);
                if (this.form.fecha_salida && this.form.fecha_salida < dateStr) {
                  this.fpSalida.setDate(dateStr);
                  this.form.fecha_salida = dateStr;
                }
              }
            }
          });
        }

        if (this.$refs.fechaSalidaInput) {
          if (this.fpSalida) this.fpSalida.destroy();
          this.fpSalida = flatpickr(this.$refs.fechaSalidaInput, {
            locale: 'es',
            dateFormat: 'Y-m-d',
            altInput: true,
            altFormat: 'j \\de F, Y',
            altInputClass: 'w-full bg-[#18181c] border border-zinc-700 rounded-xl input-with-icon-left pr-4 py-3 text-sm text-white placeholder-zinc-500 focus:border-[var(--role-primary)] focus:ring-1 focus:ring-[var(--role-primary)] cursor-pointer shadow-sm',
            disableMobile: "true",
            minDate: this.form.fecha_ingreso || 'today',
            defaultDate: this.form.fecha_salida || null,
            onChange: (selectedDates, dateStr) => {
              this.form.fecha_salida = dateStr;
            }
          });
        }
      });
    },

    async validarToken() {
      this.cargando = true;
      try {
        const res = await fetch(`/api/v1/solicitudes/publico/formulario-temporal/${encodeURIComponent(this.token)}`);
        const data = await res.json();
        if (!res.ok || !data.valido) {
          this.tokenValido = false;
          this.mensajeError = data.detail || data.mensaje || 'Enlace inválido o expirado';
          return;
        }
        this.tokenValido = true;
        this.metadata = data;
        this.catalogos = data.catalogos || { empresas: [], contratistas: [], personas: [], vehiculos: [] };
        
        // Asignar empresa contratista garantizando valor numérico
        if (data.id_empresa_contratista && !isNaN(parseInt(data.id_empresa_contratista, 10))) {
          this.form.empresa_contratista = parseInt(data.id_empresa_contratista, 10);
        } else if (data.contratista_nombre) {
          const nom = String(data.contratista_nombre).trim().toLowerCase();
          const nit = data.contratista_nit ? String(data.contratista_nit).trim().toLowerCase() : '';
          const match = (this.catalogos.contratistas || []).find(c => {
            const cNom = String(c.nombre || c.N_empresa || '').trim().toLowerCase();
            const cNit = String(c.nit || c.NIT || '').trim().toLowerCase();
            return (cNom && cNom === nom) || (nit && cNit && cNit === nit);
          });
          if (match) {
            this.form.empresa_contratista = parseInt(match.id, 10);
          }
        }
      } catch (e) {
        this.tokenValido = false;
        this.mensajeError = 'No se pudo conectar con el servidor para validar el enlace.';
      } finally {
        this.cargando = false;
      }
    },

    isPlantaSelected(plantaId) {
      return this.form.plantas.includes(plantaId);
    },

    togglePlanta(plantaId) {
      const idx = this.form.plantas.indexOf(plantaId);
      if (idx > -1) {
        this.form.plantas.splice(idx, 1);
      } else {
        this.form.plantas.push(plantaId);
      }
    },

    conteoPlantasEmpresa(emp) {
      if (!emp || !emp.plantas) return 0;
      return emp.plantas.filter(p => this.form.plantas.includes(p.id)).length;
    },

    toggleTodasPlantas(emp) {
      if (!emp || !emp.plantas || emp.plantas.length === 0) return;
      const todasSeleccionadas = emp.plantas.every(p => this.form.plantas.includes(p.id));
      if (todasSeleccionadas) {
        const ids = emp.plantas.map(p => p.id);
        this.form.plantas = this.form.plantas.filter(id => !ids.includes(id));
      } else {
        emp.plantas.forEach(p => {
          if (!this.form.plantas.includes(p.id)) {
            this.form.plantas.push(p.id);
          }
        });
      }
    },

    getNombresPlantasSeleccionadas() {
      const nombres = [];
      for (const emp of this.catalogos.empresas || []) {
        for (const p of emp.plantas || []) {
          if (this.form.plantas.includes(p.id)) {
            nombres.push(`${p.nombre} (${emp.nombre})`);
          }
        }
      }
      return nombres;
    },

    getPlantasAgrupadasPorEmpresa() {
      const agrupadas = [];
      for (const emp of this.catalogos.empresas || []) {
        const plantasSeleccionadas = (emp.plantas || []).filter(p => this.form.plantas.includes(p.id));
        if (plantasSeleccionadas.length > 0) {
          agrupadas.push({
            id: emp.id,
            nombre: emp.nombre,
            plantas: plantasSeleccionadas
          });
        }
      }
      return agrupadas;
    },

    getContratistaNombre() {
      const id = this.form.empresa_contratista || this.metadata?.id_empresa_contratista;
      if (id) {
        const match = (this.catalogos.contratistas || []).find(c => String(c.id) === String(id));
        if (match) return match.nombre || match.N_empresa;
      }
      if (this.metadata?.contratista_nombre) return this.metadata.contratista_nombre;
      return this.form.empresa_contratista || '—';
    },

    getContratistaNit() {
      const id = this.form.empresa_contratista || this.metadata?.id_empresa_contratista;
      if (id) {
        const match = (this.catalogos.contratistas || []).find(c => String(c.id) === String(id));
        if (match && (match.nit || match.NIT)) return match.nit || match.NIT;
      }
      if (this.metadata?.contratista_nit) return this.metadata.contratista_nit;
      return '';
    },

    formatearFechaLarga(fechaStr) {
      if (!fechaStr) return '—';
      try {
        const [y, m, d] = fechaStr.split('-');
        if (!y || !m || !d) return fechaStr;
        const date = new Date(parseInt(y, 10), parseInt(m, 10) - 1, parseInt(d, 10));
        return date.toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' });
      } catch (e) {
        return fechaStr;
      }
    },

    validarPaso1() {
      if (!this.form.empresa_contratista && this.metadata?.id_empresa_contratista) {
        this.form.empresa_contratista = parseInt(this.metadata.id_empresa_contratista, 10);
      }
      if (!this.form.empresa_contratista) {
        Swal.fire({
          icon: 'warning',
          title: 'Empresa Contratista no asignada',
          text: 'Este pase no tiene una empresa contratista asignada por el solicitante. Comunícate con el solicitante responsable para emitir un nuevo pase.'
        });
        return false;
      }
      if (!this.form.nivel_riesgo) {
        Swal.fire({ icon: 'warning', title: 'Nivel de riesgo requerido', text: 'Por favor selecciona el nivel de riesgo de la actividad.' });
        return false;
      }
      if (!this.form.fecha_ingreso || !this.form.fecha_salida) {
        Swal.fire({ icon: 'warning', title: 'Fechas requeridas', text: 'Por favor define las fechas estimadas de ingreso y salida en el calendario.' });
        return false;
      }
      if (this.form.plantas.length === 0) {
        Swal.fire({ icon: 'warning', title: 'Plantas requeridas', text: 'Por favor selecciona al menos una planta a visitar según la empresa.' });
        return false;
      }
      if (!this.form.actividad.trim()) {
        Swal.fire({ icon: 'warning', title: 'Descripción requerida', text: 'Por favor describe la actividad o labor a realizar.' });
        return false;
      }
      return true;
    },

    // ==========================================
    // LÓGICA DE PERSONAS
    // ==========================================
    personasFiltradas() {
      const q = (this.personaSearchQuery || '').trim().toLowerCase();
      if (!q) return [];
      const lista = this.catalogos.personas || [];
      return lista.filter(p => {
        const nom = `${p.nombre || ''} ${p.apellido || ''} ${p.nombres || ''}`.toLowerCase();
        const doc = String(p.identificacion || p.numDoc || '').toLowerCase();
        return nom.includes(q) || doc.includes(q);
      }).slice(0, 8);
    },

    personaYaAgregada(numDoc) {
      const d = String(numDoc || '').trim();
      return this.personas.some(p => String(p.numDoc || p.identificacion || '').trim() === d);
    },

    agregarPersonaDesdeBusqueda(p) {
      if (this.personaYaAgregada(p.identificacion || p.numDoc)) return;
      const docs = Array.isArray(p.documentos) ? p.documentos.map(d => ({
        id: d.id,
        tipo_doc: d.tipo_doc || 'Documento',
        nombre_archivo: d.nombre_archivo || '',
        vigencia: d.vigencia || null,
        url_acceso: d.url_acceso || (d.nombre_archivo ? `/uploads/documentos/${d.nombre_archivo}` : '')
      })) : [];

      this.personas.push({
        id: p.id || null,
        nombres: p.nombres || `${p.nombre || ''} ${p.apellido || ''}`.trim(),
        nombre: p.nombre || (p.nombres ? p.nombres.split(' ')[0] : ''),
        apellido: p.apellido || (p.nombres ? p.nombres.split(' ').slice(1).join(' ') : ''),
        tipoDoc: p.tipo_doc || p.tipoDoc || 'CC',
        numDoc: String(p.identificacion || p.numDoc || ''),
        cargo: p.cargo || 'Personal',
        correo: p.correo || '',
        observacion: p.observacion || '',
        documentos: docs
      });
      this.personaSearchQuery = '';
    },

    openPersonaModal() {
      this.isEditingPersona = false;
      this.editingPersonaIndex = -1;
      this.personaModalErrors = {};
      this.nuevaPersona = {
        id: null,
        nombres: '',
        apellidos: '',
        tipoDoc: 'CC',
        numDoc: '',
        cargo: '',
        correo: '',
        observacion: '',
        documentos: [
          { tipo_doc: 'ARL', tipo_doc_otro: '', nombre_archivo: '', vigencia: '', url_documento: '' }
        ]
      };
      this.showPersonaModal = true;
    },

    openEditPersonaModal(p, idx = -1) {
      this.isEditingPersona = true;
      this.editingPersonaIndex = idx !== -1 ? idx : this.personas.findIndex(item => String(item.numDoc || item.identificacion) === String(p.numDoc || p.identificacion));
      this.personaModalErrors = {};

      let nombres = (p.nombre || '').trim();
      let apellidos = (p.apellido || '').trim();
      if (!nombres && !apellidos && p.nombres) {
        const parts = p.nombres.trim().split(' ');
        nombres = parts[0] || '';
        apellidos = parts.slice(1).join(' ') || '';
      }

      let docs = [];
      if (Array.isArray(p.documentos) && p.documentos.length > 0) {
        docs = p.documentos.map(d => {
          const rawTipo = d.tipo_doc || 'ARL';
          const isPre = this.tiposDocAdjuntoPersona.includes(rawTipo) && rawTipo !== 'Otro documento';
          return {
            id: d.id || null,
            tipo_doc: isPre ? rawTipo : 'Otro documento',
            tipo_doc_otro: isPre ? '' : rawTipo,
            nombre_archivo: d.nombre_archivo || '',
            vigencia: d.vigencia ? String(d.vigencia).split(' ')[0] : '',
            url_documento: d.url_acceso || (d.nombre_archivo ? `/uploads/documentos/${d.nombre_archivo}` : '')
          };
        });
      }
      if (docs.length === 0) {
        docs = [{ tipo_doc: 'ARL', tipo_doc_otro: '', nombre_archivo: '', vigencia: '', url_documento: '' }];
      }

      this.nuevaPersona = {
        id: p.id || null,
        nombres: nombres,
        apellidos: apellidos,
        tipoDoc: p.tipoDoc || p.tipo_doc || 'CC',
        numDoc: String(p.numDoc || p.identificacion || ''),
        cargo: p.cargo || '',
        correo: p.correo || '',
        observacion: p.observacion || '',
        documentos: docs
      };
      this.showPersonaModal = true;
    },

    closePersonaModal() {
      this.showPersonaModal = false;
      this.personaModalErrors = {};
    },

    addDocumentoPersona() {
      this.nuevaPersona.documentos.push({
        tipo_doc: 'ARL',
        tipo_doc_otro: '',
        nombre_archivo: '',
        vigencia: '',
        url_documento: ''
      });
    },

    removeDocumentoPersona(idx) {
      if (this.nuevaPersona.documentos.length > 1) {
        this.nuevaPersona.documentos.splice(idx, 1);
      } else {
        this.nuevaPersona.documentos[0].nombre_archivo = '';
        this.nuevaPersona.documentos[0].vigencia = '';
        this.nuevaPersona.documentos[0].url_documento = '';
      }
    },

    async handleDocumentoPersonaFile(event, idx) {
      const file = event.target.files[0];
      if (!file) return;
      const tipo = this.nuevaPersona.documentos[idx]?.tipo_doc || 'cedula';
      const uploaded = await this.uploadArchivo(file, tipo);
      if (uploaded) {
        this.nuevaPersona.documentos[idx].nombre_archivo = uploaded.nombre_archivo;
        this.nuevaPersona.documentos[idx].url_documento = uploaded.url_documento;
      }
      event.target.value = '';
    },

    async guardarPersonaModal() {
      this.personaModalErrors = {};
      const numDocLimpio = String(this.nuevaPersona.numDoc || '').replace(/\D/g, '').trim();
      this.nuevaPersona.numDoc = numDocLimpio;

      if (!this.nuevaPersona.nombres.trim()) this.personaModalErrors.nombres = 'Ingresa los nombres.';
      if (!this.nuevaPersona.apellidos.trim()) this.personaModalErrors.apellidos = 'Ingresa los apellidos.';
      if (!numDocLimpio) {
        this.personaModalErrors.numDoc = 'Ingresa el número de documento.';
      } else if (!/^\d+$/.test(numDocLimpio)) {
        this.personaModalErrors.numDoc = 'El documento solo debe contener números (sin puntos ni comas).';
      }
      if (!this.nuevaPersona.cargo.trim()) this.personaModalErrors.cargo = 'Ingresa el cargo.';
      if (!this.nuevaPersona.correo.trim() || !this.nuevaPersona.correo.includes('@')) {
        this.personaModalErrors.correo = 'Ingresa un correo electrónico válido.';
      }

      // Validar que no exista otra persona con el mismo documento en la solicitud activa
      const numDocTrim = numDocLimpio;
      if (numDocTrim) {
        const esDuplicado = (this.personas || []).some((p, idx) => {
          const docP = String(p.numDoc || p.identificacion || '').trim();
          if (docP !== numDocTrim) return false;
          if (this.isEditingPersona && this.editingPersonaIndex !== -1 && idx === this.editingPersonaIndex) {
            return false;
          }
          return true;
        });
        if (esDuplicado) {
          this.personaModalErrors.numDoc = 'Ya existe una persona registrada en esta solicitud con ese número de documento.';
        }
      }

      if (Object.keys(this.personaModalErrors).length > 0) return;

      this.guardandoPersona = true;
      try {
        const payload = {
          id: this.nuevaPersona.id,
          nombre: this.nuevaPersona.nombres.trim(),
          apellido: this.nuevaPersona.apellidos.trim(),
          tipo_doc: this.nuevaPersona.tipoDoc,
          identificacion: numDocLimpio,
          cargo: this.nuevaPersona.cargo.trim(),
          correo: this.nuevaPersona.correo.trim(),
          observacion: this.nuevaPersona.observacion.trim(),
          documentos: this.nuevaPersona.documentos.filter(d => d.nombre_archivo && d.nombre_archivo.trim()).map(d => ({
            tipo_doc: d.tipo_doc === 'Otro documento' && d.tipo_doc_otro ? d.tipo_doc_otro : d.tipo_doc,
            nombre_archivo: d.nombre_archivo,
            vigencia: d.vigencia || null
          }))
        };

        const res = await fetch(`/api/v1/solicitudes/publico/formulario-temporal/${encodeURIComponent(this.token)}/personas`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok || !data.exito) {
          throw new Error(data.detail || data.mensaje || 'Error al guardar persona.');
        }

        const pSaved = data.persona || { ...payload, id: data.id };
        const pFormatted = {
          id: pSaved.id,
          nombres: `${pSaved.nombre || ''} ${pSaved.apellido || ''}`.trim(),
          nombre: pSaved.nombre,
          apellido: pSaved.apellido,
          tipoDoc: pSaved.tipo_doc || 'CC',
          numDoc: pSaved.identificacion,
          cargo: pSaved.cargo,
          correo: pSaved.correo,
          observacion: pSaved.observacion || '',
          documentos: (pSaved.documentos || []).map(d => ({
            id: d.id,
            tipo_doc: d.tipo_doc,
            nombre_archivo: d.nombre_archivo,
            vigencia: d.vigencia || null,
            url_acceso: d.url_acceso || (d.nombre_archivo ? `/uploads/documentos/${d.nombre_archivo}` : '')
          }))
        };

        // Sincronizar catálogo local
        const catIdx = (this.catalogos.personas || []).findIndex(cp => String(cp.identificacion || cp.numDoc) === String(pFormatted.numDoc));
        if (catIdx !== -1) {
          this.catalogos.personas[catIdx] = pFormatted;
        } else {
          if (!this.catalogos.personas) this.catalogos.personas = [];
          this.catalogos.personas.push(pFormatted);
        }

        // Actualizar o agregar a la solicitud activa
        if (this.isEditingPersona && this.editingPersonaIndex !== -1) {
          this.personas[this.editingPersonaIndex] = pFormatted;
        } else {
          const existSolIdx = this.personas.findIndex(p => String(p.numDoc || p.identificacion) === String(pFormatted.numDoc));
          if (existSolIdx !== -1) {
            this.personas[existSolIdx] = pFormatted;
          } else {
            this.personas.push(pFormatted);
          }
        }

        this.showPersonaModal = false;
        Swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'success',
          title: this.isEditingPersona ? 'Persona actualizada' : 'Persona agregada con éxito',
          showConfirmButton: false,
          timer: 2500
        });
      } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error al guardar', text: err.message });
      } finally {
        this.guardandoPersona = false;
      }
    },

    removePersona(idx) {
      this.personas.splice(idx, 1);
    },

    // ==========================================
    // LÓGICA DE VEHÍCULOS
    // ==========================================
    vehiculosFiltrados() {
      const q = (this.vehiculoSearchQuery || '').trim().toLowerCase();
      if (!q) return [];
      const lista = this.catalogos.vehiculos || [];
      return lista.filter(v => {
        const pl = String(v.placa || '').toLowerCase();
        const tp = String(v.tipo || v.tipo_vehiculo || '').toLowerCase();
        const cond = String(v.conductor || v.conductor_nombre || '').toLowerCase();
        return pl.includes(q) || tp.includes(q) || cond.includes(q);
      }).slice(0, 8);
    },

    vehiculoYaAgregado(placa) {
      const pl = String(placa || '').trim().toUpperCase();
      return this.vehiculos.some(v => String(v.placa || '').trim().toUpperCase() === pl);
    },

    agregarVehiculoDesdeBusqueda(v) {
      if (this.vehiculoYaAgregado(v.placa)) return;
      const docs = Array.isArray(v.documentos) ? v.documentos.map(d => ({
        id: d.id,
        tipo_doc: d.tipo_doc || 'SOAT',
        nombre_archivo: d.nombre_archivo || d.nom_documento || '',
        url_acceso: d.url_acceso || (d.nom_documento ? `/uploads/documentos/vehiculos/${d.nom_documento}` : '')
      })) : [];

      this.vehiculos.push({
        id: v.id || null,
        tipo: v.tipo || v.tipo_vehiculo || 'Camioneta',
        placa: (v.placa || '').toUpperCase().trim(),
        conductor: v.conductor || v.conductor_nombre || '',
        id_persona: v.id_persona || v.id_conductor || null,
        licencia_doc: v.licencia_doc || '',
        documentos: docs
      });
      this.vehiculoSearchQuery = '';
    },

    asignarConductorVehiculo(v, event) {
      const id = event.target.value;
      v.id_persona = id ? parseInt(id, 10) : null;
      if (v.id_persona) {
        const match = this.personas.find(p => String(p.id) === String(v.id_persona));
        v.conductor = match ? (match.nombres || `${match.nombre || ''} ${match.apellido || ''}`).trim() : '';
      } else {
        v.conductor = '';
      }
    },

    openVehiculoModal() {
      this.isEditingVehiculo = false;
      this.editingVehiculoIndex = -1;
      this.vehiculoModalErrors = {};
      this.nuevoVehiculo = {
        id: null,
        tipo: 'Camioneta',
        placa: '',
        conductor: '',
        id_persona: null,
        licencia_doc: '',
        documentos: [
          { tipo_doc: 'SOAT', tipo_doc_otro: '', nombre_archivo: '', url_documento: '' }
        ]
      };
      this.showVehiculoModal = true;
    },

    openEditVehiculoModal(v, idx = -1) {
      this.isEditingVehiculo = true;
      this.editingVehiculoIndex = idx !== -1 ? idx : this.vehiculos.findIndex(item => String(item.placa).toUpperCase() === String(v.placa).toUpperCase());
      this.vehiculoModalErrors = {};

      let docs = [];
      if (Array.isArray(v.documentos) && v.documentos.length > 0) {
        docs = v.documentos.map(d => {
          const rawTipo = d.tipo_doc || 'SOAT';
          const isPre = this.tiposDocAdjuntoVehiculo.includes(rawTipo) && rawTipo !== 'Otro documento';
          return {
            id: d.id || null,
            tipo_doc: isPre ? rawTipo : 'Otro documento',
            tipo_doc_otro: isPre ? '' : rawTipo,
            nombre_archivo: d.nombre_archivo || d.nom_documento || '',
            url_documento: d.url_acceso || (d.nom_documento ? `/uploads/documentos/vehiculos/${d.nom_documento}` : (d.nombre_archivo ? `/uploads/documentos/vehiculos/${d.nombre_archivo}` : ''))
          };
        });
      }
      if (docs.length === 0) {
        docs = [{ tipo_doc: 'SOAT', tipo_doc_otro: '', nombre_archivo: '', url_documento: '' }];
      }

      this.nuevoVehiculo = {
        id: v.id || null,
        tipo: v.tipo || v.tipo_vehiculo || 'Camioneta',
        placa: (v.placa || '').toUpperCase().trim(),
        conductor: v.conductor || v.conductor_nombre || '',
        id_persona: v.id_persona || null,
        licencia_doc: v.licencia_doc || '',
        documentos: docs
      };
      this.showVehiculoModal = true;
    },

    closeVehiculoModal() {
      this.showVehiculoModal = false;
      this.vehiculoModalErrors = {};
    },

    addDocumentoVehiculo() {
      this.nuevoVehiculo.documentos.push({
        tipo_doc: 'SOAT',
        tipo_doc_otro: '',
        nombre_archivo: '',
        url_documento: ''
      });
    },

    removeDocumentoVehiculo(idx) {
      if (this.nuevoVehiculo.documentos.length > 1) {
        this.nuevoVehiculo.documentos.splice(idx, 1);
      } else {
        this.nuevoVehiculo.documentos[0].nombre_archivo = '';
        this.nuevoVehiculo.documentos[0].url_documento = '';
      }
    },

    async handleLicenciaVehiculoFile(event) {
      const file = event.target.files[0];
      if (!file) return;
      const uploaded = await this.uploadArchivo(file, 'licencia');
      if (uploaded) {
        this.nuevoVehiculo.licencia_doc = uploaded.nombre_archivo;
      }
      event.target.value = '';
    },

    async handleDocumentoVehiculoFile(event, idx) {
      const file = event.target.files[0];
      if (!file) return;
      const tipo = this.nuevoVehiculo.documentos[idx]?.tipo_doc || 'vehicular';
      const uploaded = await this.uploadArchivo(file, tipo);
      if (uploaded) {
        this.nuevoVehiculo.documentos[idx].nombre_archivo = uploaded.nombre_archivo;
        this.nuevoVehiculo.documentos[idx].url_documento = uploaded.url_documento;
      }
      event.target.value = '';
    },

    async guardarVehiculoModal() {
      this.vehiculoModalErrors = {};
      if (!this.nuevoVehiculo.placa.trim()) this.vehiculoModalErrors.placa = 'Ingresa la placa del vehículo.';
      if (Object.keys(this.vehiculoModalErrors).length > 0) return;

      this.guardandoVehiculo = true;
      try {
        const payload = {
          id: this.nuevoVehiculo.id,
          tipo: this.nuevoVehiculo.tipo,
          placa: this.nuevoVehiculo.placa.trim().toUpperCase(),
          conductor: this.nuevoVehiculo.conductor,
          id_persona: this.nuevoVehiculo.id_persona,
          licencia_doc: this.nuevoVehiculo.licencia_doc,
          documentos: this.nuevoVehiculo.documentos.filter(d => d.nombre_archivo && d.nombre_archivo.trim()).map(d => ({
            tipo_doc: d.tipo_doc === 'Otro documento' && d.tipo_doc_otro ? d.tipo_doc_otro : d.tipo_doc,
            nombre_archivo: d.nombre_archivo
          }))
        };

        const res = await fetch(`/api/v1/solicitudes/publico/formulario-temporal/${encodeURIComponent(this.token)}/vehiculos`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok || !data.exito) {
          throw new Error(data.detail || data.mensaje || 'Error al guardar vehículo.');
        }

        const vSaved = data.vehiculo || { ...payload, id: data.id };
        const vFormatted = {
          id: vSaved.id,
          tipo: vSaved.tipo || 'Camioneta',
          placa: (vSaved.placa || '').toUpperCase().trim(),
          conductor: vSaved.conductor || '',
          id_persona: vSaved.id_persona || null,
          licencia_doc: vSaved.licencia_doc || '',
          documentos: (vSaved.documentos || []).map(d => ({
            id: d.id,
            tipo_doc: d.tipo_doc,
            nombre_archivo: d.nombre_archivo || d.nom_documento || '',
            url_acceso: d.url_acceso || (d.nom_documento ? `/uploads/documentos/vehiculos/${d.nom_documento}` : '')
          }))
        };

        // Sincronizar catálogo local
        const catIdx = (this.catalogos.vehiculos || []).findIndex(cv => String(cv.placa).toUpperCase() === String(vFormatted.placa).toUpperCase());
        if (catIdx !== -1) {
          this.catalogos.vehiculos[catIdx] = vFormatted;
        } else {
          if (!this.catalogos.vehiculos) this.catalogos.vehiculos = [];
          this.catalogos.vehiculos.push(vFormatted);
        }

        // Actualizar o agregar a la solicitud activa
        if (this.isEditingVehiculo && this.editingVehiculoIndex !== -1) {
          this.vehiculos[this.editingVehiculoIndex] = vFormatted;
        } else {
          const existIdx = this.vehiculos.findIndex(v => String(v.placa).toUpperCase() === String(vFormatted.placa).toUpperCase());
          if (existIdx !== -1) {
            this.vehiculos[existIdx] = vFormatted;
          } else {
            this.vehiculos.push(vFormatted);
          }
        }

        this.showVehiculoModal = false;
        Swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'success',
          title: this.isEditingVehiculo ? 'Vehículo actualizado' : 'Vehículo agregado con éxito',
          showConfirmButton: false,
          timer: 2500
        });
      } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error al guardar', text: err.message });
      } finally {
        this.guardandoVehiculo = false;
      }
    },

    removeVehiculo(idx) {
      this.vehiculos.splice(idx, 1);
    },

    // ==========================================
    // LÓGICA DE EQUIPOS DE CÓMPUTO
    // ==========================================
    addEquipo() {
      this.equipos.push({ marca: '', modelo: '', serie: '' });
    },

    removeEquipo(idx) {
      this.equipos.splice(idx, 1);
    },

    // ==========================================
    // MODAL VISOR DE DOCUMENTOS
    // ==========================================
    abrirModalDocsPersona(p) {
      this.modalDocsTitle = p.nombres || `${p.nombre || ''} ${p.apellido || ''}`.trim() || 'Documentos de la persona';
      this.modalDocsSubtitle = `${p.tipoDoc || 'CC'} ${p.numDoc || ''} · ${p.cargo || 'Personal'}`.trim();
      this.modalDocsIcon = 'fa-user';
      this.modalDocsList = (p.documentos || []).map(d => ({
        tipo: d.tipo_doc || d.tipo || 'Documento',
        nombre: d.nombre_archivo || d.nom_documento || 'Archivo adjunto',
        vigencia: d.vigencia ? String(d.vigencia).split(' ')[0] : null,
        url: d.url_acceso || (d.nombre_archivo ? `/uploads/documentos/${d.nombre_archivo}` : null)
      }));
      this.modalDocsOpen = true;
    },

    abrirModalDocsVehiculo(v) {
      this.modalDocsTitle = `Vehículo ${v.placa || ''} (${v.tipo || v.tipo_vehiculo || 'Vehículo'})`;
      this.modalDocsSubtitle = v.conductor || v.conductor_nombre ? `Conductor: ${v.conductor || v.conductor_nombre}` : 'Documentación vehicular';
      this.modalDocsIcon = 'fa-truck';
      const docs = [];
      if (v.licencia_doc) {
        docs.push({
          tipo: 'Licencia de Conducción',
          nombre: v.licencia_doc,
          url: `/uploads/documentos/vehiculos/${v.licencia_doc}`,
          vigencia: null
        });
      }
      if (Array.isArray(v.documentos)) {
        v.documentos.forEach(d => {
          const nom = d.nombre_archivo || d.nom_documento;
          if (nom) {
            docs.push({
              tipo: d.tipo_doc || 'Documento Vehicular',
              nombre: nom,
              url: d.url_acceso || `/uploads/documentos/vehiculos/${nom}`,
              vigencia: d.vigencia || null
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

    // Helper general de subida de archivos
    async uploadArchivo(file, tipoDocumento = 'general') {
      if (!file) return null;
      const extension = (file.name.split('.').pop() || '').toLowerCase().trim();
      const permitidos = ['pdf', 'png', 'jpg', 'jpeg'];
      if (!permitidos.includes(extension)) {
        Swal.fire({ icon: 'error', title: 'Formato no permitido', text: `La extensión .${extension} no está permitida. Solo se admiten archivos PDF, PNG o JPG.` });
        return null;
      }
      if (file.size > 10 * 1024 * 1024) {
        Swal.fire({ icon: 'warning', title: 'Archivo muy pesado', text: 'El archivo supera el límite de 10 MB. Por favor comprímelo.' });
        return null;
      }
      const formData = new FormData();
      formData.append('file', file);
      formData.append('tipo_documento', tipoDocumento);
      try {
        const res = await fetch(`/api/v1/solicitudes/publico/formulario-temporal/${encodeURIComponent(this.token)}/subir-documento`, {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (!res.ok || !data.exito) {
          throw new Error(data.detail || data.mensaje || 'Error al subir archivo');
        }
        Swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'success',
          title: 'Documento subido correctamente',
          showConfirmButton: false,
          timer: 2000
        });
        return {
          nombre_archivo: data.nombre_archivo,
          url_documento: data.url_documento,
          nombre_original: data.nombre_original || file.name
        };
      } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error de carga', text: err.message });
        return null;
      }
    },

    // ==========================================
    // ENVÍO DE LA SOLICITUD
    // ==========================================
    async enviarFormulario() {
      if (!this.validarPaso1()) {
        this.paso = 1;
        return;
      }
      if (this.personas.length === 0) {
        Swal.fire({ icon: 'warning', title: 'Personas requeridas', text: 'Debes incluir al menos una persona ingresante en el Paso 2.' });
        this.paso = 2;
        return;
      }
      if (!this.aceptoTerminos) {
        Swal.fire({ icon: 'warning', title: 'Declaración requerida', text: 'Debes confirmar la declaración de veracidad antes de enviar.' });
        return;
      }
      if (!this.aceptoTratamientoDatos) {
        Swal.fire({ icon: 'warning', title: 'Autorización requerida', text: 'Debes autorizar el tratamiento de datos personales conforme a la Ley 1581 de 2012 para continuar.' });
        return;
      }

      this.enviando = true;
      try {
        // Estructura completa compatible con SolicitudInput
        const personasIds = [];
        for (const p of this.personas) {
          if (p.id && !isNaN(parseInt(p.id)) && parseInt(p.id) > 0) {
            personasIds.push(parseInt(p.id));
          }
        }

        const vehiculosIds = [];
        for (const v of this.vehiculos) {
          if (v.id && !isNaN(parseInt(v.id)) && parseInt(v.id) > 0) {
            vehiculosIds.push(parseInt(v.id));
          }
        }

        const equiposPayload = (this.equipos || [])
          .filter(e => (e.marca && e.marca.trim()) || (e.modelo && e.modelo.trim()) || (e.serie && e.serie.trim()))
          .map(e => ({
            marca: (e.marca || "").trim() || "Genérica",
            modelo: (e.modelo || "").trim() || "General",
            serie: (e.serie || "").trim() || "S/N"
          }));

        const idContratista = parseInt(this.form.empresa_contratista || this.metadata?.id_empresa_contratista || 0, 10);
        const payload = {
          empresa_origen: 1,
          empresa_contratista: idContratista,
          tipo_personal: this.form.tipo_personal || "Contratista",
          nivel_de_riesgo: this.form.nivel_riesgo,
          nivel_riesgo: this.form.nivel_riesgo,
          fecha_inicio: this.form.fecha_ingreso,
          fecha_fin: this.form.fecha_salida,
          fecha_ingreso: this.form.fecha_ingreso,
          fecha_salida: this.form.fecha_salida,
          actividad: this.form.actividad.trim(),
          sub_plantas: this.form.plantas.map(p => parseInt(p, 10)),
          plantas_ids: this.form.plantas.map(p => parseInt(p, 10)),
          personas_ids: personasIds,
          personas: this.personas.map(p => ({
            id: p.id || undefined,
            id_persona: p.id || undefined,
            nombre: p.nombre || (p.nombres ? p.nombres.split(' ')[0] : 'Personal'),
            apellido: p.apellido || (p.nombres ? p.nombres.split(' ').slice(1).join(' ') : ''),
            tipo_identificacion: p.tipoDoc || p.tipo_doc || 'CC',
            tipo_doc: p.tipoDoc || p.tipo_doc || 'CC',
            identificacion: p.numDoc || p.identificacion || '',
            cargo: p.cargo || 'Personal',
            correo: p.correo || '',
            observacion: p.observacion || '',
            documentos: (p.documentos || []).map(d => ({
              tipo_doc: d.tipo_doc,
              nombre_archivo: d.nombre_archivo,
              vigencia: d.vigencia || null
            }))
          })),
          vehiculos_ids: vehiculosIds,
          vehiculos: this.vehiculos.map(v => ({
            id: v.id || undefined,
            id_vehiculo: v.id || undefined,
            placa: v.placa,
            tipo: v.tipo || v.tipo_vehiculo || 'Camioneta',
            tipo_vehiculo: v.tipo || v.tipo_vehiculo || 'Camioneta',
            conductor: v.conductor || '',
            conductor_nombre: v.conductor || '',
            id_persona: v.id_persona || null,
            licencia_doc: v.licencia_doc || '',
            documentos: (v.documentos || []).map(d => ({
              tipo_doc: d.tipo_doc,
              nom_documento: d.nom_documento || d.nombre_archivo || '',
              nombre_archivo: d.nombre_archivo || d.nom_documento || ''
            }))
          })),
          eq_computo: equiposPayload,
          equipos: equiposPayload,
          computos: equiposPayload
        };

        const res = await fetch(`/api/v1/solicitudes/publico/formulario-temporal/${encodeURIComponent(this.token)}/enviar`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok || !data.exito) {
          throw new Error(data.detail || data.mensaje || 'Error al radicar solicitud');
        }

        this.codigoGenerado = data.codigo || (data.codigos_generados ? data.codigos_generados[0] : 'RAD-0000');
        this.solicitudExitosa = true;
      } catch (e) {
        Swal.fire({ icon: 'error', title: 'Error al enviar', text: e.message });
      } finally {
        this.enviando = false;
      }
    }
  };
}
