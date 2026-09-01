/**
 * auth.js
 * Componente Alpine.js del formulario de inicio de sesión y recuperación de contraseña en pasos.
 * Depende de mockData.js (debe cargarse antes que este archivo).
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
        const authUrl = typeof API !== "undefined" && API.auth ? API.auth : "http://127.0.0.1:8000/auth";
        const response = await fetch(`${authUrl}/solicitar_recuperacion`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ correo: email })
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          throw new Error(data.detail || "No se pudo procesar la solicitud de recuperación.");
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
        console.warn("Backend no disponible o error en recuperación:", err);
        // Modo fallback para pruebas locales / mock
        const nuevoCodigo = Math.floor(100000 + Math.random() * 900000).toString();
        this.olvide.codigoGenerado = nuevoCodigo;
        this.olvide.enviando = false;
        this.olvide.paso = 2;
        this.olvide.codigo = "";
        this.olvide.error = "";
        this.iniciarTemporizadorCodigo();
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
        const authUrl = typeof API !== "undefined" && API.auth ? API.auth : "http://127.0.0.1:8000/auth";
        const response = await fetch(`${authUrl}/solicitar_recuperacion`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ correo: (this.olvide.correo || "").trim() })
        });
        const data = await response.json().catch(() => ({}));
        if (data.codigo_demo) {
          this.olvide.codigoGenerado = String(data.codigo_demo);
        } else {
          this.olvide.codigoGenerado = Math.floor(100000 + Math.random() * 900000).toString();
        }
      } catch (e) {
        this.olvide.codigoGenerado = Math.floor(100000 + Math.random() * 900000).toString();
      }

      this.iniciarTemporizadorCodigo();
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
        const authUrl = typeof API !== "undefined" && API.auth ? API.auth : "http://127.0.0.1:8000/auth";
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
          // Si el código coincide con el código de prueba local o 123456, permitir continuar
          if (cod === this.olvide.codigoGenerado || cod === "123456") {
            this.olvide.enviando = false;
            this.olvide.paso = 3;
            this.olvide.error = "";
            if (this.olvide.intervalo) clearInterval(this.olvide.intervalo);
            return;
          }
          this.olvide.enviando = false;
          this.olvide.error = data.detail || "El código ingresado es incorrecto o ha expirado.";
          return;
        }
      } catch (err) {
        console.warn("Backend no disponible para verificar código, usando validación de prueba:", err);
        this.olvide.enviando = false;
        if (cod === this.olvide.codigoGenerado || cod === "123456") {
          this.olvide.paso = 3;
          this.olvide.error = "";
          if (this.olvide.intervalo) clearInterval(this.olvide.intervalo);
        } else {
          this.olvide.error = "El código ingresado es incorrecto o ha expirado.";
        }
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
        const authUrl = typeof API !== "undefined" && API.auth ? API.auth : "http://127.0.0.1:8000/auth";
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

        // Actualizar en mock si el usuario existe en MOCK_USUARIOS
        try {
          if (typeof MOCK_USUARIOS !== "undefined" && Array.isArray(MOCK_USUARIOS)) {
            const u = MOCK_USUARIOS.find(usr => (usr.correo || "").toLowerCase() === (this.olvide.correo || "").toLowerCase());
            if (u) u.contrasena = p1;
          }
        } catch (e) {}

        this.olvide.enviando = false;
        this.olvide.paso = 4;

        // Redirigir al formulario de inicio de sesión con el correo precargado
        setTimeout(() => {
          this.finalizarRecuperacion();
        }, 2400);

      } catch (err) {
        console.warn("Error en actualizarContrasena:", err);

        // Si fue un error de validación de backend explícito
        if (err.message && !err.message.includes("fetch") && !err.message.includes("NetworkError")) {
          this.olvide.enviando = false;
          this.olvide.error = err.message;
          return;
        }

        // Si el backend no estaba conectado (fallback para mock)
        try {
          if (typeof MOCK_USUARIOS !== "undefined" && Array.isArray(MOCK_USUARIOS)) {
            const u = MOCK_USUARIOS.find(usr => (usr.correo || "").toLowerCase() === (this.olvide.correo || "").toLowerCase());
            if (u) u.contrasena = p1;
          }
        } catch (e) {}

        this.olvide.enviando = false;
        this.olvide.paso = 4;

        setTimeout(() => {
          this.finalizarRecuperacion();
        }, 2400);
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

    guardarSesion(nombre, correo, rol, id = null, id_rol = null, plantas_ids = [], plantas = []) {
      const datos = { 
        nombre, 
        correo, 
        rol, 
        id, 
        id_rol, 
        plantas_ids: Array.isArray(plantas_ids) ? plantas_ids.map(Number) : [],
        plantas: plantas || []
      };
      if (this.recordarme) {
        localStorage.setItem("incarsa_session", JSON.stringify(datos));
      }
      sessionStorage.setItem("incarsa_session", JSON.stringify(datos));
    },

    async submit() {
      if (!this.validate()) return;
      this.submitting = true;

      // 1. Intentar autenticación contra usuarios en backend
      try {
        const response = await fetch(`${API.usuarios}/getall`);
        if (response.ok) {
          const data = await response.json();
          const lista = Array.isArray(data) ? data : (data.datos || data.data || []);
          const matched = lista.find(u => String(u.correo || "").trim().toLowerCase() === this.correo.trim().toLowerCase());
          if (matched) {
            this.guardarSesion(
              matched.nombre_completo || `${matched.nombres || ''} ${matched.apellidos || ''}`.trim(),
              matched.correo,
              matched.rol || "USUARIO",
              matched.id,
              matched.id_rol,
              matched.plantas_ids || [],
              matched.plantas || []
            );
            window.location.href = "dashboard.html";
            return;
          }
        }
      } catch (errApi) {
        console.warn("Consulta a usuarios backend:", errApi);
      }

      // 2. Modo mock: buscar en MOCK_USUARIOS (de mockData.js)
      setTimeout(() => {
        const user = MOCK_USUARIOS.find(
          u => u.correo.toLowerCase() === this.correo.trim().toLowerCase()
        );

        if (!user) {
          this.submitting = false;
          this.error = "Correo o contraseña incorrectos.";
          return;
        }

        this.guardarSesion(
          `${user.nombres} ${user.apellidos}`.trim(),
          user.correo,
          user.rol || "GESTOR DE DOCUMENTACIÓN"
        );

        window.location.href = "dashboard.html";
      }, 700);
    }
  };
}
