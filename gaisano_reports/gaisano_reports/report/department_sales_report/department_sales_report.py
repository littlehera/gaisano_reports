# Copyright (c) 2025, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client


def execute(filters=None):
	columns, data = [], []

	report_type = filters.get('report_type')
	bu = filters.get('business_unit')
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")+datetime.timedelta(days=1)
	month_start = datetime.datetime(to_date.year, to_date.month, 1)
	year_start = datetime.datetime(to_date.year, 1, 1)

	ly_to_date = datetime.datetime(to_date.year -1, to_date.month, to_date.day)
	ly_month_start = datetime.datetime(to_date.year-1, to_date.month, 1)
	ly_year_start = datetime.datetime(to_date.year -1, 1, 1)

	branch = filters.get("branch")
	division = filters.get("division")

	branch = get_branch_list(branch)

	mtd_query = get_query(month_start, to_date, branch, division)
	ly_mtd_query = get_query(ly_month_start,ly_to_date, branch, division)

	ytd_query = get_query(year_start, to_date, branch, division)
	ly_ytd_query = get_query(ly_year_start, ly_to_date, branch, division)

	columns = get_columns(report_type)

	if report_type == 'Month to Date':
		data = get_mtd_data(bu, division, ly_mtd_query, mtd_query)
	else:
		data = get_ytd_data(bu, division, ly_ytd_query, ytd_query)

	return columns, data

def get_query_data(query):
	data = []
	client = get_clickhouse_client()
	rows = client.query(query).result_rows
	for row in rows:
		data.append({
			"division_department": str(row[0]) + "-" + str(row[1]),
			"is_concession": row[2],
			"sales": row[3]
		})
	return data

def get_mtd_data(bu, division, ly_mtd_query, mtd_query):
	data = []
	division = division if (division != "" and division is not None) else None
	category_list = get_category_list(bu, division)
	ly_mtd = get_query_data(ly_mtd_query)
	mtd = get_query_data(mtd_query)

	mtd_orsob = get_total_sales(mtd,False)
	mtd_concsob = get_total_sales(mtd, True)
	mtd_total = get_total_sales(mtd, None)

	for category in category_list:
		division_department = category['division_department']

		mtd_orty = get_sales(mtd, division_department, False)
		mtd_orly = get_sales(ly_mtd, division_department, False)
		mtd_orgr = ((mtd_orty - mtd_orly) / mtd_orly * 100) if mtd_orly != 0 else None

		mtd_concty = get_sales(mtd, division_department, True)
		mtd_concly = get_sales(ly_mtd, division_department, True)
		mtd_concgr = ((mtd_concty - mtd_concly) / mtd_concly * 100) if mtd_concly != 0 else None

		if mtd_orty == 0 and mtd_orly == 0 and mtd_concty == 0 and mtd_concly == 0:
			continue

		data.append({
			"division": category['division'],
			"department": category['department'],
			"orty": mtd_orty,
			"orly": mtd_orly,
			"orgr": mtd_orgr,
			"concty": mtd_concty,
			"concly": mtd_concly,
			"concgr": mtd_concgr,
			"totalty": mtd_orty+mtd_concty,
			"totally": mtd_orly+mtd_concly,
			"totalgr": ((mtd_orty+mtd_concty)-(mtd_orly+mtd_concly))/(mtd_orly+mtd_concly)*100 if (mtd_orly+mtd_concly)!=0 else None,
			"orsob": mtd_orty/mtd_orsob*100 if mtd_orsob!=0 else None,
			"concsob": mtd_concty/mtd_concsob*100 if mtd_concsob!=0 else None,
			"totalsob": (mtd_orty+mtd_concty)/mtd_total*100 if mtd_total!=0 else None
		})

	data = get_division_totals(data,mtd_orsob, mtd_concsob, mtd_total)

	return data

def get_ytd_data(bu, division, ly_ytd_query, ytd_query):
	data = []
	division = division if (division != "" and division is not None) else None
	category_list = get_category_list(bu, division)
	ly_ytd = get_query_data(ly_ytd_query)
	ytd = get_query_data(ytd_query)

	ytd_orsob = get_total_sales(ytd,False)
	ytd_concsob = get_total_sales(ytd, True)
	ytd_total = get_total_sales(ytd, None)

	for category in category_list:
		division_department = category['division_department']

		ytd_orty = get_sales(ytd, division_department, False)
		ytd_orly = get_sales(ly_ytd, division_department, False)

		ytd_orgr = ((ytd_orty - ytd_orly) / ytd_orly * 100) if ytd_orly != 0 else None

		ytd_concty = get_sales(ytd, division_department, True)
		ytd_concly = get_sales(ly_ytd, division_department, True)
		ytd_concgr = ((ytd_concty - ytd_concly) / ytd_concly * 100) if ytd_concly != 0 else None

		if ytd_orty == 0 and ytd_orly == 0 and ytd_concty == 0 and ytd_concly == 0:
			continue

		data.append({
			"division": category['division'],
			"department": category['department'],
			"orty": ytd_orty,
			"orly": ytd_orly,
			"orgr": ytd_orgr,
			"concty": ytd_concty,
			"concly": ytd_concly,
			"concgr": ytd_concgr,
			"totalty": ytd_orty+ytd_concty,
			"totally": ytd_orly+ytd_concly,
			"totalgr": ((ytd_orty+ytd_concty)-(ytd_orly+ytd_concly))/(ytd_orly+ytd_concly)*100 if (ytd_orly+ytd_concly)!=0 else None,
			"orsob": ytd_orty/ytd_orsob*100 if ytd_orsob!=0 else None,
			"concsob": ytd_concty/ytd_concsob*100 if ytd_concsob!=0 else None,
			"totalsob": (ytd_orty+ytd_concty)/ytd_total*100 if ytd_total!=0 else None
		})

	data = get_division_totals(data,ytd_orly, ytd_concsob, ytd_total)

	return data

def get_columns(report_type):
	if report_type == 'Month to Date':
		columns = [
			{"fieldname": "division", "label": "Division", "fieldtype": "Data"},
			{"fieldname": "department", "label": "Department", "fieldtype": "Data"},
			{"fieldname": "orty", "label": "MTD OR TY", "fieldtype": "Float", "precision": 2},
			{"fieldname": "orly", "label": "MTD OR LY", "fieldtype": "Float", "precision": 2},
			{"fieldname": "orgr", "label": "MTD OR GROWTH", "fieldtype": "Percent", "precision": 2},
			{"fieldname": "concty", "label": "MTD CONC TY", "fieldtype": "Float", "precision": 2},
			{"fieldname": "concly", "label": "MTD CONC LY", "fieldtype": "Float", "precision": 2},
			{"fieldname": "concgr", "label": "MTD CONC GROWTH", "fieldtype": "Percent", "precision": 2},
			{"fieldname": "totalty", "label": "MTD TOTAL TY", "fieldtype": "Float", "precision": 2},
			{"fieldname": "totally", "label": "MTD TOTAL LY", "fieldtype": "Float", "precision": 2},
			{"fieldname": "totalgr", "label": "MTD TOTAL GROWTH", "fieldtype": "Percent", "precision": 2},
			{"fieldname": "orsob", "label": "MTD OR SOB", "fieldtype": "Percent", "precision": 2},
			{"fieldname": "concsob", "label": "MTD CONC SOB", "fieldtype": "Percent", "precision": 2},
			{"fieldname": "totalsob", "label": "MTD TOTAL SOB", "fieldtype": "Percent", "precision": 2}
		]
	else:
		columns = [
			{"fieldname": "division", "label": "Division", "fieldtype": "Data"},
			{"fieldname": "department", "label": "Department", "fieldtype": "Data"},
			{"fieldname": "orty", "label": "YTD OR TY", "fieldtype": "Float", "precision": 2},
			{"fieldname": "orly", "label": "YTD OR LY", "fieldtype": "Float", "precision": 2},
			{"fieldname": "orgr", "label": "YTD OR GROWTH", "fieldtype": "Percent", "precision": 2},
			{"fieldname": "concty", "label": "YTD CONC TY", "fieldtype": "Float", "precision": 2},
			{"fieldname": "concly", "label": "YTD CONC LY", "fieldtype": "Float", "precision": 2},
			{"fieldname": "concgr", "label": "YTD CONC GROWTH", "fieldtype": "Percent", "precision": 2},
			{"fieldname": "totalty", "label": "YTD TOTAL TY", "fieldtype": "Float", "precision": 2},
			{"fieldname": "totally", "label": "YTD TOTAL LY", "fieldtype": "Float", "precision": 2},
			{"fieldname": "totalgr", "label": "YTD TOTAL GROWTH", "fieldtype": "Percent", "precision": 2},
			{"fieldname": "orsob", "label": "YTD OR SOB", "fieldtype": "Percent", "precision": 2},
			{"fieldname": "concsob", "label": "YTD CONC SOB", "fieldtype": "Percent", "precision": 2},
			{"fieldname": "totalsob", "label": "YTD TOTAL SOB", "fieldtype": "Percent", "precision": 2}
		]

	return columns

def get_branch_list(branch):
	branches = frappe.db.sql("""SELECT ref_code from `tabSite` where branch_mapping = %s and ref_code like %s""", (branch, '%DSSA%'))
	return branches[0][0] if branches else None

def get_category_name(category_type, id):
	return frappe.db.get_value(category_type, {"category_id": id}, "category_name")

def get_query(from_date, to_date, branch, division):
	conditions = []
	where_clause = ""	
	group_by_clause = " group by prod.division_id, prod.department_id, prod.is_concession order by prod.division_id asc, prod.department_id asc;"

	conditions.append("pos.trans_date between makeDate(%d, %d, %d) and makeDate(%d, %d, %d)"%(from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day))

	if branch != "" and branch is not None:
		conditions.append("pos.branch = '%s'"%(branch))
	
	if division != "" and division is not None:
		conditions.append("prod.division_id = %s"%(division))
	
	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause
	
	query = """select prod.division_id, prod.department_id, prod.is_concession, sum(pos.amount) from greports.product prod 
				join greports.pos_data pos on pos.barcode = prod.barcode %s %s"""%(where_clause, group_by_clause)

	print(query)
	return query

def get_category_list(bu,division=None):
	department_division_list = []
	if division is None:
		query = """select distinct division_id, department_id from greports.product order by division_id asc, department_id asc;"""
	else:
		query = """select distinct division_id, department_id from greports.product where division_id = %s order by division_id asc, department_id asc;"""%(division)
	
	client = get_clickhouse_client()
	rows = client.query(query).result_rows
	for row in rows:
		if is_in_bu(bu,row[0]):
			department_division_list.append({
				"division": get_category_name("Item Division", row[0]),
				"department": get_category_name("Item Department", row[1]),
				"division_id": row[0],
				"department_id": row[1],
				"division_department": str(row[0]) + "-" + str(row[1])
			})
	return department_division_list

def get_sales(list,division_department, is_concession):
	for item in list:
		if item['division_department'] == division_department and item['is_concession'] == is_concession:
			return item['sales']
	return 0

def get_total_sales(list, is_concession=None):
	total = 0
	for item in list:
		if is_concession is None:
			total += item['sales']
		else:
			if item['is_concession'] == is_concession:
				total+=item['sales'] 
	return total

def is_in_bu(bu, division):
	division_list = frappe.db.sql("""SELECT COUNT(*) from `tabItem Division` where (business_unit = %s or business_unit2=%s) and name = %s""", (bu,bu, division))
	if division_list[0][0]>0:
		return True
	else:
		return False

def get_division_totals(data, orsob, concsob, totalsob):
	new_list = []
	newlist = sorted(data, key=lambda d: d['division'])
	current_division = ""
	division_total = 0

	orly, orty, concly, concty = 0,0,0,0
	for item in newlist:
		if current_division == "":
			current_division = item['division']
		
		if current_division != item['division']:
			new_list.append({
				"division": current_division+" TOTAL",
				"department": "",
				"orty": orty,
				"orly": orly,
				"orgr": ((orty - orly) / orly * 100) if orly != 0 else None,
				"concgr": ((concty - concly) / concly * 100) if concly != 0 else None,
				"concty": concty,
				"concly": concly,
				"totalty": orty+concty,
				"totally": orly+concly,
				"totalgr": ((orty+concty)-(orly+concly))/(orly+concly)*100 if (orly+concly)!=0 else None,
				"orsob": orty/orsob*100 if orsob!=0 else None,
				"concsob": concty/concsob*100 if concsob!=0 else None,
				"totalsob": (orty+concty)/totalsob*100 if totalsob!=0 else None
			})
			current_division = item['division']
			orly, orty, concly, concty = 0,0,0,0

		orly += item['orly']
		orty += item['orty']
		concly += item['concly']
		concty += item['concty']
		new_list.append(item)
	new_list.append({
	"division": current_division+" TOTAL",
	"department": "",
	"orty": orty,
	"orly": orly,
	"orgr": ((orty - orly) / orly * 100) if orly != 0 else None,
	"concgr": ((concty - concly) / concly * 100) if concly != 0 else None,
	"concty": concty,
	"concly": concly,
	"totalty": orty+concty,
	"totally": orly+concly,
	"totalgr": ((orty+concty)-(orly+concly))/(orly+concly)*100 if (orly+concly)!=0 else None,
	"orsob": orty/orsob*100 if orsob!=0 else None,
	"concsob": concty/concsob*100 if concsob!=0 else None,
	"totalsob": (orty+concty)/totalsob*100 if totalsob!=0 else None
	})
	
	return new_list
