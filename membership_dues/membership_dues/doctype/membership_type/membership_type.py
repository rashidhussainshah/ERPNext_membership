# Copyright (c) 2026, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

MAX_DURATION_MONTHS = 120


class MembershipType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.SmallText | None
		duration_months: DF.Int
		fee_amount: DF.Currency
		grace_period_days: DF.Int
		is_active: DF.Check
		membership_type_name: DF.Data
	# end: auto-generated types

	_DOCTYPE_NAME = "Membership Type"

	def validate(self):
		if flt(self.fee_amount) <= 0:
			frappe.throw(_("Fee Amount must be greater than zero."))

		if not 1 <= cint(self.duration_months) <= MAX_DURATION_MONTHS:
			frappe.throw(_("Duration must be between 1 and {0} months.").format(MAX_DURATION_MONTHS))

		if cint(self.grace_period_days) < 0:
			frappe.throw(_("Grace Period cannot be negative."))
