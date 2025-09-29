// Copyright (c) 2025, Gaisano IT and contributors
// For license information, please see license.txt

frappe.query_reports["Offtake Report"] = {
	"filters": [
		{
		"fieldname": "report_type",
		"fieldtype": "Select",
		"label": "Report Type",
		"options": ["Total Only", "Past 90 Days"],
		"reqd": 1,
		"on_change": function(query_report){
			var report_type = frappe.query_report.get_filter_value('report_type');
			if (report_type == "Past 90 Days"){
				frappe.query_report.set_filter_value('to_date',frappe.datetime.get_today());
				var from_date = frappe.datetime.add_days(frappe.datetime.get_today(),-90);
				frappe.query_report.set_filter_value('from_date',from_date);
				frappe.query_report.refresh()
			}
			else{
				frappe.query_report.set_filter_value('from_date','');
				frappe.query_report.set_filter_value('to_date','');
				frappe.query_report.refresh()
			}
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
		"reqd": 1,
		"on_change": function(query_report){
			var to_date = frappe.query_report.get_filter_value('to_date');
			var report_type = frappe.query_report.get_filter_value('report_type');
			if (report_type == "Past 90 Days"){
				var from_date = frappe.datetime.add_days(to_date,-90);
				frappe.query_report.set_filter_value('from_date',from_date);
				frappe.query_report.refresh()
			}
			}
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