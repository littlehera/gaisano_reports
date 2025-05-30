// Copyright (c) 2025, Gaisano IT and contributors
// For license information, please see license.txt

frappe.query_reports["Grocery Category Growth Report"] = {
	"filters": [
		{
		"fieldname": "ref_date",
		"fieldtype": "Date",
		"label": "Reference Date",
		"reqd": 1
		}
	]
};
