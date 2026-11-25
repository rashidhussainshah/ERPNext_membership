"""Sample data for demos and manual testing. Never run this on a production site.

    bench --site <site> execute membership_dues.demo.create_demo_data
    bench --site <site> execute membership_dues.demo.delete_demo_data

Demo members use the @demo.example.com email domain, so they are easy to find and remove.
"""

import frappe
from frappe.utils import add_days, today

DEMO_DOMAIN = "demo.example.com"

MEMBERSHIP_TYPES = [
	# name, fee, months, grace days
	("Annual", 120, 12, 30),
	("Monthly", 15, 1, 7),
	("Student (Annual)", 60, 12, 30),
]

# first name, last name, membership type, payment dates (days before today), then an optional action
MEMBERS = [
	("Amina", "Khan", "Annual", [-20], None),  # Active
	("Bilal", "Ahmed", "Annual", [-350], None),  # Active, expiring in about two weeks
	("Sara", "Malik", "Monthly", [-50], None),  # Lapsed: ended ~20 days ago, 7-day grace
	("Omar", "Farooq", "Student (Annual)", [-500, -130], None),  # renewed within grace: continuous
	("Zainab", "Ali", "Annual", [], None),  # Applicant: nothing paid yet
	("Hassan", "Raza", "Annual", [-100], "suspend"),  # Suspended by a manager
]


def create_demo_data():
	frappe.only_for("System Manager")

	for name, fee, months, grace in MEMBERSHIP_TYPES:
		if not frappe.db.exists("Membership Type", name):
			frappe.get_doc(
				{
					"doctype": "Membership Type",
					"membership_type_name": name,
					"fee_amount": fee,
					"duration_months": months,
					"grace_period_days": grace,
				}
			).insert()

	for first, last, membership_type, payment_days, action in MEMBERS:
		email = f"{first}.{last}@{DEMO_DOMAIN}".lower()
		if frappe.db.exists("Member", {"email": email}):
			continue

		member = frappe.get_doc(
			{
				"doctype": "Member",
				"first_name": first,
				"last_name": last,
				"email": email,
				"membership_type": membership_type,
				"join_date": add_days(today(), payment_days[0] if payment_days else -5),
			}
		).insert()

		for days in payment_days:
			fee = frappe.db.get_value("Membership Type", membership_type, "fee_amount")
			frappe.get_doc(
				{
					"doctype": "Dues Payment",
					"member": member.name,
					"payment_date": add_days(today(), days),
					"amount": fee,
					"mode_of_payment": "Bank Transfer",
				}
			).insert().submit()

		if action == "suspend":
			member.reload()
			member.suspend(reason="Demo: membership under review")

	frappe.db.commit()
	print(
		f"Demo data ready: {frappe.db.count('Member', {'email': ('like', f'%@{DEMO_DOMAIN}')})} demo members"
	)


def delete_demo_data():
	frappe.only_for("System Manager")

	members = frappe.get_all("Member", filters={"email": ("like", f"%@{DEMO_DOMAIN}")}, pluck="name")
	for member in members:
		# Newest first: only the latest payment may be cancelled
		for payment in frappe.get_all(
			"Dues Payment",
			filters={"member": member},
			fields=["name", "docstatus"],
			order_by="period_start desc",
		):
			doc = frappe.get_doc("Dues Payment", payment.name)
			if doc.docstatus == 1:
				doc.cancel()
			frappe.delete_doc("Dues Payment", doc.name)
		frappe.delete_doc("Member", member)

	frappe.db.commit()
	print(f"Deleted {len(members)} demo members")
