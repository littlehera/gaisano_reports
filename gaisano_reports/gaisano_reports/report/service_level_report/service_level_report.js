// Copyright (c) 2025, Gaisano IT and contributors
// For license information, please see license.txt

frappe.query_reports["Service Level Report"] = {
	"filters": [
		{
		"fieldname": "report_type",
		"fieldtype": "Select",
		"label": "Report Type",
		"reqd": 1,
		"options":["Total Only", "Monthly Breakdown"],
		"on_change": function(query_report){
			var report_type = frappe.query_report.get_filter_value('report_type');
			if (report_type == "Monthly Breakdown"){
				var year = frappe.datetime.get_today().slice(0,4);
				frappe.query_report.set_filter_value('from_date',year+"-01-01");
				frappe.query_report.set_filter_value('to_date',year+"-12-31");
			}
			frappe.query_report.refresh()
			}
		},
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
		"fieldname": "supplier",
		"fieldtype": "Link",
		"label": "Supplier",
		"options": "Supplier",
		"reqd": 1
		}
	]
};
