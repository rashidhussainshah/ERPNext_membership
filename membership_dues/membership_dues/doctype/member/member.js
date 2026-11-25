// Copyright (c) 2026, Rashid Bukhari and contributors
// For license information, please see license.txt

const MANUAL_STATUSES = ["Suspended", "Resigned"];
const STATUS_COLORS = {
	Applicant: "blue",
	Active: "green",
	Lapsed: "orange",
	Suspended: "red",
	Resigned: "gray",
};

frappe.ui.form.on("Member", {
	setup(frm) {
		frm.set_query("membership_type", () => ({ filters: { is_active: 1 } }));
	},

	refresh(frm) {
		if (frm.is_new()) return;

		show_paid_period(frm);

		if (!MANUAL_STATUSES.includes(frm.doc.status)) {
			frm.add_custom_button(__("Record Dues Payment"), () =>
				frappe.new_doc("Dues Payment", { member: frm.doc.name })
			);
		}

		if (frappe.user.has_role(["Membership Manager", "System Manager"])) {
			add_status_actions(frm);
		}

		// The Customer field only exists when ERPNext is installed
		if (frm.fields_dict.customer && !frm.doc.customer) {
			frm.add_custom_button(
				__("Create Customer"),
				() =>
					frm.call("create_customer").then(({ message }) => {
						frappe.show_alert({ message: __("Customer {0} linked", [message]), indicator: "green" });
						frm.reload_doc();
					}),
				__("ERPNext")
			);
		}
	},
});

function show_paid_period(frm) {
	if (!frm.doc.paid_until) {
		frm.dashboard.set_headline_alert(__("No dues paid yet."), "blue");
		return;
	}
	const days_left = frappe.datetime.get_diff(frm.doc.paid_until, frappe.datetime.get_today());
	const until = frappe.datetime.str_to_user(frm.doc.paid_until);
	const message =
		days_left >= 0
			? __("Paid until {0} ({1} days left)", [until, days_left])
			: __("Paid period ended on {0} ({1} days ago)", [until, -days_left]);
	frm.dashboard.set_headline_alert(message, STATUS_COLORS[frm.doc.status] || "gray");
}

function add_status_actions(frm) {
	const run = (method, args = {}) =>
		frm.call(method, args).then(() => frm.reload_doc());

	const ask_reason_then = (method, title) =>
		frappe.prompt(
			{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason") },
			({ reason }) => run(method, { reason }),
			title,
			__("Confirm")
		);

	if (MANUAL_STATUSES.includes(frm.doc.status)) {
		frm.add_custom_button(__("Reinstate"), () => run("reinstate"), __("Actions"));
	} else {
		frm.add_custom_button(__("Suspend"), () => ask_reason_then("suspend", __("Suspend Member")), __("Actions"));
	}
	if (frm.doc.status !== "Resigned") {
		frm.add_custom_button(__("Resign"), () => ask_reason_then("resign", __("Record Resignation")), __("Actions"));
	}
}
