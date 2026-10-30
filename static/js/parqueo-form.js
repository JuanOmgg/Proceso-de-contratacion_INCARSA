/**
 * ============================================================================
 * parqueo-form.js — Formulario Externo / Público de Parqueos Nocturnos (INCARSA)
 * ============================================================================
 * Formulario público para vigilantes y personal de turno:
 * - No requiere autenticación ni inicio de sesión.
 * - Permite seleccionar la zona a reportar, fecha y nombre de quien reporta.
 * - Carga automáticamente los vehículos asignados a esa zona para marcar SÍ / NO.
 * - Permite añadir vehículos de otras zonas que hayan pernoctado allí esa noche.
 * - Guarda el reporte y muestra pantalla de confirmación inmediata.
 */

function reporteParqueoPublico() {
  return {
    submitting: false,
    submitted: false,
    error: '',
    resultado: null,

    // Datos del formulario
    zonasDisponibles: ['UBATÉ', 'SAMACÁ', 'VALDERRAMA'],
    form: {
      fecha: new Date().toISOString().split('T')[0],
      zona: '',
      reportador: '',
      observaciones: '',
      vehiculos: [] // { id_vehiculo, vehiculo, zona_asignada, se_quedo: bool, es_foraneo: bool, observacion: '' }
    },

    // Vehículos asignados, catálogo general y buscador
    cargandoVehiculos: false,
    otrosVehiculosDisponibles: [],
    todosLosVehiculos: [],
    vehiculosYaReportados: {},
    busquedaGeneral: '',
    mostrarDropdownBusqueda: false,

    esDeEstaZona(zona) {
      return (zona || '').trim().toUpperCase() === (this.form.zona || '').trim().toUpperCase();
    },

    estaEnLista(placa) {
      const p = (placa || '').trim().toUpperCase();
      return this.form.vehiculos.some(x => (x.vehiculo || '').toUpperCase() === p);
    },

    get vehiculosListado() {
      const query = (this.busquedaGeneral || '').trim().toUpperCase();
      if (!query) return this.form.vehiculos;
      return this.form.vehiculos.filter(v => 
        (v.vehiculo || '').toUpperCase().includes(query) ||
        (v.zona_asignada && v.zona_asignada.toUpperCase().includes(query)) ||
        (v.descripcion && v.descripcion.toUpperCase().includes(query))
      );
    },

    get vehiculosFiltrados() {
      const query = (this.busquedaGeneral || '').trim().toUpperCase();
      // Solo deben aparecer disponibles vehículos que no hayan pernoctado en ninguna zona
      const disponibles = (this.todosLosVehiculos || []).filter(v => 
        !this.vehiculosYaReportados || !this.vehiculosYaReportados[v.placa.toUpperCase()]
      );

      if (!query) {
        const enLista = new Set(this.form.vehiculos.map(x => (x.vehiculo || '').toUpperCase()));
        const noEnLista = disponibles.filter(v => !enLista.has(v.placa.toUpperCase()));
        return noEnLista.length > 0 ? noEnLista : disponibles;
      }
      return disponibles.filter(v => 
        v.placa.toUpperCase().includes(query) || 
        (v.zona && v.zona.toUpperCase().includes(query)) ||
        (v.descripcion && v.descripcion.toUpperCase().includes(query))
      );
    },

    // Compatibilidad
    get foraneosFiltrados() {
      return this.vehiculosFiltrados;
    },

    get fechaActualFormateada() {
      try {
        const hoy = new Date();
        const opciones = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        const str = hoy.toLocaleDateString('es-CO', opciones);
        return str.charAt(0).toUpperCase() + str.slice(1);
      } catch (e) {
        return new Date().toLocaleDateString();
      }
    },

    async init() {
      await this.cargarZonas();
      if (this.zonasDisponibles.length > 0) {
        this.form.zona = this.zonasDisponibles[0];
        await this.alCambiarZona();
      }
    },

    async cargarZonas() {
      try {
        const res = await fetch('/api/v1/parqueos/zonas');
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data.zonas) && data.zonas.length > 0) {
            this.zonasDisponibles = data.zonas;
          }
        }
      } catch (e) {
        console.warn('Aviso cargando zonas:', e);
      }
    },

    async alCambiarZona() {
      const zona = this.form.zona;
      if (!zona) return;

      this.cargandoVehiculos = true;
      this.error = '';
      try {
        const fecha = this.form.fecha || '';
        const url = `/api/v1/parqueos/vehiculos-por-zona/${encodeURIComponent(zona)}` + (fecha ? `?fecha=${encodeURIComponent(fecha)}` : '');
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          const asignados = data.asignados || [];
          this.otrosVehiculosDisponibles = data.otros_disponibles || [];
          this.todosLosVehiculos = [...asignados, ...this.otrosVehiculosDisponibles];
          this.vehiculosYaReportados = data.vehiculos_ya_reportados || {};

          // Los vehículos NO se precargan; solo se identifican e ingresan a través del buscador
          this.form.vehiculos = [];
        } else {
          throw new Error('No se pudieron cargar los vehículos de la zona.');
        }
      } catch (e) {
        console.error('Error al cargar vehículos de la zona:', e);
        this.error = 'No fue posible cargar el catálogo de vehículos.';
      } finally {
        this.cargandoVehiculos = false;
      }
    },

    marcarTodos(valorBooleano) {
      this.form.vehiculos.forEach(v => {
        v.se_quedo = valorBooleano;
      });
    },

    seleccionarVehiculoGeneral(item) {
      let placa = '';
      let zona = '';
      let idVehiculo = null;
      let descripcion = '';

      if (typeof item === 'object' && item !== null) {
        placa = (item.placa || item.vehiculo || '').trim().toUpperCase();
        zona = item.zona || item.zona_asignada || '';
        idVehiculo = item.id || item.id_vehiculo || null;
        descripcion = item.descripcion || '';
      } else if (typeof item === 'string') {
        placa = item.trim().toUpperCase();
        const enc = (this.todosLosVehiculos || []).find(x => x.placa.toUpperCase() === placa);
        if (enc) {
          zona = enc.zona;
          idVehiculo = enc.id;
          descripcion = enc.descripcion || '';
        } else {
          zona = 'NO REGISTRADO';
        }
      }

      if (!placa) return;

      // Validación preventiva: si ya pernoctó en cualquier zona hoy, advertir y no permitir agregarlo
      if (this.vehiculosYaReportados && this.vehiculosYaReportados[placa]) {
        const rep = this.vehiculosYaReportados[placa];
        const horaTxt = rep.hora ? ` a las ${rep.hora}` : '';
        const repTxt = rep.reportador ? ` (Reportado por: ${rep.reportador})` : '';
        const zonaTxt = rep.zona ? ` en la zona ${rep.zona}` : '';
        alert(`⚠️ ATENCIÓN: El vehículo ${placa} ya fue reportado pernoctando${zonaTxt}${horaTxt}${repTxt}.\n\nSolo es posible registrar vehículos que no hayan pernoctado en ninguna zona hasta el momento.`);
        this.busquedaGeneral = '';
        this.busquedaForaneo = '';
        this.mostrarDropdownBusqueda = false;
        this.mostrarDropdownForaneos = false;
        return;
      }

      if (!zona) {
        const enc = (this.todosLosVehiculos || []).find(x => x.placa.toUpperCase() === placa);
        if (enc) {
          zona = enc.zona;
          idVehiculo = idVehiculo || enc.id;
          descripcion = descripcion || enc.descripcion || '';
        } else {
          zona = 'NO REGISTRADO';
        }
      }

      const esPropio = this.esDeEstaZona(zona);
      const existente = this.form.vehiculos.find(x => (x.vehiculo || '').toUpperCase() === placa);

      if (existente) {
        // Si ya está en la lista, no duplicar
        this.busquedaGeneral = '';
        this.mostrarDropdownBusqueda = false;
        return;
      }

      // Agregar a la lista de vehículos que pernoctaron en el patio
      this.form.vehiculos.unshift({
        id_vehiculo: idVehiculo,
        vehiculo: placa,
        zona_asignada: zona || (esPropio ? this.form.zona : 'OTRA ZONA'),
        descripcion: descripcion,
        se_quedo: true,
        es_foraneo: !esPropio,
        observacion: esPropio ? '' : `Asignado a ${zona || 'otra zona'}`
      });

      this.busquedaGeneral = '';
      this.busquedaForaneo = '';
      this.mostrarDropdownBusqueda = false;
      this.mostrarDropdownForaneos = false;
    },

    onKeydownBuscarGeneral(event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        const filtrados = this.vehiculosFiltrados;
        if (filtrados.length > 0) {
          this.seleccionarVehiculoGeneral(filtrados[0]);
        } else if (this.busquedaGeneral.trim()) {
          this.seleccionarVehiculoGeneral(this.busquedaGeneral.trim());
        }
      } else if (event.key === 'Escape') {
        this.mostrarDropdownBusqueda = false;
      }
    },

    // Aliases para compatibilidad
    adjuntarVehiculoForaneo(item) {
      this.seleccionarVehiculoGeneral(item);
    },

    onKeydownBuscarForaneo(event) {
      this.onKeydownBuscarGeneral(event);
    },

    agregarVehiculoOtro() {
      if (!this.vehiculoOtroSeleccionado) return;
      this.adjuntarVehiculoForaneo(this.vehiculoOtroSeleccionado);
      this.vehiculoOtroSeleccionado = '';
    },

    quitarVehiculo(itemOrIndex) {
      if (typeof itemOrIndex === 'object' && itemOrIndex !== null) {
        const idx = this.form.vehiculos.findIndex(x => (x.vehiculo || '').toUpperCase() === (itemOrIndex.vehiculo || '').toUpperCase());
        if (idx !== -1) this.form.vehiculos.splice(idx, 1);
      } else if (typeof itemOrIndex === 'number') {
        this.form.vehiculos.splice(itemOrIndex, 1);
      }
    },

    async submit() {
      this.error = '';

      if (!this.form.zona) {
        this.error = 'Por favor selecciona la zona a reportar.';
        return;
      }

      if (!this.form.reportador.trim()) {
        this.error = 'Por favor ingresa tu nombre o identificación como reportador de turno.';
        return;
      }

      if (this.form.vehiculos.length === 0) {
        this.error = 'No hay vehículos para evaluar en esta zona.';
        return;
      }

      this.submitting = true;
      try {
        const payload = {
          fecha: this.form.fecha,
          zona: this.form.zona,
          reportador: this.form.reportador.trim(),
          observaciones: this.form.observaciones.trim(),
          vehiculos: this.form.vehiculos.map(v => ({
            id_vehiculo: v.id_vehiculo,
            vehiculo: v.vehiculo,
            zona_asignada: v.zona_asignada,
            se_quedo: v.se_quedo,
            observacion: v.observacion.trim()
          }))
        };

        const res = await fetch('/api/v1/parqueos/reportar-zona', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          throw new Error(data.detail || data.mensaje || 'Error al enviar el reporte.');
        }

        const totalQuedados = this.form.vehiculos.filter(v => v.se_quedo).length;
        const totalNoQuedados = this.form.vehiculos.filter(v => !v.se_quedo).length;

        this.resultado = {
          id_reporte: data.id_reporte,
          zona: this.form.zona,
          fecha: this.form.fecha,
          reportador: this.form.reportador,
          total_quedados: totalQuedados,
          total_no_quedados: totalNoQuedados
        };

        this.submitted = true;

      } catch (err) {
        console.error('Error al enviar reporte:', err);
        this.error = err.message || 'Ocurrió un error al registrar el reporte nocturno.';
      } finally {
        this.submitting = false;
      }
    },

    nuevoReporte() {
      this.submitted = false;
      this.resultado = null;
      this.error = '';
      this.form.observaciones = '';
      this.alCambiarZona();
    }
  };
}
