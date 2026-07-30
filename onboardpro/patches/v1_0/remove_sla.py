import frappe

SLA_DOCTYPES = ("SLA Policy", "SLA Priority", "SLA Working Day", "SLA Holiday")

# Columns left behind on `tabImplementation Request` — Frappe never drops a column
# when its docfield is removed from the DocType definition.
SLA_COLUMNS = (
	"sla_policy",
	"sla_creation",
	"first_responded_on",
	"on_hold_since",
	"total_hold_time",
	"fr_due_at",
	"fr_state",
	"res_due_at",
	"res_state",
)


def execute():
	"""The SLA feature was removed — drop its DocTypes and the orphaned request columns."""
	for doctype in SLA_DOCTYPES:
		frappe.delete_doc("DocType", doctype, force=True, ignore_missing=True)
		frappe.db.sql_ddl(f"DROP TABLE IF EXISTS `tab{doctype}`")

	existing = frappe.db.get_table_columns("Implementation Request")
	for column in SLA_COLUMNS:
		if column in existing:
			frappe.db.sql_ddl(f"ALTER TABLE `tabImplementation Request` DROP COLUMN `{column}`")

	frappe.db.commit()
