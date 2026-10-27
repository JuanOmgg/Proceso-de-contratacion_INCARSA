/**
 * ============================================================================
 * evaluacion-induccion.js — Controlador de Evaluación de Inducción GESCO
 * ============================================================================
 * Gestiona el flujo público de evaluación de candidatos:
 * 1. Identificación por cédula.
 * 2. Comprobación instantánea de vigencia activa previa (evita repetir si está vigente).
 * 3. Muestreo aleatorio de preguntas del banco (ej. 10 de 40 preguntas).
 * 4. Calificación automática en backend y registro de vigencia global (+1 año).
 */

function evaluacionInduccionApp() {
  return {
    formularioId: window.__FORMULARIO_ID__ || 1,
    estado: "IDENTIFICACION", // 'IDENTIFICACION' | 'VIGENTE' | 'EVALUACION' | 'RESULTADO'
    cargando: false,
    verificando: false,
    enviando: false,
    esSimulacion: false,
    perspectiva: 'candidato', // 'candidato' (Persona) | 'auditor' (Administrador con claves)
    userRole: '',
    isSuperAdmin: false,

    cedula: '',
    formulario: null,
    personaInfo: null,
    vigenciaData: null,

    // Datos del trabajador (especialmente para tipo 'Interno' o trabajadores sin registro previo)
    trabajador: {
      tipo_doc: 'CC',
      numero_documento: '',
      nombres: '',
      apellidos: '',
      correo: '',
      cargo: '',
      empresa: 'INCARSA'
    },
    mostrarCamposCompletos: false,

    // Captura de foto en vivo / evidencia biométrica
    streamCamara: null,
    camaraActiva: false,
    camaraIniciando: false,
    camaraError: null,
    fotoCapturadaDataUrl: null,

    formularioExpirado: false,
    formularioExpiradoMensaje: '',

    get esTipoInterno() {
      if (!this.formulario) return false;
      if (this.formulario.es_interno) return true;
      if (!this.formulario.tipo_personal) return false;
      const tp = String(this.formulario.tipo_personal).toLowerCase();
      return tp.includes('interno') || tp.includes('dialogo') || tp.includes('diálogo');
    },

    get fechaLimiteFormateada() {
      if (!this.formulario || !this.formulario.fecha_limite) return null;
      try {
        const d = new Date(this.formulario.fecha_limite);
        if (isNaN(d.getTime())) return String(this.formulario.fecha_limite);
        return d.toLocaleString('es-CO', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
      } catch (e) {
        return String(this.formulario.fecha_limite);
      }
    },

    preguntas: [],
    respuestas: {}, // { [id_pregunta]: id_opcion } o { [id_pregunta]: [id_opciones] }

    resultadoEvaluacion: null,

    detectarRol() {
      try {
        const raw = sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session');
        if (raw) {
          const ses = JSON.parse(raw);
          const rol = String((ses && (ses.rol || (ses.usuario && ses.usuario.rol))) || '').trim().toUpperCase();
          this.userRole = rol || 'ADMINISTRADOR';
          this.isSuperAdmin = (rol === 'SUPERADMIN' || rol === 'SUPER ADMIN');
          if (this.isSuperAdmin) {
            document.documentElement.setAttribute('data-role', 'SUPERADMIN');
            document.documentElement.classList.add('role-superadmin');
          } else {
            document.documentElement.removeAttribute('data-role');
            document.documentElement.classList.remove('role-superadmin');
          }
        } else {
          this.userRole = '';
          this.isSuperAdmin = false;
        }
      } catch (e) {
        this.userRole = '';
        this.isSuperAdmin = false;
      }
    },

    getCategoryMeta(tipo) {
      const t = String(tipo || 'GENERAL').trim().toUpperCase();
      switch (t) {
        case 'SST':
          return { label: 'SST', icon: 'fa-solid fa-hard-hat', class: 'cat-badge-sst' };
        case 'AMBIENTAL':
          return { label: 'Ambiental', icon: 'fa-solid fa-leaf', class: 'cat-badge-ambiental' };
        case 'SEGURIDAD_VIAL':
          return { label: 'Seg. Vial', icon: 'fa-solid fa-truck-moving', class: 'cat-badge-seguridad_vial' };
        case 'CALIDAD':
          return { label: 'Calidad', icon: 'fa-solid fa-award', class: 'cat-badge-calidad' };
        case 'BIOMECANICA':
          return { label: 'Biomecánica', icon: 'fa-solid fa-person-walking', class: 'cat-badge-biomecanica' };
        default:
          return { label: 'General', icon: 'fa-solid fa-layer-group', class: 'cat-badge-general' };
      }
    },

    getTipoRespuestaMeta(tipo) {
      const t = String(tipo || 'UNICA').trim().toUpperCase();
      switch (t) {
        case 'MULTIPLE':
          return { label: 'Selección Múltiple', icon: 'fa-solid fa-square-check' };
        case 'TEXTO':
        case 'ABIERTA':
          return { label: 'Pregunta Abierta', icon: 'fa-solid fa-pen-to-square' };
        case 'VERDADERO_FALSO':
          return { label: 'Verdadero / Falso', icon: 'fa-solid fa-circle-question' };
        default:
          return { label: 'Selección Única', icon: 'fa-solid fa-circle-dot' };
      }
    },

    extractYouTubeId(input) {
      if (!input) return null;
      let str = String(input).trim();
      if (!str) return null;
      // Extraer si viene en formato iframe
      const iframeMatch = str.match(/src=["']([^"']+)["']/i);
      if (iframeMatch && iframeMatch[1]) {
        str = iframeMatch[1].trim();
      }
      // Si pegaron directamente el ID de 11 caracteres
      if (/^[a-zA-Z0-9_-]{11}$/.test(str)) {
        return str;
      }
      const regExp = /(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?|shorts|live)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})/i;
      const match = str.match(regExp);
      return match && match[1] ? match[1] : null;
    },

    getYouTubeEmbedUrl(url) {
      const id = this.extractYouTubeId(url);
      return id ? `https://www.youtube.com/embed/${id}?playsinline=1&rel=0` : null;
    },

    get confirmButtonColor() {
      return this.isSuperAdmin ? '#d946ef' : '#F0323E';
    },

    get totalRespondidas() {
      let count = 0;
      for (const p of this.preguntas) {
        const val = this.respuestas[p.id];
        if (p.tipo_respuesta === "TEXTO" || p.tipo_respuesta === "ABIERTA") {
          if (typeof val === "string" && val.trim().length > 0) {
            count++;
          }
        } else if (Array.isArray(val)) {
          if (val.length > 0) count++;
        } else if (val !== undefined && val !== null && val !== "") {
          count++;
        }
      }
      return count;
    },

    /**
     * Algoritmo Fisher-Yates para barajar aleatoriamente un arreglo sin sesgos
     */
    barajarArray(array) {
      if (!Array.isArray(array)) return [];
      const arr = [...array];
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
      }
      return arr;
    },

    /**
     * Reformula el orden de las preguntas y de sus opciones de respuesta
     */
    reformularPreguntasYRespuestas() {
      if (!this.preguntas || !this.preguntas.length) return;
      // 1. Reordenar aleatoriamente la secuencia de preguntas
      const preguntasBarajadas = this.barajarArray(this.preguntas);
      // 2. Reordenar aleatoriamente las opciones de cada pregunta individual
      this.preguntas = preguntasBarajadas.map(p => ({
        ...p,
        opciones: Array.isArray(p.opciones) ? this.barajarArray(p.opciones) : []
      }));
    },

    reformularFrom() {
      this.reformularPreguntasYRespuestas();
    },


    /**
     * Muestra un toast elegante con tema oscuro glassmorphic
     */
    mostrarToast(tipo, titulo, texto = '', duracion = 2400) {
      const Toast = Swal.mixin({
        toast: true,
        position: "top-end",
        showConfirmButton: false,
        timer: duracion,
        timerProgressBar: true
      });
      Toast.fire({
        icon: tipo || 'info',
        title: titulo,
        text: texto
      });
    },

    /**
     * Alterna la perspectiva de simulación (Persona vs Auditor)
     */
    cambiarPerspectiva(nueva) {
      this.perspectiva = nueva;
      if (nueva === 'candidato') {
        this.mostrarToast('info', 'Perspectiva: Persona (Candidato)', 'Vista limpia: solo resultado, puntaje y reintento. Claves ocultas.');
      } else {
        this.mostrarToast('info', 'Perspectiva: Auditor GESCO', 'Supervisión técnica: claves correctas y desglose analítico habilitados.');
      }
    },

    async init() {
      // 0. Detectar rol del usuario de sesión para tematización de interfaz
      this.detectarRol();

      // 1. Cargar metadatos generales del formulario
      await this.cargarMetadatosFormulario();

      // 2. Comprobar si se abrió en modo de simulación (?simulacion=1)
      const urlParams = new URLSearchParams(window.location.search);
      this.esSimulacion = urlParams.get("simulacion") === "1" || urlParams.get("test") === "1";

      // Perspectiva: por defecto 'candidato' (perspectiva de las personas).
      // Solo si en la URL viene ?vista=auditor o ?modo=admin inicia en auditor.
      if (urlParams.get("vista") === "auditor" || urlParams.get("modo") === "admin" || urlParams.get("claves") === "1") {
        this.perspectiva = 'auditor';
      } else {
        this.perspectiva = 'candidato';
      }

      if (this.esSimulacion) {
        this.cedula = "SIMULADOR-TEST";
        await this.iniciarSimulacion();
        return;
      }

      // 3. Si se pasó cédula en la URL (?cedula=12345), iniciar automáticamente
      const cedParam = urlParams.get("cedula") || urlParams.get("doc");
      if (cedParam) {
        this.cedula = cedParam.trim();
        await this.verificarOIniciar();
      }
    },

    async iniciarSimulacion() {
      this.cargando = true;
      try {
        const res = await fetch(`/api/v1/formularios-gesco/${this.formularioId}/evaluacion?simulacion=true`);
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Error HTTP ${res.status}`);
        }
        const data = await res.json();
        this.formulario = data.formulario || this.formulario;
        this.personaInfo = data.persona;
        this.preguntas = data.preguntas || [];
        // Reformular aleatoriamente el orden de preguntas y de las opciones de cada pregunta
        this.reformularFrom();
        this.respuestas = {};
        this.resultadoEvaluacion = null;
        this.estado = "EVALUACION";
        window.scrollTo({ top: 0, behavior: "smooth" });
      } catch (err) {
        console.error("Error al iniciar simulación:", err);
        Swal.fire({
          icon: "error",
          title: "Error al iniciar simulador",
          text: err.message || "No se pudieron cargar las preguntas del formulario.",
          confirmButtonColor: this.confirmButtonColor
        });
      } finally {
        this.cargando = false;
      }
    },

    async probarNuevoMuestreo() {
      await this.iniciarSimulacion();
      this.mostrarToast('info', 'Nuevo muestreo generado', `${this.preguntas.length} preguntas extraídas con orden reformulado.`);
    },

    async cargarMetadatosFormulario() {
      try {
        const token = (typeof getAuthToken === "function" ? getAuthToken() : null) || sessionStorage.getItem('access_token') || localStorage.getItem('access_token');
        const headers = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`/api/v1/formularios-gesco/${this.formularioId}`, { headers });
        if (res.ok) {
          const data = await res.json();
          this.formulario = data.datos || data;
          if (this.formulario && this.formulario.nombre) {
            document.title = `${this.formulario.nombre} · INCARSA`;
          }
          if (this.esTipoInterno) {
            this.mostrarCamposCompletos = true;
          }
          if (this.formulario && this.formulario.fecha_limite && !this.esSimulacion) {
            const limite = new Date(this.formulario.fecha_limite);
            if (!isNaN(limite.getTime()) && new Date() > limite) {
              this.formularioExpirado = true;
              this.formularioExpiradoMensaje = `El plazo para responder este formulario finalizó el ${limite.toLocaleString('es-CO')}. No se admiten nuevas respuestas.`;
              this.estado = "EXPIRADO";
            }
          }
        }
      } catch (e) {
        console.warn("Aviso al cargar metadatos:", e);
      }
    },

    async consultarDatosPorCedula() {
      const docClean = (this.trabajador.numero_documento || this.cedula || '').trim();
      if (!docClean || docClean.length < 4) return;
      this.cedula = docClean;
      this.trabajador.numero_documento = docClean;

      try {
        const res = await fetch(`/api/v1/formularios-gesco/${this.formularioId}/evaluacion?cedula=${encodeURIComponent(docClean)}`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.persona) {
            const p = data.persona;
            this.personaInfo = p;
            if (!this.trabajador.nombres && p.nombres) this.trabajador.nombres = p.nombres;
            if (!this.trabajador.apellidos && p.apellidos) this.trabajador.apellidos = p.apellidos;
            if (!this.trabajador.correo && p.correo) this.trabajador.correo = p.correo;
            if (!this.trabajador.cargo && p.cargo) this.trabajador.cargo = p.cargo;
            if (p.tipo_doc) this.trabajador.tipo_doc = p.tipo_doc;
          }
        }
      } catch (e) {
        // Silencioso
      }
    },

    async verificarOIniciar() {
      const docClean = (this.trabajador.numero_documento || this.cedula || '').trim();
      this.cedula = docClean;
      this.trabajador.numero_documento = docClean;

      if (!docClean) {
        Swal.fire({
          icon: "warning",
          title: "Documento requerido",
          text: "Por favor ingresa tu número de documento para continuar.",
          confirmButtonColor: this.confirmButtonColor
        });
        return;
      }

      // Si es tipo interno o tiene abiertos los campos completos, validar nombres
      if (this.esTipoInterno || this.mostrarCamposCompletos) {
        if (!this.trabajador.nombres || !this.trabajador.nombres.trim()) {
          Swal.fire({
            icon: "warning",
            title: "Nombres requeridos",
            text: "Por favor ingresa tus nombres para registrar tu participación.",
            confirmButtonColor: this.confirmButtonColor
          });
          return;
        }
      }

      this.verificando = true;
      try {
        const url = `/api/v1/formularios-gesco/${this.formularioId}/evaluacion?cedula=${encodeURIComponent(docClean)}`;
        const res = await fetch(url);
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Error del servidor HTTP ${res.status}`);
        }

        const data = await res.json();
        this.formulario = data.formulario || this.formulario;

        // CASO 0: FORMULARIO CON FECHA LÍMITE VENCIDA
        if (data.formulario_expirado) {
          this.formularioExpirado = true;
          this.formularioExpiradoMensaje = data.mensaje || "El plazo para diligenciar este formulario ha finalizado.";
          this.estado = "EXPIRADO";
          return;
        }

        if (data.persona) {
          this.personaInfo = data.persona;
          if (!this.trabajador.nombres && data.persona.nombres) this.trabajador.nombres = data.persona.nombres;
          if (!this.trabajador.apellidos && data.persona.apellidos) this.trabajador.apellidos = data.persona.apellidos;
          if (!this.trabajador.correo && data.persona.correo) this.trabajador.correo = data.persona.correo;
          if (!this.trabajador.cargo && data.persona.cargo) this.trabajador.cargo = data.persona.cargo;
          if (data.persona.tipo_doc) this.trabajador.tipo_doc = data.persona.tipo_doc;
        }

        // CASO 1: YA TIENE INDUCCIÓN VIGENTE ACTIVA
        if (data.induccion_activa) {
          this.vigenciaData = {
            fecha_vigencia: data.fecha_vigencia,
            dias_restantes: data.dias_restantes
          };
          this.estado = "VIGENTE";
          return;
        }

        // CASO 2: REQUIERE PRESENTAR EVALUACIÓN (PREGUNTAS ALEATORIAS)
        const listaPreguntas = data.preguntas || [];
        if (listaPreguntas.length === 0) {
          Swal.fire({
            icon: "info",
            title: "Cuestionario en preparación",
            text: "Este formulario aún no tiene preguntas activas configuradas. Contacta al equipo de GESCO.",
            confirmButtonColor: this.confirmButtonColor
          });
          return;
        }

        this.preguntas = listaPreguntas;
        this.reformularFrom();
        this.respuestas = {};

        // Paso obligatorio o sugerido de foto en vivo de validación antes de comenzar
        this.estado = "FOTO";
        this.iniciarCamara();
        window.scrollTo({ top: 0, behavior: "smooth" });
      } catch (err) {
        console.error("Error al verificar documento:", err);
        Swal.fire({
          icon: "error",
          title: "Error al consultar",
          text: err.message || "Ocurrió un error al consultar el sistema.",
          confirmButtonColor: this.confirmButtonColor
        });
      } finally {
        this.verificando = false;
      }
    },

    /**
     * Inicia el flujo de cámara web/móvil para captura de foto de validación
     */
    async iniciarCamara() {
      this.camaraError = null;
      this.camaraActiva = false;
      this.camaraIniciando = true;
      this.$nextTick(async () => {
        try {
          if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.camaraError = "Tu navegador o dispositivo no soporta acceso directo a la cámara.";
            return;
          }
          this.streamCamara = await navigator.mediaDevices.getUserMedia({
            video: {
              facingMode: "user",
              width: { ideal: 640 },
              height: { ideal: 480 }
            },
            audio: false
          });
          const videoEl = this.$refs.videoCamara;
          if (videoEl) {
            videoEl.srcObject = this.streamCamara;
            await videoEl.play().catch(() => {});
            this.camaraActiva = true;
          }
        } catch (err) {
          console.warn("Aviso cámara:", err);
          if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
            this.camaraError = "Permiso de cámara denegado en el navegador. Puedes habilitarlo o continuar.";
          } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
            this.camaraError = "No se detectó ninguna cámara conectada.";
          } else {
            this.camaraError = "No se pudo activar la cámara web.";
          }
        } finally {
          this.camaraIniciando = false;
        }
      });
    },

    /**
     * Captura el fotograma actual del elemento <video> en un canvas y genera el Base64 JPEG
     */
    capturarFoto() {
      const video = this.$refs.videoCamara;
      if (!video) return;
      const w = video.videoWidth || 640;
      const h = video.videoHeight || 480;
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      // Efecto espejo si es cámara frontal
      ctx.translate(w, 0);
      ctx.scale(-1, 1);
      ctx.drawImage(video, 0, 0, w, h);
      this.fotoCapturadaDataUrl = canvas.toDataURL("image/jpeg", 0.78);
      this.apagarCamara();
    },

    repetirFoto() {
      this.fotoCapturadaDataUrl = null;
      this.iniciarCamara();
    },

    apagarCamara() {
      if (this.streamCamara) {
        this.streamCamara.getTracks().forEach(t => t.stop());
        this.streamCamara = null;
      }
      this.camaraActiva = false;
      this.camaraIniciando = false;
    },

    confirmarFotoYComenzar() {
      this.apagarCamara();
      this.estado = "EVALUACION";
      window.scrollTo({ top: 0, behavior: "smooth" });
    },

    omitirFotoYComenzar() {
      this.apagarCamara();
      this.fotoCapturadaDataUrl = null;
      this.estado = "EVALUACION";
      window.scrollTo({ top: 0, behavior: "smooth" });
    },

    toggleRespuesta(idPregunta, idOpcion, tipoRespuesta) {
      if (tipoRespuesta === "MULTIPLE") {
        const prev = Array.isArray(this.respuestas[idPregunta]) ? [...this.respuestas[idPregunta]] : [];
        const idx = prev.indexOf(idOpcion);
        if (idx >= 0) {
          prev.splice(idx, 1);
        } else {
          prev.push(idOpcion);
        }
        this.respuestas[idPregunta] = prev;
      } else {
        // UNICA o VERDADERO_FALSO
        this.respuestas[idPregunta] = idOpcion;
      }
    },

    isOpcionSeleccionada(idPregunta, idOpcion) {
      const val = this.respuestas[idPregunta];
      if (Array.isArray(val)) {
        return val.includes(idOpcion);
      }
      return val === idOpcion;
    },

    async enviarRespuestas() {
      if (this.totalRespondidas < this.preguntas.length) {
        Swal.fire({
          icon: "warning",
          title: "Preguntas pendientes",
          text: `Aún te faltan ${this.preguntas.length - this.totalRespondidas} preguntas por responder.`,
          confirmButtonColor: this.confirmButtonColor
        });
        return;
      }

      this.enviando = true;

      // Estructurar array de respuestas para calificar en backend
      const payloadRespuestas = [];
      for (const [pid, val] of Object.entries(this.respuestas)) {
        const qObj = this.preguntas.find(p => p.id === Number(pid));
        const esTexto = qObj && (qObj.tipo_respuesta === "TEXTO" || qObj.tipo_respuesta === "ABIERTA");

        if (Array.isArray(val)) {
          for (const opcId of val) {
            payloadRespuestas.push({ id_pregunta: Number(pid), id_opcion: Number(opcId) });
          }
        } else if (val !== undefined && val !== null && val !== "") {
          if (esTexto) {
            payloadRespuestas.push({ id_pregunta: Number(pid), texto_respuesta: String(val).trim() });
          } else if (!isNaN(Number(val))) {
            payloadRespuestas.push({ id_pregunta: Number(pid), id_opcion: Number(val) });
          } else {
            payloadRespuestas.push({ id_pregunta: Number(pid), texto_respuesta: String(val).trim() });
          }
        }
      }

      const bodyData = {
        numero_documento: (this.trabajador.numero_documento || this.cedula || '').trim(),
        id_persona: this.personaInfo ? this.personaInfo.id : null,
        nombre: (this.trabajador.nombres || (this.personaInfo ? this.personaInfo.nombres : '')).trim(),
        apellido: (this.trabajador.apellidos || (this.personaInfo ? this.personaInfo.apellidos : '')).trim(),
        correo: (this.trabajador.correo || (this.personaInfo ? this.personaInfo.correo : '')).trim(),
        cargo: (this.trabajador.cargo || (this.personaInfo ? this.personaInfo.cargo : '')).trim(),
        area_sede: (this.trabajador.cargo || '').trim(),
        tipo_doc: this.trabajador.tipo_doc || 'CC',
        foto_en_vivo: this.fotoCapturadaDataUrl || null,
        respuestas: payloadRespuestas
      };

      try {
        const endpoint = this.esSimulacion ? "simular" : "evaluar";
        const url = `/api/v1/formularios-gesco/${this.formularioId}/${endpoint}`;
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(bodyData)
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Error al calificar HTTP ${res.status}`);
        }

        const data = await res.json();
        this.resultadoEvaluacion = data;
        this.estado = "RESULTADO";
        window.scrollTo({ top: 0, behavior: "smooth" });

        // Si aprobó, lanzar efecto de confeti
        if (data.aprobado && typeof confetti === "function") {
          confetti({
            particleCount: 90,
            spread: 70,
            origin: { y: 0.6 }
          });
        }
      } catch (err) {
        console.error("Error al enviar respuestas:", err);
        Swal.fire({
          icon: "error",
          title: "Error al calificar",
          text: err.message || "No se pudo procesar tu evaluación.",
          confirmButtonColor: this.confirmButtonColor
        });
      } finally {
        this.enviando = false;
      }
    },

    async reintentar() {
      // Al reintentar, se resetean las respuestas y el resultado anterior
      this.respuestas = {};
      this.resultadoEvaluacion = null;
      if (this.esSimulacion) {
        await this.iniciarSimulacion();
      } else {
        await this.verificarOIniciar();
      }
      // Garantizar que tanto las preguntas como las opciones tengan un nuevo orden aleatorio
      this.reformularPreguntasYRespuestas();

      this.mostrarToast('info', 'Formulario reformulado', 'Preguntas y opciones reorganizadas para este intento.');
    },

    reiniciar() {
      this.respuestas = {};
      this.resultadoEvaluacion = null;
      if (this.esSimulacion) {
        this.iniciarSimulacion();
      } else {
        this.cedula = "";
        this.personaInfo = null;
        this.vigenciaData = null;
        this.preguntas = [];
        this.trabajador = {
          tipo_doc: 'CC',
          numero_documento: '',
          nombres: '',
          apellidos: '',
          correo: '',
          cargo: '',
          empresa: 'INCARSA'
        };
        this.mostrarCamposCompletos = this.esTipoInterno;
        this.estado = "IDENTIFICACION";
      }
    }
  };
}
