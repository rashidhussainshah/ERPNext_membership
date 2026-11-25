# Copyright (c) 2026, Your Name and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


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
