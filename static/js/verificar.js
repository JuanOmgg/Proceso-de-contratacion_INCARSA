/**
 * Verificador de Portería — PSI (Control de Acceso)
 * Lógica reactiva con Alpine.js para la consulta y visualización de solicitudes
 */

function verificadorPorteria(codigoInicial) {
  return {
    codigoInput: codigoInicial || '',
    data: null,
    cargando: false,
    errorMensaje: '',
    filtroIntegrante: '',
    horaEnVivo: '',
    fechaEnVivo: '',

    init() {
      this.iniciarReloj();
      if (this.codigoInput.trim()) {
        this.consultar(this.codigoInput.trim());
      }
    },

    iniciarReloj() {
      const actualizar = () => {
        const ahora = new Date();
        const h = ahora.getHours();
        const m = String(ahora.getMinutes()).padStart(2, '0');
        const s = String(ahora.getSeconds()).padStart(2, '0');
        const ampm = h >= 12 ? 'PM' : 'AM';
        const h12 = String(h % 12 || 12).padStart(2, '0');
        this.horaEnVivo = `${h12}:${m}:${s} ${ampm}`;

        const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        const dia = String(ahora.getDate()).padStart(2, '0');
        const mes = meses[ahora.getMonth()];
        const anio = ahora.getFullYear();
        this.fechaEnVivo = `${dia} ${mes} ${anio}`;
      };
      actualizar();
      setInterval(actualizar, 1000);
    },

    formatearFechaEspanol(fechaStr) {
      if (!fechaStr || fechaStr === '—' || fechaStr === '-') return '—';
      try {
        const raw = String(fechaStr).trim().split('T')[0].split(' ')[0];
        const partes = raw.split('-');
        if (partes.length === 3) {
          const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
          const anio = partes[0];
          const mesIdx = parseInt(partes[1], 10) - 1;
          const dia = partes[2].padStart(2, '0');
          const mesNombre = meses[mesIdx] || partes[1];
          return `${dia} ${mesNombre} ${anio}`;
        }
        return fechaStr;
      } catch (e) {
        return fechaStr;
      }
    },

    formatearPlacaConPunto(placa) {
      if (!placa || placa === '—' || placa === '-') return '—';
      const p = String(placa).trim().toUpperCase();
      const clean = p.replace(/[\s\.\-_]/g, '');
      if (clean.length === 6) {
        return clean.slice(0, 3) + ' · ' + clean.slice(3);
      }
      return p;
    },

    get integrantesFiltrados() {
      if (!this.data || !this.data.integrantes) return [];
      const q = (this.filtroIntegrante || '').trim().toLowerCase();
      if (!q) return this.data.integrantes;
      return this.data.integrantes.filter(p => {
        const nom = (p.nombre_completo || '').toLowerCase();
        const doc = String(p.identificacion || '').toLowerCase();
        return nom.includes(q) || doc.includes(q);
      });
    },

    consultarCodigo() {
      const cod = this.codigoInput.trim();
      if (!cod) return;
      this.consultar(cod);
    },

    async consultar(codigo) {
      this.cargando = true;
      this.errorMensaje = '';
      this.data = null;
      try {
        const res = await fetch(`/api/v1/solicitudes/publico/verificar/${encodeURIComponent(codigo)}`);
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'No se encontró la solicitud especificada.');
        }
        this.data = await res.json();
        // Actualizar URL sin recargar para que se pueda compartir el link
        if (window.history && window.history.replaceState) {
          window.history.replaceState(null, '', `/verificar/${encodeURIComponent(this.data.codigo || codigo)}`);
        }
      } catch (e) {
        this.errorMensaje = e.message || 'Error al conectar con el servidor.';
      } finally {
        this.cargando = false;
      }
    },

    imprimirPase() {
      window.print();
    }
  };
}
