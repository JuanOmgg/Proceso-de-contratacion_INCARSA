/**
 * auth.js
 * Componente Alpine.js del formulario de inicio de sesión y recuperación de contraseña en pasos.
 */

function loginForm() {
  return {
    // Estado de Inicio de Sesión
    correo: "",
    contrasena: "",
    recordarme: false,
    showPassword: false,
    submitting: false,
    error: "",

    // Estado de Pantalla de Carga (Splash Screen)
    splash: {
      activo: false,
      progreso: 0,
      mensaje: "Verificando credenciales...",
      usuarioNombre: "",
      completado: false
    },

    init() {
      // Si el usuario tenía "Recordarme" activo, precargar su correo
      const correoGuardado = localStorage.getItem("incarsa_recordado_correo");
      if (correoGuardado) {
        this.correo = correoGuardado;
        this.recordarme = true;
      }

      const params = new URLSearchParams(window.location.search);
      if (params.get("expired")) {
        this.error = "Tu sesión ha caducado.";
      }
    },

    // Vista actual: 'login' | 'contacto' | 'olvide' | '2fa'
    vista: "login",

    // =========================================================
    // MÓDULO: VERIFICACIÓN EN 2 PASOS (2FA)
    // =========================================================
    dosPasos: {
      tempToken: "",
      correoOfuscado: "",
      codigo: "",
      verificando: false,
      error: "",
      reenviando: false,
      temporizador: 60,
      intervalo: null,
      puedeReenviar: false
    },

    iniciarTemporizador2FA() {
      if (this.dosPasos.intervalo) clearInterval(this.dosPasos.intervalo);
      this.dosPasos.temporizador = 60;
      this.dosPasos.puedeReenviar = false;

      this.dosPasos.intervalo = setInterval(() => {
        if (this.dosPasos.temporizador > 1) {
          this.dosPasos.temporizador--;
        } else {
          this.dosPasos.temporizador = 0;
          this.dosPasos.puedeReenviar = true;
          clearInterval(this.dosPasos.intervalo);
        }
      }, 1000);
    },

    cancelar2FA() {
      if (this.dosPasos.intervalo) clearInterval(this.dosPasos.intervalo);
      this.dosPasos.tempToken = "";
      this.dosPasos.codigo = "";
      this.dosPasos.error = "";
      this.dosPasos.verificando = false;
      this.vista = "login";
    },

    async verificarCodigo2FA() {
      this.dosPasos.error = "";
      const code = (this.dosPasos.codigo || "").trim();

      if (!code || code.length !== 6) {
        this.dosPasos.error = "Ingresa el código completo de 6 dígitos.";
        return;
      }

      this.dosPasos.verificando = true;

      try {
        const authUrl = typeof API !== "undefined" && API.auth ? API.auth : `${window.location.origin}/api/v1/auth`;
        const response = await fetch(`${authUrl}/verificar-2fa`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            temp_token: this.dosPasos.tempToken,
            codigo: code
          })
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          throw new Error(data.detail || data.mensaje || "Código de verificación incorrecto o expirado.");
        }

        if (this.dosPasos.intervalo) clearInterval(this.dosPasos.intervalo);

        const matchedUser = data.usuario;
        const accessToken = data.access_token;
        const userPermisos = data.permisos || null;

        // Guardar sesión y activar animación de carga completa
        this.guardarSesion(
          matchedUser.nombre,
          matchedUser.correo,
          matchedUser.rol,
          matchedUser.id,
          matchedUser.id_rol,
          matchedUser.plantas_ids,
          matchedUser.plantas,
          accessToken,
          userPermisos
        );

        this.splash.activo = true;
        this.splash.progreso = 25;
        this.splash.completado = false;
        this.splash.mensaje = "Verificación exitosa. Iniciando sesión";
        this.splash.usuarioNombre = matchedUser.nombre || matchedUser.correo;

        await this.ejecutarPrecargaCompleta(matchedUser);

      } catch (err) {
        console.warn("Error en verificarCodigo2FA:", err);
        this.dosPasos.verificando = false;
        this.dosPasos.error = err.message || "Error al verificar el código.";
      }
    },

    async reenviarCodigo2FA() {
      if (!this.dosPasos.puedeReenviar || this.dosPasos.reenviando) return;
      this.dosPasos.error = "";
      this.dosPasos.reenviando = true;

      try {
        const authUrl = typeof API !== "undefined" && API.auth ? API.auth : `${window.location.origin}/api/v1/auth`;
        const response = await fetch(`${authUrl}/reenviar-2fa`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            temp_token: this.dosPasos.tempToken
          })
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          throw new Error(data.detail || data.mensaje || "No se pudo reenviar el código de verificación.");
        }

        this.dosPasos.reenviando = false;
        this.dosPasos.codigo = "";
        this.iniciarTemporizador2FA();

        if (typeof Swal !== "undefined") {
          Swal.fire({
            toast: true,
            position: "top-end",
            icon: "success",
            title: "Código reenviado",
            text: "Revisa tu bandeja de entrada o spam.",
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
          });
        }
      } catch (err) {
        console.warn("Error reenviando código 2FA:", err);
        this.dosPasos.reenviando = false;
        this.dosPasos.error = err.message || "Error al reenviar el código.";
      }
    },

    // =========================================================
    // MÓDULO: CONTACTAR ADMINISTRADOR
    // =========================================================
    contacto: {
      asunto: "Problemas para iniciar sesión",
      presentacion: "",
      mensaje: "",
      enviando: false,
      enviado: false
    },

    enviarContacto() {
      if (!this.contacto.presentacion.trim() || !this.contacto.mensaje.trim()) return;
      this.contacto.enviando = true;
      setTimeout(() => {
        this.contacto.enviando = false;
        this.contacto.enviado = true;
        setTimeout(() => {
          this.vista = "login";
          this.contacto.enviado = false;
          this.contacto.presentacion = "";
          this.contacto.mensaje = "";
        }, 1800);
      }, 600);
    },

    // =========================================================
    // MÓDULO: RECUPERACIÓN DE CONTRASEÑA EN PASOS
    // Paso 1: Ingreso de correo corporativo
    // Paso 2: Validación de código de verificación enviado al correo
    // Paso 3: Definición y confirmación de nueva contraseña
    // Paso 4: Confirmación de éxito y redirección
    // =========================================================
    olvide: {
      paso: 1,
      correo: "",
      codigo: "",
      nuevaContrasena: "",
      confirmarContrasena: "",
      showPass1: false,
      showPass2: false,
      enviando: false,
      error: "",
      temporizador: 60,
      intervalo: null,
      puedeReenviar: false
    },

    iniciarRecuperacion() {
      this.vista = "olvide";
      this.olvide.paso = 1;
      this.olvide.error = "";
      this.olvide.codigo = "";
      this.olvide.nuevaContrasena = "";
      this.olvide.confirmarContrasena = "";
      this.olvide.showPass1 = false;
      this.olvide.showPass2 = false;
      if (this.correo && this.correo.trim()) {
        this.olvide.correo = this.correo.trim();
      }
      if (this.olvide.intervalo) clearInterval(this.olvide.intervalo);
    },

    // Paso 1 -> Paso 2: Validar correo corporativo y solicitar código
    async enviarCodigoRecuperacion() {
      this.olvide.error = "";
      const email = (this.olvide.correo || "").trim();

      if (!email) {
        this.olvide.error = "Ingresa tu correo corporativo.";
        return;
      }

      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(email)) {
        this.olvide.error = "Ingresa un correo electrónico corporativo válido.";
        return;
      }

      this.olvide.enviando = true;

      try {
        const authUrl = typeof API !== "undefined" && API.auth ? API.auth : `${window.location.origin}/api/v1/auth`;
        const response = await fetch(`${authUrl}/solicitar_recuperacion`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ correo: email })
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          throw new Error(data.detail || data.mensaje || "No se pudo procesar la solicitud de recuperación.");
        }

        this.olvide.enviando = false;
        this.olvide.paso = 2;
        this.olvide.codigo = "";
        this.olvide.error = "";
        this.iniciarTemporizadorCodigo();

      } catch (err) {
        console.warn("Error en recuperación:", err);
        this.olvide.enviando = false;
        this.olvide.error = err.message || "No se pudo procesar la solicitud de recuperación.";
      }
    },

    iniciarTemporizadorCodigo() {
      if (this.olvide.intervalo) clearInterval(this.olvide.intervalo);
      this.olvide.temporizador = 60;
      this.olvide.puedeReenviar = false;

      this.olvide.intervalo = setInterval(() => {
        if (this.olvide.temporizador > 1) {
          this.olvide.temporizador--;
        } else {
          this.olvide.temporizador = 0;
          this.olvide.puedeReenviar = true;
          clearInterval(this.olvide.intervalo);
        }
      }, 1000);
    },

    async reenviarCodigoRecuperacion() {
      if (!this.olvide.puedeReenviar && this.olvide.temporizador > 0) return;
      this.olvide.error = "";
      this.olvide.codigo = "";

      try {
        const authUrl = typeof API !== "undefined" && API.auth ? API.auth : `${window.location.origin}/api/v1/auth`;
        const response = await fetch(`${authUrl}/solicitar_recuperacion`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ correo: (this.olvide.correo || "").trim() })
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          this.olvide.error = data.detail || data.mensaje || "Error al reenviar el código.";
          return;
        }
        this.iniciarTemporizadorCodigo();
      } catch (e) {
        this.olvide.error = e.message || "Error al reenviar código.";
      }
    },

    // Paso 2 -> Paso 3: Verificar código ingresado
    async verificarCodigoRecuperacion() {
      this.olvide.error = "";
      const cod = (this.olvide.codigo || "").trim();

      if (!cod) {
        this.olvide.error = "Ingresa el código de verificación.";
        return;
      }

      if (cod.length !== 6) {
        this.olvide.error = "El código debe tener exactamente 6 dígitos.";
        return;
      }

      this.olvide.enviando = true;

      // Intentar validar contra el backend
      try {
        const authUrl = typeof API !== "undefined" && API.auth ? API.auth : `${window.location.origin}/api/v1/auth`;
        const response = await fetch(`${authUrl}/verificar-codigo`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            correo: (this.olvide.correo || "").trim(),
            codigo: cod
          })
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok) {
          this.olvide.enviando = false;
          this.olvide.paso = 3;
          this.olvide.error = "";
          if (this.olvide.intervalo) clearInterval(this.olvide.intervalo);
          return;
        } else {
          this.olvide.enviando = false;
          this.olvide.error = data.detail || data.mensaje || "El código ingresado es incorrecto o ha expirado.";
          return;
        }
      } catch (err) {
        console.warn("Error al verificar código:", err);
        this.olvide.enviando = false;
        this.olvide.error = err.message || "El código ingresado es incorrecto o ha expirado.";
      }
    },

    // Paso 3 -> Paso 4: Validar y guardar nueva contraseña
    async actualizarContrasena() {
      this.olvide.error = "";
      const p1 = this.olvide.nuevaContrasena || "";
      const p2 = this.olvide.confirmarContrasena || "";

      if (!p1.trim()) {
        this.olvide.error = "Ingresa tu nueva contraseña.";
        return;
      }

      if (p1.length < 8) {
        this.olvide.error = "La nueva contraseña debe tener al menos 8 caracteres.";
        return;
      }

      if (p1 !== p2) {
        this.olvide.error = "Las contraseñas no coinciden.";
        return;
      }

      this.olvide.enviando = true;

      try {
        const authUrl = typeof API !== "undefined" && API.auth ? API.auth : `${window.location.origin}/api/v1/auth`;
        const response = await fetch(`${authUrl}/restablecer-contrasena`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            correo: (this.olvide.correo || "").trim(),
            codigo: (this.olvide.codigo || "").trim(),
            nueva_contrasena: p1
          })
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          // Si el servidor dio un error específico (como código inválido)
          if (data.detail) {
            throw new Error(data.detail);
          }
          throw new Error("No se pudo actualizar la contraseña.");
        }

        this.olvide.enviando = false;
        this.olvide.paso = 4;

        // Redirigir al formulario de inicio de sesión con el correo precargado
        setTimeout(() => {
          this.finalizarRecuperacion();
        }, 2400);

      } catch (err) {
        console.warn("Error en actualizarContrasena:", err);
        this.olvide.enviando = false;
        this.olvide.error = err.message || "Error al actualizar la contraseña.";
      }
    },

    finalizarRecuperacion() {
      if (this.olvide.intervalo) clearInterval(this.olvide.intervalo);
      this.correo = this.olvide.correo;
      this.contrasena = this.olvide.nuevaContrasena;
      this.vista = "login";
      this.error = "";
      this.olvide.paso = 1;
    },

    togglePassword() {
      this.showPassword = !this.showPassword;
    },

    validate() {
      this.error = "";
      if (!this.correo.trim() || !this.contrasena.trim()) {
        this.error = "Ingresa tu correo y tu contraseña.";
        return false;
      }
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(this.correo.trim())) {
        this.error = "Ingresa un correo electrónico válido.";
        return false;
      }
      return true;
    },

    guardarSesion(nombre, correo, rol, id = null, id_rol = null, plantas_ids = [], plantas = [], token = null, permisos = null) {
      const datos = { 
        nombre, 
        correo, 
        rol, 
        id, 
        id_rol, 
        plantas_ids: Array.isArray(plantas_ids) ? plantas_ids.map(Number) : [],
        plantas: plantas || [],
        token: token || null
      };

      // sessionStorage mantiene la sesión activa en la pestaña y ventanas abiertas
      sessionStorage.setItem("incarsa_session", JSON.stringify(datos));
      if (token) {
        sessionStorage.setItem("incarsa_token", token);
        // Las cookies token e incarsa_token son configuradas de forma segura y con HttpOnly desde el servidor
      }
      if (permisos) {
        sessionStorage.setItem("incarsa_permisos", JSON.stringify(permisos));
      }

      // Si el usuario marcó "Recordarme", persistir permanentemente en localStorage
      if (this.recordarme) {
        localStorage.setItem("incarsa_session", JSON.stringify(datos));
        if (token) localStorage.setItem("incarsa_token", token);
        if (permisos) localStorage.setItem("incarsa_permisos", JSON.stringify(permisos));
        localStorage.setItem("incarsa_recordado_correo", correo);
      } else {
        // Si NO marcó Recordarme, limpiar localStorage para que la sesión expire al cerrar el navegador
        localStorage.removeItem("incarsa_session");
        localStorage.removeItem("incarsa_token");
        localStorage.removeItem("incarsa_permisos");
        localStorage.removeItem("incarsa_recordado_correo");
      }
    },

    async submit() {
      if (!this.validate()) return;
      this.submitting = true;
      this.error = "";

      // Activar pantalla de carga (Splash)
      this.splash.activo = true;
      this.splash.progreso = 12;
      this.splash.completado = false;
      this.splash.mensaje = "Verificando credenciales y perfil";
      this.splash.usuarioNombre = this.correo ? this.correo.split("@")[0] : "Iniciando sesión";

      let matchedUser = null;
      let accessToken = null;
      let userPermisos = null;

      // 1. Intentar autenticación real contra el endpoint /auth/login
      try {
        const authEndpoint = (typeof API !== "undefined" && API.auth) ? `${API.auth}/login` : "/auth/login";
        const response = await fetch(authEndpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            correo: this.correo.trim().toLowerCase(),
            contrasena: this.contrasena
          })
        });

        if (response.ok) {
          const resData = await response.json();
          // Si el Superadministrador tiene activada la verificación en 2 pasos
          if (resData.requiere_2fa) {
            await new Promise(r => setTimeout(r, 200));
            this.splash.activo = false;
            this.submitting = false;
            this.dosPasos.tempToken = resData.temp_token;
            this.dosPasos.correoOfuscado = resData.correo_ofuscado || this.correo;
            this.dosPasos.codigo = "";
            this.dosPasos.error = "";
            this.dosPasos.verificando = false;
            this.vista = "2fa";
            this.iniciarTemporizador2FA();
            return;
          }

          if (resData.exito && resData.usuario) {
            matchedUser = resData.usuario;
            accessToken = resData.access_token;
            userPermisos = resData.permisos || null;
          }
        } else {
          const errData = await response.json().catch(() => ({}));
          let mensajeError = "Correo o contraseña incorrectos.";
          if (typeof errData.detail === "string") {
            mensajeError = errData.detail;
          } else if (Array.isArray(errData.detail) && errData.detail[0]?.msg) {
            mensajeError = errData.detail[0].msg;
          }

          // Si el servidor devolvió un error de validación o credenciales, detener y mostrar
          if (response.status === 401 || response.status === 403 || response.status === 422 || response.status === 404) {
            await new Promise(r => setTimeout(r, 450));
            this.splash.activo = false;
            this.submitting = false;
            this.error = mensajeError;
            return;
          }
        }
      } catch (errApi) {
        console.warn("Intento de conexión con /auth/login falló:", errApi);
        this.error = "Error de conexión con el servidor. Intente nuevamente.";
      }

      // Si no existe el usuario, cerrar splash y mostrar error
      if (!matchedUser) {
        await new Promise(r => setTimeout(r, 450));
        this.splash.activo = false;
        this.submitting = false;
        this.error = this.error || "Correo o contraseña incorrectos.";
        return;
      }

      // Usuario autenticado: guardar sesión y token JWT, y proceder con carga
      this.splash.usuarioNombre = matchedUser.nombre || matchedUser.correo;
      this.guardarSesion(
        matchedUser.nombre,
        matchedUser.correo,
        matchedUser.rol,
        matchedUser.id,
        matchedUser.id_rol,
        matchedUser.plantas_ids,
        matchedUser.plantas,
        accessToken,
        userPermisos
      );

      await this.ejecutarPrecargaCompleta(matchedUser);
    },

    async ejecutarPrecargaCompleta(user) {
      const startTime = Date.now();

      const actualizarProgreso = (pct, msg) => {
        this.splash.progreso = pct;
        if (msg) this.splash.mensaje = msg;
      };

      actualizarProgreso(25, "Cargando solicitudes y radicados");

      // Tareas de precarga real de toda la plataforma
      const tSolicitudes = fetch(`${API.solicitudes}/getall`)
        .then(async r => {
          if (!r.ok) return null;
          const data = await r.json();
          const lista = Array.isArray(data) ? data : (data.datos || []);
          sessionStorage.setItem("incarsa_preloaded_solicitudes", JSON.stringify(lista));
          return lista;
        }).catch(() => null);

      const tPlantas = fetch(`${API.plantas}/getall`)
        .then(async r => {
          if (!r.ok) return null;
          const data = await r.json();
          sessionStorage.setItem("incarsa_preloaded_plantas", JSON.stringify(data));
          return data;
        }).catch(() => null);

      const tContratistas = fetch(`${API.contratistas}/getall`)
        .then(async r => {
          if (!r.ok) return null;
          const data = await r.json();
          sessionStorage.setItem("incarsa_preloaded_contratistas", JSON.stringify(data));
          return data;
        }).catch(() => null);

      const paramsNotif = new URLSearchParams();
      if (user.id) paramsNotif.append("id_usuario", user.id);
      if (user.id_rol) paramsNotif.append("id_rol", user.id_rol);
      const notifEndpoint = (typeof API !== "undefined" && API.notificaciones) ? API.notificaciones : "/api/v1/notificaciones";
      const tNotificaciones = fetch(`${notifEndpoint}?${paramsNotif.toString()}`)
        .then(async r => {
          if (!r.ok) return null;
          const data = await r.json();
          sessionStorage.setItem("incarsa_preloaded_notificaciones", JSON.stringify(data));
          return data;
        }).catch(() => null);

      const tPermisos = fetch("/api/v1/roles/mis-permisos")
        .then(async r => {
          if (!r.ok) return null;
          const data = await r.json();
          if (data && data.permisos) {
            sessionStorage.setItem("incarsa_permisos", JSON.stringify(data.permisos));
            localStorage.setItem("incarsa_permisos", JSON.stringify(data.permisos));
            return data.permisos;
          }
        }).catch(() => null);

      const tLogo = new Promise(resolve => {
        const img = new Image();
        img.src = "/static/img/logo-sidebar.png";
        img.onload = resolve;
        img.onerror = resolve;
      });

      const tareas = [tSolicitudes, tPlantas, tContratistas, tNotificaciones, tPermisos, tLogo];
      let completadas = 0;

      tareas.forEach(p => {
        p.finally(() => {
          completadas++;
          const pct = Math.min(92, 25 + Math.round((completadas / tareas.length) * 67));
          if (completadas === 1) {
            actualizarProgreso(pct, "Sincronizando permisos y catálogos");
          } else if (completadas === 3) {
            actualizarProgreso(pct, "Cargando notificaciones y plantas");
          } else if (completadas >= 4) {
            actualizarProgreso(pct, "Preparando espacio de trabajo");
          }
        });
      });

      // Esperar resolución de todas las llamadas (con timeout de seguridad de 6s)
      const timeoutSeguridad = new Promise(resolve => setTimeout(resolve, 8000));
      await Promise.race([Promise.allSettled(tareas), timeoutSeguridad]);

      // Mínimo 1.2 segundos para asegurar apreciación visual y fluidez cinematográfica
      const transcurrido = Date.now() - startTime;
      const duracionMinima = 2200;
      if (transcurrido < duracionMinima) {
        await new Promise(res => setTimeout(res, duracionMinima - transcurrido));
      }

      // 100% Completado con animación de éxito
      actualizarProgreso(100, "¡Todo listo! Bienvenido");
      this.splash.completado = true;

      // Breve pausa para apreciar el 100% y redirigir
      await new Promise(res => setTimeout(res, 400));
      window.location.replace("/dashboard");
    }
  };
}
