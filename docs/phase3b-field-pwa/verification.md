# Phase 3B pilot verification — 6 November 2026

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
