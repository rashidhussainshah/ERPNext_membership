# Copyright (c) 2026, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, flt, getdate, today, validate_email_address

# Statuses a manager sets by hand. Payments and the daily job never override them.
MANUAL_STATUSES = ("Suspended", "Resigned")
MANAGER_ROLES = ("Membership Manager", "System Manager")


class Member(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		email: DF.Data
		first_name: DF.Data
		full_name: DF.Data | None
		join_date: DF.Date | None
		last_name: DF.Data | None
		last_payment_date: DF.Date | None
		membership_type: DF.Link
		naming_series: DF.Literal["MEM-.YYYY.-"]
		notes: DF.SmallText | None
		paid_from: DF.Date | None
		paid_until: DF.Date | None
		phone: DF.Data | None
		status: DF.Literal["Applicant", "Active", "Lapsed", "Suspended", "Resigned"]
		total_paid: DF.Currency
	# end: auto-generated types

	_DOCTYPE_NAME = "Member"

	def validate(self):
		self.first_name = (self.first_name or "").strip()
		self.last_name = (self.last_name or "").strip()
		self.full_name = " ".join(part for part in (self.first_name, self.last_name) if part)

		# One member per email address, regardless of letter case
		self.email = (self.email or "").strip().lower()
		validate_email_address(self.email, throw=True)

		self.validate_membership_type()

	def validate_membership_type(self):
		if not (self.is_new() or self.has_value_changed("membership_type")):
			return
		if not frappe.db.get_value("Membership Type", self.membership_type, "is_active"):
			frappe.throw(
				_("Membership Type {0} is inactive and cannot be assigned.").format(
					frappe.bold(self.membership_type)
				)
			)

	def update_membership_period(self):
		"""Recalculate the paid period and status from this member's submitted dues payments."""
		paid_from, paid_until, last_payment_date, total_paid = frappe.db.sql(
			"""
			select min(period_start), max(period_end), max(payment_date), sum(amount)
			from `tabDues Payment`
			where member = %s and docstatus = 1
			""",
			self.name,
		)[0]

		self.paid_from = paid_from
		self.paid_until = paid_until
		self.last_payment_date = last_payment_date
		self.total_paid = flt(total_paid)
		self.status = self.get_computed_status()

		# Called as a side effect of submitting or cancelling a payment the user is allowed to make
		self.flags.ignore_permissions = True
		self.save()

	def get_computed_status(self, on_date=None) -> str:
		"""Status implied by the paid period. Manual statuses always win."""
		if self.status in MANUAL_STATUSES:
			return self.status
		if not self.paid_until:
			return "Applicant"

		grace_days = cint(frappe.db.get_value("Membership Type", self.membership_type, "grace_period_days"))
		on_date = getdate(on_date or today())
		return "Active" if on_date <= add_days(getdate(self.paid_until), grace_days) else "Lapsed"

	@frappe.whitelist()
	def suspend(self, reason: str | None = None) -> None:
		self._set_manual_status("Suspended", reason)

	@frappe.whitelist()
	def resign(self, reason: str | None = None) -> None:
		self._set_manual_status("Resigned", reason)

	@frappe.whitelist()
	def reinstate(self) -> None:
		frappe.only_for(MANAGER_ROLES)
		if self.status not in MANUAL_STATUSES:
			frappe.throw(_("Only suspended or resigned members can be reinstated."))

		previous = self.status
		self.status = None  # let the paid period decide again
		self.status = self.get_computed_status()
		self.save()
		self.add_comment("Info", _("Reinstated (was {0})").format(_(previous)))

	def _set_manual_status(self, status: str, reason: str | None) -> None:
		frappe.only_for(MANAGER_ROLES)
		if self.status == status:
			frappe.throw(_("Member is already {0}.").format(_(status)))
		if self.status == "Resigned":
			frappe.throw(_("A resigned member must be reinstated first."))

		self.status = status
		self.save()
		self.add_comment("Info", f"{_(status)}: {reason}" if reason else _(status))

	@frappe.whitelist()
	def create_customer(self) -> str:
		"""Create (or return) the ERPNext Customer for this member. Needs ERPNext on the site."""
		from membership_dues.integrations.erpnext import create_customer_for_member

		return create_customer_for_member(self)
