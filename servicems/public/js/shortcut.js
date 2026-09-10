frappe.ui.form.on('Service Job Card', {
    refresh: function(frm) {
        // // Add Ctrl+Q shortcut to the form
        // frm.page.add_inner_button(__('Item Info (Ctrl+Q)'), function() {
        //     // This will trigger when the button is clicked
        //     ctrlQ_for_job_card(frm);
        // });


        // Add keyboard shortcut for Ctrl+Q
        $(document).off('keydown.servicems_item_info').on('keydown.servicems_item_info', function(e) {
            if (e.ctrlKey && e.which === 81) { // Ctrl + Q
                if (frm.doctype === "Service Job Card") {
                    e.preventDefault();
                    ctrlQ_for_job_card(frm);
                }
            }
        });

        // Set query for "item" field in the "parts" table
        frm.fields_dict['parts'].grid.get_field('item').get_query = function(doc, cdt, cdn) {
            return {
                query: "servicems.service_management.doctype.service_settings.service_settings.get_filtered_items"
            };
        };
    }
});

// Define the ctrlQ function to handle item info display for job card
function ctrlQ_for_job_card(frm) {
    const TableName = 'Job Card Items Supplied';
    let current_doc;
    let item_row;

    // Check if we're editing an item row (child table is open)
    if ($('.grid-row-open').length && $('.grid-row-open').closest('[data-fieldname="parts"]').length) {
        current_doc = $('.grid-row-open').attr('data-name');
        if (current_doc) {
            item_row = locals[TableName][current_doc];
        }
    }
    // Check if we have a selected row in the parts grid
    else {
        const parts_grid = frm.fields_dict['parts'].grid;
        const selected_rows = parts_grid.get_selected();

        if (selected_rows && selected_rows.length) {
            current_doc = selected_rows[0];
            item_row = locals[TableName][current_doc];
        }
    }


    // No row is selected or being edited
    if (!item_row || !item_row.item) {
        frappe.show_alert({ message: __('Please select an item row in the parts table first'), indicator: 'yellow' }, 5);
        return;
    }

    // First, get the item's stock_uom
    frappe.db.get_value('Item', item_row.item, 'stock_uom')
        .then(r => {
            const stock_uom = r.message.stock_uom || '';

            // Now call the server method to get item info
            frappe.call({
                method: 'servicems.custom_api.get_item_info',
                args: { item_code: item_row.item },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        const d = new frappe.ui.Dialog({
                            title: __('Item Balance'),
                            width: 600
                        });

                        // Add the modal content
                        $(`<div class="modal-body ui-front">
                            <h2>${item_row.item} : ${item_row.qty || 0}</h2>
                            <p>Choose Warehouse and click Select :</p>
                            <table class="table table-bordered">
                            <thead>
                            </thead>
                            <tbody>
                            </tbody>
                            </table>
                        </div>`).appendTo(d.body);

                        const thead = $(d.body).find('thead');
                        if (r.message[0].batch_no) {
                            r.message.sort((a, b) => a.expiry_status - b.expiry_status);
                            $(`<tr>
                                <th>Check</th>
                                <th>Warehouse</th>
                                <th>Qty</th>
                                <th>UOM</th>
                                <th>Batch No</th>
                                <th>Expires On</th>
                                <th>Expires in Days</th>
                                </tr>`).appendTo(thead);
                        } else {
                            $(`<tr>
                                <th>Check</th>
                                <th>Warehouse</th>
                                <th>Qty</th>
                                <th>UOM</th>
                                </tr>`).appendTo(thead);
                        }

                        // Loop over the returned items and populate the table
                        r.message.forEach(element => {
                            const tbody = $(d.body).find('tbody');
                            const tr = $(`
                                <tr>
                                    <td><input type="checkbox" class="check-warehouse" data-warehouse="${element.warehouse}"></td>
                                    <td>${element.warehouse}</td>
                                    <td>${element.actual_qty}</td>
                                    <td>${stock_uom}</td>
                                </tr>
                                `).appendTo(tbody);

                            if (element.batch_no) {
                                $(`
                                    <td>${element.batch_no}</td>
                                    <td>${element.expires_on}</td>
                                    <td>${element.expiry_status}</td>
                                    `).appendTo(tr);
                                tr.find('.check-warehouse').attr('data-batch', element.batch_no);
                                tr.find('.check-warehouse').attr('data-batchQty', element.actual_qty);
                            }

                            tbody.find('.check-warehouse').on('change', function() {
                                $('input.check-warehouse').not(this).prop('checked', false);
                            });
                        });

                        d.set_primary_action("Select", function() {
                            $(d.body).find('input:checked').each(function(i, input) {
                                frappe.model.set_value(item_row.doctype, item_row.name, 'warehouse', $(input).attr('data-warehouse'));
                                if ($(input).attr('data-batch')) {
                                    frappe.model.set_value(item_row.doctype, item_row.name, 'batch_no', $(input).attr('data-batch'));
                                }
                            });
                            d.hide();
                            frm.refresh_field('parts');
                        });

                        d.show();
                    } else {
                        frappe.show_alert({ message: __('There are no records for this item'), indicator: 'red' }, 5);
                    }
                }
            });
        })
        .catch(err => {
            frappe.show_alert({ message: __('Error fetching item details: ' + err), indicator: 'red' }, 5);
        });
}
