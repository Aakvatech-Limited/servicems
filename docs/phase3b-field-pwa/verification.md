# Phase 3B pilot verification — 6 November 2026

## Guided UI refinement — 7 November 2026

The pilot `/field` now uses a compact technician dashboard, Job Card summaries with Pre/Post indicators and history, and a five-section inspection wizard: Vehicle, Checklist, Photos, Findings and Review. Phone navigation uses numbered steps and persistent Save Draft/Back/Next controls; tablet layouts use a section rail. Navy/indigo surfaces, blue-gray light cards, complete dark styling and consistent SVG icons follow the supplied references. Photos have separate camera/library actions, larger previews, modal review, progress and retry. Completion opens a protected receipt with View Inspection and Return to Job Card actions. Only functional Home, Inspections and Account navigation is exposed.

A confirmed upload defect was corrected: the legacy Frappe save utility selected an existing private File URL when newly uploaded bytes matched a different inspection. The endpoint now creates a File from the submitted bytes through the native File lifecycle, after the existing parent-write, Draft, actual-image and size checks. Same-inspection deduplication, private downloads and immutable completed evidence remain protected. A regression verifies that matching uploaded bytes do not grant source inspection or source File access.

Executed checks for this refinement: **29 frontend tests**, **18 real-record Field backend tests**, **5 authentication tests**, **9 existing inspection unit tests**, production build, repository pre-commit/Ruff/Prettier/Semgrep, and the authenticated browser journey including Pre/Post completion, draft resume, correction ancestry, upload failure/retry, GPS denied/granted, optional photographs/GPS, account and sign-out. **200 section/viewport/theme combinations** passed: all five sections at 320, 375, 390, 430, 600, 768, 820, 834, 1024 and 1366px, portrait/landscape shapes, light/dark. No detected horizontal overflow, clipped controls, fixed-action overlap or loss of form values. Reduced keyboard-height action access also passed. See [actual browser results](refinement/browser-results.json).

### Original-reference review — 7 November 2026

The supplied `ServiceMS_Phase3B_Mockup_References.zip` was located in the server-side repository and extracted into [design-reference](design-reference/README.md). It contains **two original design sheets and one supplied crop of the second sheet**, plus its README. Original image bytes were preserved and verified against the [recorded SHA-256 checksums](design-reference/provenance.json). The upload archive remains unchanged locally; the extracted originals are versioned without duplicating the ZIP.

The originals prompted a further scoped UI refinement: ServiceMS-blue actions/progress and navy header, denser mobile cards and search/filter row, stage-specific checklist headings, expandable optional remarks, green completion styling, and a tablet checklist with adjacent evidence/findings summary. No backend rules changed in this follow-up. Twelve authenticated screenshots and the original images load directly in the [interactive comparison board](refinement/visual-comparison.html). Five actual side-by-side captures were rendered and visually inspected: [home](refinement/comparison-home.png), [checklist](refinement/comparison-checklist.png), [photos](refinement/comparison-photos.png), [completion](refinement/comparison-completion.png) and [tablet](refinement/comparison-tablet.png). See [design review and required differences](refinement/design-review.md) and [comparison capture results](refinement/comparison-results.json).

Fresh checks after these original-reference changes: **29 frontend tests, 18 Field backend tests, 5 authentication tests, 9 inspection unit tests, production build, repository pre-commit checks, 67 authenticated browser assertions and 200 responsive combinations passed**. This includes Pre/Post completion, correction history, optional/mandatory evidence and GPS, failed-upload retry, restricted-user access, retained values, dark/light modes, reduced keyboard viewport and sign-out. The original-image comparison blocker is resolved. Product Owner visual approval and physical-device acceptance are still pending; neither is inferred from Chromium results.

No customer production deployment, framework upgrades, additional PR, merge, Calendar appearance changes, Phase 2 accounting changes or Phase 4 work occurred. Test photographs are labelled generated QA fixtures; GPS, viewport/orientation and keyboard height were simulated in Chromium. Physical Android/iOS installation, real camera/GPS, hardware keyboard and safe-area behavior still require device acceptance testing. QA records are marked as test-site review fixtures; temporary testing sessions are revoked after verification.

## Photo review deletion — 7 November 2026

Photo review now supports confirmed deletion of photographs uploaded to the current Draft. Completed and inherited evidence remain protected; removal saves current edits, clears matching references and preserves mandatory completion requirements. See [photo deletion verification](refinement/photo-review-deletion.md) for the fresh tests and captures. This follow-up passed 23 Field backend tests and 29 frontend tests; its browser checks are recorded separately from the earlier 200-case guided-flow matrix.

## Login correction — 7 November 2026

Existing Desk sessions now open the native Frappe login form at `/field-login` before Field displays Job Cards. A successful Field sign-in marks only the new server session; reloading that confirmed session remains signed in. The Field header area shows the active account and a Sign out action. Sign-out clears the shared Frappe session and returns to login. The login route is network-only and uses no-store headers. No credentials or authentication tokens are stored in browser storage.

Five focused backend authentication tests passed. Authenticated Chromium verified an existing Administrator Desk session cannot skip Field login, invalid credentials remain on login, valid credentials expose only the assigned QA Job Card, the account is visible, controls fit 320/390/834px, reload retains the confirmed session, sign-out returns to login, and signed-out API access is denied. See [login results](login-verification.json) and [actual login screenshot](mobile-login.png). Frappe's native authentication/verification flow is reused; physical phone behavior and two-factor login were not separately exercised in this correction.

Pilot: `mvk-v16`, `/home/av/pilot/benches/mvk-v16`; site: https://servicems2.aakvaerp.com/field.
Branch: `feat/v16-field-pwa-inspections`; Draft PR #68 targets `version-16-v2-hotfix`.
Runtime: Frappe 16.55.2 and ERPNext 16.53.0. No framework/app upgrades or customer production sites changed.

## Completed fixes

- Require configured stage templates and freeze checklist structure, evidence and GPS requirements. Preserve correction ancestry and completed inspection/file protection.
- Enforce assigned Job Card access through list queries, direct APIs, REST and private file download, including after assignment revocation. Closed assignments and inactive employees do not confer access.
- Restrict permission seeding to the three audited Field DocTypes, avoiding installed dependency hooks granting broader linked access.
- Validate actual uploaded image bytes, size, privacy, parent permissions and Draft status. Preserve binary content and deduplicate repeated uploads within an inspection. Corrections retain authorized historical evidence.
- Add stale-draft protection and GPS accuracy/timestamp validation; reject invalid saves atomically.
- Complete correction navigation, configured answers, upload progress/previews, GPS permission recovery and unsaved-change protection. Improve wrapping, input sizing and safe-area padding.
- Supply install icons and prevent private page/API/photo caching. Service worker has no offline synchronization or private data storage.
- Legacy Job Card inspection fields remain hidden with stored data retained. VIN remains visible as the existing read-only vehicle identifier.

## Executed verification

| Check | Actual result |
| --- | --- |
| Frontend Node tests | 21 passed, including 5 Field API/cache tests |
| Vite production build | Passed on pilot |
| Field real-record backend regressions | 17 passed |
| Inspection unit tests | 9 passed |
| Booking Calendar API tests | 18 passed |
| Booking Calendar real-record tests | 16 passed |
| Relevant Phase 2 regressions | 24 passed |
| Repository pre-commit, Ruff, Prettier and Semgrep | Passed |
| Authenticated Chromium workflow | Pre/Post creation, answers, remarks, uploads, GPS, Draft, completion, corrections and history passed |
| Direct HTTP security checks | 9 passed; see [results](http-security-results.json) |
| Responsive matrix | 40 combinations passed: 320, 375, 390, 430, 600, 768, 820, 834, 1024, 1366px; portrait/landscape viewport shapes; light/dark |
| Data retention and actions | Values retained through resizing; unsaved warning and reduced keyboard viewport actions passed |
| Chromium manifest/installability | No reported errors; service worker active at Field scope |
| Browser privacy | Private photo/API no-store headers passed; no private CacheStorage, localStorage or sessionStorage entries |

See [browser results](browser-results.json) for executed assertions and viewport dimensions. Photographs are explicitly marked generated QA upload fixtures. GPS coordinates, permission changes, camera/gallery input, orientation and keyboard viewport were simulated through Chromium DevTools. These are authenticated browser tests, not physical-device tests.

## Screenshots

[Mobile Job Cards](mobile-home-light.png), [Pre checklist](mobile-pre-checklist-light.png), [photo gallery](mobile-photo-gallery-light.png), [GPS/dark mode](mobile-gps-dark.png), [completed inspection](mobile-completed-light.png), [Post inspection](mobile-post-dark.png), [tablet/light](tablet-inspection-light.png), [tablet/dark](tablet-inspection-dark.png).

## Review fixtures and remaining acceptance

Clearly marked QA Job Cards, templates, a restricted technician and completed inspection/correction history remain on the dedicated site for Product Owner review. They do not represent customer work. Temporary browser sessions are revoked after verification. A database/config backup preceded the targeted schema reload. Calendar appearance and Phase 2 accounting sources were not changed.

Physical Android Chrome and iOS Safari installation, real camera/GPS, hardware keyboard behavior and device safe areas have **not** been tested: no connected physical devices are available. Product Owner review and these hardware checks remain acceptance gates. PR #68 remains Draft and must not be merged without clearance. GitHub CI status for the published commit is recorded in the PR description.
