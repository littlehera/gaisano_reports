import frappe
from gaisano_reports.dbutils import get_clickhouse_client

def truncate_frappe_table(tablename):
	frappe.db.sql("""TRUNCATE table %s""",(tablename))
	frappe.db.commit()

#BARTER CATEGORIES SYNC


########## CODE KODIGO
	# client = get_clickhouse_client()
	# query = """SELECT distinct category, classification, subclass from greports.item_class_each order by category asc, classification asc, subclass asc"""
	# rows = client.query(query).result_rows
	# for row in rows:
	# 	data.append({
	# 		"category":row[0],
	# 		"classification":row[1],
	# 		"subclass":row[2]
	# 	})
	# return data