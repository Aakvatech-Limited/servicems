# Phase 3B UAT candidate

Pilot: `mvk-v16`, https://servicems2.aakvaerp.com/field. Existing feature branch: `feat/v16-field-pwa-inspections`; Draft PR [#68](https://github.com/Aakvatech-Limited/servicems/pull/68), target `version-16-v2-hotfix`. No separate Post approval workflow, framework upgrades, customer production deployment or merge.

## Resulting behavior

- Shared DocType validations enforce sequencing in Desk, REST and Field. Required Pre gates repair progress. Post follows completed Job Card tasks and stopped labour. Optional/Disabled stages do not introduce required-stage gates. Authorized Desk corrections retain protected history.
- Service Settings exposes Required/Optional/Disabled for each inspection stage. Defaults are Optional to preserve existing installations. No existing template/checklist, completed inspection, photograph or correction ancestry is rewritten.
- Optional GPS setup asks each user to opt in, handles permission denial, captures once on opening an enabled inspection and retains manual Retry Location. Account can disable automatic capture. GPS accuracy/time are validated. There is no continuous tracking or private browser storage; GPS becomes persistent through normal Draft/Complete saving.
- Completed Post alone retires the Job Card from ordinary Field lists, search, counts, resume and history, and prevents direct Field activity. It does not automatically change Job Card status. Billing/payment/delivery/closure do not determine retirement. Authorized Desk access and corrections remain available.
- Original reference images/comparisons, protected Draft photo deletion and compact phone layout are retained. Existing drafts blocked by a changed policy or repair progress remain reviewable rather than silently editable.

## Executed verification

The authenticated run on **9 November 2026** passed **72 assertions and 200 responsive cases**, including five explicit direct-API security checks and a concurrent Post completion race with exactly one success. It exercised GPS denial/retry/one-time behavior, Pre → repair → Post, protected completion, finished-work list/search/history removal, opt-out, disabled stages, upload/review/deletion, Draft resume, no private browser storage, installability and sign-out. Eight further [read-only draft assertions](read-only-results.json) passed. [Browser results](browser-results.json) distinguish simulations from physical-device tests. [Pilot checks](pilot-checks.json) confirm completed Post cards remain Active/draft Job Cards, with their inspections retained; temporary settings/user state were restored and test sessions revoked.

Backend/frontend/build/check results for final source verification are recorded in [test-results.json](test-results.json). Git publication and CI must be verified against the final remote HEAD; local checks do not establish GitHub CI success.

## Actual screenshots and comparisons

[Compact mobile Home](01-mobile-home-light.png), [Job Card/sequencing](02-mobile-job-card-light.png), [Pre checklist](03-mobile-pre-checklist-light.png), [gallery](04-mobile-photo-gallery-light.png), [GPS/findings](05-mobile-gps-findings-light.png), [review](06-mobile-review-light.png), [Pre completion](07-mobile-completion-light.png), [Post/dark](08-mobile-post-dark.png), [tablet light](09-tablet-inspection-light.png), [tablet dark](10-tablet-inspection-dark.png), [tablet portrait](11-tablet-portrait-light.png), [camera/library](12-mobile-camera-light.png), [delete light](13-photo-delete-review-light.png), [delete dark](14-photo-delete-review-dark.png), [finished Post receipt](15-post-completed-field-finished.png), [GPS setup](16-mobile-location-setup.png), [finished job hidden](17-mobile-retired-job-hidden.png), [disabled stages](18-disabled-stages.png).

Five current original-versus-UAT pairs: [Home](comparison-home.png), [checklist](comparison-checklist.png), [photos](comparison-photos.png), [finished Post](comparison-post-completed.png), [tablet](comparison-tablet.png). The [interactive board](../refinement/visual-comparison.html) loads the unmodified [original references](../design-reference/README.md) and latest captures. [Capture metadata](comparison-results.json) records the pairs. The artwork's fixed example questions/photo angles, Pending/In Progress labels and decorative navigation do not override real template rules, Draft/Completed states, protected evidence, GPS consent or the requested finished-work rule.

## Internal device UAT and open decisions

Use the [UAT checklist and tester instructions](UAT-CHECKLIST.md) on Android phones, iPhone, iPad and Android tablets. Physical installation, real camera/GPS, OS permissions, safe areas and hardware keyboards have **not** been executed by this agent.

Before acceptance, the Product Owner should confirm the intended global stage defaults (currently Optional for compatibility) and whether operational sites will enable GPS setup (currently off unless configured). Post Disabled intentionally does not synthesize a Completed inspection or introduce another retirement rule; cards without completed Post remain eligible according to permissions even if billing/closure has advanced. Global settings apply prospectively to ordinary activity; completed evidence and historical corrections are retained.

Known limitations: online connection required; no offline synchronization; native browser/device camera UI; browser GPS accuracy depends on device/environment; completed shared-file references prevent destructive photo removal. Cross-session list updates occur on refresh, list navigation or returning to the app; server mutation guards reject finished work immediately. Internal device results and Product Owner approval remain UAT gates. PR #68 stays Draft and unmerged.
