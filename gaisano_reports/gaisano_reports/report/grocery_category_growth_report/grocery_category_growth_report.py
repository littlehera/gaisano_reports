# Copyright (c) 2025, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	columns, data = [], []

	ref_date = filters.get('ref_date')
	
	data = get_data(ref_date)
	columns = [
		{"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 280},
		{"label": str(datetime.datetime.strptime(ref_date,"%Y-%m-%d").year-1), "fieldname": "ly", "fieldtype": "Float", "precision":2, "width": 200},
		{"label": str(datetime.datetime.strptime(ref_date,"%Y-%m-%d").year), "fieldname": "ty", "fieldtype": "Float", "precision":2, "width": 200},
		{"label": "%", "fieldname": "perc", "fieldtype": "Float", "precision":2, "width": 200}
	]

	return columns, data

def get_data(ref_date):

	data = []
	tylist = []


	today = datetime.datetime.strptime(ref_date,"%Y-%m-%d")
	
	lyFromDate = datetime.date(today.year-1,1,1)
	lyToDate = datetime.date(today.year-1,today.month, today.day)

	tyFromDate = datetime.date(today.year,1,1)
	tyToDate = today
	
	print(lyFromDate,lyToDate,tyFromDate,tyToDate)
	
	client = get_clickhouse_client()

	#the LAST YEAR query: Get the amount per category for last year
	lyquery = """SELECT cat.category, sum(pos.amount) from greports.item_class_each cat join greports.pos_data pos on cat.barcode = pos.barcode
				where trans_date between makeDate(%d,%d,%d) AND makeDate(%d,%d,%d)
				group by cat.category"""%(lyFromDate.year, lyFromDate.month, lyFromDate.day, lyToDate.year, lyToDate.month, lyToDate.day)
	lyrows = client.query(lyquery).result_rows

	#the THIS YEAR query: Get the amount per category for this year
	tyquery = """SELECT cat.category, sum(pos.amount) from greports.item_class_each cat join greports.pos_data pos on cat.barcode = pos.barcode
				where trans_date between makeDate(%d,%d,%d) AND makeDate(%d,%d,%d)
				group by cat.category"""%(tyFromDate.year, tyFromDate.month, tyFromDate.day, tyToDate.year, tyToDate.month, tyToDate.day)
	
	tyrows = client.query(tyquery).result_rows

	catquery = """SELECT distinct category from greports.item_class_each order by category asc"""
	rows = client.query(catquery).result_rows

	for row in rows:
		lyamount = get_amount(lyrows,row[0])
		tyamount = get_amount(tyrows,row[0])
		data.append({
			"category":row[0],
			"ly": lyamount,
			"ty": tyamount,
			"perc": (float(tyamount)/float(lyamount) if lyamount >0 else 1)*100
		})
	return data


def get_amount(catlist, search_value):
	amount = 0

	for row in catlist:
		if row[0] == search_value:
			amount = row[1]
			break
		else:
			continue
	return amount