frappe.listview_settings['Service Booking'] = {
    add_fields: ["status"],
    hide_name_column: true,

    get_indicator: function(doc) {
        if (doc.status == "Pending") {
            return [__("Pending"), "orange", "status,=,Pending"];
        } else if (doc.status == "In Progress") {
            return [__("In Progress"), "blue", "status,=,In Progress"];
        } else if (doc.status == "Closed") {
            return [__("Closed"), "red", "status,=,Closed"];
        } else if (doc.status == "Completed") {
            return [__("Completed"), "green", "status,=,Completed"];
        }
    },
    onload: function(listview) {
        visit_booking_page(listview);
        bulk_close_booking(listview);
    }
};
var visit_booking_page = function(listview) {
    listview.page.add_inner_button(__("View Booking Page"), function() {
        window.location.href = "/bookings";
    });
};

var bulk_close_booking = function(listview) {
    listview.page.add_inner_button(__("Close Booking"), function() {
        var selected_rows = listview.get_checked_items();
        if (!selected_rows.length) {
            frappe.msgprint(__("Please select Service Bookings to close"));
            return;
        }
        frappe.confirm(
            __("Are you sure you want to close the selected Service Bookings?"),
            function() {
                frappe.call({
                    method: "servicems.service_management.doctype.service_booking.service_booking.bulk_close_bookings",
                    args: {
                        "booking_list": selected_rows
                    },
                    callback: function(r) {
                        if (r.message) {
                            listview.refresh();
                        }
                    }
                });
            }
        );
    });
};