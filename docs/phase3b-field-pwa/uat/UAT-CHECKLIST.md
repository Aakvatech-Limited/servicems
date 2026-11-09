# Phase 3B UAT checklist

Use **https://servicems2.aakvaerp.com/field** on the dedicated `mvk-v16` pilot. Do not use customer production sites. PR #68 stays Draft and unmerged. Physical-device acceptance belongs to the internal testing team; automated Chromium results do not sign off devices.

## Prepare the test

An authorized Desk supervisor should create clearly marked UAT Job Cards with a vehicle, workshop and at least one incomplete repair task. Assign each card to its technician with an **Open ToDo assignment**, or the existing active Employee/labour relationship. Give the technician the ServiceMS Field Technician role. Use separate assigned and unassigned cards to check permissions. Never share an Administrator session or post credentials in a bug report.

In **Service Settings → Field Inspections**, select the intended Pre/Post policies. Test the main journey with **Required / Required**, then the alternatives below. Enable **Field GPS Setup and One-Time Capture** for GPS tests. Configure Pre/Post templates and include a mix of mandatory/optional answers, per-item photographs, stage photographs and optional/mandatory GPS. All newly created inspections still require a configured template. Existing inspection snapshots retain their original requirements.

Record the deployed commit, device model, OS/browser version, theme, orientation, tester, test date and QA Job Card references. Keep one screenshot or short recording for each failure. Use synthetic/non-sensitive photographs where possible. Redact credentials, location and customer details before sharing evidence.

## Device coverage — internal team to execute

| Device | Browser and installation | Required coverage | Result / tester |
| --- | --- | --- | --- |
| Android phone, including Pixel 9 Pro XL | Chrome; install from the browser and launch from the home screen | Portrait/landscape, light/dark, camera/library, GPS allow/deny, keyboard, compact dashboard | Not executed |
| iPhone | Safari; add to the home screen and launch the installed app | Permission prompts, real camera/library, safe areas, keyboard, navigation, GPS retry, logout/relaunch | Not executed |
| iPad | Safari; installed/home-screen mode | Portrait/landscape, tablet rail/evidence layout, touch/keyboard, camera/library and GPS | Not executed |
| Android tablet | Chrome; installed mode | Portrait/landscape, tablet layout, camera/library, GPS, keyboard and fixed actions | Not executed |

Use each browser's actual Install/Add to Home Screen flow. Record whether the installed app opens independently and whether permission behavior differs from the browser tab. Do not report one platform's result as another platform's pass.

## Execute on every device

| ID | Test | Expected result |
| --- | --- | --- |
| U01 | Open `/field` signed out, with an existing Desk session, and from the installed icon | Initial Field sign-in is required. A confirmed Field session may remain signed in on relaunch. Active account is visible; logout returns to login and removes private records from the screen. |
| U02 | View, search and filter assigned work; attempt an unassigned Job Card/deep link | Only permitted unfinished work appears. Unassigned direct access fails without revealing its data. Dashboard counts, resume and history use the same permitted Job Cards. |
| U03 | Fresh GPS setup: choose Not now; later enable/disable in Account | Choice is remembered for that user. No automatic GPS while opted out. Mandatory template GPS still needs a manual capture before completion. No continuous tracking. |
| U04 | Enable GPS, deny the OS/browser prompt, then grant permission and use Retry Location | Denial is explained without losing answers. Enabled opening attempts capture once; moving between sections does not request repeatedly. Retry records coordinates, accuracy and capture time. Poor/unavailable GPS has a recoverable error. |
| U05 | Start Pre-Inspection from its configured template | Correct frozen checklist and evidence/GPS requirements appear. Changing a template later does not change an existing inspection. No conventional long ERP form replaces guided navigation. |
| U06 | Before required Pre completion, try repair task completion/Repairing status in authorized Desk and Post start in Field | Server rejects both premature transitions. Complete required Pre first. No separate approval step is introduced. |
| U07 | Answer all question types, add remarks, switch sections and Save Draft; leave/resume | Exact configured values and remarks persist. Unsaved changes receive a warning. Mandatory answers/photos/GPS prevent premature completion. Draft saving itself does not require completion evidence. |
| U08 | Use the real rear camera and select multiple library photos | Private uploads show progress/previews. Valid photos retain orientation/content. Failed upload permits retry without discarding other answers. Large/invalid non-images are rejected meaningfully. |
| U09 | Review photos; cancel deletion, then delete current and last draft photo | Confirmation works. Cancel/failure retains data. Success saves current edits, removes matching references, selects another photo or closes an empty gallery. Required evidence must be replaced before completion. |
| U10 | Review a completed or inherited correction photo and try ordinary edits/deletion | Completed records/evidence remain protected. Shared bytes referenced by a completed inspection cannot be removed. Authorized Desk history/corrections remain available. |
| U11 | Complete Pre; have the supervisor record repair task completion and stop all running labour in the existing Job Card | Pre is immutable. Post stays blocked while any repair task or running labour remains. The PWA does not introduce a separate repair-task editor. |
| U12 | Complete Post with its configured evidence | Completion is final for ordinary Field work, with no approval workflow. The receipt is shown; Job Card status is not automatically changed. |
| U13 | Return to Home, search the completed card, check counts/history, refresh and relaunch | Completed Post removes its Job Card from every Field list/search/count/resume/history. No ordinary Field mutation can restart it. Other permitted cards remain available. |
| U14 | In Desk, change billing/payment/delivery state and complete/close the Job Card | These states do not control Field retirement. Completed Post remains hidden; a card without completed Post is not retired merely by billing or closure. Authorized Desk history and correction ancestry remain intact. |
| U15 | Change orientation/theme, open the keyboard, scroll checklist/gallery and use fixed actions | No horizontal overflow, clipped controls, inaccessible actions or lost values. Dashboard is compact; mobile targets remain usable. Tablet checklist/evidence layout adapts. |
| U16 | Disconnect during loading/upload/save, then reconnect | Honest connection/error state; no false save success or lost in-memory answers. There is no offline synchronization. Private Job Cards/photos are not available from an offline cache. |
| U17 | Sign out and relaunch; check another user's account | No private record is left on screen. GPS preferences belong to the authenticated user; no credentials, records or photos are stored in browser local/session storage. |

## Stage-policy alternatives

| Configuration | Expected behavior |
| --- | --- |
| Pre Required | Repair progress waits for completed Pre. |
| Pre Optional | Repairs may proceed without Pre or with an unfinished optional Pre. An uncompleted Pre becomes review-only once repairs begin; do not backdate it. |
| Pre Disabled | No ordinary new Pre activity; historic evidence stays available to authorized users. Repairs do not wait for Pre. |
| Post Required | Post waits for completed repair tasks/stopped labour; Job Card completion waits for Post. |
| Post Optional | Job Card completion does not wait for Post. If Post is performed, it still follows repair completion and retires Field work when Completed. |
| Post Disabled | No ordinary new Post activity; no Post requirement blocks Job Card completion. Under the requested retirement rule, a card without completed Post is not auto-hidden solely by closure. Record this explicit behavior in acceptance. |
| No repair tasks | No artificial repair task/status is required. Post may proceed once applicable Pre requirements and running-labour checks are satisfied. |

## Sign-off

For every case record **Pass / Fail / Blocked / Not applicable**, device/browser, QA references and evidence. Report failures with steps, expected/actual behavior and reproduction frequency. The Product Owner and technical reviewer decide acceptance after the device matrix and any open policy decisions are resolved. This checklist does not authorize merging PR #68 or deploying to customer production.
