// ============================================================
// Ironclad Welding — main client script
// Theme toggle, loader, scroll reveals, stats counter,
// gallery lightbox, FAQ, sparks, floating CTA visibility.
// ============================================================

(function () {
  'use strict';

  // ---------- LOADER ----------
  const loader = document.getElementById('loader');
  if (loader) {
    const hide = () => {
      loader.classList.add('hidden');
      setTimeout(() => loader.remove(), 700);
    };
    if (document.readyState === 'complete') {
      setTimeout(hide, 600);
    } else {
      window.addEventListener('load', () => setTimeout(hide, 500));
      // hard cap
      setTimeout(hide, 3500);
    }
  }

  // ---------- THEME ----------
  const themeBtn = document.getElementById('themeToggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const cur = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) {}
    });
  }

  // ---------- REVEAL ON SCROLL ----------
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12 });
    document.querySelectorAll('.reveal').forEach(el => io.observe(el));
  } else {
    document.querySelectorAll('.reveal').forEach(el => el.classList.add('visible'));
  }

  // ---------- STATS COUNTER ----------
  const animateNumber = (el) => {
    const target = parseInt(el.dataset.target, 10);
    if (isNaN(target)) return;
    const duration = 1400;
    const start = performance.now();
    const step = (now) => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = Math.floor(target * eased).toLocaleString();
      if (t < 1) requestAnimationFrame(step);
      else el.textContent = target.toLocaleString();
    };
    requestAnimationFrame(step);
  };

  if ('IntersectionObserver' in window) {
    const so = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          animateNumber(e.target);
          so.unobserve(e.target);
        }
      });
    }, { threshold: 0.5 });
    document.querySelectorAll('.stat-num[data-target]').forEach(el => so.observe(el));
  }

  // ---------- SPARKS ----------
  const sparkLayer = document.querySelector('.sparks');
  if (sparkLayer && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const spawn = () => {
      const s = document.createElement('span');
      s.className = 'spark';
      const left = Math.random() * 100;
      const dx = (Math.random() - 0.5) * 200;
      const dur = 2 + Math.random() * 3;
      const size = 2 + Math.random() * 3;
      s.style.left = left + '%';
      s.style.bottom = '0';
      s.style.width = size + 'px';
      s.style.height = size + 'px';
      s.style.setProperty('--dx', dx + 'px');
      s.style.animationDuration = dur + 's';
      sparkLayer.appendChild(s);
      setTimeout(() => s.remove(), dur * 1000);
    };
    setInterval(spawn, 250);
  }

  // ---------- GALLERY LIGHTBOX ----------
  const lightbox = document.getElementById('lightbox');
  const lightboxImg = document.getElementById('lightboxImg');
  if (lightbox && lightboxImg) {
    document.querySelectorAll('.gallery-item img').forEach(img => {
      img.addEventListener('click', () => {
        lightboxImg.src = img.src;
        lightbox.classList.add('open');
      });
    });
    lightbox.addEventListener('click', (e) => {
      if (e.target === lightbox || e.target.classList.contains('lightbox-close')) {
        lightbox.classList.remove('open');
      }
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') lightbox.classList.remove('open');
    });
  }

  // ---------- FLOATING CTA: hide near footer ----------
  const cta = document.querySelector('.floating-cta');
  const footer = document.querySelector('.footer');
  if (cta && footer && 'IntersectionObserver' in window) {
    const fo = new IntersectionObserver((entries) => {
      entries.forEach(e => cta.classList.toggle('hidden', e.isIntersecting));
    }, { threshold: 0.05 });
    fo.observe(footer);
  }

  // ---------- TOASTS auto-remove ----------
  document.querySelectorAll('.toast').forEach(t => {
    setTimeout(() => t.remove(), 5500);
  });

})();
