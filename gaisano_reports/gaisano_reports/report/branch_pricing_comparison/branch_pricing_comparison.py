# Copyright (c) 2026, Gaisano IT and contributors
# For license information, please see license.txt

import frappe
from gaisano_reports.dbutils import get_clickhouse_client
from decimal import Decimal, ROUND_HALF_UP


def execute(filters=None):
	columns, data = [], []

	report_type = filters.get("report_type") if filters.get("report_type") else ''
	branches = filters.get("branch") if filters.get("branch") else ''
	bu = filters.get("business_unit") if filters.get("business_unit") else ''
	supplier = filters.get("supplier") if filters.get("supplier") else ''

	columns = get_columns(branches, bu, report_type)

	data = get_data(branches, bu, supplier, report_type)

	return columns, data

def get_data(branches, bu, supplier, report_type):
	data = []

	master_conditions = []
	site_conditions = []
	master_where_clause = ""
	site_where_clause= ""

	ref_code_list = []
	sp_list = []

	client = get_clickhouse_client()

	division_list = get_division_list(bu)

	if division_list != "()":
		if supplier != "":
			master_conditions.append("product_code in (select product_code from greports.product where supplier_id = %s and division_id in %s)"%(supplier, division_list))
			site_conditions.append("P.product_code in (select product_code from greports.product where supplier_id = %s and division_id in %s)"%(supplier, division_list))
		else:
			master_conditions.append("product_code in (select product_code from greports.product where division_id in %s)"%(division_list))
			site_conditions.append("P.product_code in (select product_code from greports.product where division_id in %s)"%(division_list))
		
	master_conditions.append("product_type in ('','P')")
	site_conditions.append("P.product_type in ('','P')")

	ref_codes = "("
	if branches == '':
		branches = get_all_branches()
	ref_codes += "'MASTER'"
	for branch in branches:
		ref_code = get_refcode(branch, bu)
		if ref_code is None or ref_code=='None':
			continue
		ref_code_list.append(ref_code)
		ref_codes += "," + "'%s'"%ref_code
	ref_codes +=")"
	
	site_conditions.append("S.ref_code IN %s"%(ref_codes))

	master_where_clause = " AND ".join(master_conditions)
	if master_where_clause != "":
		master_where_clause = "WHERE " + master_where_clause
	
	site_where_clause = " AND ".join(site_conditions)
	if site_where_clause != "":
		site_where_clause = "WHERE " + site_where_clause

	main_query = """select product_code, item_name, barcode, landed_cost, retail_price, 'MASTER' as ref_code from greports.product %s"""%(master_where_clause)
	sp_query = """select SP.product_code, P.item_name, P.barcode, if(SP.landed_cost is NULL, P.landed_cost, SP.landed_cost) as landed_cost, 
				if(SP.retail_price is NULL, P.retail_price, SP.retail_price), S.ref_code from greports.site_product SP join greports.product P
				on SP.product_code = P.product_code join greports.site S on SP.site_id = S.site_id %s"""%(site_where_clause)

	print(main_query)
	print(sp_query)

	master_rows = client.query(main_query).result_rows
	sp_rows = client.query(sp_query).result_rows

	for row in sp_rows:
		ref_code = row[5]
		landed_cost = row[3]
		retail_price = Decimal(str(row[4]))
		markup = Decimal(str((retail_price-landed_cost)/landed_cost * 100)) if landed_cost > 0 else Decimal(str("0"))
		margin = Decimal(str((retail_price-landed_cost)/retail_price * 100)) if retail_price > 0 else Decimal(str("0"))
		if report_type == "SRP":
			sp_list.append({"product_code":row[0],"item_name":row[1], "barcode":row[2], ref_code: retail_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)})
		elif report_type == 'Markup':
			sp_list.append({"product_code":row[0],"item_name":row[1], "barcode":row[2], ref_code: markup.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)})
		else:
			sp_list.append({"product_code":row[0],"item_name":row[1], "barcode":row[2], ref_code: margin.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)})

	for row in master_rows:
		landed_cost = row[3]
		retail_price = row[4]
		retail_price = Decimal(str(row[4]))
		markup = Decimal(str((retail_price-landed_cost)/landed_cost * 100)) if landed_cost > 0 else Decimal(str("0"))
		margin = Decimal(str((retail_price-landed_cost)/retail_price * 100)) if retail_price > 0 else Decimal(str("0"))
		if report_type == "SRP":
			data.append({"product_code":row[0],"item_name":row[1], "barcode":row[2], "MASTER": retail_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)})
		elif report_type == 'Markup':
			data.append({"product_code":row[0],"item_name":row[1], "barcode":row[2], "MASTER": markup.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)})
		else:
			data.append({"product_code":row[0],"item_name":row[1], "barcode":row[2], "MASTER": margin.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)})
	
	for row in data:
		total = 0
		count = 1
		total+= row['MASTER']
		for ref_code in ref_code_list:
				row[ref_code] = get_branch_prices(sp_list, row['product_code'],ref_code)
				if row[ref_code] is not None:
					total+= row[ref_code]
					count += 1
		row['average_price'] = Decimal(str(total/count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

	return data

def get_columns(branches, bu, report_type):
	columns = []
	columns.append({"fieldname": "item_name", "label": "Item", "fieldtype": "Data", "width": 150})
	columns.append({"fieldname": "barcode", "label": "Barcode", "fieldtype": "Data", "width": 150})
	columns.append({"fieldname": "MASTER", "label": "Master", "fieldtype": "float", "precision": 2, "width": 150})
	if branches == '':
		branches = get_all_branches()
	for branch in branches:
		ref_code = get_refcode(branch, bu)
		if ref_code is None or ref_code=='None':
			continue
		columns.append({"fieldname": ref_code, "label": ref_code, "fieldtype": "float", "precision": 2,"width": 150})
	columns.append({"fieldname": "average_price", "label": "Average", "fieldtype": "float", "precision": 2,"width": 150})
	return columns

def get_all_branches():
	branches = frappe.get_all("Branch", fields=["name"])
	return [branch.name for branch in branches]

def get_refcode(branch, bu):
	if bu == "GROCERY":
		return frappe.db.get_value("Site", {"branch_mapping":branch, "business_unit":bu, "site_type_code":"SEA"}, "ref_code")
	else:
		return frappe.db.get_value("Site", {"branch_mapping":branch, "business_unit":"DEPTSTORE", "site_type_code":"SEA"}, "ref_code")

def get_division_list(business_unit):
	categories = "("
	rows = frappe.db.sql("""select category_id from `tabItem Division` where business_unit = %s or business_unit2 = %s""", (business_unit,business_unit))
	for i,row in enumerate(rows):
		categories+="'"+str(row[0])+"'"
		if i < len(rows) - 1:
			categories+=","
	categories+=")"
	return categories

def get_branch_prices(price_list, product_code, ref_code):
	for row in price_list:
		try:
			if row['product_code'] == product_code and row[ref_code]:
				return row[ref_code]
		except:
			continue
	return None