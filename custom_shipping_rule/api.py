import csv
import io

import frappe
from frappe import _
from frappe.utils import cint, flt

COLUMN_ALIASES = {
	"governorate": ("governorate", "shipping destination", "shipping_destination"),
	"district": ("district", "shipping district", "shipping_district"),
	"from_weight": ("from weight", "from_weight", "fromweight"),
	"to_weight": ("to weight", "to_weight", "toweight"),
	"shipping_amount": ("shipping amount", "shipping_amount", "amount", "rate"),
	"added_value": ("added value", "added_value", "addedvalue"),
}


@frappe.whitelist()
def parse_governorate_conditions_file(file_url):
	rows = _parse_upload_file(file_url)
	if not rows:
		frappe.throw(_("No data rows found in the uploaded file"))

	condition_rows = _build_condition_rows(rows)
	if not condition_rows:
		frappe.throw(_("No valid rows were imported"))

	return {"rows": condition_rows, "imported_count": len(condition_rows)}


@frappe.whitelist()
def import_governorate_conditions(shipping_rule, file_url, replace_existing=0):
	if not shipping_rule:
		frappe.throw(_("Shipping Rule is required"))

	if not frappe.db.exists("Shipping Rule", shipping_rule):
		frappe.throw(_("Shipping Rule {0} does not exist").format(shipping_rule))

	rows = _parse_upload_file(file_url)
	if not rows:
		frappe.throw(_("No data rows found in the uploaded file"))

	doc = frappe.get_doc("Shipping Rule", shipping_rule)
	if cint(replace_existing):
		doc.set("governorate_conditions", [])

	condition_rows = _build_condition_rows(rows)
	for row in condition_rows:
		doc.append("governorate_conditions", row)

	doc.save()
	return {"imported_count": len(condition_rows)}


def _build_condition_rows(rows):
	condition_rows = []
	for row in rows:
		governorate = _resolve_link("Governorate", row.get("governorate"), required=True)
		district = _resolve_link("District", row.get("district"), required=False)
		from_weight = flt(row.get("from_weight"))
		to_weight = flt(row.get("to_weight"))
		shipping_amount = flt(row.get("shipping_amount"))
		added_value = flt(row.get("added_value"))

		if not governorate:
			continue
		if from_weight >= to_weight:
			frappe.throw(
				_("From Weight must be less than To Weight for governorate {0}").format(governorate)
			)
		if district and frappe.db.exists("District", district):
			district_governorate = frappe.db.get_value("District", district, "governorate")
			if district_governorate and district_governorate != governorate:
				frappe.throw(
					_("District {0} does not belong to governorate {1}").format(district, governorate)
				)

		condition_rows.append(
			{
				"governorate": governorate,
				"district": district,
				"from_weight": from_weight,
				"to_weight": to_weight,
				"shipping_amount": shipping_amount,
				"added_value": added_value,
				"total_shipping_amount": shipping_amount + added_value,
			}
		)

	return condition_rows


def _parse_upload_file(file_url):
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not file_name:
		frappe.throw(_("File not found"))

	file_doc = frappe.get_doc("File", file_name)
	content = file_doc.get_content()
	file_name = (file_doc.file_name or "").lower()

	if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
		return _parse_excel(content)
	return _parse_csv(content)


def _parse_csv(content):
	if isinstance(content, bytes):
		content = content.decode("utf-8-sig")

	reader = csv.reader(io.StringIO(content))
	rows = list(reader)
	if not rows:
		return []

	header_map = _build_header_map(rows[0])
	data_rows = rows[1:]
	return [_normalize_row(row, header_map) for row in data_rows if any(cell.strip() for cell in row)]


def _parse_excel(content):
	try:
		import openpyxl
	except ImportError:
		frappe.throw(_("openpyxl is required to import Excel files. Please upload a CSV file instead."))

	workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
	sheet = workbook.active
	rows = list(sheet.iter_rows(values_only=True))
	if not rows:
		return []

	header = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
	header_map = _build_header_map(header)
	parsed_rows = []

	for row in rows[1:]:
		values = ["" if cell is None else str(cell).strip() for cell in row]
		if not any(values):
			continue
		parsed_rows.append(_normalize_row(values, header_map))

	return parsed_rows


def _build_header_map(header_row):
	header_map = {}
	for index, header in enumerate(header_row):
		normalized = _normalize_header(header)
		for fieldname, aliases in COLUMN_ALIASES.items():
			if normalized in aliases:
				header_map[index] = fieldname
				break
	return header_map


def _normalize_header(value):
	return str(value or "").strip().lower().replace("-", " ").replace("_", " ")


def _normalize_row(row, header_map):
	normalized = {}
	for index, value in enumerate(row):
		fieldname = header_map.get(index)
		if fieldname:
			normalized[fieldname] = str(value).strip() if value is not None else ""
	return normalized


def _resolve_link(doctype, value, required=False):
	value = (value or "").strip()
	if not value:
		if required:
			frappe.throw(_("{0} is required in one or more rows").format(doctype))
		return ""

	if frappe.db.exists(doctype, value):
		return value

	name = frappe.db.get_value(doctype, {doctype.lower().replace(" ", "_") + "_name": value}, "name")
	if name:
		return name

	if doctype == "Governorate":
		name = frappe.db.get_value(doctype, {"governorate_name": value}, "name")
		if name:
			return name

	if doctype == "District":
		name = frappe.db.get_value(doctype, {"district_name": value}, "name")
		if name:
			return name

	frappe.throw(_("{0} {1} was not found").format(doctype, value))
