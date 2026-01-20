# Copyright (c) 2026, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	columns, data = [], []

	report_type = filters.get("report_type")
	rr_date = datetime.datetime.strptime(filters.get('rr_date'),"%Y-%m-%d")
	branch = filters.get("branch")
	business_unit = filters.get("business_unit")

	if report_type == "Service Level per RR":
		columns = [
			{"label": "Supplier", 'width': 350, "fieldname": "supplier"},
			{"label": "Receiving Report", 'width': 150, "fieldname": "rr"},
			{"label": "Purchase Order", 'width': 150, "fieldname": "po"},
			{"label": "Service Level qty", 'width': 150, "fieldname": "sl_qty", "fieldtype": "Float", "precision": 2},
			{"label": "Service Level peso", 'width': 150, "fieldname": "sl_peso", "fieldtype": "Float", "precision": 2}
		]
	else:
		columns = [
			{"label": "Supplier", 'width': 150, "fieldname": "supplier"},
			{"label": "Service Level qty", 'width': 150, "fieldname": "sl_qty", "fieldtype": "Float", "precision": 2},
			{"label": "Service Level peso", 'width': 150, "fieldname": "sl_peso", "fieldtype": "Float", "precision": 2}
		]

	data = get_data(report_type,rr_date, branch, business_unit)

	return columns, data


def get_data(report_type, date, branch, business_unit):
	data = []
	where_clause = ""
	conditions = []
	po_query = ""
	group_by = ""

	client = get_clickhouse_client()

	
	
	conditions.append("RR.date == makeDate(%d, %d, %d)"%(date.year, date.month, date.day))

	if branch != "":
		site_codes = get_site_codes(branch, business_unit)
		po_query = """JOIN (select po_number, supplier_id, site_code, total_qty, total_amount from greports.po_sl where site_code in %s) 
					as PO on RR.po_number = PO.po_number"""%(site_codes)

	where_clause = " AND ".join(conditions)

	if where_clause != "":
		where_clause = "WHERE " + where_clause

	if report_type!="Service Level per RR":
		group_by = "GROUP BY PO.supplier_id"

		query = """SELECT PO.supplier_id, sum(PO.total_qty), sum(PO.total_amount), sum(RR.total_qty), sum(RR.total_amount) from greports.rr_sl RR %s %s %s"""% (po_query,where_clause, group_by)

		rows = client.query(query).result_rows

		for row in rows:
			rr_qty = row[3] if row[3] is not None else 0
			rr_peso = row[4] if row[4] is not None else 0
			data.append({
				"supplier": get_supplier_name(row[0]),
				"sl_qty": (rr_qty/row[1])*100 if row[1] > 0 else 0,
				"sl_peso": (rr_peso/row[2])*100 if row[2] > 0 else 0,
			})
	else:
		query = """SELECT RR.rr_id, PO.supplier_id, PO.site_code, PO.total_qty, PO.total_amount, RR.total_qty, RR.total_amount, PO.po_number from greports.rr_sl RR %s %s"""% (po_query,where_clause)
		rows = client.query(query).result_rows

		for row in rows:
			rr_qty = row[5] if row[5] is not None else 0
			rr_peso = row[6] if row[6] is not None else 0
			data.append({
				"supplier": get_supplier_name(row[1]),
				"rr": row[0],
				"po": row[7],
				"po_qty": row[3],
				"po_peso": row[4],
				"sl_qty": (rr_qty/row[3])*100 if row[3] > 0 else 0,
				"sl_peso": (rr_peso/row[4])*100 if row[4] > 0 else 0,
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
	print(site_codes)
	return site_codes

def get_supplier_name(supplier_id):
	supplier_name = frappe.db.get_value("Supplier", supplier_id, "supplier_name")
	return supplier_name if supplier_name else supplier_id