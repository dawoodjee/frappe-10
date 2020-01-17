# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import json
import os
import frappe
import frappe.translate
import frappe.modules.patch_handler
import frappe.model.sync
from frappe.utils.fixtures import sync_fixtures
from frappe.sessions import clear_global_cache
from frappe.desk.notifications import clear_notifications
from frappe.website import render, router
from frappe.desk.doctype.desktop_icon.desktop_icon import sync_desktop_icons
from frappe.core.doctype.language.language import sync_languages
from frappe.modules.utils import sync_customizations

def migrate(verbose=True, rebuild_website=False):
	'''Migrate all apps to the latest version, will:

	- run patches
	- sync doctypes (schema)
	- sync fixtures
	- sync desktop icons
	- sync web pages (from /www)'''

	touched_tables_file = frappe.get_site_path('touched_tables.json')
	if os.path.exists(touched_tables_file):
		os.remove(touched_tables_file)

	try:
		frappe.flags.touched_tables = set()
		frappe.flags.in_migrate = True
		clear_global_cache()

		# run patches
		frappe.modules.patch_handler.run_all()
		# sync
		frappe.model.sync.sync_all(verbose=verbose)
		frappe.translate.clear_cache()
		sync_fixtures()
		sync_customizations()
		sync_desktop_icons()
		sync_languages()

		frappe.get_doc('Portal Settings', 'Portal Settings').sync_menu()

		# syncs statics
		render.clear_cache()

		# add static pages to global search
		router.sync_global_search()

		frappe.db.commit()

		clear_notifications()

		frappe.publish_realtime("version-update")
		frappe.flags.in_migrate = False
	finally:
		with open(touched_tables_file, 'w') as f:
			json.dump(list(frappe.flags.touched_tables), f, sort_keys=True, indent=4)
		frappe.flags.touched_tables.clear()
