import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def after_install():
    setup_custom_fields()
    setup_property_setters()
    seed_governorates()

def setup_custom_fields():
    create_custom_field("Shipping Rule", {
        "fieldname": "governorate_conditions",
        "label": "Governorate Conditions",
        "fieldtype": "Table",
        "options": "Shipping Rule Governorate",
        "insert_after": "conditions"
    })
    
    for dt in ("Sales Invoice", "Sales Order"):
        create_custom_field(dt, {
            "fieldname": "shipping_destination",
            "label": "Shipping Destination",
            "fieldtype": "Link",
            "options": "Governorate",
            "insert_after": "shipping_rule"
        })

        create_custom_field(dt, {
            "fieldname": "custom_manual_shipping_amount",
            "label": "Manual Shipping Amount",
            "fieldtype": "Currency",
            "insert_after": "shipping_destination"
        })

def setup_property_setters():
    make_property_setter(
        "Shipping Rule",
        "calculate_based_on",
        "options",
        "Fixed\nNet Total\nNet Weight\nGovernorate",
        "Data"
    )

def seed_governorates():
    governorates = [
        "القاهرة", "الإسكندرية", "الجيزة", "الشرقية", "الدقهلية",
        "البحيرة", "المنوفية", "الغربية", "القليوبية", "كفر الشيخ",
        "الفيوم", "بني سويف", "المنيا", "أسيوط", "سوهاج",
        "قنا", "الأقصر", "أسوان", "البحر الأحمر", "الوادي الجديد",
        "مطروح", "شمال سيناء", "جنوب سيناء", "بورسعيد", "الإسماعيلية",
        "السويس", "دمياط"
    ]
    
    for gov_name in governorates:
        if not frappe.db.exists("Governorate", gov_name):
            frappe.get_doc({
                "doctype": "Governorate",
                "governorate_name": gov_name,
                "enabled": 1
            }).insert(ignore_permissions=True)