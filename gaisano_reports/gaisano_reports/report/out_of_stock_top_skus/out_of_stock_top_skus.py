# Copyright (c) 2026, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	columns, data = [], []

	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")
	branch = filters.get("branch")
	supplier = filters.get("supplier") if filters.get("supplier") is not None else ""
	business_unit = filters.get("business_unit")

	data = get_data(branch, supplier, business_unit)

	columns = [
		{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 250},
		{"label": "Barcode", "fieldname": "barcode", "fieldtype": "Data", "width": 200},
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 200},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 150},
		{"label": "Site", "fieldname": "site", "fieldtype": "Data", "width": 150},
		{"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 150}
	]

	return columns, data

def get_data(branch, supplier, business_unit):
	data = []
	where_clause = ""
	conditions = []

	conditions.append("P.is_top_sku = true")

	if supplier != "":
		conditions.append("P.supplier_id = '%s'"%(supplier))
	
	site_code = get_site_code(branch, business_unit)
	conditions.append("INV.site_code = '%s'"%(site_code))

	conditions.append("INV.on_hand_quantity <= 0")

	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause

	client = get_clickhouse_client()

	query = """select INV.site_code, INV.on_hand_quantity, P.item_name, P.barcode, S.supplier_name, P.status from greports.site_inventory INV 
				join greports.product P on P.product_code = INV.product_code JOIN greports.supplier S on S.sup_id = P.supplier_id %s"""%(where_clause)

	rows = client.query(query).result_rows

	for row in rows:
		data.append({
			"qty": row[1],
			"site": get_ref_code(row[0]),
			"item_name": row[2],
			"barcode": row[3],
			"supplier": row[4],
			"status": "Active" if row[5] == "A" else ("Inactive" if row[5] == "I" else ("Phased Out" if row[5] == "P" else row[5]))
		})
	return data

def get_site_code(branch, business_unit):
	site_code = frappe.db.get_value("Site", {"branch_mapping": branch, "site_type_code":"MWH", "business_unit": business_unit}, "site_code")
	return site_code

def get_ref_code(site_code):
	print(site_code)
	return frappe.db.get_value("Site", {"site_code": site_code}, "ref_code")
