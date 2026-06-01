# Copyright (c) 2026, Gaisano IT and contributors
# For license information, please see license.txt

import frappe
from gaisano_reports.dbutils import get_clickhouse_client

def execute(filters=None):
	columns, data = [], []

	bu = filters.get("business_unit") if filters.get("business_unit") else ''
	site = filters.get("site_name") if filters.get("site_name") else ''
	supplier = filters.get("supplier") if filters.get("supplier") else ''

	columns = [
		{"fieldname": "item_name", "label": "Item", "fieldtype": "Data", "width": 150},
		{"fieldname": "barcode_reg", "label": "Regular Barcode", "fieldtype": "Data", "width": 150},
		{"fieldname": "barcode_case", "label": "Case Barcode", "fieldtype": "Data", "width": 150},
		{"fieldname": "barcode_alt", "label": "Alternate Barcode", "fieldtype": "Data", "width": 150},
		{"fieldname": "packing", "label": "Case Packing", "fieldtype": "Float", "width": 150},
		{"fieldname": "basic_cost_regular", "label": "Basic: Cost - Regular", "fieldtype": "Float", "width": 150},
		{"fieldname": "basic_cost_case", "label": "Basic: Cost - Case", "fieldtype": "Float", "width": 150},
		{"fieldname": "site_cost_regular", "label": "Site: Cost - Regular", "fieldtype": "Float", "width": 150},
		{"fieldname": "site_cost_case", "label": "Site: Cost - Case", "fieldtype": "Float", "width": 150},
		{"fieldname": "basic_po_discount", "label": "Basic: PO Discount", "fieldtype": "Data", "width": 150},
		{"fieldname": "site_po_discount", "label": "Site: PO Discount", "fieldtype": "Data", "width": 150},
		{"fieldname": "basic_bo_discount", "label": "Basic: BO Discount", "fieldtype": "Data", "width": 150},
		{"fieldname": "site_bo_discount", "label": "Site: BO Discount", "fieldtype": "Data", "width": 150},
		{"fieldname": "basic_status", "label": "Basic: Status", "fieldtype": "Data", "width": 150},
		{"fieldname": "site_status", "label": "Site: Status", "fieldtype": "Data", "width": 150}
	]

	data = get_data(site, supplier)

	return columns, data

def get_data(site, supplier):
	data = []
	client = get_clickhouse_client()

	query = """select B.product_code, B.item_name, B.barcode, B.mfg_code, B.landed_cost, B.po_discount, B.bo_discount, B.status, C.barcode, C.content_qty,
				C.landed_cost, S.landed_cost, S.po_discount, S.bo_discount, S.status, A.barcode, S2.landed_cost from greports.product B 
				left outer join (select product_code, mfg_code, barcode, content_qty, landed_cost from greports.product where content_qty > 1 and product_type = 'P' and 
				is_ordering_unit = true) as C on C.mfg_code = B.mfg_code left outer join 
				(select product_code, landed_cost, po_discount, bo_discount, status from greports.site_product where site_id=%s) as S
				on S.product_code = B.product_code left outer join 
				(select product_code, landed_cost, po_discount, bo_discount, status from greports.site_product where site_id=%s) as S2
				on S2.product_code = C.product_code
				LEFT OUTER JOIN (select product_code, barcode from greports.product where is_main_alternate = true and product_type = 'A')
				as A on A.product_code = B.product_code
				where B.product_type = '' and B.supplier_id = %s order by B.product_code asc"""%(site, site, supplier)
	
	rows = client.query(query).result_rows
	for row in rows:
		data.append({
			"item_name": row[1],
			"barcode_reg": row[2],
			"barcode_case": row[8] if row[8] else "",
			"barcode_alt": row[15] if row[15] else "",
			"packing": row[9] if row[9] else 0,
			"basic_cost_regular": row[4],
			"basic_cost_case": row[10],
			"site_cost_regular": row[11],
			"site_cost_case": row[16],
			"basic_status": row[7],
			"site_status": row[14],
			"basic_po_discount": row[5],
			"site_po_discount": row[12],
			"basic_bo_discount": row[6],
			"site_bo_discount": row[13]
		})

	return data
