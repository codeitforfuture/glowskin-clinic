document.addEventListener('DOMContentLoaded', function () {
  const loader = document.getElementById('pageLoader');
  if (loader) {
    window.addEventListener('load', () => setTimeout(() => loader.classList.add('hidden'), 300));
    setTimeout(() => loader.classList.add('hidden'), 1500);
  }
  const navToggle = document.getElementById('navToggle');
  const siteNav = document.getElementById('siteNav');
  if (navToggle && siteNav) {
    navToggle.addEventListener('click', () => {
      const expanded = navToggle.getAttribute('aria-expanded') === 'true';
      navToggle.setAttribute('aria-expanded', !expanded);
      siteNav.classList.toggle('open');
    });
    siteNav.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        navToggle.setAttribute('aria-expanded', 'false');
        siteNav.classList.remove('open');
      });
    });
  }
  document.querySelectorAll('.flash-close').forEach(btn => btn.addEventListener('click', () => btn.closest('.flash').remove()));
  const header = document.getElementById('siteHeader');
  const backTop = document.getElementById('backToTop');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 20) header?.classList.add('scrolled'); else header?.classList.remove('scrolled');
    if (backTop) { if (window.scrollY > 400) backTop.classList.add('visible'); else backTop.classList.remove('visible'); }
  });
  backTop?.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  const reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) { setTimeout(() => entry.target.classList.add('visible'), i * 60); observer.unobserve(entry.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(el => observer.observe(el));
  } else { reveals.forEach(el => el.classList.add('visible')); }
  const counters = document.querySelectorAll('[data-count]');
  if ('IntersectionObserver' in window && counters.length) {
    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = parseInt(el.dataset.count);
          const duration = 1800;
          const start = performance.now();
          const update = (now) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = Math.floor(eased * target);
            el.textContent = value.toLocaleString() + (target >= 1000 ? '+' : '');
            if (progress < 1) requestAnimationFrame(update);
            else el.textContent = target.toLocaleString() + (target >= 1000 ? '+' : '');
          };
          requestAnimationFrame(update);
          counterObserver.unobserve(el);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(c => counterObserver.observe(c));
  }
});