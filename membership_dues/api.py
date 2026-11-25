"""REST API for other systems: websites, payment gateways, mobile apps.

Call with an API key and secret:
    curl -H "Authorization: token <api_key>:<api_secret>" \
        "http://<site>/api/method/membership_dues.api.get_member_status?email=ada@example.com"
"""

import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist(methods=["GET"])
def get_member_status(email: str) -> dict:
	"""Membership status for an email address (case-insensitive)."""
	frappe.has_permission("Member", "read", throw=True)

	member = frappe.db.get_value(
		"Member",
		{"email": (email or "").strip().lower()},
		["name", "full_name", "status", "membership_type", "paid_until"],
		as_dict=True,
	)
	if not member:
		frappe.throw(_("No member found with email {0}").format(email), frappe.DoesNotExistError)

	frappe.has_permission("Member", "read", doc=member.name, throw=True)
	return member


@frappe.whitelist(methods=["POST"])
def record_payment(
	member: str,
	amount: float | None = None,
	payment_date: str | None = None,
	mode_of_payment: str = "Online",
	reference_no: str | None = None,
	submit: bool = True,
) -> dict:
	"""Record (and by default submit) a dues payment.

	Safe to retry: if a payment with the same `reference_no` already exists for the member,
	that payment is returned instead of creating a duplicate.
	"""
	frappe.has_permission("Dues Payment", "create", throw=True)

	if reference_no:
		existing = frappe.db.get_value(
			"Dues Payment",
			{"member": member, "reference_no": reference_no, "docstatus": ("<", 2)},
			"name",
		)
		if existing:
			return _payment_response(frappe.get_doc("Dues Payment", existing), created=False)

	if not amount:
		membership_type = frappe.db.get_value("Member", member, "membership_type")
		amount = frappe.db.get_value("Membership Type", membership_type, "fee_amount")

	payment = frappe.get_doc(
		{
			"doctype": "Dues Payment",
			"member": member,
			"amount": flt(amount),
			"payment_date": payment_date or frappe.utils.today(),
			"mode_of_payment": mode_of_payment,
			"reference_no": reference_no,
		}
	)
	payment.insert()
	if submit:
		payment.submit()

	return _payment_response(payment, created=True)


def _payment_response(payment, created: bool) -> dict:
	return {
		"name": payment.name,
		"created": created,
		"docstatus": payment.docstatus,
		"period_start": payment.period_start,
		"period_end": payment.period_end,
		"member_status": frappe.db.get_value("Member", payment.member, "status"),
	}
