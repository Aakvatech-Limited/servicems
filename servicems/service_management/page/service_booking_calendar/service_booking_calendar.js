// The native Frappe Desk owns the Dock, header and Service Management sidebar.
// Only the central content is supplied by the existing ServiceMS Vue application.
frappe.pages["service-booking-calendar"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Booking Calendar"),
    single_column: true,
  });
  const container = page.main;
  const iframe = document.createElement("iframe");
  iframe.src = "/bookings?embedded=1";
  iframe.title = __("ServiceMS Booking Calendar");
  iframe.setAttribute("loading", "eager");
  iframe.style.cssText = "display:block;width:100%;height:calc(100vh - 170px);min-height:580px;border:0;background:#fff;";
  container.empty().append(iframe);
};
