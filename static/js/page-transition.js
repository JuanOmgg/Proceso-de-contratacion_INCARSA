/**
 * page-transition.js
 * Pantalla de carga y transición fluida entre páginas del sistema.
 */
(function () {
  const OVERLAY_ID = "page-transition-overlay";
  const NAV_DELAY_MS = 180;

  function getOverlay() {
    return document.getElementById(OVERLAY_ID);
  }

  function showOverlay() {
    const overlay = getOverlay();
    if (overlay) {
      overlay.classList.remove("is-hidden");
    }
  }

  function hideOverlay() {
    const overlay = getOverlay();
    if (overlay) {
      overlay.classList.add("is-hidden");
    }
  }

  // Exponer a nivel global para llamadas programáticas
  window.showPageTransition = showOverlay;
  window.hidePageTransition = hideOverlay;

  function esEnlaceInternoNavegable(link) {
    if (!link) return false;
    const rawHref = link.getAttribute("href");
    if (!rawHref || rawHref === "#" || rawHref.startsWith("#") || rawHref.startsWith("javascript:") || rawHref.startsWith("mailto:") || rawHref.startsWith("tel:")) {
      return false;
    }
    if (link.hasAttribute("download")) return false;
    if (link.target && link.target !== "" && link.target !== "_self") return false;
    if (link.getAttribute("role") === "button" && !rawHref.includes("/")) return false;

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

    const currentUrlClean = window.location.href.split("#")[0];
    const targetUrlClean = link.href.split("#")[0];

    // No mostrar si el enlace navega a la misma página exacta
    if (currentUrlClean === targetUrlClean && link.href.includes("#")) return;

    event.preventDefault();
    showOverlay();
    setTimeout(() => {
      window.location.href = link.href;
    }, NAV_DELAY_MS);
  });

  // Ocultar suavemente cuando la página termine de cargar
  function suaveDesvanecer() {
    setTimeout(() => {
      hideOverlay();
    }, 120);
  }

  if (document.readyState === "complete" || document.readyState === "interactive") {
    suaveDesvanecer();
  } else {
    window.addEventListener("DOMContentLoaded", suaveDesvanecer);
    window.addEventListener("load", hideOverlay);
  }

  // Si el usuario regresa con el botón atrás del navegador (bfcache)
  window.addEventListener("pageshow", function (e) {
    hideOverlay();
  });
})();

