import frappe
from frappe.utils import add_days, today

from membership_dues.tasks import mark_lapsed_members
from membership_dues.tests.factories import (
	IntegrationTestCase,
	make_member,
	make_membership_type,
	make_payment,
)


class TestMarkLapsedMembers(IntegrationTestCase):
	def test_lapses_only_members_past_their_grace_period(self):
		# Both paid periods ended ~35 days ago
		past_grace = make_member(membership_type=make_membership_type(grace_period_days=30))
		within_grace = make_member(membership_type=make_membership_type(grace_period_days=60))
		for member in (past_grace, within_grace):
			make_payment(member, payment_date=add_days(today(), -400))
			# Simulate yesterday's state: the job has not run since the period ended
			frappe.db.set_value("Member", member.name, "status", "Active")

		lapsed = mark_lapsed_members()

		self.assertIn(past_grace.name, lapsed)
		self.assertNotIn(within_grace.name, lapsed)
		self.assertEqual(frappe.db.get_value("Member", past_grace.name, "status"), "Lapsed")
		self.assertEqual(frappe.db.get_value("Member", within_grace.name, "status"), "Active")

	def test_paid_up_and_manual_statuses_are_untouched(self):
		paid_up = make_member()
		make_payment(paid_up)

		suspended = make_member()
		make_payment(suspended, payment_date=add_days(today(), -400))
		suspended.reload()
		suspended.suspend()

		lapsed = mark_lapsed_members()

		self.assertNotIn(paid_up.name, lapsed)
		self.assertEqual(frappe.db.get_value("Member", paid_up.name, "status"), "Active")
		self.assertEqual(frappe.db.get_value("Member", suspended.name, "status"), "Suspended")
