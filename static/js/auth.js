/**
 * auth.js
 * Componente Alpine.js del formulario de inicio de sesión.
 * Depende de mockData.js (debe cargarse antes que este archivo).
 *
 * Primero intenta autenticar contra el backend FastAPI.
 * Si el backend no está disponible, cae al modo mock:
 *   - valida que el correo exista en MOCK_USUARIOS
 *   - acepta cualquier contraseña no vacía.
 */

function loginForm() {
  return {
    correo: "",
    contrasena: "",
    recordarme: false,
    showPassword: false,
    submitting: false,
    error: "",

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
