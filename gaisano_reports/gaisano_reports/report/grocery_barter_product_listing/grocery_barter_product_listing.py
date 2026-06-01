# Copyright (c) 2026, Gaisano IT and contributors
# For license information, please see license.txt

import frappe
from gaisano_reports.dbutils import get_clickhouse_client

def execute(filters=None):
	columns, data = [], []

	bu = filters.get("business_unit") if filters.get("business_unit") else ''
	site = filters.get("site_name") if filters.get("site_name") else ''
	supplier = filters.get("supplier") if filters.get("supplier") else ''

	columns = [
		{"fieldname": "item_name", "label": "Item", "fieldtype": "Data", "width": 150},
		{"fieldname": "barcode_reg", "label": "Regular Barcode", "fieldtype": "Data", "width": 150},
		{"fieldname": "barcode_case", "label": "Case Barcode", "fieldtype": "Data", "width": 150},
		{"fieldname": "barcode_alt", "label": "Alternate Barcode", "fieldtype": "Data", "width": 150},
		{"fieldname": "packing", "label": "Case Packing", "fieldtype": "Float", "width": 150},
		{"fieldname": "basic_cost_regular", "label": "Basic: Cost - Regular", "fieldtype": "Float", "width": 150},
		{"fieldname": "basic_cost_case", "label": "Basic: Cost - Case", "fieldtype": "Float", "width": 150},
		{"fieldname": "site_cost_regular", "label": "Site: Cost - Regular", "fieldtype": "Float", "width": 150},
		{"fieldname": "site_cost_case", "label": "Site: Cost - Case", "fieldtype": "Float", "width": 150},
		{"fieldname": "basic_po_discount", "label": "Basic: PO Discount", "fieldtype": "Data", "width": 150},
		{"fieldname": "site_po_discount", "label": "Site: PO Discount", "fieldtype": "Data", "width": 150},
		{"fieldname": "basic_bo_discount", "label": "Basic: BO Discount", "fieldtype": "Data", "width": 150},
		{"fieldname": "site_bo_discount", "label": "Site: BO Discount", "fieldtype": "Data", "width": 150},
		{"fieldname": "basic_status", "label": "Basic: Status", "fieldtype": "Data", "width": 150},
		{"fieldname": "site_status", "label": "Site: Status", "fieldtype": "Data", "width": 150}
	]

	data = get_data(site, supplier)

	return columns, data

def get_data(site, supplier):
	data = []
	client = get_clickhouse_client()

	query = """select B.product_code, B.item_name, B.barcode, B.mfg_code, B.landed_cost, B.po_discount, B.bo_discount, B.status, C.barcode, C.content_qty,
				C.landed_cost, S.landed_cost, S.po_discount, S.bo_discount, S.status, A.barcode, S2.landed_cost from greports.product B 
				left outer join (select product_code, mfg_code, barcode, content_qty, landed_cost from greports.product where content_qty > 1 and product_type = 'P' and 
				is_ordering_unit = true) as C on C.mfg_code = B.mfg_code left outer join 
				(select product_code, landed_cost, po_discount, bo_discount, status from greports.site_product where site_id=%s) as S
				on S.product_code = B.product_code left outer join 
				(select product_code, landed_cost, po_discount, bo_discount, status from greports.site_product where site_id=%s) as S2
				on S2.product_code = C.product_code
				LEFT OUTER JOIN (select product_code, barcode from greports.product where is_main_alternate = true and product_type = 'A')
				as A on A.product_code = B.product_code
				where B.product_type = '' and B.supplier_id = %s order by B.product_code asc"""%(site, site, supplier)
	
	rows = client.query(query).result_rows
	for row in rows:
		data.append({
			"item_name": row[1],
			"barcode_reg": row[2],
			"barcode_case": row[8] if row[8] else "",
			"barcode_alt": row[15] if row[15] else "",
			"packing": row[9] if row[9] else 0,
			"basic_cost_regular": row[4],
			"basic_cost_case": row[10],
			"site_cost_regular": row[11],
			"site_cost_case": row[16],
			"basic_status": row[7],
			"site_status": row[14],
			"basic_po_discount": row[5],
			"site_po_discount": row[12],
			"basic_bo_discount": row[6],
			"site_bo_discount": row[13]
		})
		print(row)

	return data
# def get_data(branches, bu, supplier, report_type):
# 	data = []

# 	master_conditions = []
# 	site_conditions = []
# 	master_where_clause = ""
# 	site_where_clause= ""

# 	ref_code_list = []
# 	sp_list = []

# 	client = get_clickhouse_client()

# 	division_list = get_division_list(bu)

# 	if division_list != "()":
# 		if supplier != "":
# 			master_conditions.append("product_code in (select product_code from greports.product where supplier_id = %s and division_id in %s)"%(supplier, division_list))
# 			site_conditions.append("P.product_code in (select product_code from greports.product where supplier_id = %s and division_id in %s)"%(supplier, division_list))
# 		else:
# 			master_conditions.append("product_code in (select product_code from greports.product where division_id in %s)"%(division_list))
# 			site_conditions.append("P.product_code in (select product_code from greports.product where division_id in %s)"%(division_list))
		
# 	ref_codes = "("
# 	if branches == '':
# 		branches = get_all_branches()
# 	ref_codes += "'MASTER'"
# 	for branch in branches:
# 		ref_code = get_refcode(branch, bu)
# 		if ref_code is None or ref_code=='None':
# 			continue
# 		ref_code_list.append(ref_code)
# 		ref_codes += "," + "'%s'"%ref_code
# 	ref_codes +=")"
	
# 	site_conditions.append("S.ref_code IN %s"%(ref_codes))

# 	master_where_clause = " AND ".join(master_conditions)
# 	if master_where_clause != "":
# 		master_where_clause = "WHERE " + master_where_clause
	
# 	site_where_clause = " AND ".join(site_conditions)
# 	if site_where_clause != "":
# 		site_where_clause = "WHERE " + site_where_clause

# 	main_query = """select product_code, item_name, barcode, landed_cost, retail_price, 'MASTER' as ref_code from greports.product %s"""%(master_where_clause)
# 	sp_query = """select SP.product_code, P.item_name, P.barcode, if(SP.landed_cost is NULL, P.landed_cost, SP.landed_cost) as landed_cost, 
# 				if(SP.retail_price is NULL, P.retail_price, SP.retail_price), S.ref_code from greports.site_product SP join greports.product P
# 				on SP.product_code = P.product_code join greports.site S on SP.site_id = S.site_id %s"""%(site_where_clause)

# 	print(main_query)
# 	print(sp_query)

# 	master_rows = client.query(main_query).result_rows
# 	sp_rows = client.query(sp_query).result_rows

# 	for row in sp_rows:
# 		ref_code = row[5]
# 		landed_cost = row[3]
# 		retail_price = Decimal(str(row[4]))
# 		markup = Decimal(str((retail_price-landed_cost)/landed_cost * 100)) if landed_cost > 0 else Decimal(str("0"))
# 		margin = Decimal(str((retail_price-landed_cost)/retail_price * 100)) if retail_price > 0 else Decimal(str("0"))
# 		if report_type == "SRP":
# 			sp_list.append({"product_code":row[0],"item_name":row[1], "barcode":row[2], ref_code: retail_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)})
# 		elif report_type == 'Markup':
# 			sp_list.append({"product_code":row[0],"item_name":row[1], "barcode":row[2], ref_code: markup.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)})
# 		else:
# 			sp_list.append({"product_code":row[0],"item_name":row[1], "barcode":row[2], ref_code: margin.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)})

# 	for row in master_rows:
# 		landed_cost = row[3]
# 		retail_price = row[4]
# 		retail_price = Decimal(str(row[4]))
# 		markup = Decimal(str((retail_price-landed_cost)/landed_cost * 100)) if landed_cost > 0 else Decimal(str("0"))
# 		margin = Decimal(str((retail_price-landed_cost)/retail_price * 100)) if retail_price > 0 else Decimal(str("0"))
# 		if report_type == "SRP":
# 			data.append({"product_code":row[0],"item_name":row[1], "barcode":row[2], "MASTER": retail_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)})
# 		elif report_type == 'Markup':
# 			data.append({"product_code":row[0],"item_name":row[1], "barcode":row[2], "MASTER": markup.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)})
# 		else:
# 			data.append({"product_code":row[0],"item_name":row[1], "barcode":row[2], "MASTER": margin.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)})
	
# 	for row in data:
# 		total = 0
# 		count = 1
# 		total+= row['MASTER']
# 		for ref_code in ref_code_list:
# 				row[ref_code] = get_branch_prices(sp_list, row['product_code'],ref_code)
# 				if row[ref_code] is not None:
# 					total+= row[ref_code]
# 					count += 1
# 		row['average_price'] = Decimal(str(total/count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# 	return data

# def get_columns(branches, bu, report_type):
# 	columns = []
# 	columns.append({"fieldname": "item_name", "label": "Item", "fieldtype": "Data", "width": 150})
# 	columns.append({"fieldname": "barcode", "label": "Barcode", "fieldtype": "Data", "width": 150})
# 	columns.append({"fieldname": "MASTER", "label": "Master", "fieldtype": "float", "precision": 2, "width": 150})
# 	if branches == '':
# 		branches = get_all_branches()
# 	for branch in branches:
# 		ref_code = get_refcode(branch, bu)
# 		if ref_code is None or ref_code=='None':
# 			continue
# 		columns.append({"fieldname": ref_code, "label": ref_code, "fieldtype": "float", "precision": 2,"width": 150})
# 	columns.append({"fieldname": "average_price", "label": "Average Price", "fieldtype": "float", "precision": 2,"width": 150})
# 	return columns

# def get_all_branches():
# 	branches = frappe.get_all("Branch", fields=["name"])
# 	return [branch.name for branch in branches]

# def get_refcode(branch, bu):
# 	if bu == "GROCERY":
# 		return frappe.db.get_value("Site", {"branch_mapping":branch, "business_unit":bu, "site_type_code":"SEA"}, "ref_code")
# 	else:
# 		return frappe.db.get_value("Site", {"branch_mapping":branch, "business_unit":"DEPTSTORE", "site_type_code":"SEA"}, "ref_code")

# def get_division_list(business_unit):
# 	categories = "("
# 	rows = frappe.db.sql("""select category_id from `tabItem Division` where business_unit = %s or business_unit2 = %s""", (business_unit,business_unit))
# 	for i,row in enumerate(rows):
# 		categories+="'"+str(row[0])+"'"
# 		if i < len(rows) - 1:
# 			categories+=","
# 	categories+=")"
# 	return categories

# def get_branch_prices(price_list, product_code, ref_code):
# 	for row in price_list:
# 		try:
# 			if row['product_code'] == product_code and row[ref_code]:
# 				return row[ref_code]
# 		except:
# 			continue
# 	return None