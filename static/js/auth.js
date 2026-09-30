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

    // Vista actual: 'login' | 'contacto' | 'olvide'
    vista: "login",

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
      codigoGenerado: "",
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

        // Si el backend entrega código demo (modo prueba / dev), lo mostramos en el badge
        if (data.codigo_demo) {
          this.olvide.codigoGenerado = String(data.codigo_demo);
        } else {
          this.olvide.codigoGenerado = "";
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
        if (data.codigo_demo) {
          this.olvide.codigoGenerado = String(data.codigo_demo);
        } else {
          this.olvide.codigoGenerado = "";
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
        document.cookie = `token=${encodeURIComponent(token)}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
        document.cookie = `incarsa_token=${encodeURIComponent(token)}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
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
