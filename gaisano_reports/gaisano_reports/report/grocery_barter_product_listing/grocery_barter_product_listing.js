// Copyright (c) 2026, Gaisano IT and contributors
// For license information, please see license.txt

frappe.query_reports["Grocery Barter Product Listing"] = {
	"filters": [
		{
		"fieldname": "business_unit",
		"fieldtype": "Link",
		"label": "Business Unit",
		"options": "Business Unit",
		"reqd": 1
		},
		{
		"fieldname": "site_name",
		"fieldtype": "Link",
		"label": "Barter Site",
		"options": "Site",
		"reqd": 1,
		"get_query": function(){
				var business_unit = frappe.query_report.get_filter_value('business_unit');
				var filters = get_filters(business_unit);
				return{
					"filters":filters
        		}
    		}
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


function get_filters(business_unit){
    return {"business_unit":business_unit}
}
