# Copyright (c) 2025, Gaisano IT and contributors
# For license information, please see license.txt

import frappe
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	columns, data = [], []
	
	data = get_data()
	columns = [
		{"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 200},
		{"label": "Classification", "fieldname": "classification", "fieldtype": "Data", "width": 200},
		{"label": "Subclass", "fieldname": "subclass", "fieldtype": "Data", "width": 200}
	]

	return columns, data


def get_data():
	data = []
	client = get_clickhouse_client()
	query = """SELECT distinct category, classification, subclass from greports.item_class_each order by category asc, classification asc, subclass asc"""
	rows = client.query(query).result_rows
	for row in rows:
		data.append({
			"category":row[0],
			"classification":row[1],
			"subclass":row[2]
		})
	return data




# query = """
#             SELECT
#                 item_code,
#                 item_name,
#                 class_name
#             FROM your_table
#             WHERE item_code = %(name)s
#             LIMIT 1
#         """