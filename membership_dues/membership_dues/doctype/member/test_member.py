# Copyright (c) 2026, Your Name and Contributors
# See license.txt

import frappe

from membership_dues.tests.factories import (
	IntegrationTestCase,
	make_member,
	make_membership_type,
	make_payment,
)

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


class IntegrationTestMember(IntegrationTestCase):
	def test_names_and_email_are_cleaned(self):
		email = f"  Ada.{frappe.generate_hash(length=6)}@Example.COM "
		member = make_member(first_name="  Ada ", last_name=" Lovelace", email=email)

		self.assertEqual(member.full_name, "Ada Lovelace")
		self.assertEqual(member.email, email.strip().lower())

	def test_new_member_is_applicant(self):
		member = make_member()
		self.assertEqual(member.status, "Applicant")
		self.assertIsNone(member.paid_until)

	def test_email_is_unique_regardless_of_case(self):
		member = make_member()
		with self.assertRaises((frappe.UniqueValidationError, frappe.DuplicateEntryError)):
			make_member(email=member.email.upper())

	def test_invalid_email_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			make_member(email="not-an-email")

	def test_inactive_membership_type_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			make_member(membership_type=make_membership_type(is_active=0))

	def test_suspend_and_reinstate(self):
		member = make_member()
		make_payment(member)
		member.reload()
		self.assertEqual(member.status, "Active")

		member.suspend(reason="Conduct review")
		self.assertEqual(frappe.db.get_value("Member", member.name, "status"), "Suspended")

		member.reload()
		member.reinstate()
		self.assertEqual(frappe.db.get_value("Member", member.name, "status"), "Active")

	def test_resigned_member_must_be_reinstated_before_suspending(self):
		member = make_member()
		member.resign()
		with self.assertRaises(frappe.ValidationError):
			member.suspend()

	def test_only_managers_can_change_status(self):
		member = make_member()
		user = _make_user_with_role("Membership User")

		frappe.set_user(user)
		try:
			with self.assertRaises(frappe.PermissionError):
				frappe.get_doc("Member", member.name).suspend()
		finally:
			frappe.set_user("Administrator")


def _make_user_with_role(role):
	email = f"user-{frappe.generate_hash(length=8)}@example.com"
	user = frappe.get_doc(
		{"doctype": "User", "email": email, "first_name": "Test", "send_welcome_email": 0}
	).insert()
	user.add_roles(role)
	return email
