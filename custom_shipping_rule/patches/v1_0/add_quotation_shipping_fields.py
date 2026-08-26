import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
	"""Add shipping_destination, shipping_district, and custom_manual_shipping_amount
	custom fields to Quotation — matching what Sales Order and Sales Invoice already have."""

	create_custom_field("Quotation", {
		"fieldname": "shipping_destination",
		"label": "Shipping Destination",
		"fieldtype": "Link",
		"options": "Governorate",
		"insert_after": "shipping_rule",
	})

	create_custom_field("Quotation", {
		"fieldname": "shipping_district",
		"label": "Shipping District",
		"fieldtype": "Link",
		"options": "District",
		"insert_after": "shipping_destination",
	})

	create_custom_field("Quotation", {
		"fieldname": "custom_manual_shipping_amount",
		"label": "Manual Shipping Amount",
		"fieldtype": "Currency",
		"insert_after": "shipping_district",
	})
