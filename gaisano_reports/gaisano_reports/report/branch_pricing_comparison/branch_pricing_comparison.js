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
		},
		{
		"fieldname": "perc_diff",
		"fieldtype": "Float",
		"label": "Percent Difference",
		"default": 5,
		"reqd": 1
		}
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if(typeof data[column.id]=='number'){
			if(column.id!='average_price'){
				var average = row[row.length-1].content
				var current = data[column.id]
				var perc_diff = frappe.query_report.get_filter_value('perc_diff');
				if(Math.abs(current - average) / average > perc_diff / 100)
					value = '<div style="background: rgb(245, 161, 161); color: rgb(128, 5, 5); font-weight: bold; margin:0px; padding:0px;">'+value+'</div>'
			}
		}
		return value
	}
};
