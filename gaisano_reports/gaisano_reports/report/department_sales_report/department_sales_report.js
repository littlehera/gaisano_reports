// Copyright (c) 2025, Gaisano IT and contributors
// For license information, please see license.txt

frappe.query_reports["Department Sales Report"] = {
	"filters": [
		{
		"fieldname": "report_type",
		"fieldtype": "Select",
		"label": "Report Type",
		"options": ['Month to Date', 'Year to Date'],
		"reqd": 1
		},
		{
		"fieldname": "business_unit",
		"fieldtype": "Link",
		"label": "Business Unit",
		"options": "Business Unit",
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
		},
		{
		"fieldname": "division",
		"fieldtype": "Link",
		"label": "Division",
		"options": "Item Division",
		"reqd": 0,
		"get_query": function() {
			return {
				filters: {
					'status': 1
				}
			};
		}
	}

	]
};
