/**
 * page-transition.js
 * Overlay de transición al navegar entre pantallas del sistema.
 *
 * Uso: incluir en cada página, justo después de abrir <body>,
 * junto con este markup (antes de cualquier otro contenido):
 *
 *   <div id="page-transition-overlay" class="page-transition-overlay">
 *     <div class="loader"></div>
 *   </div>
 *
 * El overlay arranca visible en el HTML (evita el "flash" del
 * contenido mientras carga) y este script lo oculta apenas el
 * DOM está listo. Al hacer clic en un enlace interno (mismo
 * origen, sin target="_blank", sin modificadores de teclado),
 * intercepta la navegación, muestra el overlay y navega poco
 * después para que la transición alcance a verse.
 */
(function () {
  const OVERLAY_ID = "page-transition-overlay";
  const NAV_DELAY_MS = 220;

  function getOverlay() {
    return document.getElementById(OVERLAY_ID);
  }
  function showOverlay() {
    const overlay = getOverlay();
    if (overlay) overlay.classList.remove("is-hidden");
  }
  function hideOverlay() {
    const overlay = getOverlay();
    if (overlay) overlay.classList.add("is-hidden");
  }

  function esEnlaceInternoNavegable(link) {
    if (!link || !link.getAttribute("href")) return false;
    const href = link.getAttribute("href");
    if (href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:")) return false;
    if (link.hasAttribute("download")) return false;
    if (link.target && link.target !== "" && link.target !== "_self") return false;
    try {
      const url = new URL(link.href, window.location.href);
      return url.origin === window.location.origin;
    } catch (e) {
      return false;
    }
  }

  document.addEventListener("click", function (event) {
    if (event.defaultPrevented || event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

    const link = event.target.closest("a[href]");
    if (!esEnlaceInternoNavegable(link)) return;
    if (link.href === window.location.href) return;

    event.preventDefault();
    showOverlay();
    setTimeout(() => {
      window.location.href = link.href;
    }, NAV_DELAY_MS);
  });

  // Ocultar el overlay una vez que la página nueva ya puede verse.
  window.addEventListener("DOMContentLoaded", function () {
    requestAnimationFrame(() => requestAnimationFrame(hideOverlay));
  });

  // Si el navegador restaura la página desde el historial (bfcache),
  // aseguramos que el overlay no quede visible por error.
  window.addEventListener("pageshow", hideOverlay);
})();
