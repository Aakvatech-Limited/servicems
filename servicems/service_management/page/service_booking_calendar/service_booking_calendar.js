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
  let animation;
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
      doc.documentElement.style.setProperty(
        "--sm-font",
        getComputedStyle(wrapper).fontFamily
      );
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
    window.addEventListener("resize", resize);
    window.visualViewport?.addEventListener("resize", resize);
    resize();
  };
  wrapper.servicemsCalendarDisconnect = () => {
    resizeObserver?.disconnect();
    mutationObserver?.disconnect();
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
