// Copyright (c) 2025, Gaisano IT and contributors
// For license information, please see license.txt

frappe.query_reports["Department Sales Report"] = {
	"filters": [
		{
		"fieldname": "business_unit",
		"fieldtype": "Link",
		"label": "Business Unit",
		"options": "Business Unit",
		"reqd": 1
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
