/**
 * INCARSA - Formulario Público de Correspondencia
 * correspondencia.js
 */

function correspondenciaForm() {
  const checkEsSuperAdmin = () => {
    try {
      const ses = (typeof getAuthSession === 'function') 
        ? getAuthSession() 
        : JSON.parse(sessionStorage.getItem('incarsa_session') || localStorage.getItem('incarsa_session') || 'null');
      const r = String(ses?.rol || ses?.nombre_rol || ses?.rol_nombre || '').toUpperCase().trim();
      const u = String(ses?.tipo_usuario || ses?.usuario || '').toUpperCase().trim();
      return r === 'SUPERADMIN' 
        || u === 'SUPERADMIN' 
        || ses?.id_rol === 1 
        || ses?.id_rol === 6
        || document.documentElement.getAttribute('data-role') === 'SUPERADMIN'
        || document.documentElement.classList.contains('role-superadmin');
    } catch (e) {
      return false;
    }
  };

  return {
    form: {
      tipo_correspondencia: "",
      asunto: "",
      procedencia: "",
      destino: "",
      radicado: "",
      fecha_envio: new Date().toISOString().split("T")[0]
    },
    esSuperAdmin: checkEsSuperAdmin(),
    submitting: false,
    submitted: false,
    error: "",
    resultado: null,

    init() {
      this.esSuperAdmin = checkEsSuperAdmin();
    },

    validar() {
      this.error = "";
      if (!this.form.tipo_correspondencia) {
        this.error = "Por favor selecciona el tipo de correspondencia.";
        return false;
      }
      if (!this.form.asunto || !this.form.asunto.trim()) {
        this.error = "Por favor ingresa el asunto de la correspondencia.";
        return false;
      }
      if (!this.form.procedencia || !this.form.procedencia.trim()) {
        this.error = "Por favor especifica la procedencia o remitente.";
        return false;
      }
      if (!this.form.destino || !this.form.destino.trim()) {
        this.error = "Por favor especifica el destino de la correspondencia.";
        return false;
      }
      return true;
    },

    async submit() {
      if (!this.validar()) return;

      this.submitting = true;
      this.error = "";

      try {
        const payload = {
          tipo_correspondencia: this.form.tipo_correspondencia,
          asunto: this.form.asunto.trim(),
          procedencia: this.form.procedencia.trim(),
          destino: this.form.destino.trim(),
          fecha_envio: this.form.fecha_envio || undefined,
          radicado: this.form.radicado ? this.form.radicado.trim() : undefined
        };

        let res = await fetch("/api/v1/correspondencia", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!res.ok && res.status === 404) {
          res = await fetch("/correspondencia", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
        }

        const data = await res.json().catch(() => ({}));

        if (!res.ok || data.exito === false) {
          throw new Error(data.detail || data.mensaje || "Error al registrar la correspondencia.");
        }

        this.resultado = data;
        this.submitted = true;

        if (typeof Swal !== "undefined") {
          const radicadoAsignado = data.radicado || ('SCR-' + String(data.id_generado).padStart(3, '0'));
          Swal.fire({
            icon: "success",
            title: "¡Correspondencia Registrada!",
            html: `Correspondencia guardada exitosamente.<br><br>Código de radicado asignado:<br><strong style="font-size: 1.3rem; color: #9eebe0ff; letter-spacing: 0.08em; display: inline-block; margin-top: 6px;">${radicadoAsignado}</strong>`,
            confirmButtonText: "Aceptar",
            customClass: {
              popup: "swal-login-card"
            }
          });
        }
      } catch (err) {
        this.error = err.message || "Ocurrió un error inesperado al registrar la correspondencia.";
      } finally {
        this.submitting = false;
      }
    },

    nuevaCorrespondencia() {
      this.form = {
        tipo_correspondencia: "",
        asunto: "",
        procedencia: "",
        destino: "",
        fecha_envio: new Date().toISOString().split("T")[0]
      };
      this.error = "";
      this.submitted = false;
      this.resultado = null;
    }
  };
}
