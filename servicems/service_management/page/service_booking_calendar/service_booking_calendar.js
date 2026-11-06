// Frappe owns the Dock, Sidebar and page header. Only calendar content is embedded.
frappe.pages["service-booking-calendar"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Booking Calendar"),
    single_column: true,
  });
  wrapper.classList.add("servicems-calendar-page");
  const style = document.createElement("style");
  style.textContent = `
    .servicems-calendar-page .page-body { padding: 0; max-width: none; }
    .servicems-calendar-page .layout-main-section-wrapper { padding: 0; min-width: 0; }
    .servicems-calendar-page .layout-main-section { border: 0; box-shadow: none; min-height: 0; overflow: hidden; }
    .servicems-calendar-frame { display: block; width: 100%; min-width: 0; border: 0; outline: 0; box-shadow: none; background: var(--bg-color, #fff); }
  `;
  wrapper.appendChild(style);
  const iframe = document.createElement("iframe");
  iframe.src = "/bookings?embedded=1";
  iframe.title = __("ServiceMS Booking Calendar");
  iframe.className = "servicems-calendar-frame";
  page.main.empty().append(iframe);
  let resizeObserver;
  let mutationObserver;
  let themeObserver;
  let animation;
  const syncTheme = () => {
    const doc = iframe.contentDocument;
    if (!doc) return;
    const root = document.documentElement;
    const body = document.body;
    const rawTheme =
      root.getAttribute("data-theme") ||
      body.getAttribute("data-theme") ||
      document.documentElement.getAttribute("data-bs-theme") ||
      "";
    const isDark =
      rawTheme.toLowerCase().includes("dark") ||
      root.classList.contains("dark") ||
      body.classList.contains("dark") ||
      getComputedStyle(root).colorScheme === "dark";
    const next = isDark ? "dark" : "light";
    doc.documentElement.dataset.theme = next;
    doc.documentElement.classList.toggle("dark", isDark);
    doc.documentElement.style.setProperty(
      "--sm-font",
      getComputedStyle(wrapper).fontFamily
    );
    const deskStyle = getComputedStyle(wrapper);
    const surfaces = {
      "--sm-bg": "--bg-color",
      "--sm-surface": "--fg-color",
      "--sm-surface-muted": "--subtle-fg",
      "--sm-control-bg": "--control-bg",
      "--sm-border": "--border-color",
      "--sm-foreground": "--text-color",
      "--sm-muted": "--text-muted",
      "--sm-calendar-header": "--subtle-fg",
    };
    for (const [calendarToken, deskToken] of Object.entries(surfaces)) {
      const value = deskStyle.getPropertyValue(deskToken).trim();
      if (isDark && value && CSS.supports("color", value))
        doc.documentElement.style.setProperty(calendarToken, value);
      else doc.documentElement.style.removeProperty(calendarToken);
    }
    // Follow native Desk's primary accent whenever the installed theme exposes it.
    const accent = getComputedStyle(root).getPropertyValue("--primary").trim();
    if (accent && accent.startsWith("#"))
      doc.documentElement.style.setProperty("--sm-native-primary", accent);
  };
  const resize = () => {
    if (!wrapper.getClientRects().length) return;
    const viewport = window.visualViewport?.height || window.innerHeight;
    const height =
      Math.max(0, Math.floor(viewport - iframe.getBoundingClientRect().top)) +
      "px";
    if (iframe.style.height !== height) iframe.style.height = height;
  };
  iframe.addEventListener("load", () => {
    // Same-origin embedding: inherit Desk typography and timezone, without a second shell.
    const doc = iframe.contentDocument;
    if (doc) {
      syncTheme();
      iframe.contentWindow.dispatchEvent(new Event("resize"));
    }
    resize();
  });
  wrapper.servicemsCalendarResize = resize;
  wrapper.servicemsCalendarObserve = () => {
    resizeObserver?.disconnect();
    resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(wrapper);
    if (page.page_head?.[0]) resizeObserver.observe(page.page_head[0]);
    resizeObserver.observe(document.body);
    mutationObserver?.disconnect();
    mutationObserver = new MutationObserver(() => {
      cancelAnimationFrame(animation);
      animation = requestAnimationFrame(resize);
    });
    // Native banners can move the frame without changing the page's own size.
    mutationObserver.observe(document.body, { childList: true, subtree: true });
    themeObserver?.disconnect();
    themeObserver = new MutationObserver(syncTheme);
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme", "data-bs-theme", "class", "style"],
    });
    themeObserver.observe(document.body, {
      attributes: true,
      attributeFilter: ["data-theme", "class", "style"],
    });
    syncTheme();
    window.addEventListener("resize", resize);
    window.visualViewport?.addEventListener("resize", resize);
    resize();
  };
  wrapper.servicemsCalendarDisconnect = () => {
    resizeObserver?.disconnect();
    mutationObserver?.disconnect();
    themeObserver?.disconnect();
    cancelAnimationFrame(animation);
    window.removeEventListener("resize", resize);
    window.visualViewport?.removeEventListener("resize", resize);
  };
  $(wrapper).on("hide.servicemsCalendar", wrapper.servicemsCalendarDisconnect);
};
frappe.pages["service-booking-calendar"].on_page_show = function (wrapper) {
  wrapper.servicemsCalendarObserve?.();
};
frappe.pages["service-booking-calendar"].on_page_hide = function (wrapper) {
  wrapper.servicemsCalendarDisconnect?.();
};
