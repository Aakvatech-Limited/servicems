// Copyright (c) 2021, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Service Workshop', {
	onload: function(frm) {
		if (!frm.is_new()) return;
		frappe.db.get_single_value("Service Settings", "company")
			.then(company => {
				const fallback = (frappe.boot && frappe.boot.sysdefaults && frappe.boot.sysdefaults.company) || "";
				const target_company = company || fallback;
				if (target_company) {
					frm.set_value("company", target_company);
				}
			});
	}
});
