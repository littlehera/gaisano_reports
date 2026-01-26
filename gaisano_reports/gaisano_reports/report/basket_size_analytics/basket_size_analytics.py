# Copyright (c) 2026, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	columns, data = [], []
	
	from_date = datetime.datetime.strptime(filters.get('from_date'),"%Y-%m-%d")
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")+datetime.timedelta(days=1)
	branch = filters.get("branch") if filters.get("branch") is not None else ""
	business_unit = filters.get("business_unit")
	report_type = filters.get("report_type")

	columns = get_columns(report_type, from_date, to_date)
	if report_type =="Total Only":
		data = get_data_total(from_date, to_date, branch, business_unit)
	elif report_type == "Monthly Breakdown":
		data = get_data_total(from_date, to_date, branch, business_unit)
	else:
		data = get_total_growth(from_date, to_date, branch, business_unit)

	return columns, data

def get_columns(report_type, from_date, to_date):
	if report_type =="Total Only":
		columns = [
			{"label": "Branch", "fieldname": "branch", "fieldtype": "Data", "width": 180},
			{"label": "Gross Sales", "fieldname": "gross_sales", "fieldtype": "Currency", "width": 180},
			{"label": "# of Transactions", "fieldname": "transactions", "fieldtype": "Float", "width": 180},
			{"label": "Basket Size", "fieldname": "basket_size", "fieldtype": "Currency", "width": 180}
		]
	# elif report_type == "Monthly Breakdown":
	# 	date_limit = to_date
	# 	columns = [{
	# 		"label": "Branch", "fieldname": "branch", "fieldtype": "Data", "width": 180
	# 	}]
	# 	while from_date < date_limit:
	# 		month_year = datetime.datetime.strftime(from_date, "%b %Y")
	# 		columns.append({"label": f"{month_year}", "fieldname": f"{month_year}", "fieldtype": "Float", "Precision":2, "width": 150})
	# 		from_date = datetime.datetime(from_date.year, from_date.month + 1, 1) if from_date.month < 12 else datetime.datetime(from_date.year + 1, 1, 1)
	# 	columns.append({"label": "Average", "fieldname": "average", "fieldtype": "Float", "Precision":2, "width": 150})
	else:
		columns = [
			{"label": "Branch", "fieldname": "branch", "fieldtype": "Data", "width": 180},
			{"label": "Gross Sales", "fieldname": "gross_sales", "fieldtype": "Currency", "width": 180},
			{"label": "# of Transactions", "fieldname": "transactions", "fieldtype": "Float", "width": 180},
			{"label": "Ave. Customers per Day", "fieldname": "customers", "fieldtype": "Float", "width": 180},
			{"label": "Current Period Basket Size", "fieldname": "current_basket_size", "fieldtype": "Currency", "width": 180},
			{"label": "Previous Period Basket Size", "fieldname": "previous_basket_size", "fieldtype": "Currency", "width": 180},
			{"label": "Growth (%)", "fieldname": "growth_percentage", "fieldtype": "Percent", "width": 150}
		]
	return columns

def get_data_total(from_date, to_date, branch, business_unit):
	data = []
	conditions = []
	where_clause = ""

	client = get_clickhouse_client()

	pos_data_query = """select site_code, sum(sub_total) as gross_sales, count(distinct inventory_doc_id) as transactions, gross_sales/transactions as basket_size from greports.barter_pos_data"""
	qroup_by_clause = "group by site_code"

	conditions.append("doc_date >= makeDate(%d, %d, %d) and doc_date < makeDate(%d, %d, %d)"%(from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day))
	conditions.append("trans_code = 'REL' AND type_code = 'POS' AND status = 'P'")

	if branch != "":
		site_codes = get_site_codes(branch, business_unit)
	else:
		site_codes = get_site_codes("", business_unit)
	
	conditions.append("site_code IN %s"%(site_codes))

	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause

	final_query = "%s %s %s"%(pos_data_query, where_clause, qroup_by_clause)
	rows = client.query(final_query).result_rows

	print(final_query)
	for row in rows:
		data.append({
			"branch": get_branch(row[0]),
			"gross_sales": row[1],
			"transactions": row[2],
			"current_basket_size": row[3],
			"previous_basket_size": row[4]
		})

	return data

def get_total_monthly(from_date, to_date, branch, business_unit):
	pass

def get_total_growth(from_date, to_date, branch, business_unit):
	data = []
	conditions_current = []
	conditions_previous = []
	where_clause_current= ""
	where_clause_previous= ""
	

	client = get_clickhouse_client()

	main_query = """SELECT S.site_code, C.gross_sales, C.transactions, C.basket_size, P.basket_size from greports.site as S"""
	data_query = """LEFT JOIN (select site_code, sum(sub_total) as gross_sales, count(distinct inventory_doc_id) as transactions, gross_sales/transactions as basket_size from greports.barter_pos_data"""
	qroup_by_clause = "group by site_code"

	conditions_current.append("doc_date >= makeDate(%d, %d, %d) and doc_date < makeDate(%d, %d, %d)"%(from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day))
	conditions_current.append("trans_code = 'REL' AND type_code = 'POS' AND status = 'P'")

	conditions_previous.append("doc_date >= makeDate(%d, %d, %d) and doc_date < makeDate(%d, %d, %d)"%(from_date.year -1, from_date.month, from_date.day, to_date.year -1, to_date.month, to_date.day))
	conditions_previous.append("trans_code = 'REL' AND type_code = 'POS' AND status = 'P'")
	
	if branch != "":
		site_codes = get_site_codes(branch, business_unit)
	else:
		site_codes = get_site_codes("", business_unit)
	
	conditions_current.append("site_code IN %s"%(site_codes))
	conditions_previous.append("site_code IN %s"%(site_codes))

	where_clause_current = " AND ".join(conditions_current)
	if where_clause_current != "":
		where_clause_current = "WHERE " + where_clause_current

	where_clause_previous = " AND ".join(conditions_previous)
	if where_clause_previous != "":
		where_clause_previous = "WHERE " + where_clause_previous

	where_clause_final = "WHERE S.site_code IN %s"%(site_codes)

	current_query = "%s %s %s) C on S.site_code = C.site_code"%(data_query, where_clause_current, qroup_by_clause)
	previous_query = "%s %s %s) P on S.site_code = P.site_code"%(data_query, where_clause_previous, qroup_by_clause)

	final_query = "%s %s %s %s"%(main_query, current_query, previous_query, where_clause_final)

	rows = client.query(final_query).result_rows

	print(current_query)
	print(previous_query)
	print(final_query)
	for row in rows:
		data.append({
			"branch": get_branch(row[0]),
			"gross_sales": row[1],
			"transactions": row[2],
			"customers": row[2]/((to_date - from_date).days+1),
			"current_basket_size": row[3],
			"previous_basket_size": row[4],
			"growth_percentage": ((row[3]/row[4])-1)*100 if row[4] and row[4] !=0 else 0
		})

	return data

def get_site_codes(branch, business_unit):
	site_codes = "("
	if branch !="":
		rows = frappe.db.sql("""select site_code from `tabSite` where branch_mapping = %s and business_unit = %s and site_type_code = 'SEA'""", (branch, business_unit))
	else:
		rows = frappe.db.sql("""select site_code from `tabSite` where business_unit = %s and site_type_code = 'SEA'""", (business_unit))
	for i,row in enumerate(rows):
		site_codes+="'"+row[0]+"'"
		if i < len(rows) - 1:
			site_codes+=","
	site_codes+=")"
	return site_codes

def get_branch(site_code):
	branch = frappe.db.get_value("Site", {"site_code": site_code}, "branch_mapping")
	return branch