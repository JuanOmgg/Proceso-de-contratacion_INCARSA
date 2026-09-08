/**
 * dashboard-charts.js — Módulo de Visualización y Gráficos del Dashboard (INCARSA)
 * 
 * Gestiona:
 * - Gráfico circular de Solicitudes creadas por mes (últimos 6 meses).
 * - Gráfico circular de Distribución de usuarios por rol (activos).
 * - Adaptación automática y reactiva a cambios de tema (Dark Mode / Light Mode).
 * - Restricción automática: solo se ejecuta para ADMINISTRADOR y SUPERADMIN.
 */

(function () {
  'use strict';

  let chartMonthsInstance = null;
  let chartRolesInstance = null;

  function getChartThemeConfig() {
    const isDark = document.documentElement.classList.contains('dark') || localStorage.getItem('darkMode') === 'true';

    // Paleta neón luminosa y armoniosa para modo oscuro
    const darkPalette = [
      "#00f0ff", // Cian Neón Eléctrico (INCARSA)
      "#c084fc", // Púrpura / Violeta Neón (MILPA)
      "#00ff9d", // Verde Esmeralda Neón (UNIMINAS)
      "#ffb700", // Ámbar / Oro Neón (CARBOINSA)
      "#ff2a55", // Carmesí / Rojo Neón
      "#38bdf8", // Azul Cielo Neón
      "#f43f5e", // Rosa Neón
      "#a855f7"  // Púrpura Eléctrico
    ];

    // Paleta corporativa sólida para modo claro
    const lightPalette = [
      "#109ea9ff", // Azul Teal Corporativo
      "#a24ff0ff", // Púrpura
      "#16c857ff", // Verde Esmeralda
      "#f18811ff", // Ámbar
      "#e72626ff", // Rojo Carmesí
      "#0791d6ff", // Azul Cielo
      "#f97316"  // Naranja
    ];

    return {
      isDark,
      palette: isDark ? darkPalette : lightPalette,
      borderColor: isDark ? "#1e1e1e" : "#ffffff",
      borderWidth: 2.5,
      legendColor: isDark ? "#cbd5e1" : "#475569",
      tooltipBg: isDark ? "rgba(18, 18, 22, 0.95)" : "#0f172a",
      tooltipBorder: isDark ? "rgba(255, 255, 255, 0.15)" : "#334155",
      tooltipTitle: "#ffffff",
      tooltipBody: isDark ? "#cbd5e1" : "#f1f5f9"
    };
  }

  function syncDashboardChartsTheme() {
    const cfg = getChartThemeConfig();
    [chartMonthsInstance, chartRolesInstance].forEach(chart => {
      if (chart) {
        chart.data.datasets.forEach(ds => {
          ds.backgroundColor = cfg.palette;
          ds.borderColor = cfg.borderColor;
          ds.borderWidth = cfg.borderWidth;
        });
        if (chart.options.plugins) {
          if (chart.options.plugins.legend && chart.options.plugins.legend.labels) {
            chart.options.plugins.legend.labels.color = cfg.legendColor;
          }
          if (chart.options.plugins.tooltip) {
            chart.options.plugins.tooltip.backgroundColor = cfg.tooltipBg;
            chart.options.plugins.tooltip.borderColor = cfg.tooltipBorder;
            chart.options.plugins.tooltip.titleColor = cfg.tooltipTitle;
            chart.options.plugins.tooltip.bodyColor = cfg.tooltipBody;
          }
        }
        chart.update();
      }
    });
  }

  async function initDashboardCharts() {
    const esAdminOSuper = (typeof window.tieneRol === "function")
      ? window.tieneRol('ADMINISTRADOR', 'SUPERADMIN')
      : false;

    // Si el usuario no es Administrador ni SuperAdmin, no cargar ni renderizar las gráficas
    if (!esAdminOSuper) {
      return;
    }

    if (typeof Chart === 'undefined') {
      console.warn('⚠️ Chart.js no está disponible en la página.');
      return;
    }

    const cfg = getChartThemeConfig();
    const apiUrlSolicitudes = (typeof API !== 'undefined' && API.solicitudes) ? API.solicitudes : '/api/v1/solicitudes';
    const apiUrlUsuarios = (typeof API !== 'undefined' && API.usuarios) ? API.usuarios : '/api/v1/usuarios';

    async function graficoMeses() {
      try {
        const MonthCount = await fetch(`${apiUrlSolicitudes}/fechasCount`);
        if (!MonthCount.ok) throw new Error("Error HTTP: " + MonthCount.status);

        const dataF = await MonthCount.json();
        const mes = dataF.map(df => df.month);
        const total = dataF.map(df => df.total);

        const monthCtx = document.getElementById("chartMonths");
        if (monthCtx && dataF.length > 0) {
          if (chartMonthsInstance) {
            chartMonthsInstance.destroy();
          }
          chartMonthsInstance = new Chart(monthCtx, {
            type: "pie",
            data: {
              labels: mes,
              datasets: [{
                data: total,
                backgroundColor: cfg.palette,
                borderColor: cfg.borderColor,
                borderWidth: cfg.borderWidth
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              animation: {
                animateScale: true,
                animateRotate: true,
                duration: 1200,
                easing: 'easeInOutQuad',
              },
              hover: {
                animationDuration: 250
              },
              plugins: {
                legend: {
                  position: "bottom",
                  labels: {
                    boxWidth: 12,
                    font: { size: 11.5, weight: '600' },
                    color: cfg.legendColor,
                    padding: 14
                  }
                },
                tooltip: {
                  backgroundColor: cfg.tooltipBg,
                  borderColor: cfg.tooltipBorder,
                  borderWidth: 1,
                  titleColor: cfg.tooltipTitle,
                  bodyColor: cfg.tooltipBody,
                  padding: 10,
                  cornerRadius: 8
                }
              }
            }
          });
        }
      } catch (error) {
        console.error('❌ Error al cargar la gráfica de meses:', error);
      }
    }

    async function graficoRoles() {
      try {
        const Count = await fetch(`${apiUrlUsuarios}/usuarios/conteo-por-rol`);
        if (!Count.ok) throw new Error("Error HTTP: " + Count.status);

        const rawDatas = await Count.json();
        const datas = Array.isArray(rawDatas)
          ? rawDatas.filter(dat => String(dat.rol || '').trim().toUpperCase() !== 'SUPERADMIN')
          : [];
        const ticket = datas.map(dat => dat.rol);
        const value = datas.map(dat => dat.total);

        const rolesCtx = document.getElementById("chartRoles");
        if (rolesCtx && datas.length > 0) {
          if (chartRolesInstance) {
            chartRolesInstance.destroy();
          }
          chartRolesInstance = new Chart(rolesCtx, {
            type: "pie",
            data: {
              labels: ticket,
              datasets: [{
                data: value,
                backgroundColor: cfg.palette,
                borderColor: cfg.borderColor,
                borderWidth: cfg.borderWidth
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              animation: {
                animateScale: true,
                animateRotate: true,
                duration: 1200,
                easing: 'easeInOutQuad',
              },
              hover: {
                animationDuration: 250
              },
              plugins: {
                legend: {
                  position: "bottom",
                  labels: {
                    boxWidth: 12,
                    font: { size: 11.5, weight: '600' },
                    color: cfg.legendColor,
                    padding: 14
                  }
                },
                tooltip: {
                  backgroundColor: cfg.tooltipBg,
                  borderColor: cfg.tooltipBorder,
                  borderWidth: 1,
                  titleColor: cfg.tooltipTitle,
                  bodyColor: cfg.tooltipBody,
                  padding: 10,
                  cornerRadius: 8
                }
              }
            }
          });
        }
      } catch (error) {
        console.error('❌ Error al cargar la gráfica de roles:', error);
      }
    }

    await Promise.allSettled([graficoMeses(), graficoRoles()]);

    // Escuchar cambios de tema en el elemento raíz <html> para actualización reactiva en tiempo real
    if (!window._chartThemeObserverAttached) {
      window._chartThemeObserverAttached = true;
      const observer = new MutationObserver(mutations => {
        for (const mutation of mutations) {
          if (mutation.attributeName === 'class') {
            syncDashboardChartsTheme();
            break;
          }
        }
      });
      observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    }
  }

  // Exponer utilidades por si se requieren invocar manualmente
  window.initDashboardCharts = initDashboardCharts;
  window.syncDashboardChartsTheme = syncDashboardChartsTheme;

  if (document.readyState === 'loading') {
    document.addEventListener("DOMContentLoaded", initDashboardCharts);
  } else {
    initDashboardCharts();
  }
})();
