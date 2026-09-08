/**
 * usuario-formulario.js
 * Componente Alpine.js del formulario "Nuevo usuario" / "Editar usuario".
 * Incluye asignación dinámica de plantas/zonas para roles SST (3) y GESCO (4).
 */

function usuarioForm() {
  return {
    // ---------------------------------------------------
    // Catálogos
    // ---------------------------------------------------
    roles: [],
    catalogoPlantas: [],
    tiposDocumento: ["Cédula de ciudadanía", "Cédula de extranjería", "Pasaporte"],
    allUsers: [],

    // ---------------------------------------------------
    // Estado
    // ---------------------------------------------------
    errors: {},
    submitting: false,
    submitted: false,
    cargando: true,

    isEdit: false,
    editId: null,

    cambiarContrasena: false, // solo relevante en modo edición
    mostrarContrasena: false,
    mostrarConfirmar: false,
    guardandoUsuario: false,

    form: {
      nombres: "",
      apellidos: "",
      tipo_documento: "Cédula de ciudadanía",
      num_documento: "",
      num_telefono: "",
      correo: "",
      rol: "",
      plantas_ids: [],
      is_active: true,
      contrasena: "",
      confirmarContrasena: ""
    },

    // ---------------------------------------------------
    // Roles que requieren asignación de plantas (ÚNICAMENTE SST=5 y GESCO=6)
    // ---------------------------------------------------
    esRolConPlantas() {
      const rolVal = this.form.rol;
      if (!rolVal && rolVal !== 0) return false;

      const rolId = Number(rolVal);
      // SST = 5, GESCO = 6
      if (rolId === 5 || rolId === 6) return true;

      // Si es un ID numérico de otro rol (1=ADMINISTRADOR, 2=SUPERADMIN, 3=VIGILANTE, 4=GESTION DOCUMENTAL, 7=SCR)
      if (!isNaN(rolId) && rolId > 0 && rolId !== 5 && rolId !== 6) {
        return false;
      }

      // Si viene por nombre de rol en string
      const strVal = String(rolVal).trim().toUpperCase();
      if (strVal === "SST" || strVal === "GESCO") return true;

      // Buscar en el catálogo de roles cargados
      const rolObj = (this.roles || []).find(r => 
        Number(r.id) === rolId || 
        String(r.nombre_rol || "").trim().toUpperCase() === strVal
      );

      if (rolObj) {
        const nom = String(rolObj.nombre_rol || "").trim().toUpperCase();
        const objId = Number(rolObj.id);
        return objId === 5 || objId === 6 || nom === "SST" || nom === "GESCO";
      }

      return false;
    },

    onRolChange() {
      if (this.errors.rol) delete this.errors.rol;
      if (this.errors.id_rol) delete this.errors.id_rol;
      if (!this.esRolConPlantas()) {
        this.form.plantas_ids = [];
        if (this.errors.plantas_ids) delete this.errors.plantas_ids;
      }
    },

    // ---------------------------------------------------
    // Métodos para plantas
    // ---------------------------------------------------
    togglePlanta(id) {
      const numId = Number(id);
      const idx = this.form.plantas_ids.indexOf(numId);
      if (idx > -1) {
        this.form.plantas_ids.splice(idx, 1);
      } else {
        this.form.plantas_ids.push(numId);
      }
      if (this.errors.plantas_ids) delete this.errors.plantas_ids;
    },

    seleccionarTodasPlantas() {
      this.form.plantas_ids = this.catalogoPlantas.map(p => Number(p.id));
      if (this.errors.plantas_ids) delete this.errors.plantas_ids;
    },

    deseleccionarTodasPlantas() {
      this.form.plantas_ids = [];
    },

    // ---------------------------------------------------
    // Inicialización
    // ---------------------------------------------------
    async init() {
      const pathParts = window.location.pathname.split("/").filter(Boolean);
      let pathParam = "";
      const editIdx = pathParts.indexOf("editar");
      if (editIdx > -1 && pathParts[editIdx + 1]) {
        pathParam = decodeURIComponent(pathParts[editIdx + 1]);
      }
      const params = new URLSearchParams(window.location.search);
      const editParam = (window.__USUARIO_IDENTIFICADOR__ || pathParam || params.get("edit") || "").trim();

      await Promise.allSettled([
        this.getRoles(),
        this.getPlantas(),
        this.getUsers()
      ]);

      if (editParam) {
        const norm = (s) => String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[-_]/g, " ").replace(/\s+/g, " ").trim();
        const targetNorm = norm(editParam);

        let found = this.allUsers.find(u => {
          if (String(u.id) === String(editParam)) return true;
          const fullName = norm(`${u.nombres || ''} ${u.apellidos || ''}`);
          if (fullName && fullName === targetNorm) return true;
          if (norm(u.nombres) === targetNorm) return true;
          if (norm(u.nombre) === targetNorm) return true;
          if (norm(u.correo) === targetNorm) return true;
          return false;
        });
        
        if (!found || !found.plantas_ids) {
          try {
            const res = await fetch(`${API.usuarios}/${encodeURIComponent(editParam)}`);
            if (res.ok) {
              const uData = await res.json();
              found = uData.data || uData.datos || uData;
            }
          } catch (e) {
            console.warn("No se pudo cargar usuario por identificador directo:", e);
          }
        }

        if (found) {
          // REGLA: Los usuarios de rol ADMINISTRADOR no pueden editar administradores (exclusivo SUPERADMIN)
          const rolUsuario = String(found.rol || found.nombre_rol || "").trim().toUpperCase();
          const esAdminTarget = rolUsuario === "ADMINISTRADOR" || Number(found.id_rol) === 1 || rolUsuario === "SUPERADMIN" || Number(found.id_rol) === 2;
          const sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
          const miRol = (sesion?.rol || "").trim().toUpperCase();

          if (esAdminTarget && miRol !== "SUPERADMIN") {
            if (typeof window.showToast === "function") {
              window.showToast("Solo un usuario con rol SUPERADMIN puede editar a usuarios administradores.", "error");
            } else {
              alert("Solo un usuario con rol SUPERADMIN puede editar a usuarios administradores.");
            }
            if (typeof puedeModulo === 'function' && puedeModulo('usuarios')) {
              window.location.replace("/usuarios");
            } else {
              window.location.replace("/dashboard");
            }
            return;
          }

          this.isEdit = true;
          this.editId = Number(found.id || editParam);
          this.form.nombres = found.nombres || found.nombre || "";
          this.form.apellidos = found.apellidos || found.apellido || "";
          this.form.tipo_documento = found.tipo_documento || found.tipoDoc || "Cédula de ciudadanía";
          this.form.num_documento = String(found.num_documento || found.identificacion || found.documento || "");
          this.form.num_telefono = String(found.num_telefono || found.telefono || found.celular || "");
          this.form.correo = found.correo || found.email || "";
          this.form.rol = found.id_rol || (found.rol && found.rol.id ? found.rol.id : found.rol) || "";
          this.form.is_active = found.is_active === 1 || found.is_active === true || found.is_active === "1";

          // Cargar plantas asignadas (ÚNICAMENTE si el rol es SST o GESCO)
          let pIds = [];
          if (this.esRolConPlantas()) {
            if (Array.isArray(found.plantas_ids) && found.plantas_ids.length > 0) {
              pIds = found.plantas_ids.map(Number);
            } else if (Array.isArray(found.plantas) && found.plantas.length > 0) {
              pIds = found.plantas.map(p => Number(p.id || p.id_planta || p)).filter(Boolean);
            }
          }
          this.form.plantas_ids = pIds;
        }
      }
      this.cargando = false;
    },

    async getRoles() {
      try {
        const rol = await fetch(`${API.roles}/getall`);
        if (!rol.ok) throw new Error(`HTTP ${rol.status}`);
        const data = await rol.json();
        let listaRoles = Array.isArray(data) ? data : (data.datos || data.data || []);

        // REGLA: Solo SUPERADMIN puede crear o asignar usuarios con rol ADMINISTRADOR
        const sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
        const miRol = (sesion?.rol || "").trim().toUpperCase();

        if (miRol !== "SUPERADMIN") {
          listaRoles = listaRoles.filter(r => {
            const nom = String(r.nombre_rol || "").trim().toUpperCase();
            return nom !== "ADMINISTRADOR" && nom !== "SUPERADMIN";
          });
        }

        this.roles = listaRoles;
      } catch (error) {
        console.error("Error al cargar roles: ", error);
      } 
    },

    async getPlantas() {
      try {
        const res = await fetch(`${API.plantas}/getall`);
        if (res.ok) {
          const data = await res.json();
          this.catalogoPlantas = Array.isArray(data) ? data : (data.datos || data.data || []);
        }
      } catch (error) {
        console.error("Error al cargar catálogo de plantas:", error);
      }
    },

    async getUsers() {
      try {
        const users = await fetch(`${API.usuarios}/getall`);
        const data = await users.json();
        this.allUsers = Array.isArray(data) ? data : (data.datos || data.data || data.datos_user || []);
      } catch (error) {
        console.error("Error al cargar usuarios:", error);
      }
    },

    // ---------------------------------------------------
    // Guardar / Actualizar Usuario
    // ---------------------------------------------------
    async saveUsuario() {
      if (!this.validateUser()) return;

      const nombres = String(this.form.nombres || "").trim();
      const apellidos = String(this.form.apellidos || "").trim();
      const tipo_documento = String(this.form.tipo_documento || "").trim();
      const num_documento = String(this.form.num_documento || "").trim();
      const num_telefono = String(this.form.num_telefono || "").trim();
      const correo = String(this.form.correo || "").trim();
      const id_rol = Number(this.form.rol);
      const contrasena = String(this.form.contrasena || "").trim();
      const plantas_ids = this.esRolConPlantas() ? this.form.plantas_ids.map(Number) : [];

      this.guardandoUsuario = true;

      const usuarioData = {
        nombres: nombres,
        apellidos: apellidos,
        tipo_documento: tipo_documento,
        num_documento: num_documento,
        num_telefono: num_telefono,
        correo: correo,
        id_rol: id_rol,
        plantas_ids: plantas_ids,
        is_active: this.form.is_active === 1 || this.form.is_active === true || this.form.is_active === "1"
      };

      try {
        if (this.isEdit && this.editId) {
          // ================= MODO EDICIÓN =================
          const sesion = (typeof getAuthSession === "function") ? getAuthSession() : null;
          const miRol = (sesion?.rol || "").trim().toUpperCase();
          if (id_rol === 1 && miRol !== "SUPERADMIN") {
            throw new Error("Solo un usuario con rol SUPERADMIN puede gestionar usuarios administradores.");
          }

          const payload = { ...usuarioData };
          if (this.cambiarContrasena && contrasena) {
            payload.contrasena = contrasena;
          }

          let response = await fetch(`${API.usuarios}/${this.editId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });

          if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || errData.mensaje || `HTTP ${response.status}`);
          }

          const data = await response.json().catch(() => ({}));
          console.log("Usuario actualizado exitosamente:", data);

        } else {
          // ================= MODO CREACIÓN =================
          const payload = {
            ...usuarioData,
            contrasena: contrasena
          };

          const response = await fetch(`${API.usuarios}/post`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });

          if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            let detalle = errData.detail || errData.mensaje || `HTTP ${response.status}`;
            if (typeof detalle === "object") {
              try { detalle = JSON.stringify(detalle); } catch (e) {}
            }
            throw new Error(detalle);
          }

          const data = await response.json();
          console.log("Usuario creado exitosamente:", data);
        }

        this.submitted = true;
        setTimeout(() => {
          if (typeof puedeModulo === 'function' && puedeModulo('usuarios')) {
            window.location.href = "/usuarios";
          } else {
            window.location.href = "/dashboard";
          }
        }, 1400);

      } catch (error) {
        console.error("Error al guardar usuario en backend:", error);
        alert(`Error al ${this.isEdit ? 'actualizar' : 'crear'} usuario: ${error.message}`);
        this.guardandoUsuario = false;
      }
    },

    submitForm() {
      return this.saveUsuario();
    },

    // ---------------------------------------------------
    // Validación
    // ---------------------------------------------------
    validateUser() {
      this.errors = {};

      const nombres = String(this.form.nombres || "").trim();
      const apellidos = String(this.form.apellidos || "").trim();
      const tipo_documento = String(this.form.tipo_documento || "").trim();
      const num_documento = String(this.form.num_documento || "").trim();
      const num_telefono = String(this.form.num_telefono || "").trim();
      const correo = String(this.form.correo || "").trim();
      const id_rol = this.form.rol;

      if (!nombres) this.errors.nombres = "Este campo es obligatorio.";
      if (!apellidos) this.errors.apellidos = "Este campo es obligatorio.";
      if (!tipo_documento) this.errors.tipo_documento = "Este campo es necesario.";

      // Validación de documento
      if (!num_documento) {
        this.errors.num_documento = "Ingresa un número de documento.";
      } else {
        const documentoDuplicado = this.allUsers.some(
          u => String(u.num_documento || u.identificacion || "").trim() === num_documento && 
          Number(u.id) !== Number(this.editId)
        );
        if (documentoDuplicado) {
          this.errors.num_documento = "Ya existe un usuario con este documento.";
        }
      }
      
      // Validación de rol
      if (!id_rol) {
        this.errors.rol = "Selecciona un rol.";
      }

      // Validación de plantas obligatorias ÚNICAMENTE para SST y GESCO
      if (this.esRolConPlantas()) {
        if (!this.form.plantas_ids || this.form.plantas_ids.length === 0) {
          this.errors.plantas_ids = "Debes asignar al menos una planta para usuarios con rol SST o GESCO.";
        }
      } else {
        if (this.errors.plantas_ids) delete this.errors.plantas_ids;
      }

      // Validación de teléfono
      if (!num_telefono) {
        this.errors.num_telefono = "Este campo es obligatorio.";
      } else {
        const tiene10Digitos = num_telefono.length === 10 && /^\d+$/.test(num_telefono);
        const empiezaPor3 = num_telefono.startsWith("3");

        if (!empiezaPor3 && !tiene10Digitos) {  
          this.errors.num_telefono = "El teléfono debe comenzar con 3 y tener exactamente 10 dígitos.";
        } else if (!empiezaPor3) {
          this.errors.num_telefono = "El número de teléfono debe comenzar con el dígito 3.";
        } else if (!tiene10Digitos) {
          this.errors.num_telefono = "El número de teléfono debe tener exactamente 10 dígitos.";
        }
      }

      // Validación de correo
      if (!correo) {
        this.errors.correo = "Ingresa un correo.";
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo)) {
        this.errors.correo = "El formato de correo no es válido.";
      } else {
        const correoDuplicado = this.allUsers.some(
          c => String(c.correo || "").trim().toLowerCase() === correo.toLowerCase() &&
          Number(c.id) !== Number(this.editId)
        );

        if (correoDuplicado) {
          this.errors.correo = "Ya existe un usuario con este correo.";
        }
      }
      
      if (!this.isEdit || this.cambiarContrasena) {
        const contrasena = String(this.form.contrasena || "");
        const confirmarContrasena = String(this.form.confirmarContrasena || "");

        if (!contrasena || contrasena.length < 8) {
          this.errors.contrasena = "La contraseña debe tener al menos 8 caracteres.";
        } 
        if (contrasena !== confirmarContrasena) {
          this.errors.confirmarContrasena = "Las contraseñas no coinciden.";
        }
      }

      return Object.keys(this.errors).length === 0;
    }
  };
}
