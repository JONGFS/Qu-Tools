# Operations Guide

This guide is for the person running QU Tools after handoff. Normal operation
does not require editing Python code.

## Before the first run

1. Run `.\setup.cmd` from the `plu_matcher` directory.
2. Put approved QU credentials in `.env`.
3. Put the Aloha workbook at the `sourceWorkbook` path configured for the
   location.
4. Verify the workbook contains the `Aloha > Qu Item Migration` worksheet.
5. Run `.\run.cmd status --location <name>`.

Never commit `.env`, cached menus, real workbooks, or generated run bundles.

## Prove the installation offline

Setup creates a sanitized workbook and cache for the `demo` profile. Run:

```powershell
.\run.cmd run --location demo --offline
```

The expected exit code is `2` because the fixture deliberately contains one
ambiguous PLU. Confirm the run contains `PLU_MATCH_ID_UPDATED` in
`plu_results.csv` and one row in `plu_review.csv`. This proves caching,
flattening, reconciliation, provenance, and reporting without QU credentials.

## Daily workflow

Run:

```powershell
.\run.cmd run --location atlanta
```

The command uses one resolved location profile for the entire operation:

1. Authenticate using `.env`.
2. request the current effective menu;
3. use `PrevGenerationTime` so an unchanged menu is not downloaded again;
4. reconcile the profile's workbook against that exact cache;
5. flatten the same cache;
6. write a timestamped run bundle; and
7. return exit code `0`, `1`, or `2`.

An unchanged-menu response is normal. The metadata's `last_checked_at` changes,
while the menu generation time and saved menu stay unchanged.

If the command returns `2`, open the summary and review output in the run
directory before treating the location as clean. A review result is not a
runtime failure.

## Run individual stages

Refresh only:

```powershell
.\run.cmd refresh-menu --location atlanta
```

Check PLUs using the location's current cache:

```powershell
.\run.cmd check-plu --location atlanta
```

Flatten the current cache:

```powershell
.\run.cmd parse-menu --location atlanta
```

Inspect the selected profile and cache:

```powershell
.\run.cmd status --location atlanta
```

Use `run` for routine evidence because it keeps refresh, reconciliation, and
parser outputs together. Individual commands are useful for investigation.

## Audit versus include-unmigrated

The normal command audits rows already marked `Migrated to Qu? = Yes`:

```powershell
.\run.cmd run --location atlanta
```

This is the safe default for operational checks.

Use the following only during an intentional migration/reconciliation session:

```powershell
.\run.cmd run --location atlanta --include-unmigrated
```

That option also evaluates unmigrated Aloha rows. A unique current PLU match can
be populated and marked migrated in the generated workbook. It never overwrites
the source workbook, but its results should still be reviewed before the
generated workbook becomes a new approved baseline.

## PLU-first decision policy

The Aloha PLU is the current business key. The stored QU item ID is treated as a
derived reference.

| Current effective-menu evidence | Action |
|---|---|
| Exact PLU belongs to one item ID on one path | Approve |
| Exact PLU belongs to one item ID on several paths | Approve identity; review path when needed |
| Exact PLU uniquely identifies a new ID | Update ID in generated workbook |
| Exact PLU belongs to several item IDs | Do not choose; manual review |
| Exact PLU is absent | Preserve available source evidence; manual review |

An ID update is therefore expected when a workbook previously pointed to a
combo wrapper but its Aloha PLU uniquely identifies the nested sellable item.

## Run-bundle discipline

Keep every artifact in its original timestamped run directory. The bundle's
manifest is the evidence that these files belong together:

- location, channel, and order type;
- menu snapshot and generation time;
- cache checked/saved times;
- source-workbook identity;
- generated workbook;
- flattened menu exports;
- review records; and
- summary and tool version.

The standard `run` bundle is:

```text
runs/<profile>/<UTC timestamp>/
  manifest.json
  summary.txt
  reconciled_mapping.xlsx
  plu_results.csv
  plu_review.csv
  flattened_menu.csv
  flattened_menu.json
```

Use `plu_review.csv` as the operator work queue. `plu_results.csv` is the
portable full audit. The flattened CSV and JSON preserve every occurrence of an
item, including repeated combo paths.

Do not compare a reconciled workbook from one timestamp with a menu or report
from another timestamp. If a result looks stale, run `run` again.

## Adding a location

Edit `config/locations.json` and add a unique lowercase profile key:

```json
{
  "profiles": {
    "example": {
      "displayName": "Example Location",
      "locationId": 12345,
      "orderChannelId": 4685,
      "orderTypeId": 4723,
      "sourceWorkbook": "inputs/Aloha_Qu_Menu.xlsx"
    }
  }
}
```

Requirements:

- Use numeric QU IDs.
- Keep the workbook path relative to `plu_matcher` whenever possible.
- Confirm the selected channel and order type are the ones being audited.
- Do not put credentials in this file.
- Validate the profile before its first live request:

```powershell
.\run.cmd status --location example
```

Then make a complete baseline run and review every non-safe status.

If a location requires different channel/order-type contexts, add explicit
profiles for each context rather than reusing a cache. A cache key is:

```text
<locationId>-<orderChannelId>-<orderTypeId>
```

## Promoting a generated workbook

QU Tools intentionally writes a new workbook. It does not overwrite the source.

Before making a generated workbook the next approved baseline:

1. Confirm its run manifest references the intended location and snapshot.
2. Resolve all review statuses.
3. Confirm the command returned `0`.
4. Retain the previous approved workbook according to team retention policy.
5. Copy the approved generated workbook to the configured source path.
6. Run another audit to verify the promoted baseline.

## Handoff acceptance check

A new operator should be able to complete these without help:

1. Install from a clean checkout.
2. Configure credentials without committing them.
3. Run `status` for Atlanta and NYC.
4. Produce one complete run for each location.
5. explain one safe status and one review status;
6. locate the flattened menu export; and
7. recover from a deliberately missing credential or locked workbook.
