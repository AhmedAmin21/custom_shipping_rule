import frappe

from custom_shipping_rule.install import setup_custom_fields


def execute():
	setup_custom_fields()
