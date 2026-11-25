"""Helpers that create test data. Every record gets a unique name or email, so tests never collide."""

import frappe
from frappe.utils import today

try:
	from frappe.tests import IntegrationTestCase
except ImportError:  # Frappe v15
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase


def make_membership_type(fee=100, duration_months=12, grace_period_days=30, **kwargs):
	return frappe.get_doc(
		{
			"doctype": "Membership Type",
			"membership_type_name": f"Test Type {frappe.generate_hash(length=8)}",
			"fee_amount": fee,
			"duration_months": duration_months,
			"grace_period_days": grace_period_days,
			**kwargs,
		}
	).insert()


def make_member(membership_type=None, **kwargs):
	membership_type = membership_type or make_membership_type()
	return frappe.get_doc(
		{
			"doctype": "Member",
			"first_name": "Test",
			"last_name": "Member",
			"email": f"member-{frappe.generate_hash(length=10)}@example.com",
			"membership_type": membership_type.name,
			**kwargs,
		}
	).insert()


def make_payment(member, payment_date=None, amount=None, submit=True, **kwargs):
	fee = frappe.db.get_value("Membership Type", member.membership_type, "fee_amount")
	payment = frappe.get_doc(
		{
			"doctype": "Dues Payment",
			"member": member.name,
			"payment_date": payment_date or today(),
			"amount": fee if amount is None else amount,
			"mode_of_payment": "Cash",
			**kwargs,
		}
	).insert()
	if submit:
		payment.submit()
	return payment
