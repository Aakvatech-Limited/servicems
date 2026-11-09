"""Shared Desk and Field inspection sequencing, using existing repair tasks."""

import frappe
from frappe import _

INSPECTION = "Service Vehicle Inspection"
POLICIES = ("Required", "Optional", "Disabled")


def settings():
	doc = frappe.get_cached_doc("Service Settings")
	return {
		"Pre-Service": doc.get("pre_inspection_policy") or "Optional",
		"Post-Service": doc.get("post_inspection_policy") or "Optional",
		"gps_enabled": bool(doc.get("field_gps_enabled")),
	}


def finished(job_card):
	return _completed_stage(job_card, "Post-Service")


def require_field_open(job_card):
	if finished(job_card):
		frappe.throw(
			_("Field work is finished for this Job Card. Use authorized Desk access for its history.")
		)


def pre_completed(job_card):
	return _completed_stage(job_card, "Pre-Service")


def _completed_stage(job_card, stage):
	return bool(
		frappe.db.sql(
			"""select name from `tabService Vehicle Inspection`
		where service_job_card=%s and inspection_stage=%s and inspection_status='Completed'
		limit 1 for update""",
			(job_card, stage),
		)
	)


def repair_started(card):
	return (
		card.status in ("Repairing", "Completed", "Closed")
		or any(row.completed for row in card.tasks)
		or any(row.started_at for row in card.labour_entries)
	)


def repair_complete(card):
	return all(row.completed for row in card.tasks) and not any(
		row.started_at and not row.stopped_at for row in card.labour_entries
	)


def stage_reason(card, stage, policy=None):
	policy = policy or settings()
	if finished(card.name):
		return _("Field work is finished for this Job Card.")
	if policy[stage] == "Disabled":
		return _("This inspection stage is disabled in Service Settings.")
	if stage == "Pre-Service" and repair_started(card):
		return _("Pre-Inspection must be recorded before repair work begins.")
	if stage == "Post-Service":
		if policy["Pre-Service"] == "Required" and not pre_completed(card.name):
			return _("Complete the required Pre-Inspection before Post-Inspection.")
		if not repair_complete(card):
			return _("Complete all repair tasks and stop running labour before Post-Inspection.")
	return ""


def stage_state(card):
	policy = settings()
	return {
		stage: {"policy": policy[stage], "reason": stage_reason(card, stage, policy)}
		for stage in ("Pre-Service", "Post-Service")
	}


def validate_inspection(doc):
	if not doc.service_job_card or not doc.inspection_stage:
		return
	card = frappe.get_doc("Service Job Card", doc.service_job_card, for_update=True)
	if doc.corrects_inspection:
		from servicems.field_permissions import _field_user

		if _field_user():
			require_field_open(card.name)
		return
	reason = stage_reason(card, doc.inspection_stage)
	if reason:
		frappe.throw(reason)


def validate_repair(card):
	previous = card.get_doc_before_save() if not card.is_new() else None
	old_tasks = {row.name: row.completed for row in previous.tasks} if previous else {}
	old_labour = {row.name for row in previous.labour_entries} if previous else set()
	progress = (
		any(row.completed and not old_tasks.get(row.name) for row in card.tasks)
		or any(row.started_at and row.name not in old_labour for row in card.labour_entries)
		or (
			card.status in ("Repairing", "Completed", "Closed")
			and (
				not previous
				or (
					card.status != previous.status
					and (card.status == "Repairing" or previous.status not in ("Completed", "Closed"))
				)
			)
		)
	)
	if not progress:
		return
	frappe.db.get_value("Service Job Card", card.name, "name", for_update=True)
	policy = settings()
	post_done = finished(card.name)
	if policy["Pre-Service"] == "Required" and not post_done and not pre_completed(card.name):
		frappe.throw(_("Complete the required Pre-Inspection before starting repair work."))
	if (
		previous
		and post_done
		and (
			any(row.completed and not old_tasks.get(row.name) for row in card.tasks)
			or any(row.started_at and row.name not in old_labour for row in card.labour_entries)
			or card.status == "Repairing"
		)
	):
		frappe.throw(_("Post-Inspection is completed. Create a new Job Card for further repair work."))
	if card.status in ("Completed", "Closed") and policy["Post-Service"] == "Required" and not post_done:
		frappe.throw(_("Complete the required Post-Inspection before completing the Job Card."))
