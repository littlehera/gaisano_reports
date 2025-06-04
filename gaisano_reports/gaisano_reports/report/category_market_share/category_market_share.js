// Copyright (c) 2025, Gaisano IT and contributors
// For license information, please see license.txt

frappe.query_reports["Category Market Share"] = {
	"filters": [
		{
		"fieldname": "from_date",
		"fieldtype": "Date",
		"label": "From Date",
		"reqd": 1
		},
		{
		"fieldname": "to_date",
		"fieldtype": "Date",
		"label": "To Date",
		"reqd": 1
		},
		{
		"fieldname": "branch",
		"fieldtype": "Link",
		"label": "Branch",
		"options": "Branch",
		"reqd": 0
		}
	]
};
