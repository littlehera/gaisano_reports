# Copyright (c) 2026, Gaisano IT and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DepartmentBudget(Document):
	pass

@frappe.whitelist()
def get_branches():
	branches = frappe.get_all("Branch",fields=["name"], filters = {"is_branch":1})
	print(branches)
	return branches