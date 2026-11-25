# Copyright (c) 2026, Rashid Bukhari and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, add_months, getdate, today

from membership_dues.tests.factories import (
	IntegrationTestCase,
	make_member,
	make_membership_type,
	make_payment,
)

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


def end_of_period(start, months=12):
	return add_days(add_months(getdate(start), months), -1)


class IntegrationTestDuesPayment(IntegrationTestCase):
	def test_first_payment_activates_member(self):
		member = make_member(membership_type=make_membership_type(fee=120))
		payment = make_payment(member)

		self.assertEqual(getdate(payment.period_start), getdate(today()))
		self.assertEqual(getdate(payment.period_end), end_of_period(today()))

		member.reload()
		self.assertEqual(member.status, "Active")
		self.assertEqual(getdate(member.paid_until), getdate(payment.period_end))
		self.assertEqual(member.total_paid, 120)

	def test_early_renewal_continues_after_paid_period(self):
		member = make_member()
		first = make_payment(member)
		second = make_payment(member)  # paid again on the same day

		self.assertEqual(getdate(second.period_start), add_days(getdate(first.period_end), 1))
		member.reload()
		self.assertEqual(getdate(member.paid_until), getdate(second.period_end))

	def test_late_renewal_within_grace_keeps_continuity(self):
		member = make_member(membership_type=make_membership_type(grace_period_days=30))
		first = make_payment(member, payment_date=add_days(today(), -375))  # ended ~10 days ago
		second = make_payment(member)

		self.assertEqual(getdate(second.period_start), add_days(getdate(first.period_end), 1))

	def test_renewal_after_grace_starts_on_payment_date(self):
		member = make_member(membership_type=make_membership_type(grace_period_days=30))
		make_payment(member, payment_date=add_days(today(), -450))  # ended ~85 days ago
		member.reload()
		self.assertEqual(member.status, "Lapsed")

		renewal = make_payment(member)
		self.assertEqual(getdate(renewal.period_start), getdate(today()))
		member.reload()
		self.assertEqual(member.status, "Active")

	def test_amount_below_fee_rejected(self):
		member = make_member(membership_type=make_membership_type(fee=100))
		with self.assertRaises(frappe.ValidationError):
			make_payment(member, amount=99.99)

	def test_future_payment_date_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			make_payment(make_member(), payment_date=add_days(today(), 1))

	def test_duplicate_reference_rejected(self):
		member = make_member()
		make_payment(member, reference_no="BANK-123")
		with self.assertRaises(frappe.ValidationError):
			make_payment(member, reference_no="BANK-123")

	def test_resigned_member_cannot_pay(self):
		member = make_member()
		member.resign()
		with self.assertRaises(frappe.ValidationError):
			make_payment(member)

	def test_cancel_recalculates_member(self):
		member = make_member()
		payment = make_payment(member)

		payment.cancel()
		member.reload()
		self.assertEqual(member.status, "Applicant")
		self.assertIsNone(member.paid_until)
		self.assertEqual(member.total_paid, 0)

	def test_earlier_payment_cannot_be_cancelled_before_later_one(self):
		member = make_member()
		first = make_payment(member)
		second = make_payment(member)

		with self.assertRaises(frappe.ValidationError):
			first.cancel()

		second.cancel()
		first.reload()
		first.cancel()
		member.reload()
		self.assertEqual(member.status, "Applicant")
