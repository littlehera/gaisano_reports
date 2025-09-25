import frappe
from gaisano_reports.dbutils import get_clickhouse_client

def truncate_frappe_table(tablename):
	frappe.db.sql("""TRUNCATE table %s""",(tablename))
	frappe.db.commit()

# #BARTER CATEGORIES SYNC
# def category_sync():
# 	client = get_clickhouse_client()
# 	query = """SELECT * from greports.category"""
# 	rows = client.query(query).result_rows
# 	for row in rows:
# 		print(row)

#BARTER SITE SYNC
def site_sync():
	client = get_clickhouse_client()
	query = """SELECT * from greports.site"""
	rows = client.query(query).result_rows
	for row in rows:
		print(row)
		if site_in_db(row[0]):
			print("update site")
			item_doc = frappe.get_doc("Site", {"site_id": row[0]})
			item_doc.site_code = row[1]
			item_doc.ref_code = row[2]
			item_doc.site_name = row[3]
			item_doc.active = 1 if row[4] == 'A' else 0
			item_doc.site_type_code = row[5]
			item_doc.business_unit= row[6]
			item_doc.company = row[7]
			item_doc.save(ignore_permissions=True)
			frappe.db.commit()
		else:
			try:
				print("insert site")
				site = frappe.get_doc({
					"doctype": "Site",
					"site_id": row[0],
					"site_code": row[1],
					"ref_code": row[2],
					"site_name": row[3],
					"active": 1 if row[4] == 'A' else 0,
					"site_type_code": row[5],
					"business_unit": row[6],
					"company": row[7]
				})
			except Exception as e:
				print(f"Error creating Site {row[2]}: {e}")
			else:
				site.insert(ignore_permissions=True)
				frappe.db.commit()
				print(f"Site {row[2]} created successfully.")

#BARTER SUPPLIER SYNC
def supplier_sync():
	client = get_clickhouse_client()
	query = """SELECT * from greports.supplier"""
	rows = client.query(query).result_rows
	for row in rows:
		print(row)
		if supplier_in_db(row[0]):
			print("update supplier")
			item_doc = frappe.get_doc("Supplier", {"sup_id": row[0]})
			item_doc.sup_code = row[1]
			item_doc.supplier_name = row[2]
			item_doc.cycle_days_a = int(row[3])
			item_doc.cycle_days_b = int(row[4])
			item_doc.offtake_days = int(row[7])
			item_doc.active = 1 if row[5] == 'A' else 0
			item_doc.save(ignore_permissions=True)
			frappe.db.commit()
		else:
			try:
				print("insert supplier")
				sup = frappe.get_doc({
					"doctype": "Supplier",
					"sup_id": row[0],
					"sup_code": row[1],
					"supplier_name": row[2],
					"cycle_days_a": int(row[3]),
					"cycle_days_b": int(row[4]),
					"offtake_days": int(row[7]),
					"active": 1 if row[5] == 'A' else 0
				})
			except Exception as e:
				print(f"Error creating Supplier {row[2]}: {e}")
			else:
				sup.insert(ignore_permissions=True)
				frappe.db.commit()
				print(f"Supplier {row[2]} created successfully.")
	#return data

def supplier_in_db(sup_id):
	sup = frappe.db.get_value("Supplier", {"sup_id": sup_id}, "name")
	if sup:
		return True
	else:
		return False

def site_in_db(site_id):
	site = frappe.db.get_value("Site", {"site_id": site_id}, "name")
	if site:
		return True
	else:
		return False