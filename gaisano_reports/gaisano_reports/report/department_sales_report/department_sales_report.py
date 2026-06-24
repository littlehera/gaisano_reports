# Copyright (c) 2025, Gaisano IT and contributors
# For license information, please see license.txt

import frappe, datetime
from gaisano_reports.dbutils import get_clickhouse_client
import pandas as pd


def execute(filters=None):
	columns, data = [], []

	bu = filters.get('business_unit')
	from_date = datetime.datetime.strptime(filters.get('from_date'),"%Y-%m-%d")
	to_date = datetime.datetime.strptime(filters.get('to_date'),"%Y-%m-%d")+datetime.timedelta(days=1)

	ly_from_date = datetime.datetime(from_date.year -1, from_date.month, from_date.day)
	ly_to_date = datetime.datetime(to_date.year -1, to_date.month, to_date.day)

	branch = filters.get("branch")
	division = filters.get("division")
	department = filters.get("department")
	section = filters.get("section")
	category = filters.get("category")

	if branch is None or branch == []:
		frappe.throw("Please select Branch/es!")

	branches = get_branch_list(bu, branch)
	division_list = get_division_list(bu, division)

	data = get_query_data(ly_from_date, ly_to_date, from_date, to_date, branches, division_list, division, department, section, category)

	# df = pd.DataFrame(data)
	# data.extend(df.groupby(["division", "department", "section"])[["ly_amount_concession","ty_amount_concession", "ly_amount_outright", "ty_amount_outright", "ly_amount_total", "ty_amount_total"]].sum().reset_index().to_dict("records"))
	# data.extend(df.groupby(["division", "department"])[["ly_amount_concession","ty_amount_concession", "ly_amount_outright", "ty_amount_outright", "ly_amount_total", "ty_amount_total"]].sum().reset_index().to_dict("records"))
	# data.extend(df.groupby(["division"])[["ly_amount_concession","ty_amount_concession", "ly_amount_outright", "ty_amount_outright", "ly_amount_total", "ty_amount_total"]].sum().reset_index().to_dict("records"))

	# data = data_sort(data)


	columns = [
		{"fieldname": "division", "label": "Division", "fieldtype": "Link", "options": "Item Division", "width": 150},
		{"fieldname": "department", "label": "Department", "fieldtype": "Data", "options": "Item Department", "width": 150},
		{"fieldname": "section", "label": "Section", "fieldtype": "Data", "options": "Item Section", "width": 150},
		{"fieldname": "category", "label": "Category", "fieldtype": "Data", "options": "Item Category", "width": 150},
		{"fieldname": "ly_amount_concession", "label": "LY Concession", "fieldtype": "Currency", "width": 120},
		{"fieldname": "ty_amount_concession", "label": "TY Concession", "fieldtype": "Currency", "width": 120},
		{"fieldname": "growth_concession", "label": "Growth Concession", "fieldtype": "Float", "precision": 2, "width": 120},
		{"fieldname": "ly_amount_outright", "label": "LY Outright", "fieldtype": "Currency", "width": 120},
		{"fieldname": "ty_amount_outright", "label": "TY Outright", "fieldtype": "Currency", "width": 120},
		{"fieldname": "growth_outright", "label": "Growth Outright", "fieldtype": "Float", "precision": 2, "width": 120},
		{"fieldname": "ly_amount_total", "label": "LY Total", "fieldtype": "Currency", "width": 120},
		{"fieldname": "ty_amount_total", "label": "TY Total", "fieldtype": "Currency", "width": 120},
		{"fieldname": "growth_total", "label": "Growth Total", "fieldtype": "Float", "precision": 2, "width": 120}
		
	]

	return columns, data


def get_query_data(ly_from_date, ly_to_date, from_date, to_date, branches, division_list=None, division=None, department=None, section=None, category=None):
	data = []
	conditions = []
	ly_conditions = []
	main_where_conditions = []
	where_clause = ""	
	ly_where_clause = ""
	main_where_clause = ""
	group_by_clause = ""
	group_by_list = []

	client = get_clickhouse_client()

	group_by_list.append("prod.division_id")
	group_by_list.append("prod.department_id")
	group_by_list.append("prod.section_id")
	group_by_list.append("prod.category_id")
	group_by_list.append("id")

	conditions.append("pos.trans_date >= makeDate(%d, %d, %d) and trans_date < makeDate(%d, %d, %d)"%(from_date.year, from_date.month, from_date.day, to_date.year, to_date.month, to_date.day))
	ly_conditions.append("pos.trans_date >= makeDate(%d, %d, %d) and trans_date < makeDate(%d, %d, %d)"%(ly_from_date.year, ly_from_date.month, ly_from_date.day, ly_to_date.year, ly_to_date.month, ly_to_date.day))

	if branches != "" and branches is not None:
		conditions.append("pos.branch in %s"%(branches))
		ly_conditions.append("pos.branch in %s"%(branches))
	
	if division != "" and division is not None:
		conditions.append("prod.division_id = %s"%(division))
		ly_conditions.append("prod.division_id = %s"%(division))
		main_where_conditions.append("division_id = %s"%(division))

	if department != "" and department is not None:
		conditions.append("prod.department_id = %s"%(department))
		ly_conditions.append("prod.department_id = %s"%(department))
		main_where_conditions.append("department_id = %s"%(department))

	if section != "" and section is not None:
		conditions.append("prod.section_id = %s"%(section))
		ly_conditions.append("prod.section_id = %s"%(section))
		main_where_conditions.append("section_id = %s"%(section))

	if category != "" and category is not None:
		conditions.append("prod.category_id = %s"%(category))
		ly_conditions.append("prod.category_id = %s"%(category))
		main_where_conditions.append("category_id = %s"%(category))

	if division_list !="" and division_list is not None:
		conditions.append("prod.division_id in %s"%division_list)
		ly_conditions.append("prod.division_id in %s"%division_list)
		main_where_conditions.append("division_id in %s "%division_list)

	group_by_clause = ",".join(group_by_list)
	if group_by_clause != "":
		group_by_clause = " group by " + group_by_clause + " order by " + group_by_clause

	main_where_clause = " AND ".join(main_where_conditions)
	if main_where_clause != "":
		main_where_clause = "WHERE " + main_where_clause

	where_clause = " AND ".join(conditions)
	if where_clause != "":
		where_clause = "WHERE " + where_clause

	ly_where_clause = " AND ".join(ly_conditions)
	if ly_where_clause != "":
		ly_where_clause = "WHERE " + ly_where_clause
	
	
	ty_con_query = """LEFT OUTER JOIN (select prod.division_id, prod.department_id, prod.section_id, prod.category_id,
				concat(prod.division_id, '-', prod.department_id, '-', prod.section_id, '-', prod.category_id) as id, sum(pos.amount) as amount from greports.product prod 
				join greports.pos_data pos on pos.barcode = prod.barcode %s and prod.is_concession = True %s) AS A on A.id = E.id"""%(where_clause, group_by_clause)
	
	ty_or_query = """LEFT OUTER JOIN (select prod.division_id, prod.department_id, prod.section_id, prod.category_id,
				concat(prod.division_id, '-', prod.department_id, '-', prod.section_id, '-', prod.category_id) as id,sum(pos.amount) as amount from greports.product prod 
				join greports.pos_data pos on pos.barcode = prod.barcode %s and prod.is_concession = False %s) AS B on B.id = E.id"""%(where_clause, group_by_clause)

	ly_con_query = """LEFT OUTER JOIN (select prod.division_id, prod.department_id, prod.section_id, prod.category_id,
	 			concat(prod.division_id, '-', prod.department_id, '-', prod.section_id, '-', prod.category_id) as id, sum(pos.amount) as amount from greports.product prod 
				join greports.pos_data pos on pos.barcode = prod.barcode %s and prod.is_concession = True %s) AS C on C.id = E.id"""%(ly_where_clause, group_by_clause)
	
	ly_or_query = """LEFT OUTER JOIN (select prod.division_id, prod.department_id, prod.section_id, prod.category_id,
	 			concat(prod.division_id, '-', prod.department_id, '-', prod.section_id, '-', prod.category_id) as id, sum(pos.amount) as amount from greports.product prod 
				join greports.pos_data pos on pos.barcode = prod.barcode %s and prod.is_concession = False %s) AS D on D.id = E.id"""%(ly_where_clause, group_by_clause)

	main_query = """select E.division_id, E.department_id, E.section_id, E.category_id,	E.id , A.amount as ty_con, B.amount as ty_or, 
				C.amount as ly_con, D.amount as ly_or from (select distinct division_id, department_id, section_id, category_id, 
				concat(division_id, '-', department_id, '-', section_id, '-', category_id) as id from greports.product %s) E %s %s %s %s"""%(main_where_clause,ty_con_query, ty_or_query, ly_con_query, ly_or_query)

	rows = client.query(main_query).result_rows

	for row in rows:
		ty_con = row[5] if row[5] is not None else 0
		ty_or = row[6] if row[6] is not None else 0
		ly_con = row[7] if row[7] is not None else 0
		ly_or = row[8] if row[8] is not None else 0

		data.append({
			"id":row[4],
			"division": get_category_name("division", row[0]),
			"department": get_category_name("department", row[1]),
			"section": get_category_name("section", row[2]),
			"category": get_category_name("category", row[3]),
			"division_no": row[0],
			"department_no": row[1],
			"section_no": row[2],
			"category_no": row[3],
			"ty_amount_concession": ty_con,
			"ty_amount_outright": ty_or,
			"ly_amount_concession": ly_con,
			"ly_amount_outright": ly_or,
			"ty_amount_total": ty_con + ty_or,
			"ly_amount_total": ly_con + ly_or,
			"growth_concession": ((ty_con - ly_con)/ly_con*100) if ly_con != 0 else 0,
			"growth_outright": ((ty_or - ly_or)/ly_or*100) if ly_or != 0 else 0,
			"growth_total": ((ty_con + ty_or - ly_con - ly_or)/ (ly_con + ly_or)*100) if (ly_con + ly_or) != 0 else 0
		})
	
	data.sort(key=lambda x: (x["division"] or "", x["department"] or "", x["section"] or "", x["category"] or ""))

	return data


def get_branch_list(bu, branches):
	branch_str = "("
	cur_branch = ""
	for i, branch in enumerate(branches):
		if i == 0:
			if bu == "GROCERY":
				cur_branch = branch
			else:
				cur_branch = get_branch_refcode(branch)
			branch_str += "'%s'"%(cur_branch)
		else:
			if bu == "GROCERY":
				cur_branch = branch
			else:
				cur_branch = get_branch_refcode(branch)
			branch_str += ",'%s'"%(cur_branch)
	branch_str += ")"
	return branch_str

def get_branch_refcode(branch_mapping):
	return frappe.db.get_value("Site", {"branch_mapping": branch_mapping, "site_type_code":"SEA", "business_unit": "DEPTSTORE"}, "ref_code")

def get_division_list(bu,division):
	division_list = "("
	if division != "" and division is not None:
		return "("+str(division)+")"
	else:
		divisions = frappe.db.get_list("Item Division",filters={"business_unit":bu},pluck="name")
		for i,division in enumerate(divisions):
			if i == 0:
				division_list += str(division)
			else:
				division_list += ","+(str(division))
		division_list += ")"
	return division_list

def get_category_name(cat_type, id):
	if cat_type == "division":
		return frappe.db.get_value("Item Division", id, "category_name")
	elif cat_type == "department":
		return frappe.db.get_value("Item Department", id, "category_name")
	elif cat_type == "section":
		return frappe.db.get_value("Item Section", id, "category_name")
	elif cat_type == "category":
		return frappe.db.get_value("Item Category", id, "category_name")
