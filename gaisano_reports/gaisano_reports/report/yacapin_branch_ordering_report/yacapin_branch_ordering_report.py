# Copyright (c) 2026, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime, decimal
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	columns, data = [], []
	from_date = datetime.datetime.strptime(filters.get('from_date'),"%Y-%m-%d")
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")+datetime.timedelta(days=1)
	branch = filters.get("branch")
	business_unit = filters.get("business_unit")
	supplier = filters.get("supplier") if filters.get("supplier")  is not None else ""
	multiplier = filters.get("multiplier") if filters.get("multiplier")  is not None else 1

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
		{"label": "Order Qty", "fieldname": "order_qty", "fieldtype": "Int", "width": 180},
		{"label": "Last Delivery", "fieldname": "last_delivery", "fieldtype": "Data", "width": 200}
	]
	
	rows = get_all_products(business_unit, supplier)
	site_code = get_site_code(branch, business_unit)
	for i,row in enumerate(rows):
		print(i," | ",len(rows)," | ", row[2])
		inv = get_inventory(row[0], site_code)
		item_sales = get_raw_data(from_date, to_date, branch, business_unit, row[0])
		daily_offtake = item_sales/days
		item_inv = inv if inv is not None else 0
		ordering_item = get_ordering_item(row[3])
		#last_delivery = get_last_delivery(row[0],site_code)
		order_qty = int(daily_offtake * multiplier - item_inv)
		if ordering_item is None:
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
			#last_delivery = get_last_delivery(ordering_item[0],site_code)
			case_offtake = item_sales/ordering_item[3]
			ave_offtake = case_offtake/days
			case_inv = inv/ordering_item[3] if inv is not None else 0
			order_qty = int(ave_offtake * multiplier - case_inv)
			data.append({
				'barcode': row[1],
				'case_barcode': ordering_item[1],
				'item_name': ordering_item[2],
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

def get_raw_data(from_date, to_date, branch, business_unit, product_code):
	data = []
	raw_data = []
	where_clause = ""
	group_by = ""
	conditions = []

	client = get_clickhouse_client()

	conditions.append("prod.product_code = '%s'"%(product_code))

	conditions.append("pos.trans_date >= makeDate(%d, %d, %d) and pos.trans_date <= makeDate(%d, %d, %d)"%(from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day))

	if branch != "":
		if business_unit == "GROCERY":
			conditions.append("pos.branch = '%s'"%(branch))
		else:
			conditions.append("pos.branch = '%s'"%(get_ref_code(branch)))

	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause
	
	query = """SELECT sum(pos.qty) from greports.product prod JOIN greports.pos_data pos ON pos.barcode = prod.barcode %s """% (where_clause)
	rows = client.query(query).result_rows
	for row in rows:
		return row[0]
	return 0

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

def get_ordering_item(mfg_code):
	query = """SELECT product_code, barcode, item_name, content_qty from greports.product where product_type = 'P' and 
				mfg_code = %s and is_ordering_unit = 1 """%("'"+mfg_code+"'")
	client = get_clickhouse_client()
	rows = client.query(query).result_rows
	for row in rows:
		return row
	return None

def get_all_products(business_unit, supplier_id = None):
	site_suffix = ""
	if business_unit == "GROCERY":
		site_suffix = '%GRSA%'
	else:
		site_suffix = '%DSSA%'
	if supplier_id != "":
		query = """SELECT product_code, barcode, item_name, mfg_code, supplier_id from greports.product where status not in ('D','I') and
					valid_site like %s and supplier_id = %s and product_type !='P'"""%("'"+site_suffix+"'", "'"+supplier_id+"'")
	else:
		query = """SELECT product_code, barcode, item_name, mfg_code, supplier_id from greports.product where status not in ('D','I') and
					valid_site like %s and product_type !='P'"""%("'"+site_suffix+"'")
	client = get_clickhouse_client()
	rows = client.query(query).result_rows
	return rows

def get_last_delivery(product_code, site_code):
	query = """SELECT H.doc_date, D.quantity from greportsraw.barter___inventory_doc_header H join greportsraw.barter___inventory_doc_detail D on 
			H.inventory_doc_id = D.inventory_doc_id where H.trans_code = 'REC' and H.status = 'P' and D.line_number >0 and D.product_code = %s
			and H.site_code = %s order by H.doc_date desc limit 1;"""%("'"+product_code+"'","'"+site_code+"'")
	client = get_clickhouse_client()
	rows = client.query(query).result_rows
	for row in rows:
		return datetime.datetime.strftime(row[0],"%Y-%m-%d")+" (QTY:"+str(row[1])+")"
	return "N/A"