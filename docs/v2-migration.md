# ServiceMS v16 migration compatibility

This development branch targets Frappe 16 and ERPNext 16. ERPNext must be available on the bench; ServiceMS declares it as a required app and installs it on a new site. Fleet integration remains optional. No HRMS dependency is required for technician tracking: Employee belongs to ERPNext.

## Verified behavior

The audit used Frappe 16.52.0, a clean framework-only site, and a separate site installed from legacy commit `ef340ca762ab84385376d656c6a7f6406aab94d4`. The latter is a representative pre-v2 baseline, not certification of every historical customer fork.

- Fresh install imports the standard Workspace and native Sidebar. Bay Management and Final QC default to off; a booking can be saved without a Bay.
- The pre-model-sync Bay patch reads stored Singles values without requiring the new DocField. Existing explicit zero/one settings are retained. When no setting exists, historical Bay allocations enable Bay Management without changing those records.
- Existing completed cards are not retroactively required to pass QC. New completions require confirmation when QC is enabled, recording the current user and timestamp.
- Technician start/stop uses Employee records, calculates actual hours, rejects a second active card for the same technician, and blocks completion while labour is running.
- The representative upgrade preserved 44 historical records across 46 business tables, including a submitted Job Card, invoice, stock and ledger records. Original column values, custom fields and Property Setters were checked before any test fixtures were refreshed.
- The 15 integration tests passed on both fresh and upgraded sites. Two additional full migrations on each site left navigation records, settings, patch counts and navigation backup filenames unchanged.

## Customer navigation preservation

Before model sync, the upgrade writes private JSON snapshots under `sites/<site>/backups/servicems-navigation/`. These include the Workspace, native Sidebar, Custom Workspace and Custom Sidebar records. A missing record is represented explicitly. Snapshots are mode 0600 and are retained rather than deleted by the migration.

The new standard Workspace replaces the legacy app-owned base. Direct edits made to that old base are archived, not automatically merged into the six-section v2 layout. Review those snapshots with the customer and restore their selected layout/widgets through native Custom Workspace customization before production cutover. Do not discard the backups or assume a successful migrate means that an old customer layout remains active. Existing native customization layers survive forced standard imports and retain their effective rendered layout.

## Remaining release gaps

1. The legacy `/bookings` Vue SPA still unconditionally requires a Bay in `frontend/src/components/CreateBooking.vue`, and its data endpoint is Bay-oriented. The native Desk booking flow supports Bay Management off; the SPA has not been adapted or browser-certified for that mode. Do not advertise or release that combination as supported until a focused follow-up is tested.
2. Standard 1.x data has no equivalent of the new labour-entry table. Existing customer-specific technician/time fields remain intact, but no automatic conversion from customer extensions or third-party time logs is provided. Agree a mapping where required; never infer historical clock times.
3. The app still reports version `0.0.1`; the v2 release version/tag and release notes must be prepared before distribution. No production release or tag was made by this audit.
4. Older customer forks, Fleet-enabled installations, and the legacy SPA's browser flows require customer-specific staging checks. The audit starts on Frappe 16.52.0 and does not certify a Frappe/ERPNext 15-to-16 framework upgrade or those other combinations.

## Reproducing the audit

Use disposable sites with `allow_tests` enabled and schedulers paused. Never run fixture creation on a customer database. Run from the bench's `sites` directory, selecting the app checkout with `PYTHONPATH`:

```bash
export PYTHONPATH=/path/to/servicems
../env/bin/python "$PYTHONPATH/scripts/audit_v2_migration.py" fresh-install --site fresh-audit.localhost
../env/bin/python "$PYTHONPATH/scripts/audit_v2_migration.py" test --site fresh-audit.localhost
../env/bin/python "$PYTHONPATH/scripts/audit_v2_migration.py" idempotence --site fresh-audit.localhost
```

For an upgrade, first use the legacy checkout on `PYTHONPATH` with `legacy-install` and `legacy-seed --snapshot /private/path/before.json`; the runner itself comes from this development checkout. Switch `PYTHONPATH` to the development checkout, run a complete Frappe migration, then run `verify-upgrade --snapshot /private/path/before.json`, `idempotence`, and `verify-upgrade` again. Run `test` last: its fixture setup intentionally prepares the disposable test company and Employee. `docs/migration-tests.workflow.yml` is a CI template for both paths against Frappe/ERPNext version-16. It never deploys a site. To activate it, use a credential with workflow-write permission to place it at `.github/workflows/migration-tests.yml`; publishing this template alone does not enable Actions.

## Recommended release procedure

1. Resolve the intended release scope and the gaps above. Confirm upstream CI, assign a release version, and freeze a reviewed candidate commit.
2. Restore each customer's database, public/private files and site configuration to isolated staging. Pin compatible Frappe/ERPNext versions and verify any installed Fleet/custom apps.
3. Take and verify full backups before migration, including navigation snapshots. Record document/ledger totals, Bay/QC settings, custom fields, Property Setters, and customer navigation layers.
4. Migrate without `--skip-failing`. Verify historical records and financial links, Bay behavior, QC transitions, technician timing, navigation targets and role-filtered visibility. Run migrate twice more and check that state is unchanged.
5. Review archived legacy Workspace edits with the customer and preserve their required experience through native customization. Validate the final UI with real operational roles.
6. Rehearse rollback of code, database, files and configuration together. Only after staging acceptance should a separately authorized production maintenance window be scheduled. This development audit does not authorize production deployment.
