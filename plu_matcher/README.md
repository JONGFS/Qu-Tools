# QU Tools

QU Tools is a location-aware internal utility for two related jobs:

1. Validate Aloha PLUs against the latest effective QU menu and create an
   auditable reconciled workbook.
2. Flatten the cached nested menu into operator-friendly CSV and JSON exports.

The normal operator workflow is one command:

```powershell
qu-tools run --location atlanta
```

The source workbook is never overwritten. Each run creates a timestamped bundle
so its menu snapshot, reports, and reconciled workbook stay together.

## Important validation boundary

This tool validates the menu returned by QU for one exact combination of
location, order channel, and order type. That is the **effective menu** used by
that ordering context.

It does not query the complete QU Enterprise Intelligence database. An item can
exist in EI and still be absent from the effective menu because it is inactive,
not assigned to the selected context, or excluded by other configuration. A
successful result means the Aloha PLU is represented correctly in the returned
menu—not that every EI configuration screen has been independently checked.

## Five-minute setup

Prerequisites:

- Windows Command Prompt or PowerShell
- Python 3.11 or newer
- Access to the approved Python package index for the first setup
- Approved QU client credentials
- The Aloha mapping workbook

From the `plu_matcher` directory:

```powershell
.\setup.cmd
```

Edit `.env` and enter the credentials issued for this integration:

```dotenv
QU_BASE_URL=https://gateway-api.qubeyond.com
QU_CLIENT_ID=
QU_CLIENT_SECRET=
QU_X_INTEGRATION=
```

Do not add `.env` to Git or send it with a run bundle.

Place the workbook at:

```text
inputs/Aloha_Qu_Menu.xlsx
```

Confirm the profile and cache state, then run the tool:

```powershell
.\run.cmd status --location atlanta
.\run.cmd run --location atlanta
```

`setup.cmd` installs an editable `qu-tools` command as well, so the equivalent
command inside the activated environment is:

```powershell
qu-tools run --location atlanta
```

Before adding credentials or a company workbook, verify the complete workflow
with the generated sanitized demo:

```powershell
.\run.cmd run --location demo --offline
```

The demo intentionally returns exit code `2`: it includes safe PLU matches, an
automatic stale-ID update, and one ambiguous PLU for the review report.
`--offline` means the demo makes no QU API request; the first setup still needs
package-index access to install Python dependencies.

## Commands

```powershell
qu-tools refresh-menu --location atlanta
qu-tools check-plu --location atlanta
qu-tools parse-menu --location atlanta
qu-tools run --location atlanta
qu-tools status --location atlanta
```

- `refresh-menu` requests the latest menu and safely updates its context cache.
- `check-plu` reconciles the configured workbook against the cached menu.
- `parse-menu` exports the latest cached nested menu as flattened CSV and JSON.
- `run` refreshes, reconciles, parses, and bundles one consistent run.
- `status` displays the resolved profile and current cache information without
  changing the cache or workbook.

Run any command with `--help` to see its accepted options. Help does not make a
network request.

## Audit and reconciliation modes

The default is an audit of rows already marked `Migrated to Qu? = Yes`.

```powershell
qu-tools run --location atlanta
```

To deliberately include rows not yet marked as migrated:

```powershell
qu-tools run --location atlanta --include-unmigrated
```

`--include-unmigrated` is reconciliation behavior, not just a wider report. A
unique PLU match may be written into the generated workbook and marked migrated.
Use it only when the operator intends to discover and backfill mappings. The
source workbook remains unchanged in both modes.

Matching is PLU-first:

- One exact PLU mapping to one QU item ID is safe.
- The same item ID on multiple menu paths is still a safe identity match, but
  path selection can require review.
- A stale stored QU ID is replaced in the generated workbook when the exact PLU
  uniquely identifies a different ID.
- One PLU mapping to multiple item IDs is ambiguous and is never auto-approved.
- A missing PLU or an item missing from the current context requires review.

See [STATUS_REFERENCE.md](STATUS_REFERENCE.md) for all result meanings.

## Locations

Non-secret location settings live in
[`config/locations.json`](config/locations.json). The supplied profiles are:

- `demo`: sanitized offline fixture, no credentials required
- `atlanta`: location 11934, channel 4685, order type 4723
- `nyc`: location 11526, channel 4685, order type 4723

Select a location by profile name; do not edit Python files or switch location
IDs in `.env`. See [OPERATIONS.md](OPERATIONS.md) before adding a profile.

## Run results

Complete runs are written below:

```text
runs/<location>/<UTC timestamp>/
  manifest.json
  summary.txt
  reconciled_mapping.xlsx
  plu_results.csv
  plu_review.csv
  flattened_menu.csv
  flattened_menu.json
```

`plu_results.csv` contains every processed Aloha row. `plu_review.csv`
contains only unsafe/manual-review rows.
`flattened_menu.csv` contains one row per current menu occurrence, so repeated
combo paths are preserved. The manifest records the location context,
snapshot/generation metadata, source-workbook hash, artifact hashes, status
counts, and tool version.

Always share the complete run directory—not a workbook copied from a different
run.

Generated data, company workbooks, API responses, caches, and credentials are
ignored by Git.

## Exit codes

| Code | Meaning |
|---:|---|
| `0` | Completed and no manual-review result remains |
| `1` | Configuration, authentication, API, file, or validation failure |
| `2` | Completed successfully, but one or more results require review |

In PowerShell, inspect the most recent exit code with:

```powershell
$LASTEXITCODE
```

## Tests

From `plu_matcher`:

```powershell
python -m pytest
```

From the repository root:

```powershell
python -m pytest .\plu_matcher\tests
```

## Handoff documentation

- [OPERATIONS.md](OPERATIONS.md): routine runs, profiles, and artifact handling
- [STATUS_REFERENCE.md](STATUS_REFERENCE.md): reconciliation and path statuses
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md): common failures and recovery
- [ARCHITECTURE.md](ARCHITECTURE.md): data flow, boundaries, and components
- [FUTURE_WORK.md](FUTURE_WORK.md): deliberately deferred capabilities
