# Copyright (c) 2026, Your Name and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


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
