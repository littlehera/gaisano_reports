# Copyright (c) 2025, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	columns, data = [], []

	report_type = filters.get("report_type")
	from_date = datetime.datetime.strptime(filters.get('from_date'),"%Y-%m-%d")
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")+datetime.timedelta(days=1)
	branch = filters.get("branch") if filters.get("branch") else ""
	business_unit = filters.get("business_unit")
	supplier = filters.get("supplier")

	columns = get_columns(report_type, from_date, to_date)
	data = get_data(report_type, from_date, to_date, branch, business_unit, supplier)
	return columns, data


def get_columns(report_type, from_date, to_date):
	columns = []
	if report_type == "Total Only":
		columns = [
		{"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 180},
		{"label": "RR Total Gross", "fieldname": "rr_gross", "fieldtype": "Float", "Precision":2, "width": 180},
		{"label": "RR Total Net", "fieldname": "rr_net", "fieldtype": "Float", "Precision":2, "width": 180}
		]
	else:
		date_limit = to_date
		columns = [
		{"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 180}
		]
		while from_date < date_limit:
			month_year = datetime.datetime.strftime(from_date, "%b %Y")
			columns.append({"label": f"{month_year}", "fieldname": f"{month_year}", "fieldtype": "Float", "Precision":2, "width": 150})
			from_date = datetime.datetime(from_date.year, from_date.month + 1, 1) if from_date.month < 12 else datetime.datetime(from_date.year + 1, 1, 1)
		columns.append({"label": "Total", "fieldname": "total", "fieldtype": "Float", "Precision":2, "width": 150})
	return columns

def get_data(report_type, from_date, to_date, branch, business_unit, supplier):
	from_date_original = from_date
	data = []
	if report_type == "Total Only":
		rr_data = get_rr_data(from_date, to_date, branch, business_unit, supplier)
		data = get_branch_totals(rr_data, report_type)
	else:
		date_limit = to_date
		while from_date < date_limit:
			to_date_monthly = datetime.datetime(from_date.year, from_date.month + 1, 1) if from_date.month < 12 else datetime.datetime(from_date.year + 1, 1, 1)
			month_year = datetime.datetime.strftime(from_date, "%b %Y")
			rr_data = get_rr_data(from_date, to_date_monthly, branch, business_unit, supplier)
			data += get_branch_totals(rr_data, report_type, month_year)
			from_date = datetime.datetime(from_date.year, from_date.month + 1, 1) if from_date.month < 12 else datetime.datetime(from_date.year + 1, 1, 1)
		print(data)
		data = get_rr_monthly(data, from_date_original, to_date, branch)
	return data


def get_rr_data(from_date, to_date, branch, business_unit, supplier):
	data = []
	client = get_clickhouse_client()
	where_clause = ""
	conditions = []	
	
	conditions.append("date >= makeDate(%d, %d, %d) and date < makeDate(%d, %d, %d)"%(from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day))
	conditions.append("status = 'P'")
	
	site_codes = get_site_codes(branch, business_unit)
	conditions.append("site_code in %s"%(site_codes))

	if supplier != "":
		conditions.append("supplier_id = %s"%(supplier))

	where_clause = " AND ".join(conditions)

	if where_clause != "":
		where_clause = "WHERE " + where_clause

	order_by = "ORDER BY site_code, date"

	query = """select site_code, date, supplier_id, discount_text, sub_total from greports.barter_rr_item %s %s"""% (where_clause, order_by)
	rows = client.query(query).result_rows

	for row in rows:
		branch = get_branch(row[0])
		date = row[1]
		supplier_id = row[2]
		discount_list = str(row[3]).split(",")
		sub_total = float(row[4])
		net_total = sub_total
		for discount in discount_list:
			discount = discount.replace('%','')
			if discount:
				net_total -= (float(net_total) * (float(str(discount)) / 100))
		data.append({
			'branch': branch,
			'date': date,
			'supplier_id': supplier_id,
			'sub_total': sub_total,
			'net_total': net_total
		})
	data = sorted(data, key=lambda d: d['branch'])
	return data

def get_branch_totals(rows, report_type, month_year=None):
	current_branch = ""
	rr_gross = 0
	rr_net = 0
	data = []
	for row in rows:
		branch = row['branch']
		sub_total = row['sub_total']
		net_total = row['net_total']
		if current_branch == "":
			current_branch = branch

		if branch != current_branch:
			if month_year is not None:
				data.append({
					'branch': current_branch,
					'month_year': month_year,
					month_year: rr_gross if report_type == "Monthly Breakdown (Gross)" else rr_net
				})
			else:
				data.append({
					'branch': current_branch,
					'rr_gross': rr_gross,
					'rr_net': rr_net
				})
			current_branch = branch
			rr_gross = 0
			rr_net = 0

		rr_gross += sub_total
		rr_net += net_total
	if month_year is not None:
		data.append({
			'branch': current_branch,
			'month_year': month_year,
			month_year: rr_gross if report_type == "Monthly Breakdown (Gross)" else rr_net
			})
	else:
		data.append({
				'branch': current_branch,
				'rr_gross': rr_gross,
				'rr_net': rr_net
				})
	return data

def get_rr_monthly(data, from_date, to_date, branch):
	from_date_original = from_date
	branches = []
	branch_list = []
	date_limit = to_date

	if branch == "":
		branches = frappe.db.sql("""select DISTINCT branch_mapping from `tabSite` order by branch_mapping asc""")
		for b in branches:
			if b[0] is None or b[0] == "":
				continue
			branch_list.append({'branch':b[0]})
			print(b[0])
	else:
		branch_list.append({'branch':branch})
		
	for b in branch_list:
			total = 0
			while from_date < date_limit:
				month_year = datetime.datetime.strftime(from_date, "%b %Y")			
				amount= get_month_year_data(data, b['branch'], month_year)
				total += amount
				b[month_year] = amount
				from_date = datetime.datetime(from_date.year, from_date.month + 1, 1) if from_date.month < 12 else datetime.datetime(from_date.year + 1, 1, 1)
			b['total'] = total
			from_date = from_date_original
	print(branch_list)
	return branch_list

def get_month_year_data(data, branch, month_year):
	for row in data:
		if row['branch'] == branch and row['month_year'] == month_year:
			return row[month_year]
	return 0


def get_site_codes(branch=None, business_unit=None):
	site_codes = "("
	rows = ""
	if branch == "":
		rows = frappe.db.sql("""select site_code from `tabSite` where business_unit = %s""", (business_unit))
	else:
		rows = frappe.db.sql("""select site_code from `tabSite` where branch_mapping = %s and business_unit = %s""", (branch, business_unit))

	for i,row in enumerate(rows):
		site_codes+="'"+row[0]+"'"
		if i < len(rows) - 1:
			site_codes+=","
	site_codes+=")"
	return site_codes

def get_branch(site_code):
	rows = frappe.db.sql("""select branch_mapping from `tabSite` where site_code = %s""", (site_code))
	return rows[0][0] if rows else None