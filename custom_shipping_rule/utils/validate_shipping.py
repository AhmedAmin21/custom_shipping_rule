import frappe
from frappe import _
from frappe.utils import flt

from custom_shipping_rule.utils.shipping_utils import get_governorate_shipping_amount


def validate_governorate_shipping(doc, method=None):
	if not doc.get("shipping_rule"):
		return

	shipping_rule = frappe.get_doc("Shipping Rule", doc.shipping_rule)
	if shipping_rule.calculate_based_on != "Governorate":
		return

	if not doc.get("shipping_destination"):
		frappe.throw(
			_("Please select a Shipping Destination for the Governorate-based shipping rule.")
		)

	manual_amount = doc.get("custom_manual_shipping_amount")
	if manual_amount and flt(manual_amount) > 0:
		return

	total_weight = shipping_rule._get_weight_in_kg(doc)
	shipping_amount = get_governorate_shipping_amount(
		doc.shipping_rule,
		doc.shipping_destination,
		total_weight,
		doc.get("shipping_district"),
		show_message=False,
	)

	if not shipping_amount:
		location_label = doc.shipping_destination
		if doc.get("shipping_district"):
			location_label = f"{location_label} / {doc.shipping_district}"

		frappe.throw(
			_("No shipping rate found for {0} at weight {1}kg.").format(location_label, total_weight)
		)
