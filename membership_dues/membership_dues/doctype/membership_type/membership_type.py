# Copyright (c) 2026, Your Name and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


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
