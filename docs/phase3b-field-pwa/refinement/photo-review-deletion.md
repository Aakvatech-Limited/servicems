# Delete photographs during draft review

The photo review dialog now offers **Delete photo** for private photographs uploaded to the current Draft inspection. A confirmation precedes removal. The request saves current answers and remarks, clears references to the removed photograph and deletes its File through the existing protected lifecycle in one transaction. Required evidence must be replaced before completion. Completed photographs, inherited correction evidence and bytes referenced by a completed inspection remain protected.

The endpoint checks inspection write permission and Job Card access, locks the inspection, verifies exact attachment ownership, enforces Draft status and rejects stale edits. Other attachments and inaccessible Job Cards cannot be targeted. UI controls disable while busy or offline. Failed requests retain the gallery and edits and show an error in the review dialog. Removing the current photo selects the next/previous remaining photo; removing the last closes the dialog.

Verified on the dedicated `mvk-v16` pilot, `servicems2.aakvaerp.com`, on 7 November 2026:

- 23 Field backend tests passed, including five new deletion regressions for required references/retained edits, completed/inherited protection, foreign/unassigned access, completed shared-file references, and stale/invalid edits.
- 29 frontend tests, the production build and scoped pre-commit checks passed.
- Authenticated Chromium checks passed for confirmation/cancel, network failure/retry, current/last-photo navigation, preserved edits, required-evidence blocking, offline controls and completed-photo protection. Delete controls fit 320, 390, 834 and 1024px in both themes. See [executed results](photo-delete-results.json).
- Actual review captures: [light](13-photo-delete-review-light.png), [dark](14-photo-delete-review-dark.png). Photographs are labelled QA fixtures. These are browser simulations, not physical phone tests.

The pilot frontend was rebuilt and only its verified port-8007 runner was reloaded. No customer production sites or framework versions changed. PR #68 remains Draft and unmerged. GitHub publication/CI must be confirmed separately; a successful local build or pilot check does not establish remote CI success.
