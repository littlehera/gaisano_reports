# Copyright (c) 2026, Gaisano IT and contributors
# For license information, please see license.txt

from tokenize import group
import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client

def execute(filters=None):
	columns, data = [], []

	report_type = filters.get("report_type")
	from_date = datetime.datetime.strptime(filters.get('from_date'),"%Y-%m-%d")
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")+datetime.timedelta(days=1)
	branch = filters.get("branch")
	warehouse_type = filters.get("warehouse_type")
	business_unit = filters.get("business_unit")
	supplier = filters.get("supplier") if filters.get("supplier") is not None else ""

	wh_type_code = "MWH" if warehouse_type == "Main Warehouse" else "SEA" if warehouse_type == "Selling Area" else "DSC"

	columns = get_columns(report_type)
	data = get_data(from_date, to_date, branch, business_unit, supplier, wh_type_code)

	return columns, data

def get_columns(report_type):
	columns = []
	if report_type == "QTY only":
		columns = [
			{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 300},
			{"label": "barcode", "fieldname": "barcode", "fieldtype": "Data", "width": 150},
			{"label": "RR Qty", "fieldname": "rr_qty", "fieldtype": "Float", "width": 100},
			{"label": "Sales Qty", "fieldname": "sales_qty", "fieldtype": "Float", "width": 100},
			{"label": "Ending Inventory Qty", "fieldname": "inventory_qty", "fieldtype": "Float", "width": 100}
		]
	elif report_type == "With Peso Value (Cost)":
		columns = [
			{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 300},
			{"label": "barcode", "fieldname": "barcode", "fieldtype": "Data", "width": 150},
			{"label": "Cost", "fieldname": "cost", "fieldtype": "Float", "width": 180},
			{"label": "RR Qty", "fieldname": "rr_qty", "fieldtype": "Float", "width": 100},
			{"label": "RR Peso", "fieldname": "rr_cost", "fieldtype": "Currency", "width": 220},
			{"label": "Sales Qty", "fieldname": "sales_qty", "fieldtype": "Float", "width": 100},
			{"label": "Sales Peso", "fieldname": "sales_cost", "fieldtype": "Currency", "width": 220},
			{"label": "Ending Inventory Qty", "fieldname": "inventory_qty", "fieldtype": "Float", "width": 100},
			{"label": "Ending Inventory Peso", "fieldname": "inventory_cost", "fieldtype": "Currency", "width": 220}
		]
	else:
		columns = [
			{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 300},
			{"label": "barcode", "fieldname": "barcode", "fieldtype": "Data", "width": 150},
			{"label": "Price", "fieldname": "price", "fieldtype": "Float", "width": 100},
			{"label": "RR Qty", "fieldname": "rr_qty", "fieldtype": "Float", "width": 100},
			{"label": "RR Peso", "fieldname":"rr_price", "fieldtype":"Currency", "width":"220"},
			{"label": "Sales Qty", "fieldname": "sales_qty", "fieldtype": "Float", "width": 100},
			{"label": "Sales Peso", "fieldname": "sales_price", "fieldtype": "Currency", "width": 220},
			{"label": "Ending Inventory Qty", "fieldname": "inventory_qty", "fieldtype": "Float", "width": 100},
			{"label": "Ending Inventory Peso", "fieldname": "inventory_price", "fieldtype": "Currency", "width": 220}
		]
	return columns

def get_data(from_date, to_date, branch, business_unit, supplier, wh_type_code):
	data = []
	where_clause = ""
	conditions = []

	client = get_clickhouse_client()

	conditions.append("p.supplier_id = %s"%supplier)
	conditions.append("p.product_type !='P' and p.product_type !='A'")

	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause

	site_code = get_site_code(branch, business_unit, wh_type_code)
	branch_code = get_branch(branch, business_unit)

	# RR TOTAL QUERY:

	rr_query = """LEFT OUTER JOIN (select P.product_code as product_code, C.product_code as case_code, sum(C.quantity * C.content_quantity) as total_qty 
				from greports.barter_rr_item C join (select mfg_code, product_code from greports.product) mfg on C.product_code = mfg.product_code
				join (select product_code, mfg_code from greports.product where content_qty = 1) P on mfg.mfg_code = P.mfg_code
				where C.supplier_id = %s and C.date >=makeDate(%d,%d,%d) and C.date < makeDate(%d,%d,%d) and C.status = 'P' and C.site_code = '%s'
				group by P.product_code, C.product_code) rr on p.product_code = rr.product_code"""%(supplier, from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day, site_code)

	print(rr_query)

	# INVENTORY QUERY
	inv_query = """LEFT OUTER JOIN (select product_code, sum(quantity) as total_qty from greports.inventory_movement where site_code = '%s' 
				and doc_date<makeDate(%d,%d,%d)	group by product_code) inv on p.product_code = inv.product_code"""%(site_code, to_date.year, to_date.month, to_date.day)
	
	print(inv_query)

	# REGULAR SALES QUERY
	pos_query = """LEFT OUTER JOIN (select P1.product_code, sum(pos.amount) as total_amount, sum(pos.qty) as total_qty from greports.pos_data pos join 
				(select mfg_code, barcode from greports.product where content_qty = 1) prod on pos.barcode = prod.barcode 
				join (select product_code, mfg_code from greports.product where content_qty = 1) P1 on P1.mfg_code = prod.mfg_code where branch = '%s' 
				and trans_date >= makeDate(%d,%d,%d) and trans_date < makeDate(%d,%d,%d)
				group by P1.product_code, pos.barcode) pos on p.product_code = pos.product_code"""%(branch_code, from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day)
	
	print(pos_query)
	
	# WHOLESALE SALES QUERY
	ws_query = """LEFT OUTER JOIN (select P1.product_code, sum(pos.amount) as total_amount, sum(pos.qty*prod.content_qty) as total_qty 
				from greports.pos_data pos join (select mfg_code, barcode, content_qty from greports.product where content_qty > 1) 
				prod on pos.barcode = prod.barcode join (select product_code, mfg_code from greports.product where content_qty = 1) P1 on 
				P1.mfg_code = prod.mfg_code where branch = '%s' and trans_date >= makeDate(%d,%d,%d) and trans_date < makeDate(%d,%d,%d)
				group by P1.product_code, pos.barcode,prod.content_qty) ws on p.product_code = ws.product_code"""%(branch_code, from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day)

	print(ws_query)

	# Fetch site cost, site price if existing. If not, use basic.
	sp_query = """LEFT OUTER JOIN (select product_code, landed_cost, retail_price from greports.site_product where site_id = %s) sp on 
				p.product_code = sp.product_code"""%(site_code)

	print(sp_query)

	query = """select p.item_name, p.barcode, rr.total_qty, inv.total_qty, pos.total_amount, pos.total_qty, ws.total_amount, ws.total_qty,
			sp.landed_cost, sp.retail_price, p.landed_cost, p.retail_price from greports.product p %s %s %s %s %s %s"""%(rr_query, inv_query, pos_query, ws_query, sp_query, where_clause)

	print(query)

	rows = client.query(query).result_rows
	for row in rows:
		pos_qty = row[5] if row[5] is not None else 0
		pos_sales = row[4] if row[4] is not None else 0
		ws_qty = row[7] if row[7] is not None else 0
		ws_sales = row[6] if row[6] is not None else 0
		
		data.append({
			"item_name": row[0],
			"barcode": row[1],
			"cost": row[8] if row[8] is not None else row[10],
			"price": row[9] if row[9] is not None else row[11],
			"rr_qty": row[2],
			"rr_cost": row[2]*row[8] if (row[8] is not None and row[8]>0) else row[2]*row[10],
			"rr_price": row[2]*row[9] if (row[9] is not None and row[9]>0) else row[2]*row[11],
			"inventory_qty": row[3],
			"inventory_cost": row[3]*row[8] if (row[8] is not None and row[8]>0) else row[3]*row[10],
			"inventory_price": row[3]*row[9] if (row[9] is not None and row[9]>0) else row[3]*row[11],
			"sales_qty": pos_qty + ws_qty,
			"sales_cost": (pos_qty * row[8] if (row[8] is not None and row[8]>0) else pos_qty * row[10]) + (ws_qty * row[8] if (row[8] is not None and row[8]>0) else ws_qty * row[10]),
			"sales_price": pos_sales + ws_sales
		})

	return data

def get_site_code(branch, business_unit, wh_type_code): #get site_code for INV queries (RR, Inv Movement)
	return frappe.db.get_value("Site", {"branch_mapping": branch, "business_unit": business_unit, "site_type_code": wh_type_code},"site_code")

def get_branch(branch, business_unit): #get branch for POS_DATA table
	if business_unit == "GROCERY":
		return branch
	else:
		return frappe.db.get_value("Site", {"branch_mapping": branch, "business_unit": "DEPTSTORE", "wh_type_code": "SEA"},"ref_code")