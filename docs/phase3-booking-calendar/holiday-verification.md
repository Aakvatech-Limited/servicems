# Approved theme and holiday verification — 5 November 2026

Built `be0b2e4` on the dedicated `mvk-v16` bench for
`servicems2.aakvaerp.com`. One CSS line was corrected after actual screenshot
inspection: Month grid rows now respect their content height so a holiday label
cannot hide the third booking or + More. No other product changes were needed.

- ServiceMS frontend build: passed.
- Frontend helper tests: 12 passed.
- Focused Booking API tests, including holiday permissions/data handling: 14 passed.
- 23 authenticated browser checks passed: live light/dark switching without iframe
  replacement, all four status colors and readable text, Today/selected highlights,
  weekend shading, configured holiday and weekly-off labels, three-chip limit,
  count and + More opening all bookings, actual cell bounds containing the third
  chip and + More, Month final-date reachability at 1920 × 720, responsive layouts
  and booking form opening.
- Zero console errors, uncaught exceptions or failed requests in these checks.
- Six screenshots captured at 1920 × 1080, 768 × 1024 and 390 × 844.

The company's original default Holiday List is **unset**. Its empty response was
verified before testing. A clearly marked temporary Holiday List and seven display
bookings were used to verify real records through the live endpoint. Original
company configuration was restored; all temporary records and the browser session
were removed. Real holiday indicators will appear after an appropriate default
Holiday List is configured for the company. Screenshots show the temporary QA data.

| View | Light | Dark |
| --- | --- | --- |
| Desktop Month | [Screenshot](holiday-desktop-light.png) | [Screenshot](holiday-desktop-dark.png) |
| Tablet agenda | [Screenshot](holiday-tablet-light.png) | [Screenshot](holiday-tablet-dark.png) |
| Mobile agenda | [Screenshot](holiday-mobile-light.png) | [Screenshot](holiday-mobile-dark.png) |

Only ServiceMS was built and only the target site's cache cleared. No migrations,
framework updates, native navigation changes, bench-wide updates or service
restarts. Existing local generated assets remain uncommitted. PR #67 remains Draft
and unmerged pending Product Owner UI approval. The separate reported
label-failed-prs automation failure was not changed in this UI task.
