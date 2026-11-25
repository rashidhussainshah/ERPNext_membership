from membership_dues.integrations.erpnext import setup_custom_fields


def execute():
	"""Sites that installed the app before the ERPNext integration existed get the Customer field on migrate."""
	setup_custom_fields()
