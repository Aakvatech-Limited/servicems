def get_data():
	return {
		"non_standard_fieldname": {
			dt: "service_job_card"
			for dt in ("Stock Entry", "Service Vehicle Inspection", "Quotation", "Sales Invoice")
		},
		"transactions": [
			{"items": ["Stock Entry", "Service Vehicle Inspection", "Quotation", "Sales Invoice"]}
		],
	}
