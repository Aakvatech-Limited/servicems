"""Protect physical inspection evidence before Frappe deletes a File."""

from servicems.service_management.doctype.service_vehicle_inspection.service_vehicle_inspection import (
	protect_completed_photo,
)


class InspectionEvidenceMixin:
	def on_trash(self):
		protect_completed_photo(self)
		return super().on_trash()
