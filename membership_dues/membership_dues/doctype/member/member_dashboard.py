from frappe import _


def get_data():
	"""Linked documents shown in the Member form's Connections tab."""
	return {
		"fieldname": "member",
		"transactions": [{"label": _("Dues"), "items": ["Dues Payment"]}],
	}
