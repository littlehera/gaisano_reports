// Copyright (c) 2026, Gaisano IT and contributors
// For license information, please see license.txt

frappe.query_reports["Yacapin Branch Ordering Report"] = {
	"filters": [
		{
		"fieldname": "report_type",
		"fieldtype": "Select",
		"label": "Report Type",
		"options": ["All Items","With Order Qty Only"],
		"reqd": 1
		},
		{
		"fieldname": "past_eight_weeks",
		"fieldtype": "Check",
		"label": "Past 8 Weeks?",
		"on_change": function(query_report){
			var past_eight_weeks = frappe.query_report.get_filter_value('past_eight_weeks');
			if (past_eight_weeks){
				var to_date = frappe.datetime.add_days(frappe.datetime.get_today(),-1);
				frappe.query_report.set_filter_value('to_date',to_date);
				var from_date = frappe.datetime.add_days(frappe.datetime.get_today(),-56);
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
		},
		{
		"fieldname": "branch",
		"fieldtype": "Link",
		"label": "Branch",
		"options": "Branch",
		"reqd": 1
		},
		{
		"fieldname": "supplier",
		"fieldtype": "MultiSelectList",
		"label": "Supplier",
		"options": "Supplier",
		"width": 200,
		"get_data": function (txt) {
				return frappe.db.get_link_options("Supplier", txt);
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
		"fieldname": "multiplier",
		"fieldtype": "Float",
		"label": "Offtake Multiplier",
		"default": 5,
		"reqd": 0
		}
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		console.log(value, row, column, data)
        if(!(typeof data["inventory"]=="undefined"))
            if (data["inventory"]<=0){
				if(column.id=='inventory')
                	value = '<div style="background: #e69d59ff; margin:0px; padding:0px;">'+value+'</div>'
        }
        if(!(typeof data["order_qty"]=="undefined"))
            if (data["order_qty"] > 0){
				if(column.id=='order_qty')
               		value = '<div style="background: #6b9ddfff; margin:0px; padding:0px;">'+value+'</div>'
        }
		if(!(typeof data["cisl30"]=="undefined"))
            if (data["cisl30"] >= 1){
				if(column.id=='cisl30')
               		value = '<div style="background: #6bdf88ff; margin:0px; padding:0px;">'+value+'</div>'
        }
		return value
	}
};
