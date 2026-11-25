// Copyright (c) 2026, Your Name and contributors
// For license information, please see license.txt

frappe.ui.form.on("Dues Payment", {
	setup(frm) {
		frm.set_query("member", () => ({
			filters: { status: ["not in", ["Suspended", "Resigned"]] },
		}));
	},

	refresh(frm) {
		// Opened from the Member form's "Record Dues Payment" button: fill in the fee
		if (frm.is_new() && frm.doc.membership_type && !frm.doc.amount) {
			frm.trigger("membership_type");
		}

		if (frm.doc.period_start && frm.doc.period_end) {
			frm.dashboard.set_headline_alert(
				__("Covers {0} to {1}", [
					frappe.datetime.str_to_user(frm.doc.period_start),
					frappe.datetime.str_to_user(frm.doc.period_end),
				]),
				frm.doc.docstatus === 1 ? "green" : "blue"
			);
		}
	},

	// Set when the member is picked (fetched from Member)
	membership_type(frm) {
		if (!frm.doc.membership_type || frm.doc.docstatus !== 0) return;
		frappe.db
			.get_value("Membership Type", frm.doc.membership_type, "fee_amount")
			.then(({ message }) => message && frm.set_value("amount", message.fee_amount));
	},
});
