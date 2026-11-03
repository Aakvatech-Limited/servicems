# ServiceMS 2.0 Phase 2 handover

Verified on 2026-11-03 against `servicems2.aakvaerp.com`, Pilot bench `v16`.
Branch: `version-16-v2-hotfix`. Starting remote/local HEAD: `c1d3c782e7a786ddbb7b65f31f46452bb71cbaa6`.

The five development gates are implemented and the automated test-site checks pass. Development Manager acceptance remains the sign-off step; this handover does not authorize Phase 3 or a production rollout.

| Gate | Implementation | Tests executed | Result | Commit SHA |
|---|---|---|---|---|
| 1 — Inventory & Accounting | Standard transfers, explicit Material Issues, returns, source-row reconciliation, request idempotency, current reads and Job Card locks; expense/cost-center attribution | Real stock/GL postings, partial movements, repeated issues, duplicates, overspending prevention, reversals, cross-company warehouses, insufficient stock, competing posting request | Pass | `0ba9e89` |
| 2 — Configurable Inspections | Existing templates/checklists, snapshots, mandatory stage photos, item photo rules, completion identity/time, immutable completed records and files, reasoned correction copies | Pre/Post, draft/completed, multiple uploaded photos, detailed checklist preservation, template changes, correction and evidence protection, opt-in legacy migration | Pass | `0ba9e89` |
| 3 — Job Costing | Existing labour entries with internal/charge rates; submitted Stock Ledger consumption costs and supplier invoice costs; estimates, variance and provisional margin | Labour totals/rate correction, repeated recalculation, stock/supplier reversals, internal closure without customer invoice | Pass | `0ba9e89` |
| 4 — Billing & Insurance | Standard quotations and supplemental approvals; source-keyed partial invoices without stock updates; separate Customer payer contributions; linked supplier expenses and standard payments | Approval gate, duplicate prevention, partial draft reservations, insurer/owner receivables, supplier cost reversal, payment, commercial closure, revenue and cost reconciliation | Pass | `0ba9e89`, `bfe1842` |
| 5 — Integration & Migration | Additive metadata, authorized-site migration/cache clear, discoverable v16 tests, rollback-safe compatibility fixtures; explicit historical source mapping with audit comments | 33 unit + 24 integration tests; internal, commercial, insurance, inventory exceptions and historical compatibility; full repository checks | Pass | `798e37f`, `5bf939a`, `bfe1842` |

## Executed verification

```bash
pilot -b v16 frappe --site servicems2.aakvaerp.com migrate
pilot -b v16 frappe --site servicems2.aakvaerp.com clear-cache
pilot -b v16 frappe --site servicems2.aakvaerp.com run-tests --app servicems
```

Final result: **57 passed, 0 failures, 0 errors** (33 unit tests and 24 integration tests). Targeted Job Card, inspection, posting, legacy reconciliation and billing tests were also run while fixing failures. Earlier failures are not counted as successful runs.

The configured `pre-commit run --all-files` passed against the identical source tree published as implementation commit `bfe1842be123500e4d6169924a63dd43c0835f60`, including pinned Ruff/Prettier and Frappe Semgrep security checks. JavaScript syntax checks passed for Job Card, inspection and Booking form scripts. A pre-existing Booking formatter failure required the small formatting-only commit `944eb52`.

Migration completed successfully, including `after_migrate` hooks. No frontend build was needed for unbundled DocType scripts. Pre-existing generated frontend assets and `servicems/www/bookings.html` changes were preserved and excluded from these commits.

## Ledger evidence

These are assertions against **actual ERPNext postings made with disposable test records**, subsequently rolled back, not customer ledger figures:

- Issue 10 units, consume 6, return 4: outstanding and workshop Stock Ledger quantity both zero.
- Consumption stock value change: -60; actual parts cost: 60; GL debit and credit totals: 60 each; expense debit is attributed to the selected account and cost center.
- Transfers and returns do not debit the maintenance expense account. Billing already-consumed parts generates no second Stock Ledger movement.
- Separate insurer/owner net charges of 90 and 30 reconcile to parts revenue of 120; ERPNext applies taxes and currency rounding independently to each receivable.
- Standard Payment Entry clears the commercial receivable. Supplier repair expense of 35 reconciles to the selected expense/cost center; cancellation removes it from actual costs.
- Historical source mapping leaves existing Stock Ledger rows unchanged and counts stock-updating legacy invoices as consumption, preventing a second issue.

Evidence logs are saved in `/home/av/pilot/pr-artifacts/servicems-phase2-20261103/` (`tests.log`, `migrate.log`, `pre-commit.log`).

## Operating and migration notes

1. Set the Job Card company, workshop warehouses, maintenance expense account and cost center. Explicitly selected companies are preserved. Mark internal maintenance when no customer invoice is required.
2. Issue owned planned parts with the existing Stock Entry action; consume/return by exact issued item row through the Parts actions. Add a new planned row for further issues. Customer-supplied parts create neither owned-stock consumption nor a parts resale charge; record installation as a service.
3. Record existing technician labour time and its internal/charge rates. Internal labour costing is managerial allocation, not an additional payroll journal. Supplier costs come from submitted non-stock Purchase Invoice item rows linked to the Job Card; matching Purchase Order item links are available.
4. Create and submit standard repair quotations; the same action creates supplemental quotations for newly added charges. Use ERPNext cancellation/amendment for revisions. Approve rates before invoicing. Payer amounts are net of tax and must reconcile to actual billable charges. Each payer is its own ERPNext Customer; invoices allocate the approved contribution through rates while preserving whole part quantities.
5. Draft and submitted invoices reserve quantities. Submit all payer invoices and reconcile all workshop stock before commercial Job Card submission. Internal cards can close without invoices. Confirm all supplier and labour costs before presenting gross margin as final.
6. Legacy acceptance conversion is explicit via `migrate_legacy_acceptance`; it creates one linked Draft snapshot, keeps original Job Card fields and does not complete or overwrite historical records.
7. For unallocated historical movements, a System Manager uses `servicems.legacy_parts.reconcile_historical_parts(job_card, mappings, reason)`. Each mapping identifies `doctype`, `document`, `detail` and `issue_detail`. All ambiguous rows must be explicitly reconciled together; the action adds source references and an audit comment without changing quantities, valuation or GL. Existing source references cannot be overwritten. Aggregated or ambiguous historical allocations that cannot match exact issued rows require reviewed standard document reversal/amendment; the migration deliberately does not guess.
8. Existing detailed inspection tables remain. Selecting a template saves/populates a checklist snapshot. Completed records and their photographs are retained; corrections create new linked Draft records with reasons.

## Limits and sign-off

No unresolved failures remain in the executed suite, and repository/Pilot access was available. No production site or release branch was migrated or pushed.

The site has **zero enabled custom accounting dimensions**. The posting path copies configured dimensions when the corresponding fields exist on the Job Card and target ERPNext documents; vehicle-dimension posting was therefore not exercised against a configured dimension. Validate that configuration before enabling it. Browser-based user acceptance and hosted GitHub Actions were not executed; the configured local repository checks and backend integration scenarios were executed.

Phase 2 implementation and automated verification are ready for Development Manager review. Final acceptance/sign-off remains with the Development Manager.
