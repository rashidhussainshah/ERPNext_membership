"""Optional ERPNext integration.

The app works on plain Frappe. When ERPNext is installed on the site, members can be linked to an
ERPNext Customer, so dues can later be invoiced and accounted for in ERPNext.
"""

import frappe
from frappe import _

CUSTOM_FIELDS = {
	"Member": [
		{
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"label": "Customer",
			"insert_after": "total_paid",
			"read_only": 1,
			"no_copy": 1,
			"description": "ERPNext Customer for this member",
		}
	]
}


def is_erpnext_installed() -> bool:
	return "erpnext" in frappe.get_installed_apps()


def setup_custom_fields() -> None:
	"""Add the Customer link to Member. Does nothing on sites without ERPNext."""
	if not is_erpnext_installed():
		return

	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(CUSTOM_FIELDS, update=True)


def create_customer_for_member(member) -> str:
	if not is_erpnext_installed():
		frappe.throw(_("ERPNext is not installed on this site."))

	if member.get("customer") and frappe.db.exists("Customer", member.customer):
		return member.customer

	customer = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": member.full_name,
			"customer_type": "Individual",
			"customer_group": _get_leaf_default("Customer Group", "customer_group"),
			"territory": _get_leaf_default("Territory", "territory"),
		}
	)
	customer.insert()  # checks the user's permission to create customers

	member.db_set("customer", customer.name)
	member.add_comment("Info", _("Linked to Customer {0}").format(customer.name))
	return customer.name


def _get_leaf_default(doctype: str, selling_settings_field: str) -> str:
	"""ERPNext rejects group nodes here, so use Selling Settings' default or the first non-group record."""
	value = frappe.db.get_single_value("Selling Settings", selling_settings_field)
	if value and not frappe.db.get_value(doctype, value, "is_group"):
		return value

	value = frappe.db.get_value(doctype, {"is_group": 0}, "name", order_by="lft asc")
	if not value:
		frappe.throw(_("Please create a {0} that is not a group.").format(_(doctype)))
	return value
