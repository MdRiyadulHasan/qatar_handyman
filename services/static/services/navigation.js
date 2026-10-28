(() => {
  const header = document.querySelector('[data-site-header]');
  if (!header) return;
  const toggle = header.querySelector('.nav-mobile-toggle');
  const nav = header.querySelector('.site-navigation');
  const dropdown = header.querySelector('[data-nav-dropdown]');
  const summary = dropdown.querySelector('summary');
  const desktop = window.matchMedia('(min-width: 1001px)');
  const canHover = window.matchMedia('(hover: hover) and (pointer: fine)');
  let closeTimer;
  const closeDropdown = () => { window.clearTimeout(closeTimer); dropdown.open = false; };
  toggle.hidden = false;
  header.classList.add('nav-ready');
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
    if (!open) closeDropdown();
  });
  dropdown.addEventListener('pointerenter', () => {
    window.clearTimeout(closeTimer);
    if (desktop.matches && canHover.matches) dropdown.open = true;
  });
  dropdown.addEventListener('pointerleave', () => {
    if (desktop.matches && canHover.matches && !dropdown.querySelector('.nav-mega-panel').contains(document.activeElement)) closeTimer = window.setTimeout(closeDropdown, 220);
  });
  header.addEventListener('focusout', (event) => {
    if (!dropdown.contains(event.relatedTarget)) closeDropdown();
  });
  document.addEventListener('click', (event) => {
    if (!header.contains(event.target)) {
      closeDropdown();
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
  header.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    if (dropdown.open) { closeDropdown(); summary.focus(); }
    else if (nav.classList.contains('is-open')) {
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.focus();
    }
  });
  desktop.addEventListener('change', () => {
    closeDropdown();
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
  });
})();
