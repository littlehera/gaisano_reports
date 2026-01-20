# Copyright (c) 2026, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime, decimal
from gaisano_reports.dbutils import get_clickhouse_client

def get_conditions(filters):
	conditions = []
	return conditions

def execute(filters=None):
	columns, data = [], []
	from_date = datetime.datetime.strptime(filters.get('from_date'),"%Y-%m-%d")
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")+datetime.timedelta(days=1)
	branch = filters.get("branch")
	business_unit = filters.get("business_unit")
	supplier = filters.get("supplier") if filters.get("supplier")  is not None else ""
	multiplier = filters.get("multiplier") if filters.get("multiplier")  is not None else 1

	print(supplier)

	date_diff = to_date - from_date
	days = date_diff.days if date_diff.days > 0 else 1

	columns = [
		{"label": "Supplier Name", "fieldname": "supplier_name", "fieldtype": "Data", "width": 180},
		{"label": "Item Barcode", "fieldname": "barcode", "fieldtype": "Data", "width": 180},
		{"label": "Case Barcode", "fieldname": "case_barcode", "fieldtype": "Data", "width": 180},
		{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 180},
		{"label": "Qty Sold", "fieldname": "qty_sold", "fieldtype": "Float", "Precision":2, "width": 100},
		{"label": "Ave. Daily Offtake", "fieldname": "offtake", "fieldtype": "Float", "Precision":2, "width": 100},
		{"label": "30 Days Offtake", "fieldname": "cisl30", "fieldtype": "Float", "Precision":2, "width": 100},
		{"label": "Offtake x Multiplier", "fieldname": "cisl", "fieldtype": "Float", "Precision":2, "width": 100},
		{"label": "Inventory", "fieldname": "inventory", "fieldtype": "Float", "Precision":2, "width": 80},
		{"label": "Order Qty", "fieldname": "order_qty", "fieldtype": "Int", "width": 180}
		#{"label": "Last Delivery", "fieldname": "last_delivery", "fieldtype": "Data", "width": 200}
	]
	
	rows = get_raw_data(from_date, to_date, branch, supplier, business_unit)
	for i,row in enumerate(rows):
		print(i," | ",len(rows)," | ")
		
		item_sales = row[5]
		daily_offtake = item_sales/days
		item_inv = row[6]
		packing = row[8] if (row[8] is not None and row[8]!=0) else 1
		order_qty = int(daily_offtake * multiplier - item_inv)
		
		if order_qty == 1:
			data.append({
				'barcode': row[1],
				'case_barcode': "",
				'item_name': row[2],
				'supplier_id': row[4],
				'supplier_name': get_supplier_name(row[4]),
				'qty_sold': item_sales,
				'offtake': daily_offtake,
				'cisl': daily_offtake*multiplier,
				'cisl30': daily_offtake*30,
				'inventory': item_inv,
				'order_qty': order_qty
				#'last_delivery': last_delivery
			})
		else:
			case_offtake = item_sales/packing
			ave_offtake = case_offtake/days
			case_inv = item_inv/packing if item_inv is not None else 0
			order_qty = int(ave_offtake * multiplier - case_inv)
			data.append({
				'barcode': row[1],
				'case_barcode': row[7],
				'item_name': row[2],
				'supplier_id': row[4],
				'supplier_name': get_supplier_name(row[4]),
				'qty_sold': case_offtake,
				'offtake': ave_offtake,
				'cisl': ave_offtake*multiplier,
				'cisl30': ave_offtake*30,
				'inventory': case_inv,
				'order_qty': order_qty
				#'last_delivery': last_delivery
			})

	return columns, data

def get_raw_data(from_date, to_date, branch, supplier, business_unit):
	data = []
	raw_data = []
	where_clause = ""
	conditions = []
	site_code = get_site_code(branch, business_unit)
	pos_query = ""
	inv_query = ""
	orderitem_query = ""

	client = get_clickhouse_client()

	if branch != "":
		if business_unit == "GROCERY":
			pos_query = """LEFT OUTER JOIN (SELECT barcode, sum(qty) as offtake from greports.pos_data where branch = %s and trans_date >= makeDate(%d, %d, %d) 
					and trans_date <= makeDate(%d, %d, %d) group by barcode) as POS on PROD.barcode = POS.barcode"""%("'"+branch+"'", from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day)

		else:
			pos_query = """LEFT OUTER JOIN (SELECT barcode, sum(qty) as offtake from greports.pos_data where branch = %s and trans_date >= makeDate(%d, %d, %d) 
					and trans_date <= makeDate(%d, %d, %d) group by barcode) as POS on PROD.barcode = POS.barcode"""%("'"+get_ref_code(branch)+"'", from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day)
	
	inv_query = """ LEFT OUTER JOIN (SELECT product_code, on_hand_quantity from greports.site_inventory where site_code = %s) as INV on PROD.product_code = INV.product_code"""%("'"+site_code+"'")

	orderitem_query = """ LEFT OUTER JOIN (SELECT mfg_code, barcode as c_barcode, content_qty from greports.product where product_type = 'P' and is_ordering_unit = 1) as ORDITEM on PROD.mfg_code = ORDITEM.mfg_code"""


	conditions.append("PROD.status not in ('D','I') and PROD.product_type !='P'")

	if supplier != "" and supplier!=[]:
		supplier_list = "("
		for i,sup in enumerate(supplier):
			if i==0:
				supplier_list += "'"+sup+"'"
			else:
				supplier_list += "," + "'"+sup+"'"
		supplier_list += ")"
		#print(supplier_list)
		conditions.append("PROD.supplier_id in %s"%supplier_list)

	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause

	query = """SELECT PROD.product_code, PROD.barcode, PROD.item_name, PROD.mfg_code, PROD.supplier_id, POS.offtake, INV.on_hand_quantity, 
				ORDITEM.c_barcode, ORDITEM.content_qty from greports.product PROD %s %s %s %s ORDER BY PROD.supplier_id"""% (pos_query,inv_query, orderitem_query, where_clause)
	rows = client.query(query).result_rows
	return rows

def get_site_code(branch, business_unit):
	return frappe.db.get_value('Site',{'business_unit':business_unit,'site_type_code':'MWH', 'branch_mapping':branch},'site_code')

def get_supplier_name(supplier_id):
	supplier_name = frappe.db.get_value("Supplier", supplier_id, "supplier_name")
	return supplier_name if supplier_name else supplier_id

def get_inventory(product_code, site_code):
	query = """SELECT on_hand_quantity from greports.site_inventory where product_code = %s and site_code = %s"""%("'"+product_code+"'", "'"+site_code+"'")
	client = get_clickhouse_client()
	rows = client.query(query).result_rows

	for row in rows:
		return row[0]

def get_ref_code(branch):
	return frappe.db.get_value('Site',{'business_unit':'DEPTSTORE','site_type_code':'SEA', 'branch_mapping':branch},'ref_code')
