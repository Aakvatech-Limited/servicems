# ServiceMS Customer App — Development Notes

This is the **single Phase 4 delivery**, developed on `feat/v16-customer-app` alongside Phase 3B on its own branch.

## Implemented foundation

- `Customer App Settings`: one record per Company, **disabled by default**. Contains company-wide branding and registration policy.
- `Customer App Workshop Availability`: existing Service Workshop records only; unavailable by default.
- `Customer App Account`: explicit Company + Customer + Website User link, requiring verified ERPNext Portal User relationship.
- Company-specific manager role plus Company User Permissions, with server-side permission and list guards.
- Initial APIs: available workshops, historical bookings, Job Cards, quotations, invoices and create customer booking.

## Required remaining work (not yet implemented)

- Responsive Customer App frontend for mobile/tablet/desktop; standalone PWA route, scoped service worker and manifest.
- Invitation-only and Hybrid registration with identity verification and expiring one-time invitations.
- Verified onboarding and customer/vehicle/company association policy, including cross-company Vehicle edge cases.
- Customer-facing document details, PDF downloads, permission-filtered attachments, inspection snapshots from Phase 3B.
- Quotation approval/rejection workflow, cancellation/rescheduling, notifications and account profile.
- Feature toggles and full Desk configuration UI with live branding preview.
- Secure migration and compatibility tests, E2E tests, PWA install and offline cache behavior.
- Verify and restrict existing public Service Job Card web views before release.

## Important constraints

Never modify ERPNext's global login or Portal Settings. Existing records must survive disable/re-enable. Workshop opt-out affects **new customer bookings only**. Internal ServiceMS Desk and Field Operations PWA remain independent.

**The code is not ready for deployment or merge.** No Frappe runtime/migration tests have been executed in the current environment.
