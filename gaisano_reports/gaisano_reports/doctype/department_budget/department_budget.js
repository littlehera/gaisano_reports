// Copyright (c) 2026, Gaisano IT and contributors
// For license information, please see license.txt

frappe.ui.form.on("Department Budget", {
	refresh(frm) {
        if(frm.doc.enable_editing == 1){
            frm.set_df_property('department_budget_details_section', 'hidden', 0);
            frm.set_df_property('breakdown_section', 'hidden', 0);
            frm.set_df_property('section_break_juxf', 'hidden', 0);
        }
        else{
            frm.set_df_property('department_budget_details_section', 'hidden', 1);
            frm.set_df_property('breakdown_section', 'hidden', 1);
            frm.set_df_property('section_break_juxf', 'hidden', 1);
        }
	}
});


frappe.ui.form.on("Department Budget", "division", function(frm){
    frm.set_query('department', () => {
        return {
            filters: {
                parent_id: frm.doc.division
            }
        }
    })
});

frappe.ui.form.on("Department Budget", "enable_editing", function(frm){
        if(frm.doc.enable_editing == 1){
            frm.set_df_property('department_budget_details_section', 'hidden', 0);
            frm.set_df_property('breakdown_section', 'hidden', 0);
            frm.set_df_property('section_break_juxf', 'hidden', 0);
        }
        else{
            frm.set_df_property('department_budget_details_section', 'hidden', 1);
            frm.set_df_property('breakdown_section', 'hidden', 1);
            frm.set_df_property('section_break_juxf', 'hidden', 1);
        }
})

frappe.ui.form.on("Department Budget", "calculate_breakdown", function(frm){
    frappe.call({
        method: "gaisano_reports.gaisano_reports.doctype.department_budget.department_budget.get_branches",
        args:{},
        callback: function(r) {
            if(r.message){
                frm.clear_table('items');
                var amount_from_breakdown = 0
                var amount = frm.doc.total_budget/(12*(r.message.length));
                var months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
                for(var i = 0; i < r.message.length; i++){
                    for(var j = 0; j < months.length; j++){
                        var d = frm.add_child('items');
                        d.branch = r.message[i].name;
                        d.month = months[j];
                        d.year = frm.doc.year;
                        d.amount = amount;
                        d.date = ""+frm.doc.year+"-"+(j+1)+"-01";
                        amount_from_breakdown+=d.amount;
                    }
                frm.set_value('total_from_breakdown', amount_from_breakdown);
                frm.refresh_field('items');
                }
            }
        }
    })
  
});

frappe.ui.form.on("Budget Item", "amount", function(frm, cdt, cdn){
    var items = frm.doc.items;
    var total_from_breakdown = 0;
    for(var i = 0; i < items.length; i++){
        total_from_breakdown += items[i].amount;
    }
    frm.set_value('total_from_breakdown', total_from_breakdown);
    frm.refresh_field('total_from_breakdown');
});