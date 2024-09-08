// Copyright (c) 2024, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Service Booking', {
	refresh: function(frm) {
		frm.trigger("set_filters");
		frm.trigger("disable_form");
		frm.trigger("close_booking");
	},
	onload: (frm) => {
		frm.trigger("set_filters");
		frm.trigger("disable_form");
		frm.trigger("close_booking");
	},
	disable_form: (frm) => {
		if (frm.doc.status != "Pending") {
			frm.disable_save();
		}
	},
	close_booking: (frm) => {
		frm.add_custom_button(__("Close Booking"), function() {
			frm.set_value("status", "Closed");
			frm.save();
		});
	},
	create_job_card: (frm) => {
		frm.trigger("create_service_job_card_record")
	},
	create_service_job_card_record: (frm) => {
		frappe.new_doc("Service Job Card", {
			"workshop": frm.doc.workshop,
			"service_item_name": frm.doc.service_vehicle,
			"customer": frm.doc.customer,
			"mobile_no": frm.doc.phone_no,
			"service_booking": frm.doc.name,
			"bay": frm.doc.bay
		}, doc => {});
	},
	set_filters: (frm) => {
		frm.set_query("service_vehicle", function() {
			return {
				"filters": {
					"customer": frm.doc.customer
				}
			};
		});
		frm.set_query("bay", function() {
			return {
				"filters": {
					"service_workshop": frm.doc.workshop
				}
			};
		});
	},
});
