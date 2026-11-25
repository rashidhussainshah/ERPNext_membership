import frappe
from frappe.utils import getdate, today


def mark_lapsed_members() -> list[str]:
	"""Daily job: mark Active members as Lapsed once their paid period and grace period have ended."""
	expired = frappe.get_all(
		"Member",
		filters={"status": "Active", "paid_until": ("<", getdate(today()))},
		pluck="name",
	)

	lapsed = []
	for name in expired:
		member = frappe.get_doc("Member", name)
		if member.get_computed_status() == "Lapsed":
			member.status = "Lapsed"
			member.flags.ignore_permissions = True
			member.save()
			lapsed.append(name)

	return lapsed
