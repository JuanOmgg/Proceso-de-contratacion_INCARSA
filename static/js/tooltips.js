/**
 * tooltips.js — Sistema Universal de Tooltips Modernos (INCARSA)
 * 
 * Reemplaza y embellece los atributos nativos [title], [data-tooltip] y [data-title].
 * - Auto-posicionamiento inteligente (arriba / abajo según espacio en viewport).
 * - Suprime el recuadro negro nativo del navegador al transferir [title] -> [data-tooltip].
 * - Dismissal fluido al hacer scroll, click o retirar el cursor.
 */

(function () {
  'use strict';

  let tooltipEl = null;
  let activeTarget = null;

  function getTooltipEl() {
    if (!tooltipEl) {
      tooltipEl = document.getElementById('incarsa-global-tooltip');
      if (!tooltipEl) {
        tooltipEl = document.createElement('div');
        tooltipEl.id = 'incarsa-global-tooltip';
        tooltipEl.className = 'incarsa-global-tooltip';
        document.body.appendChild(tooltipEl);
      }
    }
    return tooltipEl;
  }

  function showTooltip(target, text) {
    if (!text || !text.trim()) return;
    const tip = getTooltipEl();
    tip.textContent = text.trim();
    tip.classList.remove('is-active', 'pos-bottom');
    tip.style.display = 'block';

    const rect = target.getBoundingClientRect();
    const tipRect = tip.getBoundingClientRect();

    let top = rect.top - tipRect.height - 8;
    let posClass = 'pos-top';

    // Si se sale por arriba de la pantalla visible, colocar abajo
    if (top < 8) {
      top = rect.bottom + 8;
      posClass = 'pos-bottom';
    }

    let left = rect.left + (rect.width / 2) - (tipRect.width / 2);
    // Limitar dentro de los bordes izquierdo y derecho
    const maxLeft = window.innerWidth - tipRect.width - 12;
    left = Math.max(12, Math.min(left, maxLeft));

    tip.style.top = `${top + window.scrollY}px`;
    tip.style.left = `${left + window.scrollX}px`;
    tip.classList.add(posClass, 'is-active');
    activeTarget = target;
  }

  function hideTooltip() {
    if (tooltipEl) {
      tooltipEl.classList.remove('is-active');
    }
    activeTarget = null;
  }

  // Interceptar al pasar el cursor sobre elementos con title o data-tooltip
  document.addEventListener('mouseover', function (e) {
    const target = e.target.closest ? e.target.closest('[title], [data-tooltip], [data-title]') : null;
    if (!target) return;

    let text = target.getAttribute('data-tooltip') || target.getAttribute('data-title');

    // Si tiene atributo title nativo, transferir su contenido y suprimir title para evitar el tooltip nativo
    if (target.hasAttribute('title')) {
      const nativeTitle = target.getAttribute('title');
      if (nativeTitle && nativeTitle.trim()) {
        text = nativeTitle.trim();
        target.setAttribute('data-tooltip', text);
      }
      target.removeAttribute('title'); // Elimina la caja negra nativa del navegador
    }

    if (text && text.trim()) {
      showTooltip(target, text);
    }
  }, true);

  // Ocultar al retirar el cursor
  document.addEventListener('mouseout', function (e) {
    if (activeTarget && (!e.relatedTarget || !activeTarget.contains(e.relatedTarget))) {
      hideTooltip();
    }
  }, true);

  window.addEventListener('scroll', hideTooltip, { passive: true });
  document.addEventListener('click', hideTooltip, true);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') hideTooltip();
  });

  // Exponer API opcional
  window.IncarsaTooltip = {
    show: showTooltip,
    hide: hideTooltip
  };
})();
