import frappe
from gaisano_reports.dbutils import get_clickhouse_client

def truncate_frappe_table(tablename):
	frappe.db.sql("""TRUNCATE table %s""",(tablename))
	frappe.db.commit()

def execute_sync():
	site_sync()
	supplier_sync()
	division_sync()
	department_sync()

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

#BARTER DIVISION SYNC
def division_sync():
	client = get_clickhouse_client()
	query = """SELECT * from greports.category where level = 0"""
	rows = client.query(query).result_rows
	for row in rows:
		if division_in_db(row[0]):
			print("update division", row[1])
			item_doc = frappe.get_doc("Item Division", {"category_id": row[0]})
			item_doc.category_name = row[1]
			item_doc.status = 1 if row[2] == "A" else 0
			item_doc.save(ignore_permissions=True)
			frappe.db.commit()
		else:
			try:
				print("insert division", row[1])
				site = frappe.get_doc({
					"doctype": "Item Division",
					"category_id": row[0],
					"category_name": row[1],
					"status": 1 if row[2] == "A" else 0
				})
			except Exception as e:
				print(f"Error creating Division {row[1]}: {e}")
			else:
				site.insert(ignore_permissions=True)
				frappe.db.commit()
				print(f"Division {row[1]} created successfully.")

#BARTER DEPARTMENT SYNC
def department_sync():
	client = get_clickhouse_client()
	query = """SELECT * from greports.category where level = 1"""
	rows = client.query(query).result_rows
	for row in rows:
		if department_in_db(row[0]):
			print("update Department", row[1])
			item_doc = frappe.get_doc("Item Department", {"category_id": row[0]})
			item_doc.category_name = row[1]
			item_doc.status = 1 if row[2] == "A" else 0
			item_doc.parent_id = row[3]
			item_doc.save(ignore_permissions=True)
			frappe.db.commit()
		else:
			try:
				print("insert Department", row[1])
				site = frappe.get_doc({
					"doctype": "Item Department",
					"category_id": row[0],
					"category_name": row[1],
					"status": 1 if row[2] == "A" else 0,
					"parent_id": row[3]
				})
			except Exception as e:
				print(f"Error creating Department {row[1]}: {e}")
			else:
				site.insert(ignore_permissions=True)
				frappe.db.commit()
				print(f"Department {row[1]} created successfully.")

#BARTER SECTION SYNC
def section_sync():
	client = get_clickhouse_client()
	query = """SELECT * from greports.category where level = 2"""
	rows = client.query(query).result_rows
	for row in rows:
		if section_in_db(row[0]):
			print("update Section", row[1])
			item_doc = frappe.get_doc("Item Section", {"category_id": row[0]})
			item_doc.category_name = row[1]
			item_doc.status = 1 if row[2] == "A" else 0
			item_doc.parent_id = row[3]
			item_doc.save(ignore_permissions=True)
			frappe.db.commit()
		else:
			try:
				print("insert Section")
				site = frappe.get_doc({
					"doctype": "Item Section",
					"category_id": row[0],
					"category_name": row[1],
					"status": 1 if row[2] == "A" else 0,
					"parent_id": row[3]
				})
			except Exception as e:
				print(f"Error creating Section {row[1]}: {e}")
			else:
				site.insert(ignore_permissions=True)
				frappe.db.commit()
				print(f"Section {row[1]} created successfully.")

#BARTER CATEGORY SYNC
def category_sync():
	client = get_clickhouse_client()
	query = """SELECT * from greports.category where level = 3"""
	rows = client.query(query).result_rows
	for row in rows:
		if category_in_db(row[0]):
			print("update Category", row[1])
			item_doc = frappe.get_doc("Item Category", {"category_id": row[0]})
			item_doc.category_name = row[1]
			item_doc.status = 1 if row[2] == "A" else 0
			item_doc.parent_id = row[3]
			item_doc.save(ignore_permissions=True)
			frappe.db.commit()
		else:
			try:
				print("insert Category", row[1])
				site = frappe.get_doc({
					"doctype": "Item Category",
					"category_id": row[0],
					"category_name": row[1],
					"status": 1 if row[2] == "A" else 0,
					"parent_id": row[3]
				})
			except Exception as e:
				print(f"Error creating Category {row[0]}: {e}")
				continue
			else:
				site.insert(ignore_permissions=True)
				frappe.db.commit()
				print(f"Category {row[1]} created successfully.")

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

def division_in_db(category_id):
	division = frappe.db.get_value("Item Division", category_id)
	if division:
		return True
	else:
		return False

def department_in_db(category_id):
	department = frappe.db.get_value("Item Department", category_id)
	if department:
		return True
	else:
		return False

def section_in_db(category_id):
	section = frappe.db.get_value("Item Section", category_id)
	if section:
		return True
	else:
		return False

def category_in_db(category_id):
	category = frappe.db.get_value("Item Category", category_id)
	if category:
		return True
	else:
		return False