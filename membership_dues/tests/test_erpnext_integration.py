import unittest

import frappe

from membership_dues.integrations.erpnext import is_erpnext_installed
from membership_dues.tests.factories import IntegrationTestCase, make_member


@unittest.skipUnless(is_erpnext_installed(), "ERPNext is not installed on this site")
class TestERPNextIntegration(IntegrationTestCase):
	def test_customer_field_exists(self):
		self.assertTrue(frappe.get_meta("Member").has_field("customer"))

	def test_create_customer_links_member_and_is_idempotent(self):
		member = make_member(first_name="Grace", last_name="Hopper")

		customer = member.create_customer()
		self.assertEqual(frappe.db.get_value("Customer", customer, "customer_name"), "Grace Hopper")
		self.assertEqual(frappe.db.get_value("Member", member.name, "customer"), customer)

		member.reload()
		self.assertEqual(member.create_customer(), customer)
		self.assertEqual(frappe.db.count("Customer", {"customer_name": "Grace Hopper"}), 1)
