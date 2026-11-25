import frappe
from frappe.utils import getdate

from membership_dues.api import get_member_status, record_payment
from membership_dues.tests.factories import IntegrationTestCase, make_member, make_membership_type


class TestMembershipAPI(IntegrationTestCase):
	def test_get_member_status_by_email_ignores_case(self):
		member = make_member()
		result = get_member_status(member.email.upper())

		self.assertEqual(result.name, member.name)
		self.assertEqual(result.status, "Applicant")

	def test_get_member_status_unknown_email(self):
		with self.assertRaises(frappe.DoesNotExistError):
			get_member_status("nobody-here@example.com")

	def test_record_payment_defaults_to_fee_and_submits(self):
		member = make_member(membership_type=make_membership_type(fee=75))
		result = record_payment(member=member.name, reference_no="GATEWAY-1")

		self.assertTrue(result["created"])
		self.assertEqual(result["docstatus"], 1)
		self.assertEqual(result["member_status"], "Active")
		self.assertEqual(frappe.db.get_value("Dues Payment", result["name"], "amount"), 75)

	def test_record_payment_is_safe_to_retry(self):
		member = make_member()
		first = record_payment(member=member.name, reference_no="GATEWAY-RETRY")
		retry = record_payment(member=member.name, reference_no="GATEWAY-RETRY")

		self.assertFalse(retry["created"])
		self.assertEqual(retry["name"], first["name"])
		self.assertEqual(frappe.db.count("Dues Payment", {"member": member.name}), 1)
		self.assertEqual(getdate(retry["period_end"]), getdate(first["period_end"]))
