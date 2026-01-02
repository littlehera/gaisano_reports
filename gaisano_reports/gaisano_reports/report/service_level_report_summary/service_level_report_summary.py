# Copyright (c) 2025, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	columns, data = [], []

	from_date = datetime.datetime.strptime(filters.get('from_date'),"%Y-%m-%d")
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")+datetime.timedelta(days=1)
	branch = filters.get("branch")
	business_unit = filters.get("business_unit")
	service_level = filters.get("service_level") if filters.get("service_level")  is not None else 0

	data = get_data(from_date, to_date, branch, business_unit, service_level)
	columns = [
	{"label": "Supplier ID", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 180},
	{"label": "Supplier Name", "fieldname": "supplier_name", "fieldtype": "Data", "width": 180},
	{"label": "PO qty", "fieldname": "po_qty", "fieldtype": "Float", "Precision":2, "width": 180},
	{"label": "PO Peso Value", "fieldname": "po_peso", "fieldtype": "Float", "Precision":2, "width": 180},
	{"label": "RR qty", "fieldname": "rr_qty", "fieldtype": "Float", "Precision":2, "width": 180},
	{"label": "RR Peso Value", "fieldname": "rr_peso", "fieldtype": "Float", "Precision":2, "width": 180},
	{"label": "SL Qty %", "fieldname": "sl_qty", "fieldtype": "Float", "Precision":2, "width": 180},
	{"label": "SL Peso %", "fieldname": "sl_peso", "fieldtype": "Float", "Precision":2, "width": 180}]

	#disable_prepared_report_being_checked("Service Level Report Summary")

	return columns, data

def get_data(from_date, to_date, branch, business_unit, service_level):
	data = []
	raw_data = []
	where_clause = ""
	conditions = []

	client = get_clickhouse_client()
	
	
	conditions.append("date >= makeDate(%d, %d, %d) and date < makeDate(%d, %d, %d)"%(from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day))

	if branch != "":
		site_codes = get_site_codes(branch, business_unit)
		conditions.append("site_code in %s"%(site_codes))

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
	
	data = get_sl_percentage(raw_data, service_level)

	return data

def get_sl_percentage(raw_data, service_level):
	data = []
	total_po_qty, total_po_peso, total_rr_qty, total_rr_peso = 0, 0, 0, 0
	current_supplier = ""

	raw_data.sort(key=lambda x: x['supplier'])
	for row in raw_data:
		if current_supplier =="":
			current_supplier = row['supplier']
		if current_supplier != row['supplier']:
			sl_qty = (total_rr_qty / total_po_qty * 100) if total_po_qty > 0 else 0
			sl_peso =(total_rr_peso / total_po_peso * 100) if total_po_peso > 0 else 0
			if (service_level ==0) or (sl_peso<=service_level or sl_qty<=service_level):
				data.append({
					'supplier':	current_supplier,
					'supplier_name': get_supplier_name(current_supplier),
					'po_qty': total_po_qty,
					'po_peso': total_po_peso,
					'rr_qty': total_rr_qty,
					'rr_peso': total_rr_peso,
					'sl_qty': sl_qty,
					'sl_peso': sl_peso
				})
			total_po_qty, total_po_peso, total_rr_qty, total_rr_peso = 0, 0, 0, 0
			current_supplier = row['supplier']
		
		total_po_qty += row["po_qty"]
		total_po_peso += row["po_peso"]
		total_rr_qty += row["rr_qty"]
		total_rr_peso += row["rr_peso"]

	sl_qty = (total_rr_qty / total_po_qty * 100) if total_po_qty > 0 else 0
	sl_peso =(total_rr_peso / total_po_peso * 100) if total_po_peso > 0 else 0
	print(sl_qty, sl_peso)
	if (service_level ==0) or (sl_peso<=service_level or sl_qty<=service_level):
		data.append({
			"supplier": current_supplier,
			"supplier_name": get_supplier_name(current_supplier),
			"po_qty": total_po_qty,
			"po_peso": total_po_peso,
			"rr_qty": total_rr_qty,
			"rr_peso": total_rr_peso,
			"sl_qty": sl_qty,
			"sl_peso": sl_peso
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

# def disable_prepared_report_being_checked(report_name):
#     """
#     Uncheck the prepared_report checkbox and remove `Prepared Report` entity (if any)
#     """
#     frappe.db.set_value('Report', report_name, 'prepared_report', 0)
#     # frappe.db.delete('Prepared Report')               # Truncates the entire table
#     frappe.db.delete('Prepared Report', {'report_name': report_name})
#     frappe.db.commit()

def get_supplier_name(supplier_id):
	supplier_name = frappe.db.get_value("Supplier", supplier_id, "supplier_name")
	return supplier_name if supplier_name else supplier_id