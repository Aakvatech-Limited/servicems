# Booking Calendar verification — 5 November 2026

Test site: `servicems2.aakvaerp.com`, isolated Pilot bench `mvk-v16` (one site).
Frappe 16.55.2; ERPNext 16.53.0; timezone Africa/Dar_es_Salaam.
Branch: `feat/v16-booking-calendar-responsive`; draft PR #67.

## Result

The existing iframe is retained inside the native Frappe Page. The Dock and
Service Management Sidebar remain native. Calendar links now use the Page route
in the same tab. Responsive sizing, scrolling and form behavior were verified in
an authenticated Chrome session against actual Frappe records.

## Automated verification

- `yarn build`: PASS, ServiceMS only. Existing large-bundle warning remains.
- `node --test --test-isolation=none frontend/tests/*.test.mjs`: 12 passed.
- Site-scoped `run-tests --app servicems --module servicems.api.test_calendar --skip-before-tests`: 11 passed.
- Site-scoped `run-tests --app servicems --module servicems.api.test_calendar_integration --skip-before-tests`: 10 passed. Includes actual-record actions, permissions, native navigation preservation and native link searches reaching Customer/Vehicle records beyond the first 500. Bulk test fixtures were rolled back.
- Two independent database sessions booking the same Bay/date/start: one succeeded, one rejected. Temporary concurrency fixture deleted.
- Authenticated HTTP request creating a Customer then referencing a missing Vehicle Model returned 404 DoesNotExistError; no partial Customer remained after rollback.
- Repository pre-commit hooks passed.

The model stores an explicit start time, not a duration. Bay validation prevents
identical explicit starts; it does not claim full time-range conflict detection.
Stored seconds remain intact during date-only rescheduling.

## Actual browser verification

- Day, Week, Month; Today and period navigation; workshop, customer, vehicle,
  registration search and status filters.
- Existing Customer/Vehicle booking, new Customer and Vehicle with the site's
  required identity fields, booking details, editing and rescheduling.
- Bay-enabled allocation and Bay-disabled creation; invalid related-record
  validation displayed inline; unauthenticated API access denied.
- Native Booking form and linked Job Card navigation. Removed a stale call to an
  undefined Job Card UI helper that interrupted form refresh; no business logic changed.
- Desktop 1920 × 1080, tablet 768 × 1024, mobile 390 × 844.
- No iframe borders, duplicate application navigation, horizontal overflow or
  nested document scrolling. Mobile calendar and booking dialog each use one
  active vertical scroller. Footer remains reachable.
- Final normal user flows: zero console errors, uncaught exceptions or failed requests.
- Original Bay-enabled setting restored. Dock and unrelated Sidebar configuration
  preserved; only the calendar navigation target changed.

## Screenshots

| Actual capture | Screenshot |
| --- | --- |
| Desktop Month | [1920 × 1080](desktop-month.png) |
| Desktop Week | [1920 × 1080](desktop-week.png) |
| Desktop Day | [1920 × 1080](desktop-day.png) |
| Tablet agenda | [768 × 1024](tablet-agenda.png) |
| Mobile agenda | [390 × 844](mobile-agenda.png) |
| Mobile booking form | [390 × 844](mobile-booking-form.png) |
| Bay-enabled calendar | [1920 × 1080](bay-enabled.png) |
| Bay-disabled calendar | [1920 × 1080](bay-disabled.png) |

## Deployment scope and review limitation

Only ServiceMS frontend was built. Target-site Page reload, calendar navigation
synchronization and cache clearing were used. No framework upgrades, migrations,
bench-wide updates, maintenance mode or service restarts occurred. Existing local
generated assets were preserved before building and excluded from commits.
Marked Calendar UAT records remain on the test site for Product Owner review.

The Product Owner replied that the approved design was attached, but no design
image was available to this session. Exact comparison with that reference remains
pending. These screenshots show the actual implementation; they are not mockups.
PR #67 remains draft and unmerged for Product Owner approval.
