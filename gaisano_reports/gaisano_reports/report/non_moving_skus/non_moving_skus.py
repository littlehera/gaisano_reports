# Copyright (c) 2026, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	columns, data = [], []

	from_date = datetime.datetime.strptime(filters.get('from_date'),"%Y-%m-%d")
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")+datetime.timedelta(days=1)
	branch = filters.get("branch")
	business_unit = filters.get("business_unit")
	supplier = filters.get("supplier") if filters.get("supplier") is not None else ""

	columns = [
		{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 250},
		{"label": "Barcode", "fieldname": "barcode", "fieldtype": "Data", "width": 200},
		#{"label": "Product Type", "fieldname": "product_type", "fieldtype": "Data", "width": 200},
		{"label": "Supplier ID", "fieldname": "supplier_id", "fieldtype": "Data", "width": 200},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 150}
	]

	data = get_data(from_date, to_date, branch, business_unit, supplier)

	return columns, data


def get_data(from_date, to_date, branch, business_unit, supplier):
	data = []
	where_clause = ""
	conditions = []

	client = get_clickhouse_client()

	valid_site = "%" + get_ref_code(branch, business_unit) + "%"

	if business_unit == 'DEPTSTORE':
		branch = get_ref_code(branch, business_unit)

	inner_query= """(select distinct barcode from greports.pos_data where branch = %s and trans_date >= makeDate(%d, %d, %d) and 
					trans_date < makeDate(%d, %d, %d))"""% ("'"+branch+"'", from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day)

	conditions.append("P.product_type <> 'P' and P.product_type <> 'A'")
	conditions.append("P.valid_site like '%s'"%(valid_site))
	conditions.append("P.barcode NOT IN %s"%(inner_query))
	conditions.append("P.mfg_code not in (select mfg_code from greports.product where barcode in %s)"%inner_query)

	if supplier != "":
		conditions.append("P.supplier_id = '%s'"%(supplier))
	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause

	query = """select P.item_name, P.barcode, P.product_type, S.supplier_name, P.status from greports.product P left join greports.supplier S
	 			on P.supplier_id = S.sup_id %s order by S.supplier_name asc"""% (where_clause)
	
	rows = client.query(query).result_rows
	for row in rows:
		data.append({
			"item_name": row[0],
			"barcode": row[1],
			"product_type": row[2],
			"supplier_id": row[3],
			"status": "Active" if row[4] == "A" else ("Inactive" if row[4] == "I" else ("Phased Out" if row[4] == "P" else row[4]))
		})
	return data


def get_ref_code(branch, business_unit):
	ref_code = frappe.db.get_value("Site", {"branch_mapping": branch, "site_type_code":"SEA", "business_unit": business_unit}, "ref_code")
	return ref_code
