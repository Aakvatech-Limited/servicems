# Original mockup comparison — 7 November 2026

The supplied archive contains two original design sheets and a mobile-flow crop of the second sheet. [Provenance and checksums](../design-reference/provenance.json) identify the unmodified source images. The [interactive board](visual-comparison.html) uses CSS masks for matched details and can display either full sheet or the supplied crop. It compares actual authenticated pilot screenshots, not reconstructed mockups.

## Reviewed pairs and resulting refinements

| Original screen | Actual capture | Review outcome |
| --- | --- | --- |
| Mobile Home / Job List | [Side by side](comparison-home.png) | Navy/ServiceMS-blue shell, pale background, compact assigned Job Cards and status pills. Requested dashboard counts and resume card remain; mobile search/filter share a row. |
| Pre-Inspection checklist | [Side by side](comparison-checklist.png) | Blue progress/actions, clear stage heading, compact condition rows and persistent navigation. Optional remarks expand within a row; configured answers remain available. |
| Capture Photos | [Side by side](comparison-photos.png) | Camera and library actions, private evidence grid, previews and upload progress/retry retained. Evidence is not replaced with stock vehicle photos. |
| Completion | [Side by side](comparison-completion.png) | Green completion action/receipt, View Inspection and Return to Job Card. Completed records stay protected. |
| Tablet inspection | [Side by side](comparison-tablet.png) | Section rail, checklist and evidence/findings summary share the landscape workspace at 1024px and above. [834px portrait](11-tablet-portrait-light.png) uses the adaptive rail layout. |

All five saved pairs were opened and visually inspected after rendering in Chromium. [Capture metadata](comparison-results.json) records the matching original source, actual screenshot and dimensions. The source image bytes remain unchanged. Twelve standalone [actual captures](visual-comparison.html#gallery) include Job Card details, findings/GPS, review, Post-Inspection and light/dark tablet views. The photo comparison shows the scrolled gallery; [camera/library controls](12-mobile-camera-light.png) are captured separately from an existing saved Draft without changing its data.

## Intentional differences required by existing behavior

- Templates define the real checklist, configured answer values, mandatory evidence and GPS. The artwork's example questions, damage badges, four photo angles and simple checkboxes are not imposed on unrelated templates.
- Inspection status remains Draft / Completed. Job Card status is shown separately; not-started stage labels are derived from history.
- Completed photographs cannot be deleted. Authorized corrections retain protected evidence and ancestry.
- Camera uses the device/browser capture interface. The PWA does not simulate a live camera, flash or lens controls. No generated vehicle illustration stands in for actual vehicle evidence or data absent from the Field API.
- Only working Home, Inspections and Account navigation is exposed. No fake notification counters, future modules, settings destinations or offline synchronization are added.
- The requested vehicle overview and completion review remain separate wizard sections. The artwork depicts fewer screens; required answers/photos/GPS are checked before completion.
- Dark mode follows the same structure and blue accents. The supplied artwork notes dark support but does not provide a full dark screen set; dark captures are compared with the light artwork for structure only.

## Verification and acceptance

Fresh verification passed: 29 frontend tests, 18 real-record Field backend tests, 5 authentication tests, 9 inspection unit tests, production build, repository pre-commit checks, 67 authenticated browser assertions and 200 responsive cases. The responsive cases cover five wizard sections at 320, 375, 390, 430, 600, 768, 820, 834, 1024 and 1366px in portrait/landscape shapes and both themes. Browser checks also cover optional/mandatory evidence, GPS denied/granted, failed upload/retry, Draft resume, Pre/Post completion, correction ancestry and sign-out. See [browser results](browser-results.json) and [verification report](../verification.md).

Photo fixtures are explicitly labelled QA images. GPS, keyboard height and orientation were simulated. Physical Android Chrome/iOS Safari installation, real camera/GPS and device safe areas remain untested, and Product Owner approval remains pending. The original-file comparison is complete; these remaining acceptance gates are not claimed as passed. PR #68 stays Draft and unmerged.
