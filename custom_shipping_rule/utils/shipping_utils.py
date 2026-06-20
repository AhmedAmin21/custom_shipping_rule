import frappe
from frappe import _

def get_governorate_shipping_amount(shipping_rule, governorate, total_weight):
    matched = frappe.get_all(
        "Shipping Rule Governorate",
        filters={
            "parent": shipping_rule,
            "governorate": governorate,
            "from_weight": ["<=", total_weight],
            "to_weight": [">=", total_weight]
        },
        fields=["shipping_amount"],
        order_by="from_weight",
        limit=1
    )
    
    if matched:
        return matched[0].shipping_amount
    
    frappe.msgprint(
        _("No shipping rate found for {0} at weight {1}kg.").format(governorate, total_weight),
        alert=True
    )
    return 0