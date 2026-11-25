from membership_dues.integrations.erpnext import setup_custom_fields


def after_install():
	setup_custom_fields()


def after_app_install(app_name):
	"""Runs when any app is installed later. Adds the ERPNext fields if ERPNext arrives after this app."""
	if app_name == "erpnext":
		setup_custom_fields()
