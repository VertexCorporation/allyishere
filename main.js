/* main.js — Ally web behaviors (shared by every page)
   Vertex Corporation · no analytics, no trackers, vanilla JS only. */
(function () {
  "use strict";

  var root = document.documentElement;

  /* ---------- theme (dark-first, persisted) ---------- */
  var THEME_KEY = "ally-theme";

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    var moon = document.getElementById("themeIconMoon");
    var sun = document.getElementById("themeIconSun");
    if (moon) moon.style.display = theme === "dark" ? "none" : "block";
    if (sun) sun.style.display = theme === "dark" ? "block" : "none";
  }

  function storedTheme() {
    try {
      return localStorage.getItem(THEME_KEY) || localStorage.getItem("theme") || null;
    } catch (e) {
      return null;
    }
  }

  var initial = storedTheme() || "dark";
  applyTheme(initial);

  function bindThemeButton(id) {
    var btn = document.getElementById(id);
    if (!btn) return;
    btn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(next);
      try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
    });
  }

  bindThemeButton("themeBtn");
  bindThemeButton("themeToggle");

  /* ---------- sticky nav ---------- */
  var nav = document.getElementById("nav");
  if (nav) {
    var onScroll = function () {
      nav.classList.toggle("scrolled", window.scrollY > 12);
    };
    document.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* ---------- mobile menu ---------- */
  var hbBtn = document.getElementById("hamburgerBtn");
  var mobileMenu = document.getElementById("mobileMenu");
  if (hbBtn && mobileMenu) {
    hbBtn.addEventListener("click", function () {
      var open = mobileMenu.classList.toggle("open");
      hbBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    mobileMenu.querySelectorAll("a, button").forEach(function (el) {
      el.addEventListener("click", function () {
        mobileMenu.classList.remove("open");
        hbBtn.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ---------- language dropdown ---------- */
  var langWrap = document.getElementById("langWrap");
  var langBtn = document.getElementById("langBtn");
  if (langWrap && langBtn) {
    langBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = langWrap.classList.toggle("open");
      langBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", function () {
      langWrap.classList.remove("open");
      langBtn.setAttribute("aria-expanded", "false");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        langWrap.classList.remove("open");
        langBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---------- scroll reveal ---------- */
  var reduceMotion = false;
  try {
    reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) {}

  var revealEls = document.querySelectorAll(".reveal");
  if (reduceMotion || !("IntersectionObserver" in window)) {
    revealEls.forEach(function (el) {
      el.classList.add("in");
      el.classList.add("active");
    });
  } else {
    var revealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            entry.target.classList.add("active");
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach(function (el) {
      revealObserver.observe(el);
    });
  }

  /* ---------- lazy lottie (plays only when visible) ---------- */
  var players = document.querySelectorAll("dotlottie-player, lottie-player");
  players.forEach(function (player) {
    player.setAttribute("aria-hidden", "true");
    player.removeAttribute("autoplay");
  });

  if (players.length && !reduceMotion && "IntersectionObserver" in window) {
    var lottieObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          var el = entry.target;
          if (!entry.isIntersecting) return;
          lottieObserver.unobserve(el);
          var play = function () {
            if (typeof el.play === "function") el.play();
          };
          if (el.loaded || el.customElements) {
            play();
          } else {
            el.addEventListener("ready", play, { once: true });
            setTimeout(play, 900);
          }
        });
      },
      { threshold: 0.25 }
    );
    players.forEach(function (el) {
      lottieObserver.observe(el);
    });
  }

  /* ---------- ally ring: gentle loop with a pause ---------- */
  var ringPlayer = document.getElementById("ringplayer");
  if (ringPlayer) {
    ringPlayer.addEventListener("complete", function () {
      setTimeout(function () {
        try {
          ringPlayer.seek(0);
          ringPlayer.play();
        } catch (e) {}
      }, 2000);
    });
  }
})();
