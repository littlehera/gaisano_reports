# Copyright (c) 2025, Gaisano IT and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import clickhouse_connect, frappe
from gaisano_reports.dbutils import connect_to_clickhouse


class ClickhouseSettings(Document):
	def validate(self):
		frappe.msgprint(connect_to_clickhouse(self.hostname, self.username, self.port_no))
	pass

