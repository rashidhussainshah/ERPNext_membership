# Copyright (c) 2026, Rashid Bukhari and Contributors
# See license.txt

import frappe

from membership_dues.tests.factories import IntegrationTestCase, make_membership_type

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


class IntegrationTestMembershipType(IntegrationTestCase):
	def test_valid_type_is_saved(self):
		membership_type = make_membership_type(fee=120, duration_months=12, grace_period_days=15)
		self.assertTrue(frappe.db.exists("Membership Type", membership_type.name))

	def test_fee_must_be_positive(self):
		for fee in (0, -10):
			with self.assertRaises(frappe.ValidationError):
				make_membership_type(fee=fee)

	def test_duration_must_be_within_limits(self):
		for months in (0, 121):
			with self.assertRaises(frappe.ValidationError):
				make_membership_type(duration_months=months)

	def test_grace_period_cannot_be_negative(self):
		with self.assertRaises(frappe.ValidationError):
			make_membership_type(grace_period_days=-1)
