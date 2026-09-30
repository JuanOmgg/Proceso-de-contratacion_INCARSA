/**
 * token-formulario.js
 * Gestor autónomo del Modal "Pase de Diligenciamiento / Token para Terceros"
 * INCARSA - Sistema de Proceso de Contratación
 */

function tokenFormularioManager() {
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
                || window.location.pathname.includes('/superadmin')
                || document.documentElement.getAttribute('data-role') === 'SUPERADMIN'
                || document.documentElement.classList.contains('role-superadmin');
        } catch (e) {
            return false;
        }
    };

    return {
        esSuperAdmin: checkEsSuperAdmin(),
        isOpen: false,
        modalTokenTab: 'crear', // 'crear' | 'historial'
        cargandoTokens: false,
        cargandoContratistas: false,

        // Contratistas para el buscador dinámico tipo wizard
        tokenContratistas: [],
        tokenContratistaId: "",
        tokenContratistaSearch: "",
        tokenBuscadorAbierto: false,

        // Configuración de Vigencia
        tokenModoTiempo: 'rapido', // 'rapido' | 'exacto'
        tokenDuracion: '24',       // horas por defecto
        tokenFechaPersonalizada: "",

        // Resultados y enlaces
        tokenGeneradoUrl: "",
        tokenInfoGenerado: null,
        tokenCopiado: false,
        copiadoToast: false,

        // Historial
        tokensHistorial: [],

        init() {
            // Escuchar evento global para abrir modal desde sidebar u otras vistas
            window.addEventListener('open-token-formulario-modal', (e) => {
                const tab = e && e.detail && e.detail.tab ? e.detail.tab : 'crear';
                this.abrirModal(tab);
            });

            window.addEventListener('abrir-modal-token-formulario', (e) => {
                const tab = e && e.detail && e.detail.tab ? e.detail.tab : 'crear';
                this.abrirModal(tab);
            });

            // Verificar si la URL solicita abrir el modal directamente
            const params = new URLSearchParams(window.location.search);
            if (params.get('modal') === 'token-terceros' || params.get('token_modal') === '1') {
                this.abrirModal('crear');
            }
        },

        async abrirModal(tab = 'crear') {
            this.esSuperAdmin = checkEsSuperAdmin();
            this.isOpen = true;
            this.modalTokenTab = tab;
            this.tokenBuscadorAbierto = false;
            
            // Cargar directorio de contratistas si no están en memoria
            await this.cargarContratistas();

            if (tab === 'historial') {
                await this.cargarHistorialTokens();
            } else if (!this.tokenGeneradoUrl) {
                this.resetFormulario();
            }
        },

        cerrarModal() {
            this.isOpen = false;
            this.tokenBuscadorAbierto = false;
        },

        resetFormulario() {
            this.tokenContratistaId = "";
            this.tokenContratistaSearch = "";
            this.tokenBuscadorAbierto = false;
            this.tokenModoTiempo = 'rapido';
            this.tokenDuracion = '24';
            this.tokenFechaPersonalizada = "";
            this.tokenGeneradoUrl = "";
            this.tokenInfoGenerado = null;
            this.tokenCopiado = false;
        },

        async cargarContratistas() {
            if (this.tokenContratistas && this.tokenContratistas.length > 0) return;
            this.cargandoContratistas = true;
            try {
                const token = typeof getAuthToken === 'function' ? getAuthToken() : null;
                const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
                const endpoint = (typeof API !== 'undefined' && API.contratistas ? API.contratistas : '/emp_contratista');
                let res = await fetch(`${endpoint}/getall`, { headers });
                if (!res.ok) {
                    res = await fetch(`${endpoint}/`, { headers });
                }
                if (res.ok) {
                    const data = await res.json();
                    this.tokenContratistas = Array.isArray(data) ? data : (data.datos || data.data || []);
                }
            } catch (e) {
                console.warn("No se pudieron cargar contratistas para el pase:", e);
                this.tokenContratistas = [];
            } finally {
                this.cargandoContratistas = false;
            }
        },

        contratistasFiltrados() {
            if (!this.tokenContratistas || !Array.isArray(this.tokenContratistas)) return [];
            const term = (this.tokenContratistaSearch || "").trim().toLowerCase();
            if (!term) return this.tokenContratistas.slice(0, 30);
            return this.tokenContratistas.filter(c => {
                const nombre = (c.nombre || c.N_empresa || "").toLowerCase();
                const nit = (c.nit || c.NIT || "").toString().toLowerCase();
                return nombre.includes(term) || nit.includes(term);
            }).slice(0, 30);
        },

        getContratistaSeleccionada() {
            if (!this.tokenContratistaId || !this.tokenContratistas) return null;
            return this.tokenContratistas.find(c => String(c.id) === String(this.tokenContratistaId)) || null;
        },

        seleccionarContratista(empresa) {
            this.tokenContratistaId = empresa.id;
            this.tokenContratistaSearch = empresa.nombre || empresa.N_empresa || "";
            this.tokenBuscadorAbierto = false;
        },

        quitarContratista() {
            this.tokenContratistaId = "";
            this.tokenContratistaSearch = "";
            this.tokenBuscadorAbierto = true;
        },

        fpInstance: null,

        getSignalColor() {
            return getComputedStyle(document.documentElement).getPropertyValue('--signal-500').trim() || '#fa051a';
        },

        initFlatpickrFechaExacta(el) {
            if (typeof flatpickr === "undefined" || !el) return;
            if (el._flatpickr) {
                this.fpInstance = el._flatpickr;
                return;
            }

            const now = new Date();
            now.setMinutes(now.getMinutes() + 15);
            const defDate = new Date();
            defDate.setHours(defDate.getHours() + 24);

            this.fpInstance = flatpickr(el, {
                locale: flatpickr.l10ns?.es || "es",
                enableTime: true,
                time_24hr: false,
                dateFormat: "Y-m-d H:i",
                altInput: true,
                altFormat: "d/m/Y h:i K",
                altInputClass: "input-field flatpickr-input-custom w-full rounded-xl pl-9 pr-10 py-2.5 text-sm bg-white dark:bg-[#1a1a1a] border border-[var(--paper-shadow)] dark:border-white/10 text-[var(--paper-ink)] dark:text-white focus:border-[var(--signal-500)] focus:ring-1 focus:ring-[var(--signal-500)]/20 shadow-xs cursor-pointer font-medium",
                minDate: now,
                defaultDate: this.tokenFechaPersonalizada || defDate,
                disableMobile: true,
                onChange: (selectedDates, dateStr) => {
                    this.tokenFechaPersonalizada = dateStr;
                }
            });

            if (!this.tokenFechaPersonalizada) {
                this.tokenFechaPersonalizada = this.fpInstance.formatDate(defDate, "Y-m-d H:i");
            }
        },

        abrirPickerFechaExacta() {
            if (this.fpInstance) {
                this.fpInstance.open();
            } else if (this.$refs.inputFechaExacta) {
                this.initFlatpickrFechaExacta(this.$refs.inputFechaExacta);
                setTimeout(() => this.fpInstance && this.fpInstance.open(), 50);
            }
        },

        setFechaMinima() {
            this.$nextTick(() => {
                if (this.$refs.inputFechaExacta) {
                    this.initFlatpickrFechaExacta(this.$refs.inputFechaExacta);
                }
            });
        },

        async generarTokenFormulario() {
            const signalColor = this.getSignalColor();

            // Si el usuario escribió el nombre pero no hizo clic en el dropdown, intentar resolverlo
            if (!this.tokenContratistaId && this.tokenContratistaSearch.trim()) {
                const term = this.tokenContratistaSearch.trim().toLowerCase();
                const match = (this.tokenContratistas || []).find(c => {
                    const nom = (c.nombre || c.N_empresa || '').toLowerCase();
                    const nit = (c.nit || c.NIT || '').toString().toLowerCase();
                    return nom === term || nit === term;
                });
                if (match) {
                    this.tokenContratistaId = match.id;
                }
            }

            if (!this.tokenContratistaId) {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Empresa requerida',
                        text: 'Debes buscar y seleccionar la Empresa Contratista para emitir el pase.',
                        confirmButtonColor: signalColor
                    });
                } else {
                    alert('Debes seleccionar la Empresa Contratista.');
                }
                return;
            }

            if (this.tokenModoTiempo === 'exacto' && !this.tokenFechaPersonalizada) {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Fecha requerida',
                        text: 'Por favor define la fecha y hora límite de vigencia del pase.',
                        confirmButtonColor: signalColor
                    });
                } else {
                    alert('Por favor define la fecha límite.');
                }
                return;
            }

            const empresaSel = this.getContratistaSeleccionada();
            const payload = {
                id_empresa_contratista: parseInt(this.tokenContratistaId, 10),
                destinatario_nombre: empresaSel ? (empresaSel.nombre || empresaSel.N_empresa) : null,
                duracion_horas: this.tokenModoTiempo === 'rapido' ? (parseFloat(this.tokenDuracion) || 24.0) : null,
                fecha_expiracion_personalizada: this.tokenModoTiempo === 'exacto' ? this.tokenFechaPersonalizada : null
            };

            const endpoint = (typeof API !== 'undefined' && API.solicitudes ? API.solicitudes : '/api/v1/solicitudes') + '/tokens-formulario';
            const tokenAuth = typeof getAuthToken === 'function' ? getAuthToken() : null;

            this.cargandoTokens = true;
            try {
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(tokenAuth ? { 'Authorization': `Bearer ${tokenAuth}` } : {})
                    },
                    body: JSON.stringify(payload)
                });

                const data = await res.json().catch(() => ({}));
                if (!res.ok || !data.exito) {
                    throw new Error(data.detail || data.mensaje || 'Error al emitir el pase.');
                }

                const datos = data.datos || data;
                this.tokenGeneradoUrl = datos.url_formulario;
                this.tokenInfoGenerado = datos;
                this.tokenCopiado = false;

                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'success',
                        title: '¡Pase Emitido!',
                        text: 'El enlace del formulario ha sido generado correctamente.',
                        confirmButtonColor: signalColor,
                        timer: 1500,
                        timerProgressBar: true
                    });
                }
            } catch (err) {
                console.error("Error al generar token:", err);
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'error',
                        title: 'No se pudo emitir',
                        text: err.message || 'Ocurrió un problema al generar el enlace.',
                        confirmButtonColor: signalColor
                    });
                } else {
                    alert(err.message || 'Error al generar el pase.');
                }
            } finally {
                this.cargandoTokens = false;
            }
        },

        async cargarHistorialTokens() {
            this.cargandoTokens = true;
            const endpoint = (typeof API !== 'undefined' && API.solicitudes ? API.solicitudes : '/api/v1/solicitudes') + '/tokens-formulario';
            const tokenAuth = typeof getAuthToken === 'function' ? getAuthToken() : null;
            try {
                const res = await fetch(endpoint, {
                    headers: {
                        ...(tokenAuth ? { 'Authorization': `Bearer ${tokenAuth}` } : {})
                    }
                });
                const data = await res.json();
                if (res.ok && data.exito) {
                    this.tokensHistorial = data.datos || [];
                }
            } catch (e) {
                console.warn("No se pudo cargar el historial de pases:", e);
                this.tokensHistorial = [];
            } finally {
                this.cargandoTokens = false;
            }
        },

        async revocarToken(id) {
            const confirm = typeof Swal !== 'undefined'
                ? await Swal.fire({
                    title: '¿Revocar este pase?',
                    text: 'El enlace dejará de funcionar de inmediato para quien lo tenga.',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#c1443c',
                    cancelButtonColor: '#6c757d',
                    confirmButtonText: 'Sí, revocar pase',
                    cancelButtonText: 'Cancelar'
                }).then(r => r.isConfirmed)
                : window.confirm('¿Deseas revocar este pase temporal?');

            if (!confirm) return;

            const endpoint = (typeof API !== 'undefined' && API.solicitudes ? API.solicitudes : '/api/v1/solicitudes') + `/tokens-formulario/${id}/revocar`;
            const tokenAuth = typeof getAuthToken === 'function' ? getAuthToken() : null;

            try {
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        ...(tokenAuth ? { 'Authorization': `Bearer ${tokenAuth}` } : {})
                    }
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.exito) {
                    await this.cargarHistorialTokens();
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'success',
                            title: 'Pase Revocado',
                            text: 'El enlace ha quedado invalidado permanentemente.',
                            confirmButtonColor: this.getSignalColor(),
                            timer: 2000,
                            showConfirmButton: false
                        });
                    }
                } else {
                    throw new Error(data.detail || data.mensaje || 'No se pudo revocar.');
                }
            } catch (e) {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({ icon: 'error', title: 'Error', text: e.message || 'No fue posible revocar el pase.', confirmButtonColor: this.getSignalColor() });
                } else {
                    alert('Error al revocar el pase.');
                }
            }
        },

        copiarUrlToken(url) {
            if (!url) return;
            navigator.clipboard.writeText(url).then(() => {
                this.tokenCopiado = true;
                this.copiadoToast = true;
                setTimeout(() => {
                    this.tokenCopiado = false;
                    this.copiadoToast = false;
                }, 2800);
            }).catch(() => {
                const temp = document.createElement('input');
                temp.value = url;
                document.body.appendChild(temp);
                temp.select();
                document.execCommand('copy');
                document.body.removeChild(temp);
                this.tokenCopiado = true;
                this.copiadoToast = true;
                setTimeout(() => {
                    this.tokenCopiado = false;
                    this.copiadoToast = false;
                }, 2800);
            });
        }
    };
}
