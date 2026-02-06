// Copyright (c) 2026, Gaisano IT and contributors
// For license information, please see license.txt

frappe.query_reports["RR Sales Inventory per Supplier"] = {
	"filters": [
		{
		"fieldname": "report_type",
		"fieldtype": "Select",
		"label": "Report Type",
		"options": ["QTY only", "With Peso Value (Cost)", "With Peso Value (Price)"],
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
		"fieldtype": "Link",
		"label": "Branch",
		"options": "Branch",
		"reqd": 1
		},
		{
		"fieldname": "warehouse_type",
		"fieldtype": "Select",
		"label": "Warehouse Type",
		"options": ["Main Warehouse","Selling Area","Distribution Center"],
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
