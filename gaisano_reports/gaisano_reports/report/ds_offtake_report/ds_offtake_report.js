// Copyright (c) 2026, Gaisano IT and contributors
// For license information, please see license.txt

frappe.query_reports["DS Offtake Report"] = {
	"filters": [
		{
		"fieldname": "report_type",
		"fieldtype": "Select",
		"label": "Report Type",
		"options": ["Total Only", "Past 90 Days", "Monthly Offtake"],
		"reqd": 1,
		"on_change": function(query_report){
			var report_type = frappe.query_report.get_filter_value('report_type');
			if (report_type == "Past 90 Days"){
				frappe.query_report.set_filter_value('to_date',frappe.datetime.get_today());
				var from_date = frappe.datetime.add_days(frappe.datetime.get_today(),-89);
				frappe.query_report.set_filter_value('from_date',from_date);
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
		"reqd": 1,
		"on_change": function(query_report){
			var to_date = frappe.query_report.get_filter_value('to_date');
			var report_type = frappe.query_report.get_filter_value('report_type');
			if (report_type == "Past 90 Days"){
				var from_date = frappe.datetime.add_days(to_date,-89);
				frappe.query_report.set_filter_value('from_date',from_date);
				frappe.query_report.refresh()
			}
			frappe.query_report.refresh()
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
		},
		{
		"fieldname": "department",
		"fieldtype": "Link",
		"label": "Department",
		"options": "Item Department",
		"reqd": 0,
		"get_query": function() {
			var division = frappe.query_report.get_filter_value('division');
			if(division){
				return {
					filters: {
						'status': 1,
						'parent_id': division
					}
				};
			}
			else{
				return{
						filters: {
						'status': 1
					}
				};
			}
		}
		},
		{
		"fieldname": "section",
		"fieldtype": "Link",
		"label": "Section",
		"options": "Item Section",
		"reqd": 0,
		"get_query": function() {
			var department = frappe.query_report.get_filter_value('department');
			if(department){
				return {
					filters: {
						'status': 1,
						'parent_id': department
					}
				};
			}
			else{
				return{
						filters: {
						'status': 1
					}
				};
			}
		}
		},
		{
		"fieldname": "category",
		"fieldtype": "Link",
		"label": "Category",
		"options": "Item Category",
		"reqd": 0,
		"get_query": function() {
			var section = frappe.query_report.get_filter_value('section');
			if(section){
				return {
					filters: {
						'status': 1,
						'parent_id': section
					}
				};
			}
			else{
				return{
						filters: {
						'status': 1
					}
				};
			}
		}
		}
	]
};
