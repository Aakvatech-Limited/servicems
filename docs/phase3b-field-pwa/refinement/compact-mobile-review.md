# Compact mobile dashboard — 7 November 2026

Following the Product Owner's Pixel 9 Pro XL screenshot, mobile dashboard spacing is tighter: 24px greeting, smaller branding, denser metric cards, less vertical padding, a narrower filter and a horizontal Resume panel even at narrow widths. The repeated decorative Job Cards eyebrow is hidden on phones. Mobile Job Cards use less padding. Header controls retain 44px touch targets; text scaling, input font sizes and safe-area padding remain supported. The wizard sticky offset follows the shorter header.

Actual authenticated Chromium comparison on the dedicated pilot:

| Viewport | First Job Card top before | After | Space recovered |
| --- | --- | --- | --- |
| 360 × 800 | 654.8px | 478.4px | 176.4px |
| 448 × 998 | 560.7px | 445.3px | 115.4px |

Before/after dark captures: [360px before](compact-before-360-dark.png), [360px after](compact-after-360-dark.png), [448px before](compact-before-448-dark.png), [448px after](compact-after-448-dark.png). These are simulated CSS viewports, not physical Pixel measurements.

57 assertions passed across 24 layout cases: 320/360/375/390/430/448/600/768/834/1024/1366px and a short 800 × 360 landscape viewport, light/dark. Checks cover horizontal overflow, mobile touch targets, first-card visibility, unchanged 1366px desktop geometry, wizard sticky-header clearance and Save Draft above navigation. No browser exceptions occurred. See [before measurements](compact-before-results.json) and [executed after results](compact-after-results.json).

29 existing frontend tests, the production build and focused CSS pre-commit checks passed. Only CSS changed; backend tests were not rerun for this presentation change. The rebuilt frontend is served on `servicems2.aakvaerp.com/field`. No framework upgrades or customer production changes occurred. PR #68 remains Draft and unmerged; Git publication of the pilot follow-up commits is still pending. Physical-device acceptance remains with the Product Owner.
