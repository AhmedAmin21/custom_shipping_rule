frappe.ui.form.on('Shipping Rule', {
    calculate_based_on: function(frm) {
        toggle_condition_tables(frm);
        setup_upload_button(frm);
    },

    refresh: function(frm) {
        toggle_condition_tables(frm);
        setup_governorate_conditions_queries(frm);
        setup_upload_button(frm);
        recalculate_all_totals(frm);
    }
});

frappe.ui.form.on('Shipping Rule Governorate', {
    governorate: function(frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, 'district', '');
    },

    shipping_amount: function(frm, cdt, cdn) {
        update_total_shipping_amount(cdt, cdn);
    },

    added_value: function(frm, cdt, cdn) {
        update_total_shipping_amount(cdt, cdn);
    }
});

function update_total_shipping_amount(cdt, cdn) {
    const row = locals[cdt][cdn];
    frappe.model.set_value(
        cdt,
        cdn,
        'total_shipping_amount',
        flt(row.shipping_amount) + flt(row.added_value)
    );
}

function recalculate_all_totals(frm) {
    (frm.doc.governorate_conditions || []).forEach(row => {
        update_total_shipping_amount(row.doctype, row.name);
    });
}

function toggle_condition_tables(frm) {
    const is_governorate = frm.doc.calculate_based_on === "Governorate";

    frm.set_df_property('conditions', 'hidden', is_governorate);
    frm.set_df_property('governorate_conditions', 'hidden', !is_governorate);

    frm.toggle_reqd('conditions', !is_governorate && frm.doc.calculate_based_on !== "Fixed");
    frm.toggle_reqd('governorate_conditions', is_governorate);
}

function setup_governorate_conditions_queries(frm) {
    frm.set_query('district', 'governorate_conditions', function(doc, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.governorate) {
            return { filters: { name: ['in', []] } };
        }
        return {
            filters: {
                governorate: row.governorate
            }
        };
    });
}

function setup_upload_button(frm) {
    if (frm.doc.calculate_based_on !== "Governorate") {
        return;
    }

    const add_button = () => {
        const grid = frm.fields_dict.governorate_conditions?.grid;
        if (!grid) {
            return false;
        }

        grid.add_custom_button(__('Upload File'), () => {
            show_upload_conditions_dialog(frm);
        });
        return true;
    };

    if (!add_button()) {
        frm.refresh_field('governorate_conditions');
        frappe.after_ajax(() => add_button());
    }
}

function show_upload_conditions_dialog(frm) {
    const d = new frappe.ui.Dialog({
        title: __('Upload Governorate Conditions'),
        fields: [
            {
                fieldname: 'file',
                fieldtype: 'Attach',
                label: __('File'),
                reqd: 1,
                description: __('Upload a CSV or Excel file with columns: Governorate, District (optional), From Weight, To Weight, Shipping Amount, Added Value (optional)')
            },
            {
                fieldname: 'replace_existing',
                fieldtype: 'Check',
                label: __('Replace Existing Rows'),
                default: 0
            }
        ],
        primary_action_label: __('Import'),
        primary_action(values) {
            frappe.call({
                method: 'custom_shipping_rule.api.parse_governorate_conditions_file',
                args: {
                    file_url: values.file
                },
                freeze: true,
                freeze_message: __('Importing conditions...'),
                callback(r) {
                    if (!r.message) {
                        return;
                    }

                    if (cint(values.replace_existing)) {
                        frm.clear_table('governorate_conditions');
                    }

                    (r.message.rows || []).forEach(row => {
                        frm.add_child('governorate_conditions', row);
                    });

                    recalculate_all_totals(frm);
                    frm.refresh_field('governorate_conditions');
                    frappe.show_alert({
                        message: __('Imported {0} row(s)', [r.message.imported_count]),
                        indicator: 'green'
                    });
                }
            });
            d.hide();
        }
    });
    d.show();
}
