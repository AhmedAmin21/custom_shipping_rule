import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.doctype.shipping_rule.shipping_rule import ShippingRule
from custom_shipping_rule.utils.shipping_utils import get_governorate_shipping_amount

class CustomShippingRule(ShippingRule):
    def validate(self):
        super().validate()
        self.validate_governorate_conditions()
    
    def validate_governorate_conditions(self):
        if self.calculate_based_on != "Governorate":
            return
        
        conditions = self.get("governorate_conditions", [])
        
        for i, d1 in enumerate(conditions):
            if flt(d1.from_weight) >= flt(d1.to_weight):
                frappe.throw(
                    _("Row {0}: From Weight must be less than To Weight").format(d1.idx)
                )
            
            for j, d2 in enumerate(conditions):
                if i >= j:
                    continue
                
                if d1.governorate != d2.governorate:
                    continue
                
                # Check overlap
                if flt(d1.from_weight) <= flt(d2.to_weight) and flt(d2.from_weight) <= flt(d1.to_weight):
                    frappe.throw(
                        _("Row {0} and Row {1}: Overlapping weight ranges for governorate {2}").format(
                            d1.idx, d2.idx, d1.governorate
                        )
                    )
    
    def apply(self, doc):
        if self.calculate_based_on == "Governorate":
            # Check manual override
            manual_amount = doc.get("custom_manual_shipping_amount")
            if manual_amount and flt(manual_amount) > 0:
                shipping_amount = flt(manual_amount)
            else:
                if not doc.shipping_destination:
                    frappe.msgprint(
                        _("Please select a Shipping Destination to apply the Governorate-based shipping rule."),
                        alert=True
                    )
                    return
                
                total_weight = self._get_weight_in_kg(doc)
                shipping_amount = get_governorate_shipping_amount(
                    self.name,
                    doc.shipping_destination,
                    total_weight
                )
            
            # Currency conversion
            if doc.currency != doc.company_currency:
                shipping_amount = flt(shipping_amount / doc.conversion_rate, 2)
            
            self.add_shipping_rule_to_tax_table(doc, shipping_amount)
        else:
            super().apply(doc)

    def _get_weight_in_kg(self, doc):
        total_weight = flt(doc.total_net_weight)

        # Try to determine weight UOM
        weight_uom = None

        # 1. Check if document has a weight_uom field
        if doc.get("weight_uom"):
            weight_uom = doc.weight_uom
        # 2. Check items for weight_uom
        elif doc.get("items"):
            for item in doc.items:
                if item.get("weight_uom"):
                    weight_uom = item.weight_uom
                    break

        if weight_uom and weight_uom != "Kg":
            conversion_factor = self._get_weight_conversion_factor(weight_uom)
            if conversion_factor:
                total_weight = total_weight * flt(conversion_factor)

        return total_weight

    def _get_weight_conversion_factor(self, weight_uom):
        # Try standard UOM conversion
        conversion_factor = frappe.db.get_value(
            "UOM Conversion Factor",
            {"category": "Mass", "from_uom": weight_uom, "to_uom": "Kg"},
            "value"
        )
        if conversion_factor:
            return flt(conversion_factor)

        # Common fallbacks
        weight_uom_lower = weight_uom.lower()
        if weight_uom_lower in ("gram", "grams", "g"):
            return 0.001
        elif weight_uom_lower in ("ton", "tons", "tonne", "tonnes"):
            return 1000
        elif weight_uom_lower in ("pound", "pounds", "lb", "lbs"):
            return 0.453592
        elif weight_uom_lower in ("ounce", "ounces", "oz"):
            return 0.0283495

        return None