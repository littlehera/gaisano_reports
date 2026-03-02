// Copyright (c) 2026, Gaisano IT and contributors
// For license information, please see license.txt

frappe.query_reports["Branch Pricing Comparison"] = {
	"filters": [
		{
		"fieldname": "report_type",
		"fieldtype": "Select",
		"label": "Report Type",
		"options": ["SRP", "Markup", "Margin"],
		"reqd": 1
		},
		{
		"fieldname": "branch",
		"fieldtype": "MultiSelectList",
		"label": "Branch",
		"options": "Branch",
		"get_data": function (txt) {
				return frappe.db.get_link_options("Branch", txt);
			},
			get_query: () => {
				return {
					filters: {}
				};
			},
		"reqd": 0
		},
		{
		"fieldname": "business_unit",
		"fieldtype": "Link",
		"label": "Business Unit",
		"options": "Business Unit",
		"reqd": 1
		},
		{
		"fieldname": "supplier",
		"fieldtype": "Link",
		"label": "Supplier",
		"options": "Supplier",
		"reqd": 1
		}
	]
};
