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
	data = get_ctrl(data)

	columns = [
		{"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 180},
		{"label": "Marketshare %", "fieldname": "marketshare", "fieldtype": "Float", "Precision":2, "width": 180},
		{"label": "% Ctrl", "fieldname": "ctrl", "fieldtype": "Float", "Precision":2, "width": 180}
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

	q_total = """(select sum(amount) from greports.pos_data pos join greports.item_class_each cat on pos.barcode = cat.barcode %s)"""%(where_clause)

	q_item_list = """select distinct cat.category, 100*sum(pos.amount)/%s as marketshare from greports.item_class_each cat
					join greports.pos_data pos on pos.barcode = cat.barcode %s group by cat.category
					order by marketshare desc
					"""%(q_total, where_clause)
	item_list = client.query(q_item_list).result_rows

	for row in item_list:

		data.append({
			"category":row[0],
			"marketshare": float(row[1])
		})
	
	return data

def get_ctrl(data):
	for i,row in enumerate(data):
		if i==0:
			data[i]['ctrl'] = data[i]['marketshare']
		else:
			data[i]['ctrl'] = data[i-1]['ctrl']+data[i]['marketshare']
	return data
