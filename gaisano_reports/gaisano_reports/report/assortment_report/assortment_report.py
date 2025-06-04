# Copyright (c) 2025, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client

def execute(filters=None):
	columns, data = [], []

	from_date = datetime.datetime.strptime(filters.get('from_date'),"%Y-%m-%d")
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")
	branch = filters.get('branch') if filters.get('branch') is not None else ""

	data = get_data(from_date, to_date, branch)

	columns = [
		{"label": "Item", "fieldname": "item_name", "fieldtype": "Data", "width": 300},
		{"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 180},
		{"label": "Classification", "fieldname": "classification", "fieldtype": "Data", "width": 180},
		{"label": "Subclass", "fieldname": "subclass", "fieldtype": "Data", "width": 180},
		{"label": "Marketshare", "fieldname": "marketshare", "fieldtype": "Float", "Precision":2, "width": 180}
	]

	return columns, data


def get_data(from_date, to_date, branch):
	data = []
	client = get_clickhouse_client()

	where_clause = ""
	conditions = []

	if branch != "":
		conditions.append("branch = %s"%("'"+branch+"'"))
	
	conditions.append("trans_date BETWEEN makeDate(%d,%d,%d) AND makeDate(%d,%d,%d)"%(from_date.year, from_date.month, from_date.day, 
																				   to_date.year, to_date.month, to_date.day))
	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause


	q_item_list = """select cat.item_name, sum(pos.amount), cat.category, cat.classification, cat.subclass from greports.item_class_each cat
					join greports.pos_data pos on pos.barcode = cat.barcode %s group by cat.category, cat.classification, cat.subclass, cat.item_name
					"""%(where_clause)
	item_list = client.query(q_item_list).result_rows

	q_total = """select sum(amount) from greports.pos_data %s"""%(where_clause)
	total_sales = client.query(q_total).result_rows

	total_sales = float(total_sales[0][0])

	for row in item_list:

		item_amount = float(row[1])
		marketshare = 100*(item_amount/total_sales)

		data.append({
			"item_name": row[0],
			"category":row[2],
			"classification":row[3],
			"subclass": row[4],
			"marketshare": marketshare
		})
	
	return data
