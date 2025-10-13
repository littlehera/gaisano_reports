# Copyright (c) 2025, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	columns, data = [], []

	report_type = filters.get("report_type")
	from_date = datetime.datetime.strptime(filters.get('from_date'),"%Y-%m-%d")
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")+datetime.timedelta(days=1)
	branch = filters.get("branch")
	business_unit = filters.get("business_unit")
	supplier = filters.get("supplier")

	if report_type == "Total Only":
		data = get_data(from_date, to_date, branch, business_unit, supplier)
		columns = [
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 180},
		{"label": "PO qty", "fieldname": "po_qty", "fieldtype": "Float", "Precision":2, "width": 180},
		{"label": "PO Peso Value", "fieldname": "po_peso", "fieldtype": "Float", "Precision":2, "width": 180},
		{"label": "RR qty", "fieldname": "rr_qty", "fieldtype": "Float", "Precision":2, "width": 180},
		{"label": "RR Peso Value", "fieldname": "rr_peso", "fieldtype": "Float", "Precision":2, "width": 180},
		{"label": "SL qty %", "fieldname": "sl_qty", "fieldtype": "Float", "Precision":2, "width": 180},
		{"label": "SL Peso %", "fieldname": "sl_peso", "fieldtype": "Float", "Precision":2, "width": 180}
	]
	else:
		data = get_monthly_data(from_date, to_date, branch, business_unit, supplier)
		columns = [
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 180},
		{"label": "PO qty", "fieldname": "po_qty", "fieldtype": "Float", "Precision":2, "width": 180},
		{"label": "PO Peso Value", "fieldname": "po_peso", "fieldtype": "Float", "Precision":2, "width": 180},
		{"label": "RR qty", "fieldname": "rr_qty", "fieldtype": "Float", "Precision":2, "width": 180},
		{"label": "RR Peso Value", "fieldname": "rr_peso", "fieldtype": "Float", "Precision":2, "width": 180},
		{"label": "SL qty %", "fieldname": "sl_qty", "fieldtype": "Float", "Precision":2, "width": 180},
		{"label": "SL Peso %", "fieldname": "sl_peso", "fieldtype": "Float", "Precision":2, "width": 180}
		]

	return columns, data

def get_data(from_date, to_date, branch, business_unit, supplier):
	data = []
	raw_data = []
	total_po_qty, total_po_peso, total_rr_qty, total_rr_peso = 0, 0, 0, 0
	where_clause = ""
	conditions = []

	client = get_clickhouse_client()
	
	
	conditions.append("date >= makeDate(%d, %d, %d) and date < makeDate(%d, %d, %d)"%(from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day))

	if branch != "":
		site_codes = get_site_codes(branch, business_unit)
		conditions.append("site_code in %s"%(site_codes))

	if supplier != "":
		conditions.append("supplier_id = %s"%("'"+supplier+"'"))

	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause

	query = """SELECT * from greports.po_sl %s"""% (where_clause)


	rows = client.query(query).result_rows

	for row in rows:
		rr_data = get_rr_data(row[0])
		raw_data.append({
			"supplier": row[1],
			"po_qty": row[4],
			"po_peso": row[5],
			"rr_qty": rr_data.get("rr_qty", 0),
			"rr_peso": rr_data.get("rr_peso", 0)
		})
	
	for row in raw_data:
		total_po_qty += row.get("po_qty", 0)
		total_po_peso += row.get("po_peso", 0)
		total_rr_qty += row.get("rr_qty", 0)
		total_rr_peso += row.get("rr_peso", 0)
	
	sl_qty = (total_rr_qty / total_po_qty * 100) if total_po_qty > 0 else 0
	sl_peso = (total_rr_peso / total_po_peso * 100) if total_po_peso > 0 else 0

	data.append({
		"supplier": supplier,
		"po_qty": total_po_qty,
		"po_peso": total_po_peso,
		"rr_qty": total_rr_qty,
		"rr_peso": total_rr_peso,
		"sl_qty": sl_qty,
		"sl_peso": sl_peso
	})

	return data

def get_monthly_data(from_date,to_date,_branch,business_unit,supplier):
	data = []
	date_counter = from_date
	while date_counter < to_date:
		from_ = date_counter
		to_ = datetime.datetime(date_counter.year, date_counter.month+1, 1) if date_counter.month < 12 else datetime.datetime(date_counter.year+1, 1, 1)
		print(from_,to_)
		temp = get_data(from_, to_, _branch, business_unit, supplier)
		temp[0]['supplier']= str(datetime.datetime.strftime(from_, "%B %Y"))
		data+=temp
		date_counter = to_
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

def get_rr_data(po_number):
	rrs = {"rr_qty": 0, "rr_peso": 0}
	query = """select sum(total_qty) as rr_qty, sum(total_amount) as rr_peso from greports.rr_sl where po_number = %s 
					 group by po_number"""%("'"+po_number+"'")
	client = get_clickhouse_client()
	rows = client.query(query).result_rows
	for row in rows:
		rrs['rr_qty']=row[0]
		rrs['rr_peso']=row[1]
	return rrs