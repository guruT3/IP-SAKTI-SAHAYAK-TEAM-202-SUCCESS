// IP-SAKTI SAHAYAK — shared app utilities: theme toggle (persisted), nav interactions, fetch helper.

(function () {
  const root = document.documentElement;
  const toggleBtn = document.getElementById('theme-toggle');
  const stored = localStorage.getItem('ip-sakti-theme');
  if (stored) root.setAttribute('data-theme', stored);

  function toggleTheme() {
    const current = root.getAttribute('data-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    localStorage.setItem('ip-sakti-theme', next);
  }

  if (toggleBtn) toggleBtn.addEventListener('click', toggleTheme);
})();

// ---- Navbar: mobile drawer, active link, scroll shadow ----
(function () {
  const navbar = document.getElementById('site-navbar');
  const navToggle = document.getElementById('nav-toggle');
  const navLinks = document.getElementById('nav-links');
  const navBackdrop = document.getElementById('nav-backdrop');

  function closeNav() {
    if (!navLinks) return;
    navLinks.classList.remove('open');
    navToggle && navToggle.setAttribute('aria-expanded', 'false');
    navBackdrop && navBackdrop.classList.remove('visible');
    document.body.classList.remove('nav-open');
  }

  function openNav() {
    if (!navLinks) return;
    navLinks.classList.add('open');
    navToggle && navToggle.setAttribute('aria-expanded', 'true');
    navBackdrop && navBackdrop.classList.add('visible');
    document.body.classList.add('nav-open');
  }

  if (navToggle) {
    navToggle.addEventListener('click', () => {
      const isOpen = navLinks.classList.contains('open');
      isOpen ? closeNav() : openNav();
    });
  }
  if (navBackdrop) navBackdrop.addEventListener('click', closeNav);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeNav();
  });
  // Close the drawer after picking a link (mobile)
  document.querySelectorAll('[data-nav]').forEach((link) => {
    link.addEventListener('click', closeNav);
  });

  // Highlight the current section in the nav
  const path = window.location.pathname.replace(/\/+$/, '') || '/';
  document.querySelectorAll('[data-nav]').forEach((link) => {
    const linkPath = link.getAttribute('href').replace(/\/+$/, '') || '/';
    if (linkPath === path || (linkPath !== '/' && path.startsWith(linkPath))) {
      link.classList.add('active');
      link.setAttribute('aria-current', 'page');
    }
  });

  // Deepen the navbar shadow once the page has scrolled
  function onScroll() {
    if (!navbar) return;
    if (window.scrollY > 8) navbar.classList.add('scrolled');
    else navbar.classList.remove('scrolled');
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();

// ---- Footer: dynamic year + back-to-top ----
(function () {
  const yearEl = document.getElementById('footer-year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  const backToTop = document.getElementById('back-to-top');
  if (!backToTop) return;

  function onScroll() {
    if (window.scrollY > 480) backToTop.classList.add('visible');
    else backToTop.classList.remove('visible');
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();

async function apiFetch(url, options = {}) {
  const opts = Object.assign({ headers: { 'Content-Type': 'application/json' } }, options);
  const res = await fetch(url, opts);
  let data;
  try {
    data = await res.json();
  } catch (e) {
    data = { success: false, error: 'Unexpected server response.' };
  }
  if (!res.ok && data.success === undefined) {
    data = { success: false, error: data.error || `Request failed (${res.status}).` };
  }
  return data;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}