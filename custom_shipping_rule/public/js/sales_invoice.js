frappe.ui.form.on('Sales Invoice', {
    shipping_rule: function(frm) {
        toggle_shipping_destination(frm);
    },

    shipping_destination: function(frm) {
        if (frm.doc.shipping_rule && frm.doc.shipping_destination) {
            frm.trigger('shipping_rule');
        }
    },

    refresh: function(frm) {
        toggle_shipping_destination(frm);
    }
});

function toggle_shipping_destination(frm) {
    if (!frm.doc.shipping_rule) {
        frm.set_df_property('shipping_destination', 'hidden', 1);
        frm.set_df_property('shipping_destination', 'reqd', 0);
        frm.set_value('shipping_destination', '');
        frm.set_value('custom_manual_shipping_amount', 0);
        return;
    }
    
    frappe.db.get_value('Shipping Rule', frm.doc.shipping_rule, 'calculate_based_on')
        .then(r => {
            const is_governorate = r.message && r.message.calculate_based_on === 'Governorate';
            
            frm.set_df_property('shipping_destination', 'hidden', !is_governorate);
            frm.set_df_property('shipping_destination', 'reqd', is_governorate);
            
            if (!is_governorate) {
                frm.set_value('shipping_destination', '');
                frm.set_value('custom_manual_shipping_amount', 0);
            } else {
                check_and_show_weight_dialog(frm);
            }
        });
}

function check_and_show_weight_dialog(frm) {
    const items_without_weight = frm.doc.items.filter(item => !flt(item.total_weight));
    
    if (items_without_weight.length === 0) return;
    
    const item_list = items_without_weight.map(i => `<li>${i.item_code}</li>`).join("");
    
    const d = new frappe.ui.Dialog({
        title: __("Weight Data Missing"),
        fields: [
            {
                fieldtype: "HTML",
                options: `<p>These items have no weight:</p><ul>${item_list}</ul>`
            }
        ],
        primary_action_label: __("Fix Items"),
        primary_action: () => {
            d.hide();
            items_without_weight.forEach(item => {
                window.open(`/app/item/${item.item_code}`, '_blank');
            });
        }
    });
    
    d.add_custom_button(__("Continue Without Weight"), () => {
        d.hide();
        frappe.show_alert(__("Proceeding with available weight data."));
    });
    
    d.add_custom_button(__("Enter Manual Amount"), () => {
        d.hide();
        frappe.prompt(
            {
                fieldname: "amount",
                label: __("Shipping Amount"),
                fieldtype: "Currency",
                reqd: 1
            },
            (values) => {
                frm.set_value("custom_manual_shipping_amount", values.amount);
                frappe.show_alert(__("Manual shipping amount set to {0}", [values.amount]));
            },
            __("Manual Shipping Amount")
        );
    });
    
    d.show();
}