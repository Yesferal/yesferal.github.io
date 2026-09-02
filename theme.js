(function () {
  const root = document.documentElement;
  const toggle = document.getElementById("theme-toggle");

  function getPreferredTheme() {
    const stored = localStorage.getItem("theme");
    if (stored === "light" || stored === "dark") {
      return stored;
    }
    return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    if (toggle) {
      toggle.setAttribute("aria-label", theme === "light" ? "Switch to dark mode" : "Switch to light mode");
      toggle.textContent = theme === "light" ? "☀️" : "🌙";
    }
  }

  function initCarousels() {
    document.querySelectorAll("[data-carousel]").forEach((carousel) => {
      const viewport = carousel.querySelector(".carousel-viewport");
      const prev = carousel.querySelector("[data-carousel-prev]");
      const next = carousel.querySelector("[data-carousel-next]");
      if (!viewport || !prev || !next) return;

      const scrollAmount = () => {
        const card = viewport.querySelector(".carousel-item");
        return card ? card.offsetWidth + 24 : 300;
      };

      prev.addEventListener("click", () => {
        viewport.scrollBy({ left: -scrollAmount(), behavior: "smooth" });
      });

      next.addEventListener("click", () => {
        viewport.scrollBy({ left: scrollAmount(), behavior: "smooth" });
      });
    });
  }

  applyTheme(getPreferredTheme());

  if (toggle) {
    toggle.addEventListener("click", () => {
      const next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      localStorage.setItem("theme", next);
      applyTheme(next);
    });
  }

  initCarousels();
})();
