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
	supplier = filters.get("supplier")

	if report_type == "Total Only":
		data = get_data_total(from_date, to_date, branch, business_unit, supplier)
	else:
		data = get_data_3months(from_date, to_date, branch, business_unit, supplier)
	columns = get_columns(report_type, from_date, to_date)

	return columns, data

def get_columns(report_type, from_date, to_date):
	columns = []
	if report_type == "Total Only":
		columns = [
			{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 250},
			{"label": "Barcode", "fieldname": "barcode", "fieldtype": "Data", "width": 200},
			{"label": "UOM", "fieldname": "uom", "fieldtype": "Data", "width": 60},
			{"label": "Packing", "fieldname": "content_qty", "fieldtype": "Data", "width": 60},
			{"label": "Total Offtake", "fieldname": "total_offtake", "fieldtype": "Float", "precision":2, "width": 120},
			{"label": "Ave. Daily Offtake", "fieldname": "ave_daily_offtake", "fieldtype": "Float", "precision":2, "width": 120},
		]
	else:
		m1 = str(from_date.date()) + " to " + str((from_date + datetime.timedelta(days=30)).date())
		m2 = str((from_date + datetime.timedelta(days=30)).date()) + " to " + str((from_date + datetime.timedelta(days=60)).date())
		m3 = str((from_date + datetime.timedelta(days=60)).date()) + " to " + str((from_date + datetime.timedelta(days=90)).date())
		columns = [
			{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 250},
			{"label": "Barcode", "fieldname": "barcode", "fieldtype": "Data", "width": 200},
			{"label": "UOM", "fieldname": "uom", "fieldtype": "Data", "width": 60},
			{"label": "Packing", "fieldname": "content_qty", "fieldtype": "Data", "width": 60},
			{"label": m1, "fieldname": "m1", "fieldtype": "Float", "precision":2, "width": 120},
			{"label": m2, "fieldname": "m2", "fieldtype": "Float", "precision":2, "width": 120},
			{"label": m3, "fieldname": "m3", "fieldtype": "Float", "precision":2, "width": 120},
			{"label": "Total Offtake", "fieldname": "total_offtake", "fieldtype": "Float", "precision":2, "width": 120},
			{"label": "Ave. Daily Offtake", "fieldname": "ave_daily_offtake", "fieldtype": "Float", "precision":2, "width": 120},
		]
	return columns

def get_data_total(from_date, to_date, branch, business_unit, supplier):
	data = []
	raw_data = []
	where_clause = ""
	conditions = []

	to_date += datetime.timedelta(days=1) 

	client = get_clickhouse_client()
	
	conditions.append("pos.trans_code = 'REL' and pos.type_code='POS' and pos.status = 'P'")
	conditions.append("pos.doc_date >= makeDate(%d, %d, %d) and pos.doc_date < makeDate(%d, %d, %d)"%(from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day))

	if branch != "":
		site_codes = get_site_codes(branch, business_unit)
		conditions.append("pos.site_code in %s"%(site_codes))

	if supplier != "":
		conditions.append("prod.supplier_id = %s"%("'"+supplier+"'"))

	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause

	group_by = "group by prod.item_name, prod.barcode, prod.base_unit, prod.content_qty"

	query = """select prod.item_name, prod.barcode, prod.base_unit, prod.content_qty, sum(pos.quantity) from greports.barter_pos_data pos join greports.product prod 
	on prod.product_code = pos.product_code %s %s"""% (where_clause, group_by)

	print(query)

	rows = client.query(query).result_rows

	for row in rows:
		print(row)
		data.append({
			"item_name": row[0],
			"barcode": row[1],
			"uom": row[2],
			"content_qty": row[3],
			"total_offtake": row[4],
			"ave_daily_offtake": row[4] / (to_date - from_date).days
		})

	return data

def get_data_3months(from_date, to_date, branch, business_unit, supplier):
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

	total_data = get_data_total(from_date, to_date, branch, business_unit, supplier)
	m1_data = get_data_total(m1_from, m1_to, branch, business_unit, supplier)
	m2_data = get_data_total(m2_from, m2_to, branch, business_unit, supplier)
	m3_data = get_data_total(m3_from, m3_to, branch, business_unit, supplier)

	

	for row in total_data:
		print(row)
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

def get_site_codes(branch, business_unit):
	site_codes = "("
	rows = frappe.db.sql("""select site_code from `tabSite` where branch_mapping = %s and business_unit = %s""", (branch, business_unit))
	for i,row in enumerate(rows):
		site_codes+="'"+row[0]+"'"
		if i < len(rows) - 1:
			site_codes+=","
	site_codes+=")"
	return site_codes

def get_month_sales(mlist, barcode):
	for m in mlist:
		if m['barcode'] == barcode:
			return m['total_offtake']
	return 0