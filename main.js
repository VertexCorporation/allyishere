/* main.js — Ally web behaviors (shared by every page).
   Vertex Corporation · vanilla JS · no trackers.
   Everything here is progressive enhancement: with JS disabled the site
   remains fully readable and navigable. */
(function () {
  "use strict";

  var root = document.documentElement;
  root.classList.add("js");

  var reduceMotion = false;
  try {
    reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) {}

  /* ---------- theme ---------- */
  var THEME_KEY = "ally-theme";

  function storedTheme() {
    try {
      var t = localStorage.getItem(THEME_KEY);
      return t === "light" || t === "dark" ? t : null;
    } catch (e) {
      return null;
    }
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    var btn = document.getElementById("themeBtn");
    if (btn) btn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
  }

  applyTheme(storedTheme() || "dark");

  var themeBtn = document.getElementById("themeBtn");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(next);
      try {
        localStorage.setItem(THEME_KEY, next);
      } catch (e) {}
    });
  }

  /* ---------- sticky nav state ---------- */
  var nav = document.getElementById("nav");
  if (nav) {
    var ticking = false;
    var updateNav = function () {
      ticking = false;
      nav.classList.toggle("scrolled", (window.scrollY || 0) > 12);
    };
    document.addEventListener(
      "scroll",
      function () {
        if (!ticking) {
          ticking = true;
          window.requestAnimationFrame(updateNav);
        }
      },
      { passive: true }
    );
    updateNav();
  }

  /* ---------- mobile menu ---------- */
  var hamburger = document.getElementById("hamburgerBtn");
  var mobileMenu = document.getElementById("mobileMenu");
  if (hamburger && mobileMenu) {
    var setMenu = function (open) {
      mobileMenu.classList.toggle("open", open);
      hamburger.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
    };
    hamburger.addEventListener("click", function () {
      setMenu(!mobileMenu.classList.contains("open"));
    });
    mobileMenu.addEventListener("click", function (e) {
      if (e.target.closest("a")) setMenu(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && mobileMenu.classList.contains("open")) {
        setMenu(false);
        hamburger.focus();
      }
    });
  }

  /* ---------- language menu ---------- */
  var langWrap = document.getElementById("langWrap");
  var langBtn = document.getElementById("langBtn");
  var langMenu = document.getElementById("langMenu");

  function closeLang() {
    if (!langWrap || !langBtn) return;
    langWrap.classList.remove("open");
    langBtn.setAttribute("aria-expanded", "false");
  }

  if (langWrap && langBtn && langMenu) {
    langBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = !langWrap.classList.contains("open");
      langWrap.classList.toggle("open", open);
      langBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });

    document.addEventListener("click", function (e) {
      if (!langWrap.contains(e.target)) closeLang();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && langWrap.classList.contains("open")) {
        closeLang();
        langBtn.focus();
      }
    });

    // Keyboard support: arrows move through languages, Home/End jump.
    var items = Array.prototype.slice.call(langMenu.querySelectorAll("a"));
    langBtn.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        langWrap.classList.add("open");
        langBtn.setAttribute("aria-expanded", "true");
        (e.key === "ArrowDown" ? items[0] : items[items.length - 1]).focus();
      }
    });
    items.forEach(function (item, i) {
      item.addEventListener("keydown", function (e) {
        if (e.key === "ArrowDown") {
          e.preventDefault();
          items[(i + 1) % items.length].focus();
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          items[(i - 1 + items.length) % items.length].focus();
        } else if (e.key === "Home") {
          e.preventDefault();
          items[0].focus();
        } else if (e.key === "End") {
          e.preventDefault();
          items[items.length - 1].focus();
        }
      });
      // Remember the choice so the root router can honor it next visit.
      item.addEventListener("click", function () {
        try {
          localStorage.setItem("ally_language", item.getAttribute("lang") || "");
        } catch (err) {}
      });
    });
  }


  /* ---------- reveal on scroll (progressive; never hides content) ---------- */
  var revealEls = Array.prototype.slice.call(document.querySelectorAll(".reveal"));

  function showAll() {
    revealEls.forEach(function (el) {
      el.classList.add("in");
    });
  }

  if (reduceMotion || !("IntersectionObserver" in window)) {
    showAll();
  } else {
    var revealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -36px 0px" }
    );
    revealEls.forEach(function (el) {
      revealObserver.observe(el);
    });
    // Safety net: nothing may stay hidden if observation is interrupted.
    window.setTimeout(showAll, 2500);
  }

  /* ---------- lottie: play only while visible ---------- */
  var players = Array.prototype.slice.call(
    document.querySelectorAll("dotlottie-player, lottie-player")
  );
  players.forEach(function (el) {
    el.setAttribute("aria-hidden", "true");
  });

  if (players.length && !reduceMotion && "IntersectionObserver" in window) {
    var play = function (el) {
      try {
        if (typeof el.play === "function") el.play();
      } catch (e) {}
    };
    var pause = function (el) {
      try {
        if (typeof el.pause === "function") el.pause();
      } catch (e) {}
    };
    var lottieObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) play(entry.target);
          else pause(entry.target);
        });
      },
      { threshold: 0.2 }
    );
    players.forEach(function (el) {
      lottieObserver.observe(el);
    });
  }
})();
