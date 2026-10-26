/**
 * ============================================================================
 * dataProcessing.js — Controlador de Tratamiento de Datos Personales (Ley 1581)
 * ============================================================================
 * Gestiona el flujo público y de previsualización de autorización de datos:
 * 1. Carga y parseo del catálogo de empresas / NITs para previsualización.
 * 2. Consulta y validación del token criptográfico ante la API backend.
 * 3. Modo interactivo SuperAdmin (simulación de estados Pendiente, Autorizado, Rechazado, Expirado).
 * 4. Captura forense de alta entropía del dispositivo del cliente (Client Hints + GPU WebGL fallback).
 * 5. Envío de aceptación o rechazo con observaciones y descarga del certificado en PDF.
 */

function cargarEmpresasCatalogo() {
  try {
    const el = document.getElementById('empresas-data');
    if (el && el.textContent) {
      return JSON.parse(el.textContent);
    }
  } catch (e) {
    console.error("Error al cargar empresas del servidor:", e);
  }
  return [];
}

function autorizacionDatosApp() {
  return {
    token: window.__TOKEN_AUTORIZACION__ || "",
    esPreview: false,
    cargando: true,
    enviando: false,
    error: false,
    errorTitulo: "",
    errorMensaje: "",
    checkLeido: false,
    checkValido: false,
    checkAutorizo: false,
    get aceptaTerminos() {
      return Boolean(this.checkLeido && this.checkValido && this.checkAutorizo);
    },
    empresasCatalogo: cargarEmpresasCatalogo(),
    seleccionarEmpresaPreview(emp) {
      this.datos.empresa_origen = emp.nombre;
      this.datos.nit_empresa = emp.nit;
      this.datos.correo_institucional = emp.correo;
    },
    
    get correoInstitucional() {
      return this.datos.correo_institucional || 'incarsasas@incarsa.com.co';
    },
    get nitEmpresa() {
      return this.datos.nit_empresa || '830.078.829-5';
    },
    datos: {
      nombre_completo: "",
      tipo_doc: "C.C.",
      identificacion: "",
      cedula: "",
      cargo: "",
      correo: "",
      codigo_radicado: "",
      empresa_origen: "INCARSA S.A.S.",
      nit_empresa: "830.078.829-5",
      correo_institucional: "incarsasas@incarsa.com.co",
      empresa_contratista: "",
      plantas_texto: "",
      estado_datos: "PENDIENTE",
      fecha_respuesta_datos: ""
    },

    async iniciar() {
      const urlParams = new URLSearchParams(window.location.search);
      const queryPreview = urlParams.get('preview') === 'true' || urlParams.get('preview') === '1';

      // Detectar modo previsualización SuperAdmin
      if (window.__ES_PREVIEW__ || this.token.includes('demo') || this.token.includes('preview') || queryPreview) {
        this.esPreview = true;
        const primeraEmpresa = (this.empresasCatalogo && this.empresasCatalogo.length > 0) ? this.empresasCatalogo[0] : null;
        this.datos = {
          nombre_completo: "Diego Alejandro Cardozo",
          tipo_doc: "C.C.",
          identificacion: "1.098.765.432",
          cedula: "1.098.765.432",
          cargo: "Supervisor de Operaciones y Mantenimiento",
          correo: "diego.cardozo@ejemplo.com",
          codigo_radicado: "RAD-LGKS84",
          empresa_origen: primeraEmpresa ? primeraEmpresa.nombre : "INCARSA S.A.S.",
          nit_empresa: primeraEmpresa ? primeraEmpresa.nit : "830.078.829-5",
          correo_institucional: primeraEmpresa ? primeraEmpresa.correo : "incarsasas@incarsa.com.co",
          empresa_contratista: "AGRÍCOLA & SERVICIOS INDUSTRIALES S.A.S.",
          plantas_texto: "PLANTA 1 INCARSA",
          tipo_personal: "Contratista",
          modo_entrega: "DIRECTO",
          tipo_enlace: "GESCO",
          formulario_asignado: {
            id: 8,
            nombre: "Evaluación General de Inducción GESCO",
            tipo_personal: "Contratista",
            vigencia: "1 año",
            cantidad_preguntas: 10,
            creador_nombre: "Auditor GESCO",
            url_evaluacion: "/evaluacion-induccion/8?simulacion=1",
            url_simulacion: "/evaluacion-induccion/8?simulacion=1"
          },
          estado_datos: "PENDIENTE",
          fecha_respuesta_datos: ""
        };
        this.cargando = false;
        return;
      }


      if (!this.token) {
        this.mostrarError("Token no proporcionado", "El enlace no contiene el token de verificación requerido.");
        this.cargando = false;
        return;
      }

      try {
        const resp = await fetch(`/api/v1/solicitudes/publico/autorizacion-datos/${encodeURIComponent(this.token)}`);
        const data = await resp.json();

        if (!resp.ok || !data.exito) {
          this.mostrarError("Enlace no válido o expirado", data.detail || data.mensaje || "No se encontró el registro asociado.");
          this.cargando = false;
          return;
        }

        this.datos = data.datos;
        this.cargando = false;
      } catch (e) {
        console.error("Error al consultar token:", e);
        this.mostrarError("Error de Conexión", "No se pudo establecer comunicación con el servidor. Por favor intente más tarde.");
        this.cargando = false;
      }
    },

    setEstadoPreview(nuevoEstado) {
      this.error = false;
      this.cargando = false;
      this.datos.estado_datos = nuevoEstado;
      if (nuevoEstado === 'AUTORIZADO' && !this.datos.fecha_respuesta_datos) {
        this.datos.fecha_respuesta_datos = new Date().toLocaleString('es-CO');
      }
    },

    simularErrorToken() {
      this.cargando = false;
      this.mostrarError(
        "Enlace no válido o expirado (Simulación)",
        "Este es un ejemplo de cómo ve el usuario la pantalla si el token ya venció o no existe en la base de datos."
      );
    },

    mostrarError(titulo, mensaje) {
      this.error = true;
      this.errorTitulo = titulo;
      this.errorMensaje = mensaje;
    },

    cambiarADecision() {
      this.datos.estado_datos = "PENDIENTE";
      this.checkLeido = false;
      this.checkValido = false;
      this.checkAutorizo = false;
    },

    async abrirModalRechazo() {
      const nombreEmpresaOrigen = this.datos.empresa_origen || 'la empresa';
      const { value: confirmacion } = await Swal.fire({
        title: '¿Rechazar Autorización?',
        html: `
          <div class="swal-rechazo-body">
            <p class="swal-rechazo-aviso" style="margin-bottom: 12px;">
              ⚠️ <strong>Atención:</strong> Si rechaza el tratamiento de datos personales, el sistema de portería de <strong>${nombreEmpresaOrigen}</strong> bloqueará automáticamente su ingreso a las instalaciones físicas.
            </p>
            <label class="swal-rechazo-label">
              Motivo del rechazo (opcional):
            </label>
            <textarea id="swal-motivo-rechazo" class="eval-textarea" style="width: 100%; height: 75px; border-radius: 10px; padding: 10px; font-size: 12px;" placeholder="Indique si tiene alguna observación..."></textarea>
          </div>
        `,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, Rechazar y No Ingresar',
        cancelButtonText: 'Volver a Leer',
        reverseButtons: true,
        confirmButtonColor: '#e11d48',
        cancelButtonColor: '#64748b',
        preConfirm: () => {
          const motivo = document.getElementById('swal-motivo-rechazo')?.value || '';
          return { rechazar: true, motivo: motivo };
        }
      });

      if (confirmacion && confirmacion.rechazar) {
        await this.enviarRespuesta(false, confirmacion.motivo);
      }
    },

    async enviarRespuesta(acepto, motivo = null) {
      if (this.enviando) return;
      this.enviando = true;

      // Modo Previsualización SuperAdmin: Simulación interactiva sin alterar base de datos
      if (this.esPreview) {
        await new Promise(r => setTimeout(r, 300));
        this.datos.estado_datos = acepto ? "AUTORIZADO" : "RECHAZADO";
        this.datos.fecha_respuesta_datos = new Date().toLocaleString('es-CO');

        if (acepto) {
          const formAsig = this.datos.formulario_asignado;
          const esModoDirecto = this.datos.modo_entrega === 'DIRECTO' || this.esPreview;

          if (formAsig && formAsig.url_evaluacion && esModoDirecto) {
            await Swal.fire({
              title: '¡Consentimiento Autorizado!',
              html: `
                <div style="text-align: left; font-size: 13px; color: #cbd5e1; line-height: 1.5;">
                  <p style="margin-bottom: 12px;">Su autorización legal ha sido confirmada conforme a la <strong>Ley 1581 de 2012</strong>.</p>
                  <div style="background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.45); border-radius: 12px; padding: 14px; margin-top: 10px;">
                    <div style="font-size: 11px; font-weight: 800; color: #818cf8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
                      🎓 Inducción Asignada · Modo Directo / Pruebas (${this.datos.tipo_personal || 'Personal'})
                    </div>
                    <div style="color: #ffffff; font-size: 15px; font-weight: 700; line-height: 1.3;">
                      ${formAsig.nombre}
                    </div>
                    <p style="font-size: 11.5px; color: #94a3b8; margin: 6px 0 0 0;">
                      Como está activo el <strong>Modo Directo</strong> para pruebas, puede presentar de inmediato su curso y evaluación de inducción.
                    </p>
                  </div>
                </div>
              `,
              icon: 'success',
              showCancelButton: true,
              confirmButtonText: '<i class="fa-solid fa-play" style="margin-right: 6px;"></i> Iniciar Inducción Ahora',
              cancelButtonText: 'Descargar Certificado PDF',
              confirmButtonColor: '#6366f1',
              cancelButtonColor: '#334155'
            }).then((result) => {
              if (result.isConfirmed) {
                window.location.href = formAsig.url_evaluacion;
              } else {
                window.open('/api/v1/solicitudes/publico/autorizacion-datos/' + encodeURIComponent(this.token || 'preview') + '/certificado-pdf', '_blank');
              }
            });
          } else {
            await Swal.fire({
              title: '¡Autorización Exitosa!',
              text: 'Su consentimiento ha sido registrado formalmente bajo la Ley 1581 de 2012. Puede presentarse en portería en las fechas programadas.',
              icon: 'success',
              showCancelButton: true,
              confirmButtonText: 'Descargar Certificado PDF',
              cancelButtonText: 'Continuar'
            }).then((result) => {
              if (result.isConfirmed) {
                window.open('/api/v1/solicitudes/publico/autorizacion-datos/' + encodeURIComponent(this.token || 'preview') + '/certificado-pdf', '_blank');
              }
            });
          }
        } else {
          await Swal.fire({
            title: 'Respuesta Registrada',
            text: 'Se ha registrado su rechazo al tratamiento de datos. El ingreso a la planta queda restringido.',
            icon: 'info',
            confirmButtonText: 'Aceptar'
          });
        }
        this.enviando = false;
        return;
      }

      // Captura forense de alta entropía del dispositivo (Client Hints + GPU WebGL Fallback)
      let modeloCliente = '';
      try {
        if (navigator.userAgentData && typeof navigator.userAgentData.getHighEntropyValues === 'function') {
          const hints = await navigator.userAgentData.getHighEntropyValues(['model', 'platform', 'platformVersion']);
          if (hints && hints.model) {
            modeloCliente = String(hints.model).trim();
          }
        }
      } catch (eHint) {}

      if (!modeloCliente) {
        try {
          const canvas = document.createElement('canvas');
          const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
          if (gl) {
            const dbg = gl.getExtension('WEBGL_debug_renderer_info');
            if (dbg) {
              const gpu = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) || '';
              if (gpu && !gpu.includes('SwiftShader') && !gpu.includes('llvmpipe')) {
                modeloCliente = 'GPU: ' + gpu.trim();
              }
            }
          }
        } catch (eGpu) {}
      }

      try {
        const resp = await fetch(`/api/v1/solicitudes/publico/autorizacion-datos/${encodeURIComponent(this.token)}/responder`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            acepto: acepto,
            motivo_rechazo: motivo,
            dispositivo_cliente: modeloCliente || null
          })
        });

        const resData = await resp.json();

        if (!resp.ok || !resData.exito) {
          Swal.fire({
            title: 'Error',
            text: resData.detail || resData.mensaje || 'No se pudo registrar su respuesta.',
            icon: 'error'
          });
          this.enviando = false;
          return;
        }

        // Actualizar estado local
        this.datos.estado_datos = resData.nuevo_estado;
        this.datos.fecha_respuesta_datos = resData.fecha;
        if (resData.formulario_asignado) {
          this.datos.formulario_asignado = resData.formulario_asignado;
        }
        if (resData.modo_entrega) {
          this.datos.modo_entrega = resData.modo_entrega;
        }
        if (resData.tipo_personal) {
          this.datos.tipo_personal = resData.tipo_personal;
        }

        if (acepto) {
          const formAsig = this.datos.formulario_asignado;
          const esModoDirecto = this.datos.modo_entrega === 'DIRECTO';

          if (formAsig && formAsig.url_evaluacion && esModoDirecto) {
            Swal.fire({
              title: '¡Consentimiento Autorizado!',
              html: `
                <div style="text-align: left; font-size: 13px; color: #cbd5e1; line-height: 1.5;">
                  <p style="margin-bottom: 12px;">Su autorización legal ha sido confirmada conforme a la <strong>Ley 1581 de 2012</strong>.</p>
                  <div style="background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.45); border-radius: 12px; padding: 14px; margin-top: 10px;">
                    <div style="font-size: 11px; font-weight: 800; color: #818cf8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
                      🎓 Inducción Asignada · Modo Directo / Pruebas (${this.datos.tipo_personal || 'Personal'})
                    </div>
                    <div style="color: #ffffff; font-size: 15px; font-weight: 700; line-height: 1.3;">
                      ${formAsig.nombre}
                    </div>
                    <p style="font-size: 11.5px; color: #94a3b8; margin: 6px 0 0 0;">
                      Como está activo el <strong>Modo Directo</strong> para pruebas, puede presentar de inmediato su curso y evaluación de inducción.
                    </p>
                  </div>
                </div>
              `,
              icon: 'success',
              showCancelButton: true,
              confirmButtonText: '<i class="fa-solid fa-play" style="margin-right: 6px;"></i> Iniciar Inducción Ahora',
              cancelButtonText: 'Descargar Certificado PDF',
              confirmButtonColor: '#6366f1',
              cancelButtonColor: '#334155'
            }).then((result) => {
              if (result.isConfirmed) {
                window.location.href = formAsig.url_evaluacion;
              } else {
                window.open('/api/v1/solicitudes/publico/autorizacion-datos/' + encodeURIComponent(this.token) + '/certificado-pdf', '_blank');
              }
            });
          } else {
            Swal.fire({
              title: '¡Autorización Exitosa!',
              text: 'Su consentimiento ha sido registrado formalmente bajo la Ley 1581 de 2012. Puede presentarse en portería en las fechas programadas.',
              icon: 'success',
              showCancelButton: true,
              confirmButtonText: 'Descargar Certificado PDF',
              cancelButtonText: 'Continuar'
            }).then((result) => {
              if (result.isConfirmed) {
                window.open('/api/v1/solicitudes/publico/autorizacion-datos/' + encodeURIComponent(this.token) + '/certificado-pdf', '_blank');
              }
            });
          }
        } else {
          Swal.fire({
            title: 'Respuesta Registrada',
            text: 'Se ha registrado su rechazo al tratamiento de datos. El ingreso a la planta queda restringido.',
            icon: 'info'
          });
        }
      } catch (e) {
        console.error("Error al registrar respuesta:", e);
        Swal.fire({
          title: 'Error de Red',
          text: 'Ocurrió un fallo al comunicar la respuesta al servidor.',
          icon: 'error'
        });
      } finally {
        this.enviando = false;
      }

    }
  };
}
