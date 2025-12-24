document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const themeToggleBtn = document.getElementById("themeToggle");

  let particleEngine = null;

  // THEME
  function setTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
    if (particleEngine) particleEngine.syncTheme();
  }
  const stored = localStorage.getItem("theme") || "dark";
  setTheme(stored);

  themeToggleBtn.addEventListener("click", () => {
    const current = root.getAttribute("data-theme");
    setTheme(current === "dark" ? "light" : "dark");
  });

  // HERO PARALLAX
  const hero = document.querySelector(".hero");
  const heroGlow = document.querySelector(".hero-bg-glow");
  if (hero && heroGlow) {
    hero.addEventListener("mousemove", (e) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 15;
      const y = (e.clientY / window.innerHeight - 0.5) * 15;
      heroGlow.style.transform = `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`;
    });
  }

  // SCROLL REVEAL
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("active");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: "0px 0px -50px 0px" });
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

  // PARTICLES
  class ParticleEngine {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.particles = [];
      this.resize = this.resize.bind(this);
      this.animate = this.animate.bind(this);
      window.addEventListener("resize", this.resize);
      this.resize();
      this.syncTheme();
      this.animate();
    }
    syncTheme() {
      const isDark = root.getAttribute("data-theme") === "dark";
      this.color = isDark ? "255, 255, 255" : "0, 0, 0";
      this.baseAlpha = isDark ? 0.1 : 0.05;
    }
    resize() {
      this.w = this.canvas.width = window.innerWidth;
      this.h = this.canvas.height = window.innerHeight;
      this.initParticles();
    }
    initParticles() {
      this.particles = [];
      const count = Math.floor(this.w / 25);
      for (let i = 0; i < count; i++) {
        this.particles.push({
          x: Math.random() * this.w,
          y: Math.random() * this.h,
          vx: (Math.random() - 0.5) * 0.15,
          vy: (Math.random() - 0.5) * 0.15,
          size: Math.random() * 2,
          alpha: Math.random() * 0.5 + 0.5
        });
      }
    }
    animate() {
      this.ctx.clearRect(0, 0, this.w, this.h);
      this.particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = this.w; if (p.x > this.w) p.x = 0;
        if (p.y < 0) p.y = this.h; if (p.y > this.h) p.y = 0;
        this.ctx.beginPath();
        this.ctx.fillStyle = `rgba(${this.color}, ${p.alpha * this.baseAlpha})`;
        this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        this.ctx.fill();
      });
      requestAnimationFrame(this.animate);
    }
  }
  const canvas = document.getElementById("particle-canvas");
  if (canvas) particleEngine = new ParticleEngine(canvas);
});