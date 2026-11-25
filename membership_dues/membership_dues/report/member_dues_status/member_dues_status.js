// Copyright (c) 2026, Rashid Bukhari and contributors
// For license information, please see license.txt

frappe.query_reports["Member Dues Status"] = {
	filters: [
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nApplicant\nActive\nLapsed\nSuspended\nResigned",
		},
		{
			fieldname: "membership_type",
			label: __("Membership Type"),
			fieldtype: "Link",
			options: "Membership Type",
		},
		{
			fieldname: "expiring_within_days",
			label: __("Expiring Within (Days)"),
			fieldtype: "Int",
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "days_left" && data && data.days_left !== null && data.days_left < 0) {
			value = `<span class="text-danger">${value}</span>`;
		}
		return value;
	},
};
