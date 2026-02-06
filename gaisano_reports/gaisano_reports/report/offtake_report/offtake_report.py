# Copyright (c) 2025, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	columns, data = [], []

	report_type = filters.get("report_type")
	from_date = datetime.datetime.strptime(filters.get('from_date'),"%Y-%m-%d")
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")
	branch = filters.get("branch")
	business_unit = filters.get("business_unit")
	division = filters.get("division") if filters.get("division") is not None else ""
	supplier = filters.get("supplier")

	if report_type == "Past 90 Days":
		data = get_data_3months(from_date, to_date, branch, business_unit, supplier, division)
	else:
		data = get_data_total(from_date, to_date, branch, business_unit, supplier, division)
	columns = get_columns(report_type, from_date, to_date)

	return columns, data

def get_columns(report_type, from_date, to_date):
	columns = []
	if report_type == "Total Only":
		columns = [
			{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 250},
			{"label": "Barcode", "fieldname": "barcode", "fieldtype": "Data", "width": 200},
			{"label": "UOM", "fieldname": "uom", "fieldtype": "Data", "width": 60},
			{"label": "Case Pack", "fieldname": "content_qty", "fieldtype": "Data", "width": 80},
			{"label": "Total Offtake", "fieldname": "total_offtake", "fieldtype": "Float", "precision":2, "width": 120},
			{"label": "Ave. Daily Offtake", "fieldname": "ave_daily_offtake", "fieldtype": "Float", "precision":2, "width": 120}
		]
	elif report_type == "Past 90 Days":
		m1 = str(from_date.date()) + " to " + str((from_date + datetime.timedelta(days=29)).date())
		m2 = str((from_date + datetime.timedelta(days=30)).date()) + " to " + str((from_date + datetime.timedelta(days=59)).date())
		m3 = str((from_date + datetime.timedelta(days=60)).date()) + " to " + str((from_date + datetime.timedelta(days=90)).date())
		columns = [
			{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 250},
			{"label": "Barcode", "fieldname": "barcode", "fieldtype": "Data", "width": 200},
			{"label": "UOM", "fieldname": "uom", "fieldtype": "Data", "width": 60},
			{"label": "Case Pack", "fieldname": "content_qty", "fieldtype": "Data", "width": 80},
			{"label": m1, "fieldname": "m1", "fieldtype": "Float", "precision":2, "width": 120},
			{"label": m2, "fieldname": "m2", "fieldtype": "Float", "precision":2, "width": 120},
			{"label": m3, "fieldname": "m3", "fieldtype": "Float", "precision":2, "width": 120},
			{"label": "Total Offtake", "fieldname": "total_offtake", "fieldtype": "Float", "precision":2, "width": 120},
			{"label": "Ave. Daily Offtake", "fieldname": "ave_daily_offtake", "fieldtype": "Float", "precision":2, "width": 120}
		]
	else: # Monthly Offtake
		columns = [
			{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 250},
			{"label": "Barcode", "fieldname": "barcode", "fieldtype": "Data", "width": 200},
			{"label": "UOM", "fieldname": "uom", "fieldtype": "Data", "width": 60},
			{"label": "Case Pack", "fieldname": "content_qty", "fieldtype": "Data", "width": 80},
			{"label": "Total Offtake", "fieldname": "total_offtake", "fieldtype": "Float", "precision":2, "width": 120},
			{"label": "Ave. Daily Offtake", "fieldname": "ave_daily_offtake", "fieldtype": "Float", "precision":2, "width": 120},
			{"label": "Ave. Monthly Offtake", "fieldname": "ave_monthly_offtake", "fieldtype": "Float", "precision":2, "width": 120}
		]
	return columns

def get_data_total(from_date, to_date, branch, business_unit, supplier, division = None):
	data = []
	where_clause = ""
	conditions = []

	to_date += datetime.timedelta(days=1) 

	if division != "":
		conditions.append("p.division_id = %s"%division)

	conditions.append("p.supplier_id = %s"%supplier)
	conditions.append("p.product_type !='P' and p.product_type !='A'")

	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause

	branch_code = get_branch(branch, business_unit)


	client = get_clickhouse_client()

	branch_code = get_branch(branch, business_unit)

	# REGULAR SALES QUERY
	pos_query = """LEFT OUTER JOIN (select P1.product_code, sum(pos.amount) as total_amount, sum(pos.qty) as total_qty from greports.pos_data pos join 
				(select mfg_code, barcode from greports.product where content_qty = 1) prod on pos.barcode = prod.barcode 
				join (select product_code, mfg_code from greports.product where content_qty = 1) P1 on P1.mfg_code = prod.mfg_code where branch = '%s' 
				and trans_date >= makeDate(%d,%d,%d) and trans_date < makeDate(%d,%d,%d)
				group by P1.product_code, pos.barcode) pos on p.product_code = pos.product_code"""%(branch_code, from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day)
	
	# WHOLESALE SALES QUERY
	ws_query = """LEFT OUTER JOIN (select P1.product_code, sum(pos.amount) as total_amount, sum(pos.qty*prod.content_qty) as total_qty 
				from greports.pos_data pos join (select mfg_code, barcode, content_qty from greports.product where content_qty > 1) 
				prod on pos.barcode = prod.barcode join (select product_code, mfg_code from greports.product where content_qty = 1) P1 on 
				P1.mfg_code = prod.mfg_code where branch = '%s' and trans_date >= makeDate(%d,%d,%d) and trans_date < makeDate(%d,%d,%d)
				group by P1.product_code, pos.barcode,prod.content_qty) ws on p.product_code = ws.product_code"""%(branch_code, from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day)

	# PACKING QUERY
	pck_query = """LEFT OUTER JOIN (select mfg_code, max(content_qty) as content_qty from greports.product group by mfg_code) as pck on p.mfg_code = pck.mfg_code"""

	query = """SELECT p.item_name, p.barcode, p.base_unit, pos.total_qty, ws.total_qty, pck.content_qty from greports.product p %s %s %s %s"""%(pos_query, ws_query, pck_query,where_clause)

	rows = client.query(query).result_rows

	for row in rows:
		pos = row[3] if row[3] is not None else 0
		ws = row[4] if row[4] is not None else 0
		total_offtake = pos + ws
		data.append({
			"item_name": row[0],
			"barcode": row[1],
			"uom": row[2],
			"content_qty": row[5] if row[5] is not None else 1,
			"total_offtake": total_offtake,
			"ave_daily_offtake": total_offtake / (to_date - from_date).days,
			"ave_monthly_offtake": 30* float(total_offtake) / float((to_date - from_date).days)
		})

	return data

def get_data_3months(from_date, to_date, branch, business_unit, supplier, division = None):
	data, m1_data, m2_data, m3_data = [], [], [], []
	raw_data = []
	where_clause = ""
	conditions = []
	m1, m2, m3 = 0,0,0
	
	m1_from= from_date
	m1_to = from_date + datetime.timedelta(days=29)
	m2_from = m1_to + datetime.timedelta(days=1)
	m2_to = m1_to + datetime.timedelta(days=29)
	m3_from = m2_to + datetime.timedelta(days=1)
	m3_to = to_date

	print(m1_from, m1_to)
	print(m2_from, m2_to)
	print(m3_from, m3_to)

	total_data = get_data_total(from_date, to_date, branch, business_unit, supplier, division)
	m1_data = get_data_total(m1_from, m1_to, branch, business_unit, supplier, division)
	m2_data = get_data_total(m2_from, m2_to, branch, business_unit, supplier, division)
	m3_data = get_data_total(m3_from, m3_to, branch, business_unit, supplier, division)

	for row in total_data:
		data.append({
			"item_name": row["item_name"],
			"barcode": row["barcode"],
			"uom": row["uom"],
			"content_qty": row["content_qty"],
			"total_offtake": row["total_offtake"],
			"ave_daily_offtake": row["total_offtake"]/90,
			"m1": get_month_sales(m1_data, row["barcode"]),
			"m2": get_month_sales(m2_data, row["barcode"]),
			"m3": get_month_sales(m3_data, row["barcode"])
			})
			
	return data

def get_branch(branch, business_unit):
	if business_unit == "GROCERY":
		return branch
	else:
		return frappe.db.get_value("Site",{"branch_mapping":branch,"site_type_code":"SEA","business_unit":"DEPTSTORE"},"ref_code")
	
def get_month_sales(mlist, barcode):
	for m in mlist:
		if m['barcode'] == barcode:
			return m['total_offtake']
	return 0
