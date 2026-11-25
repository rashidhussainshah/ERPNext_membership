# Copyright (c) 2026, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, cint, flt, fmt_money, get_link_to_form, getdate, today

BLOCKED_MEMBER_STATUSES = ("Suspended", "Resigned")


class DuesPayment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		amount: DF.Currency
		member: DF.Link
		member_name: DF.Data | None
		membership_type: DF.Link | None
		mode_of_payment: DF.Literal["Cash", "Bank Transfer", "Card", "Online", "Cheque", "Other"]
		naming_series: DF.Literal["DUES-.YYYY.-"]
		payment_date: DF.Date
		period_end: DF.Date | None
		period_start: DF.Date | None
		reference_no: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Dues Payment"

	def validate(self):
		self.membership_type = self.membership_type or frappe.db.get_value(
			"Member", self.member, "membership_type"
		)
		self.validate_member()
		self.validate_payment_date()
		self.validate_amount()
		self.validate_duplicate_reference()
		self.set_period()

	def before_submit(self):
		# Lock the member row so two payments submitted at the same moment cannot cover the same period
		frappe.db.get_value("Member", self.member, "name", for_update=True)
		self.set_period()

	def on_submit(self):
		frappe.get_doc("Member", self.member).update_membership_period()

	def before_cancel(self):
		later = frappe.db.get_value(
			"Dues Payment",
			{
				"member": self.member,
				"docstatus": 1,
				"name": ("!=", self.name),
				"period_start": (">", self.period_start),
			},
			"name",
		)
		if later:
			frappe.throw(
				_("Cancel the later payment {0} first, so the membership period stays continuous.").format(
					get_link_to_form("Dues Payment", later)
				)
			)

	def on_cancel(self):
		frappe.get_doc("Member", self.member).update_membership_period()

	def validate_member(self):
		status = frappe.db.get_value("Member", self.member, "status")
		if status in BLOCKED_MEMBER_STATUSES:
			frappe.throw(
				_("Cannot record dues for {0}: the member is {1}. Reinstate the member first.").format(
					frappe.bold(self.member_name or self.member), _(status)
				)
			)

	def validate_payment_date(self):
		if getdate(self.payment_date) > getdate(today()):
			frappe.throw(_("Payment Date cannot be in the future."))

	def validate_amount(self):
		fee = flt(frappe.db.get_value("Membership Type", self.membership_type, "fee_amount"))
		if flt(self.amount) < fee:
			frappe.throw(
				_("Amount {0} is less than the {1} fee of {2}.").format(
					fmt_money(self.amount), frappe.bold(self.membership_type), fmt_money(fee)
				)
			)

	def validate_duplicate_reference(self):
		if not self.reference_no:
			return
		duplicate = frappe.db.get_value(
			"Dues Payment",
			{
				"member": self.member,
				"reference_no": self.reference_no,
				"docstatus": ("<", 2),
				"name": ("!=", self.name),
			},
			"name",
		)
		if duplicate:
			frappe.throw(
				_("Reference No {0} is already used by {1}.").format(
					frappe.bold(self.reference_no), get_link_to_form("Dues Payment", duplicate)
				)
			)

	def set_period(self):
		"""Work out which period this payment covers.

		- Paid up (or within the grace period): continue the day after the current paid period ends.
		- Lapsed beyond the grace period: start again on the payment date.
		"""
		duration, grace_days = frappe.db.get_value(
			"Membership Type", self.membership_type, ["duration_months", "grace_period_days"]
		)
		payment_date = getdate(self.payment_date)
		paid_until = self.get_current_paid_until()

		if paid_until and payment_date <= add_days(paid_until, cint(grace_days)):
			start = add_days(paid_until, 1)
		else:
			start = payment_date

		self.period_start = start
		self.period_end = add_days(add_months(start, cint(duration)), -1)

	def get_current_paid_until(self):
		paid_until = frappe.db.sql(
			"""
			select max(period_end) from `tabDues Payment`
			where member = %s and docstatus = 1 and name != %s
			""",
			(self.member, self.name or ""),
		)[0][0]
		return getdate(paid_until) if paid_until else None
