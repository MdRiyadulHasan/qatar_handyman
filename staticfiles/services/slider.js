(() => {
  document.querySelectorAll("[data-slider]").forEach((slider) => {
    const slides = Array.from(slider.querySelectorAll("[data-slide]"));
    if (slides.length < 2) return;
    const controls = slider.querySelector("[data-slider-controls]");
    const dots = Array.from(slider.querySelectorAll("[data-slider-dot]"));
    const toggle = slider.querySelector("[data-slider-toggle]");
    const status = slider.querySelector("[data-slider-status]");
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let index = 0;
    let paused = reducedMotion.matches;
    let hovering = false;
    let timer = null;
    const stop = () => { if (timer !== null) window.clearInterval(timer); timer = null; };
    const show = (next, announce = false) => {
      index = (next + slides.length) % slides.length;
      slides.forEach((slide, i) => { slide.hidden = i !== index; });
      dots.forEach((dot, i) => {
        if (i === index) dot.setAttribute("aria-current", "true");
        else dot.removeAttribute("aria-current");
      });
      const counter = slider.querySelector("[data-slider-count]");
      if (counter) counter.textContent = String(index + 1).padStart(2, "0") + " / " + String(slides.length).padStart(2, "0");
      if (announce) status.textContent = "Slide " + (index + 1) + " of " + slides.length;
    };
    const schedule = () => {
      stop();
      toggle.textContent = paused ? "Play" : "Pause";
      toggle.setAttribute("aria-label", paused ? "Play automatic slideshow" : "Pause automatic slideshow");
      if (!paused && !hovering && !document.hidden && !slider.contains(document.activeElement)) {
        timer = window.setInterval(() => show(index + 1), 4000);
      }
    };
    const navigate = (next) => { show(next, true); schedule(); };
    // Swiping changes category without intercepting vertical page scrolling.
    let touchStart = null;
    const viewport = slider.querySelector(".slider-viewport");
    viewport.addEventListener("touchstart", (event) => {
      const touch = event.touches[0];
      touchStart = event.touches.length === 1 ? { x: touch.clientX, y: touch.clientY } : null;
    }, { passive: true });
    viewport.addEventListener("touchend", (event) => {
      if (!touchStart || !event.changedTouches.length) return;
      const touch = event.changedTouches[0];
      const dx = touch.clientX - touchStart.x;
      const dy = touch.clientY - touchStart.y;
      touchStart = null;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) navigate(index + (dx < 0 ? 1 : -1));
    }, { passive: true });
    viewport.addEventListener("touchcancel", () => { touchStart = null; }, { passive: true });
    controls.hidden = false;
    slider.querySelector("[data-slider-prev]").addEventListener("click", () => navigate(index - 1));
    slider.querySelector("[data-slider-next]").addEventListener("click", () => navigate(index + 1));
    dots.forEach((dot, i) => dot.addEventListener("click", () => navigate(i)));
    toggle.addEventListener("click", () => { paused = !paused; schedule(); });
    slider.addEventListener("mouseenter", () => { hovering = true; schedule(); });
    slider.addEventListener("mouseleave", () => { hovering = false; schedule(); });
    slider.addEventListener("focusin", stop);
    slider.addEventListener("focusout", () => window.setTimeout(schedule, 0));
    slider.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") { event.preventDefault(); navigate(index - 1); }
      if (event.key === "ArrowRight") { event.preventDefault(); navigate(index + 1); }
    });
    document.addEventListener("visibilitychange", schedule);
    reducedMotion.addEventListener("change", (event) => { if (event.matches) paused = true; schedule(); });
    schedule();
  });
})();
