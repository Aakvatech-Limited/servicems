// Copyright (c) 2021, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Service Job Card', {
	onload: function (frm) {
		setMatrialBtn(frm);
		toggleTyreManagementFields(frm);
		toggleTyreMovementFields(frm);

	},
	refresh: function (frm) {
		setMatrialBtn(frm);
		toggleTyreManagementFields(frm);
		toggleTyreMovementFields(frm);
		cur_frm.set_query("item", "parts", () => {
			return {
				query: "servicems.service_management.doctype.service_settings.service_settings.get_filtered_items",
			};
		});
	},
	tyre_movement_type: function (frm) {
		toggleTyreMovementFields(frm);
	},

	unbill_item: function (frm) {
		if (frm.doc.docstatus == 0) {
			frappe.call("servicems.service_management.doctype.service_job_card.service_job_card.get_all_supplied_parts", {
				job_card: frm.doc.name
			}).then(records => {
				var data = records.message;
				if (data.length > 0){
					let d = new frappe.ui.Dialog({
						title: "Select Item to Unbill",
						fields: [
							{
								fieldname: "open_space",
								fieldtype: "HTML",
							}
						],

					});
					
					let html = `<table class="table table-hover" style="width:100%;">
						<colgroup>
							<col width="5%">
							<col width="5%">
							<col width="15%">
							<col width="20%">
							<col width="5%">
							<col width="15%">
							<col width="5%">
							<col width="5%">
							<col width="5%">
							<col width="25%">
						</colgroup>
						<tr style="background-color: #D3D3D3;">
							<th></th>
							<th>S/N</th>
							<th>Item</th>
							<th>Item Name</th>
							<th></th>
							<th>Rate</th>
							<th></th>
							<th>Qty</th>
							<th></th>
							<th>Qty to Return</th>
						</tr>`
					
					data.forEach(row => {
						html += `<tr>
							<td><input type="checkbox"/></td>
							<td id="idx" data-idx="${row.idx}">${row.idx}</td>
							<td id="item" data-item="${row.item}">${row.item}</td>
							<td id="item_name" data-item_name="${row.item_name}">${row.item_name}</td>
							<td id="stock_entry" data-stock_entry="${row.stock_entry}"></td>
							<td id="rate" data-rate="${row.rate}">${row.rate}</td>
							<td id="parent" data-parent="${row.parent}"></td>
							<td id="qty" data-qty="${row.qty}">${row.qty}</td>
							<td id="parenttype" data-parenttype="${row.parenttype}"></td>
							<td id="qty_to_return"></td>
						</tr>`
					});
					html += `</table>`

					let wrapper = d.fields_dict.open_space.$wrapper
					
					wrapper.html(html);

					wrapper.find("table").hover(function() {
						get_qty_to_return(wrapper);
					});
					
					d.set_primary_action(__("Select Item"), function() {
						let items = [];
						
						wrapper.find('tr:has(input:checkbox:checked)').each(function() {
							items.push({
								"item":  $(this).find("#item").attr("data-item"),
								"item_name":  $(this).find("#item_name").attr("data-item_name"),
								"stock_entry": $(this).find("#stock_entry").attr("data-stock_entry"),
								"rate": $(this).find("#rate").attr("data-rate"),
								"parent": $(this).find("#parent").attr("data-parent"),
								"qty": $(this).find("#qty").attr("data-qty"),
								"parenttype": $(this).find("#parenttype").attr("data-parenttype"),
								"qty_to_return": $(this).find("#parenttype").attr("data-qty_to_return")
							});
						});

						if (items.length > 0) {
							frappe.call("servicems.service_management.doctype.service_job_card.service_job_card.get_selected_items", {
								items: items
							}).then(r => {
								frm.reload_doc()
							});
							d.hide();

						} else {
							frappe.msgprint({
								title: __('Message'),
								indicator: 'red',
								message: __(
									'<h4 class="text-center" style="background-color: #D3D3D3; font-weight: bold;">\
									No any Item selected<h4>'
								)
							});
						}
					});
					d.$wrapper.find('.modal-content').css({
						"width": "900px",
						"max-height": "1500px",
						"overflow-y": "auto",
						"display": "table-cell",
						"text-align": "left"
					});
					
					d.show();
				
				} else {
					let d = new frappe.ui.Dialog({
						title: "Select Items Unbill",
						fields: [{fieldname: "html",fieldtype: "HTML"}]
					});
					d.fields_dict.html.$wrapper.append(`<div class="multiselect-empty-state"
						style="border: 1px solid #d1d8dd; border-radius: 3px; height: 200px; overflow: auto;">
						<span class="text-center" style="margin-top: -40px;">
							<i class="fa fa-2x fa-heartbeat text-extra-muted"></i>
							<p class="text-extra-muted text-center" style="font-size: 16px; font-weight: bold;">
							No Item(s) to unbill</p>
						</span>
					</div>`);
					d.show()
				};
			});
		}
	}
});

const toggleTyreManagementFields = frm => {
	const tyre_fields = [
		"tyre_management_section",
		"tyre_serial",
		"tyre_movement_type",
		"tyre_install_on",
		"tyre_from_position",
		"tyre_to_position",
		"tyre_position"
	];

	frappe.db.get_single_value("Transport Settings", "create_tyre_movement_from_service_job_card")
		.then(enabled => {
			const show = cint(enabled || 0) === 1;
			tyre_fields.forEach(fieldname => {
				if (frm.fields_dict[fieldname]) {
					frm.set_df_property(fieldname, "hidden", show ? 0 : 1);
				}
			});
			if (!show) {
				frm.set_value("tyre_serial", "");
				frm.set_value("tyre_movement_type", "");
				frm.set_value("tyre_install_on", "");
				frm.set_value("tyre_from_position", "");
				frm.set_value("tyre_to_position", "");
				frm.set_value("tyre_position", "");
			}
		})
		.catch(() => {
			tyre_fields.forEach(fieldname => {
				if (frm.fields_dict[fieldname]) {
					frm.set_df_property(fieldname, "hidden", 1);
				}
			});
		});
};

const toggleTyreMovementFields = frm => {
	const movement_type = frm.doc.tyre_movement_type || "";
	const is_positional = movement_type === "Positional Change";
	const has_movement = !!movement_type;

	if (frm.fields_dict.tyre_install_on) {
		frm.set_df_property("tyre_install_on", "hidden", has_movement ? 0 : 1);
	}
	if (frm.fields_dict.tyre_from_position) {
		frm.set_df_property("tyre_from_position", "hidden", is_positional ? 0 : 1);
	}
	if (frm.fields_dict.tyre_to_position) {
		frm.set_df_property("tyre_to_position", "hidden", is_positional ? 0 : 1);
	}
	if (frm.fields_dict.tyre_position) {
		frm.set_df_property("tyre_position", "hidden", is_positional ? 1 : 0);
	}

	if (is_positional) {
		frm.set_value("tyre_position", "");
	} else {
		frm.set_value("tyre_from_position", "");
		frm.set_value("tyre_to_position", "");
	}

	if (!has_movement) {
		frm.set_value("tyre_install_on", "");
	}
};


const setMatrialBtn = frm => {
	if (!frm.is_dirty() && frm.doc.docstatus == 0) {
		frm.add_custom_button('Create Stock Entry', () => {
			createStockEntry(frm);
		});
	}
	else {
		frm.remove_custom_button('Create Stock Entry');
	}
};

const createStockEntry = async function (frm) {
	if (frm.is_dirty()) {
		await frm.save();
	}
	frm.call('create_stock_entry', { type: "call" })
		.then(r => {
			frm.reload_doc();
		});
};

var get_qty_to_return = function(wrapper) {
	$.each(wrapper.find("tr:has(input:checkbox)"), function(index, row) {
		$(this).on("click", "input:checkbox", function() {
			if ($("input:checkbox").is(":checked") == true) {
				if ($(this).parent().siblings().last().html() == "") {
					$("<input type='number' id='return' style='border: 3px solid red; width: 60px;'>")
					.appendTo($(this).parent().siblings().last());

					$("#return").focusout("input", function() {
						let row_qty = $(this).parent().siblings().eq(-2).text();

						if (parseInt($("#return").val()) <= parseInt(row_qty) && parseInt($("#return").val()) > 0) {
							// store data to qty_to_return
							$(this).parent().siblings().last().attr("data-qty_to_return", $("#return").val())
							$("#return").css("border", "1px solid blue");

						} else {
							$("#return").css({ "border": "4px solid red", "font-weight": "bold" }).val("");
							frappe.msgprint({
								title: __('Message'),
								indicator: 'red',
								message: __(
									'<h4 class="text-center" style="background-color: orange; font-size: 13pt; font-weight: bold;">\
									Qty to return cannot be Negative, cannot be Zero(0) or Empty<br>\
									and cannot be greater than Qty<h4>'
								)
							});
						};
					});
				}
			} else {
				$(this).parent().siblings().last().html("");
			}
		});
	});
};