# Copyright (c) 2025, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	from_date = datetime.datetime.strptime(filters.get('from_date'),"%Y-%m-%d")
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")+datetime.timedelta(days=1)
	branch = filters.get("branch")
	business_unit = filters.get("business_unit")
	supplier = filters.get("supplier")

	actual_branch = get_branch(branch, business_unit)

	columns = get_columns(from_date, to_date)
	data = get_data(from_date, to_date, actual_branch, supplier)

	return columns, data

def get_branch(branch, business_unit):
	if business_unit == "GROCERY":
		return branch
	else:
		branches = frappe.db.sql("""SELECT ref_code from `tabSite` where branch_mapping = %s and ref_code like '%DSSA%'""", branch)
		branch_list = [b.ref_code for b in branches]
		return branch_list[0][0] if branch_list else None
	
def get_data(from_date, to_date, branch, supplier):
	data = []
	ly_from = datetime.datetime(from_date.year -1, from_date.month, from_date.day)
	ly_to = datetime.datetime(to_date.year -1, to_date.month, to_date.day)

	ly_data = get_totals(ly_from, ly_to, branch, supplier)
	ty_data = get_totals(from_date, to_date, branch, supplier)

	growth_amount = ty_data[0] - ly_data[0]
	growth_percent = (growth_amount / ly_data[0] * 100) if ly_data[0] != 0 else 0
	data.append({"supplier": supplier if supplier != "" else "All Suppliers", 
			  "ly_sales": ly_data[0], "ty_sales": ty_data[0],
			  "growth_amount": growth_amount,
			  "growth_percent": growth_percent,
			  "ave_sellout": (ty_data[0] / ((to_date - from_date).days)) if (to_date - from_date).days > 0 else 0
			  })

	return data

def get_totals(from_date, to_date, branch, supplier):
	inner_query = ""
	data = []
	conditions = []

	client = get_clickhouse_client()
	
	
	conditions.append("trans_date >= makeDate(%d, %d, %d) and trans_date <= makeDate(%d, %d, %d)"%(from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day))

	if branch != "":
		conditions.append("branch = '%s'"%(branch))

	if supplier != "":
		conditions.append("barcode in (SELECT barcode from greports.product where supplier_id = '%s')"%(supplier))

	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause

	query = """SELECT sum(amount), sum(qty) from greports.pos_data %s"""% (where_clause)
	rows = client.query(query).result_rows

	return rows[0] if rows else (0,0)

def get_columns(from_date, to_date):
	ly_from = datetime.datetime(from_date.year -1, from_date.month, from_date.day)
	ly_to = datetime.datetime(to_date.year -1, to_date.month, to_date.day)
	ly_string = " %s to %s"%(ly_from.strftime("%b %d, %Y"), ly_to.strftime("%b %d, %Y"))
	ty_string = " %s to %s"%(from_date.strftime("%b %d, %Y"), to_date.strftime("%b %d, %Y"))
	columns = [
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 180},
		{"label": ly_string, "fieldname": "ly_sales", "fieldtype": "Float", "Precision":2, "width": 250},
		{"label": ty_string, "fieldname": "ty_sales", "fieldtype": "Float", "Precision":2, "width": 250},
		{"label": "Growth Amount", "fieldname": "growth_amount", "fieldtype": "Float", "Precision":2, "width": 250},
		{"label": "Growth %", "fieldname": "growth_percent", "fieldtype": "Percent", "Precision":2, "width": 180},
		{"label": "Ave. Daily Sellout", "fieldname": "ave_sellout", "fieldtype": "Float", "Precision":2, "width": 180}
	]
	return columns