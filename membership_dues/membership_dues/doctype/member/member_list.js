frappe.listview_settings["Member"] = {
	add_fields: ["status", "paid_until"],
	get_indicator(doc) {
		const colors = {
			Applicant: "blue",
			Active: "green",
			Lapsed: "orange",
			Suspended: "red",
			Resigned: "gray",
		};
		return [__(doc.status), colors[doc.status] || "gray", "status,=," + doc.status];
	},
};
