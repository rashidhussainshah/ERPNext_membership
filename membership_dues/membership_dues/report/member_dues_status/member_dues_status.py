# Copyright (c) 2026, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, cint, date_diff, flt, today

STATUSES = ("Applicant", "Active", "Lapsed", "Suspended", "Resigned")
EXPIRING_SOON_DAYS = 30


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = get_data(filters)
	return get_columns(), data, None, get_chart(data), get_summary(data)


def get_columns():
	return [
		{"label": _("Member"), "fieldname": "name", "fieldtype": "Link", "options": "Member", "width": 150},
		{"label": _("Full Name"), "fieldname": "full_name", "fieldtype": "Data", "width": 180},
		{
			"label": _("Membership Type"),
			"fieldname": "membership_type",
			"fieldtype": "Link",
			"options": "Membership Type",
			"width": 150,
		},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Paid Until"), "fieldname": "paid_until", "fieldtype": "Date", "width": 110},
		{"label": _("Days Left"), "fieldname": "days_left", "fieldtype": "Int", "width": 90},
		{"label": _("Last Payment"), "fieldname": "last_payment_date", "fieldtype": "Date", "width": 110},
		{"label": _("Total Paid"), "fieldname": "total_paid", "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	conditions = {}
	if filters.status:
		conditions["status"] = filters.status
	if filters.membership_type:
		conditions["membership_type"] = filters.membership_type
	if cint(filters.expiring_within_days) > 0:
		conditions["paid_until"] = ["between", [today(), add_days(today(), cint(filters.expiring_within_days))]]

	# get_list (not get_all) so the user's permissions apply
	rows = frappe.get_list(
		"Member",
		filters=conditions,
		fields=["name", "full_name", "membership_type", "status", "paid_until", "last_payment_date", "total_paid"],
		order_by="paid_until asc",
	)
	for row in rows:
		row.days_left = date_diff(row.paid_until, today()) if row.paid_until else None
	return rows


def get_chart(data):
	counts = {status: 0 for status in STATUSES}
	for row in data:
		counts[row.status] = counts.get(row.status, 0) + 1

	statuses = [status for status in STATUSES if counts[status]]
	if not statuses:
		return None
	return {
		"data": {
			"labels": [_(status) for status in statuses],
			"datasets": [{"name": _("Members"), "values": [counts[status] for status in statuses]}],
		},
		"type": "donut",
	}


def get_summary(data):
	active = [row for row in data if row.status == "Active"]
	expiring = [row for row in active if row.days_left is not None and 0 <= row.days_left <= EXPIRING_SOON_DAYS]
	return [
		{"label": _("Active Members"), "value": len(active), "indicator": "Green", "datatype": "Int"},
		{
			"label": _("Lapsed Members"),
			"value": sum(1 for row in data if row.status == "Lapsed"),
			"indicator": "Orange",
			"datatype": "Int",
		},
		{
			"label": _("Expiring in {0} Days").format(EXPIRING_SOON_DAYS),
			"value": len(expiring),
			"indicator": "Blue",
			"datatype": "Int",
		},
		{
			"label": _("Total Dues Collected"),
			"value": sum(flt(row.total_paid) for row in data),
			"datatype": "Currency",
		},
	]
