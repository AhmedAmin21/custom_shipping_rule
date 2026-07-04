import frappe
from frappe import _
from frappe.utils import flt


def get_governorate_shipping_amount(shipping_rule, governorate, total_weight, district=None):
	if district:
		matched = _get_matching_condition(shipping_rule, governorate, total_weight, district)
		if matched:
			return matched

	matched = _get_matching_condition(shipping_rule, governorate, total_weight, district=None)
	if matched:
		return matched

	location_label = governorate
	if district:
		location_label = f"{governorate} / {district}"

	frappe.msgprint(
		_("No shipping rate found for {0} at weight {1}kg.").format(location_label, total_weight),
		alert=True,
	)
	return 0


def _get_matching_condition(shipping_rule, governorate, total_weight, district=None):
	filters = {
		"parent": shipping_rule,
		"governorate": governorate,
		"from_weight": ["<=", total_weight],
		"to_weight": [">=", total_weight],
	}
	if district:
		filters["district"] = district
	else:
		filters["district"] = ["in", ["", None]]

	matched = frappe.get_all(
		"Shipping Rule Governorate",
		filters=filters,
		fields=["shipping_amount", "added_value"],
		order_by="from_weight",
		limit=1,
	)

	if matched:
		return flt(matched[0].shipping_amount) + flt(matched[0].added_value)

	return None
