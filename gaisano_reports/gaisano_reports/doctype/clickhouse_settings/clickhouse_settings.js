// Copyright (c) 2025, Gaisano IT and contributors
// For license information, please see license.txt

frappe.ui.form.on("Clickhouse Settings", {
	test_conn: function(frm){
        var hostname = frm.doc.hostname;
        var username = frm.doc.username;
        var src_port = frm.doc.port_no;            

        frappe.call({
            method: 'gaisano_reports.dbutils.connect_to_clickhouse',
            args: {
                'hostname': hostname,
                'username': username, 
                'src_port': src_port
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(r.message);
                }
            },
            error: function(err){
                frappe.msgprint(__("Something went wrong."))
            }
        })
    }
});