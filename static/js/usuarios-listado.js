/**
 * usuarios-listado.js
 * Componente Alpine.js de la tabla de Usuarios: búsqueda, filtros,
 * paginación y acciones (editar / activar-desactivar / eliminar).
 * Conectado directamente a las APIs REST del backend (FastAPI).
 */ 

function usuariosCards() {
  return {
    totalActivos: 0,
    totalInactivos: 0,
    cargando: true,

    init() {
      window.addEventListener("usuarios-updated", (e) => {
        const list = e.detail || [];
        this.actualizarConteo(list);
      });
      this.cargarInicial();
    },

    actualizarConteo(lista) {
      this.totalActivos = lista.filter(u => u.is_active === 1 || u.is_active === true || u.is_active === "1").length;
      this.totalInactivos = lista.filter(u => u.is_active === 0 || u.is_active === false || u.is_active === "0").length;
      this.cargando = false;
    },

    async cargarInicial() {
      this.cargando = true;

      try {
        const res = await fetch(`${API.usuarios}/getall`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        
        const data = await res.json();
        const usuarios = Array.isArray(data) ? data : (data.datos || data.data || []);
        this.actualizarConteo(usuarios);

      } catch (error) {
        console.warn("Aviso al consultar usuarios para tarjetas:", error.message);
        this.actualizarConteo([]);
      } finally {
        this.cargando = false;
      }
    },

    get totalUsuarios() {
      return this.totalActivos + this.totalInactivos;
    }
  };
}

function usuariosTable() {
  return {
    // ---------------------------------------------------
    // Datos
    // ---------------------------------------------------
    usuarios: [],
    roles: [],

    // ---------------------------------------------------
    // Filtros / búsqueda
    // ---------------------------------------------------
    search: "",
    filtroRol: "",
    filtroEstado: "todos", // todos | activos | inactivos

    // ---------------------------------------------------
    // Paginación
    // ---------------------------------------------------
    currentPage: 1,
    pageSize: 5,

    // ---------------------------------------------------
    // Detalle de usuario
    // ---------------------------------------------------
    showDetailModal: false,
    usuarioDetalle: null,

    // ---------------------------------------------------
    // Modal de Plantas
    // ---------------------------------------------------
    showPlantasModal: false,
    usuarioPlantasModal: null,

    // ---------------------------------------------------
    // Eliminación
    // ---------------------------------------------------
    showDeleteModal: false,
    deleteModalOpen: false,
    usuarioAEliminar: null,

    // ---------------------------------------------------
    // Inicialización
    // ---------------------------------------------------
    async init() {

      await Promise.allSettled([
        this.getUsers(),
        this.getRoles(),        
      ]);
      
      this.$watch("search", () => (this.currentPage = 1));
      this.$watch("filtroRol", () => (this.currentPage = 1));
      this.$watch("filtroEstado", () => (this.currentPage = 1));
    },

    // ---------------------------------------------------
    // Datos derivados
    // ---------------------------------------------------

    notificarCambio() {
      window.dispatchEvent(new CustomEvent("usuarios-updated", { detail: this.usuarios }));
    },

    async getUsers() {
      try {
        const user = await fetch(`${API.usuarios}/getall`);
        if(!user.ok) throw new Error(`HTTP ${user.status}`);
        const data = await user.json();
        const raw = Array.isArray(data) ? data : (data.datos || data.data || []);
        // Excluir cuentas SUPERADMIN del listado estándar de usuarios
        this.usuarios = raw.filter(u => String(u.rol || '').trim().toUpperCase() !== 'SUPERADMIN');
        this.notificarCambio();
      } catch (error) {
        console.error("Error al cargar usuarios: ", error);
      }
    },

    async getRoles(){
      try {
        const response = await fetch(`${API.roles}/getall`);
        if(!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        const rawRoles = Array.isArray(data) ? data : (data.data || []);
        // Excluir rol SUPERADMIN del filtro de roles de usuarios
        this.roles = rawRoles.filter(r => String(r.nombre_rol || '').trim().toUpperCase() !== 'SUPERADMIN');
      } catch (error) {
        console.error("Error al cargar roles: ", error);
      }
    },


    get usuariosFiltrados() {
      const texto = this.search.trim().toLowerCase();
      return this.usuarios.filter(u => {
        if (!u) return false;
        const nombreCompleto = `${u.nombres || ''} ${u.apellidos || ''}`.toLowerCase();
        const numDoc = String(u.num_documento || '').toLowerCase();
        const correo = String(u.correo || '').toLowerCase();
        const telefono = String(u.num_telefono || '').toLowerCase();
        const rol = String(u.rol || u.nombre_rol || '').toLowerCase();

        const matchTexto =
          !texto ||
          nombreCompleto.includes(texto) ||
          numDoc.includes(texto) ||
          correo.includes(texto) ||
          telefono.includes(texto) ||
          rol.includes(texto);

        const matchRol = !this.filtroRol || String(u.id_rol) === String(this.filtroRol);
        const isActive = u.is_active === 1 || u.is_active === true || u.is_active === "1";
        const matchEstado =
          this.filtroEstado === "todos" ||
          (this.filtroEstado === "activos" && isActive) ||
          (this.filtroEstado === "inactivos" && !isActive);

        return matchTexto && matchRol && matchEstado;
      });
    },

    get totalUsuarios() {
      return this.usuarios.length;
    },
    get totalActivos() {
      return this.usuarios.filter(u => u.is_active === 1 || u.is_active === true || u.is_active === "1").length;
    },
    get totalInactivos() {
      return this.usuarios.filter(u => u.is_active === 0 || u.is_active === false || u.is_active === "0").length;
    },

    get totalPaginas() {
      return Math.max(1, Math.ceil(this.usuariosFiltrados.length / this.pageSize));
    },
    get usuariosPagina() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.usuariosFiltrados.slice(start, start + this.pageSize);
    },
    get rangoMostrado() {
      if (this.usuariosFiltrados.length === 0) return "0 de 0";
      const start = (this.currentPage - 1) * this.pageSize + 1;
      const end = Math.min(this.currentPage * this.pageSize, this.usuariosFiltrados.length);
      return `${start}–${end} de ${this.usuariosFiltrados.length}`;
    },
    get paginasVisibles() {
      const total = this.totalPaginas;
      let startP = Math.max(1, this.currentPage - 2);
      let endP = Math.min(total, startP + 4);
      startP = Math.max(1, endP - 4);
      const pages = [];
      for (let i = startP; i <= endP; i++) pages.push(i);
      return pages;
    },

    get esSuperAdmin() {
      try {
        const sesion = (typeof getAuthSession === "function") ? getAuthSession() : 
                       JSON.parse(sessionStorage.getItem("incarsa_session") || localStorage.getItem("incarsa_session") || "null");
        const miRol = String(sesion?.rol || sesion?.nombre_rol || "").trim().toUpperCase();
        const idRol = Number(sesion?.id_rol || sesion?.rol_id || 0);
        return miRol === "SUPERADMIN" || idRol === 2;
      } catch (e) {
        return false;
      }
    },

    puedeGestionar(usuario) {
      if (!usuario) return false;
      const rolTarget = String(usuario.rol || usuario.nombre_rol || "").trim().toUpperCase();
      const idRol = Number(usuario.id_rol);
      const esAdminTarget = rolTarget === "ADMINISTRADOR" || idRol === 1 || rolTarget === "SUPERADMIN" || idRol === 2;
      
      // Los roles regulares (GESCO, SST, VIGILANTE, GESTIÓN DOCUMENTAL, SCR, etc.)
      // pueden ser editados y activados/desactivados por el Administrador
      if (!esAdminTarget) return true;

      // Si el usuario en la fila es un Administrador, función ÚNICA de SUPERADMIN
      return this.esSuperAdmin;
    },
    rolNombre(idRolONombre) {
      if (!idRolONombre && idRolONombre !== 0) return "—";
      if (typeof idRolONombre === "string" && isNaN(Number(idRolONombre))) {
        return idRolONombre;
      }
      const rol = this.roles.find(r => r.id === Number(idRolONombre));
      return rol ? rol.nombre_rol : (typeof idRolONombre === "string" ? idRolONombre : "—");
    },
    rolClase(rolONombre) {
      const r = String(rolONombre || "").toUpperCase();
      if (r.includes("ADMIN")) return "status-rol-admin";
      if (r.includes("GESCO")) return "status-rol-gesco";
      if (r.includes("SST")) return "status-rol-sst";
      if (r.includes("VIGILANTE")) return "status-rol-vigilante";
      if (r.includes("SCR")) return "status-rol-scr";
      if (r.includes("DOCUMENTAL")) return "status-rol-documental";
      return "status-rol-default";
    },
    getPlantasUsuario(usuario) {
      if (!usuario) return [];
      if (Array.isArray(usuario.plantas)) return usuario.plantas;
      return [];
    },
    rolDescripcion(idRolONombre) {
      if (!idRolONombre && idRolONombre !== 0) return "—";
      const rol = this.roles.find(r => 
        r.id === Number(idRolONombre) || 
        (r.nombre_rol && r.nombre_rol.toLowerCase() === String(idRolONombre).toLowerCase())
      );
      return rol && rol.descripcion ? rol.descripcion : (rol ? rol.nombre_rol : idRolONombre);
    },
    esRolSSToGESCO(usuario) {
      if (!usuario) return false;
      const rolTexto = String(usuario.rol || usuario.nombre_rol || "").toUpperCase();
      if (rolTexto.includes("SST") || rolTexto.includes("GESCO")) return true;
      const rolId = Number(usuario.id_rol);
      const rolObj = (this.roles || []).find(r => Number(r.id) === rolId);
      if (rolObj) {
        const nom = String(rolObj.nombre_rol || "").trim().toUpperCase();
        return nom === "SST" || nom === "GESCO";
      }
      return rolId === 6 || rolId === 7;
    },
    formatearFecha(fechaStr) {
      if (!fechaStr) return "No registrada";
      try {
        const fecha = new Date(fechaStr);
        if (isNaN(fecha.getTime())) return fechaStr;
        return fecha.toLocaleDateString("es-CO", {
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit"
        });
      } catch {
        return fechaStr;
      }
    },

    // ---------------------------------------------------
    // Paginación
    // ---------------------------------------------------
    resetPage() {
      this.currentPage = 1;
    },
    goToPage(n) {
      if (n >= 1 && n <= this.totalPaginas) this.currentPage = n;
    },
    prevPage() {
      this.goToPage(this.currentPage - 1);
    },
    nextPage() {
      this.goToPage(this.currentPage + 1);
    },

    // ---------------------------------------------------
    // Filtros
    // ---------------------------------------------------
    limpiarFiltros() {
      this.search = "";
      this.filtroRol = "";
      this.filtroEstado = "todos";
      this.currentPage = 1;
    },

    // ---------------------------------------------------
    // Acciones
    // ---------------------------------------------------
    async toggleActivo(usuario) {
      if (!this.puedeGestionar(usuario)) {
        if (typeof window.showToast === "function") {
          window.showToast("Solo un usuario con rol SUPERADMIN puede modificar administradores.", "warning");
        } else {
          alert("Solo un usuario con rol SUPERADMIN puede modificar administradores.");
        }
        return;
      }

      const nuevoEstado = !(usuario.is_active === 1 || usuario.is_active === true || usuario.is_active === "1");
      usuario.is_active = nuevoEstado;
      const idx = this.usuarios.findIndex(u => u.id === usuario.id);
      if (idx > -1) this.usuarios[idx].is_active = nuevoEstado;

      this.notificarCambio();

      try {
        const res = await fetch(`${API.usuarios}/${usuario.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_active: nuevoEstado })
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          console.warn(`Error al actualizar estado en backend (HTTP ${res.status}):`, errData);
          if (typeof window.showToast === "function") {
            window.showToast(errData.detail || "No se pudo actualizar el estado del usuario.", "error");
          }
          // Revertir cambio local
          usuario.is_active = !nuevoEstado;
          if (idx > -1) this.usuarios[idx].is_active = !nuevoEstado;
          this.notificarCambio();
        }
      } catch (err) {
        console.error("Error en PATCH de usuario:", err);
      }
    },

    verUsuario(usuario) {
      this.usuarioDetalle = usuario;
      this.showDetailModal = true;
    },
    cerrarDetalle() {
      this.showDetailModal = false;
      this.usuarioDetalle = null;
    },

    abrirModalPlantas(usuario) {
      this.usuarioPlantasModal = usuario;
      this.showPlantasModal = true;
    },
    cerrarModalPlantas() {
      this.showPlantasModal = false;
      this.usuarioPlantasModal = null;
    },

    confirmarEliminar(usuario) {
      if (!this.esSuperAdmin) {
        if (typeof window.showToast === "function") {
          window.showToast("La eliminación de cuentas es una función exclusiva del rol SUPERADMIN. Desactive la cuenta si desea suspender su acceso.", "warning");
        } else {
          alert("La eliminación de cuentas es una función exclusiva del rol SUPERADMIN.");
        }
        return;
      }
      this.usuarioAEliminar = usuario;
      this.showDeleteModal = true;
      this.deleteModalOpen = true;
    },
    confirmDelete(usuario) {
      this.confirmarEliminar(usuario);
    },
    cancelarEliminar() {
      this.usuarioAEliminar = null;
      this.showDeleteModal = false;
      this.deleteModalOpen = false;
    },
    cancelDelete() {
      this.cancelarEliminar();
    },
    executeDelete() {
      return this.eliminarUsuario();
    },
    async eliminarUsuario() {
      if (!this.usuarioAEliminar) return;
      if (!this.esSuperAdmin) {
        if (typeof window.showToast === "function") {
          window.showToast("Solo un usuario con rol SUPERADMIN puede eliminar usuarios.", "error");
        } else {
          alert("Solo un usuario con rol SUPERADMIN puede eliminar usuarios.");
        }
        this.cancelarEliminar();
        return;
      }
      const id = this.usuarioAEliminar.id;
      
      // Cerrar modal de inmediato reseteando todas las banderas
      this.cancelarEliminar();

      // Eliminación optimista local
      this.usuarios = this.usuarios.filter(u => u.id !== id);
      this.notificarCambio();
      if (this.currentPage > this.totalPaginas) this.currentPage = Math.max(1, this.totalPaginas);

      try {
        const res = await fetch(`${API.usuarios}/${id}`, {
          method: "DELETE"
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          console.warn(`Error al eliminar usuario en backend (HTTP ${res.status}):`, data);
          if (typeof window.showToast === "function") {
            window.showToast(data.detail || "No se pudo eliminar el usuario.", "error");
          }
          await this.getUsers();
        } else if (data.desactivado_por_fk) {
          if (typeof window.showToast === "function") {
            window.showToast(data.mensaje || "El usuario posee solicitudes históricas; fue desactivado permanentemente para proteger la trazabilidad.", "info");
          }
          await this.getUsers();
        }
      } catch (err) {
        console.error("Error en DELETE de usuario:", err);
        await this.getUsers();
      }
    }
  };
}
