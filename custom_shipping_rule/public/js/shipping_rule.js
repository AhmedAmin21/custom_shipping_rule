frappe.ui.form.on('Shipping Rule', {
    calculate_based_on: function(frm) {
        toggle_condition_tables(frm);
    },
    
    refresh: function(frm) {
        toggle_condition_tables(frm);
    }
});

function toggle_condition_tables(frm) {
    const is_governorate = frm.doc.calculate_based_on === "Governorate";
    
    frm.set_df_property('conditions', 'hidden', is_governorate);
    frm.set_df_property('governorate_conditions', 'hidden', !is_governorate);
    
    frm.toggle_reqd('conditions', !is_governorate && frm.doc.calculate_based_on !== "Fixed");
    frm.toggle_reqd('governorate_conditions', is_governorate);
}