import frappe, clickhouse_connect


@frappe.whitelist()
def connect_to_clickhouse(hostname,username,src_port):
	msg = ""
	settings = frappe.get_single("Clickhouse Settings")
	password = settings.get_password('password')
	try:
		client = clickhouse_connect.get_client(
					host=hostname,
					port=src_port,
					username=username,
					password=password)
		query = "show tables"	
		result = client.query(query) # Execute the query	
		rows = result.result_rows # Fetch the result
		for row in rows:
			print(row) # Print the result
	except Exception as e:
		msg = str(f"An error occurred: {e}")
	else 	:
		msg = ("Destination Connection Successful!")
	return msg

def get_clickhouse_client():
    settings = frappe.get_single("Clickhouse Settings")
    hostname = settings.hostname
    username = settings.username
    password = settings.get_password('password')
    src_port = settings.port_no
    
    client = clickhouse_connect.get_client(
			    host=hostname,
				port=src_port,
				username=username,
				password=password)

    return client