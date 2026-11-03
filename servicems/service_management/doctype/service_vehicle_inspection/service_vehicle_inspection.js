frappe.ui.form.on("Service Vehicle Inspection", {
  inspection_template(frm) {
    if (frm.is_dirty()) frm.save().then(() => frm.reload_doc());
  },
  refresh(frm) {
    if (frm.doc.inspection_status === "Completed") {
      frm.add_custom_button(__("Create Correction"), () => {
        frappe.prompt(
          {
            fieldname: "reason",
            fieldtype: "Small Text",
            label: __("Correction Reason"),
            reqd: 1,
          },
          ({ reason }) =>
            frm
              .call("create_correction", { reason })
              .then((r) =>
                frappe.set_route(
                  "Form",
                  "Service Vehicle Inspection",
                  r.message
                )
              )
        );
      });
    }
  },
});
