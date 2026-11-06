# Month and theme check — 5 November 2026

Checked PR #67 after `53d8ab7` on the dedicated `mvk-v16` bench,
`servicems2.aakvaerp.com`. This report supersedes the earlier screenshots for UI review.

Two small corrections:

- Declare existing frontend imports in `frontend/package.json` and lockfile, including the Vite plugin. Clean builds no longer depend on root-level installed packages.
- Give the theme surface rules enough CSS specificity to override Vue scoped styles. Dark inputs, buttons, date text, dialogs and muted card text remain readable.

Verification:

- ServiceMS-only Pilot build passed.
- Clean frontend-only frozen-lockfile install and build in a temporary directory passed without the Pilot root dependencies. Existing large-bundle warnings remain.
- All 12 frontend helper tests passed.
- 18 focused authenticated browser checks passed: all four Month status colors, text contrast >= 4.5:1, live Desk light/dark changes without iframe replacement, Today versus selected-date highlights, three-chip limit/count/+ More opening all six bookings, responsive layouts and booking form opening.
- Both themes captured at desktop 1920 × 1080, tablet 768 × 1024 and mobile 390 × 844. Tablet/mobile use the responsive agenda.
- Zero console errors, uncaught exceptions or failed HTTP requests in these checks.
- Seven temporary display records and the temporary browser session were removed. Screenshots include those marked test bookings to demonstrate status colors and overflow.

| Size | Light | Dark |
| --- | --- | --- |
| Desktop Month | [Screenshot](ui-desktop-light.png) | [Screenshot](ui-desktop-dark.png) |
| Tablet agenda | [Screenshot](ui-tablet-light.png) | [Screenshot](ui-tablet-dark.png) |
| Mobile agenda | [Screenshot](ui-mobile-light.png) | [Screenshot](ui-mobile-dark.png) |

Only ServiceMS was built, and only the target site's calendar Page was reloaded and cache cleared. No native navigation changes, migrations, framework upgrades or service restarts. Backend tests were not rerun for these dependency/CSS corrections. PR #67 remains draft and unmerged; Product Owner UI approval is still required.
